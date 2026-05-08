"""
Tool execution endpoints for Vellum's hosted workflow runner.

When Vellum executes the AstridWorkflow on their servers, it calls these
endpoints to run the tool functions. Django runs the tool scripts as subprocesses
and returns the results.

Each endpoint: POST /api/tools/<tool_name>/
Body: JSON with the tool's input arguments
Response: JSON with the tool's output (raw string from the script)
"""

import json
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

SCRIPTS_DIR = settings.BASE_DIR / 'skill' / 'scripts'

# Allowlist of permitted tool names — prevents path traversal via tool_name
ALLOWED_TOOLS = {
    'get_celestial_bodies',
    'get_todays_apod',
    'get_visible_tonight',
    'lookup_simbad',
    'lookup_jpl_horizons',
}


def _run_script(tool_name: str, tool_input: dict) -> str:
    """Execute a tool script as a subprocess and return its output."""
    if tool_name not in ALLOWED_TOOLS:
        return json.dumps({'error': f'Unknown tool: {tool_name}'})

    script_path = SCRIPTS_DIR / f'{tool_name}.py'

    if not script_path.exists():
        return json.dumps({'error': f'Tool script not found: {tool_name}'})

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), json.dumps(tool_input)],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(SCRIPTS_DIR),
        )
        if result.returncode != 0:
            return json.dumps({
                'error': f'Tool {tool_name} failed',
                'details': result.stderr[:500] if result.stderr else 'Unknown error'
            })
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return json.dumps({'error': f'Tool {tool_name} timed out after 15 seconds'})
    except Exception as e:
        return json.dumps({'error': f'Tool execution error: {str(e)}'})


def _tool_endpoint(tool_name: str):
    """Factory that creates a view function for a given tool."""
    @csrf_exempt
    @require_POST
    def view(request):
        try:
            tool_input = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            tool_input = {}

        output = _run_script(tool_name, tool_input)
        return JsonResponse({'output': output})

    view.__name__ = f'tool_{tool_name}'
    return view


get_celestial_bodies_view = _tool_endpoint('get_celestial_bodies')
get_todays_apod_view = _tool_endpoint('get_todays_apod')
get_visible_tonight_view = _tool_endpoint('get_visible_tonight')
lookup_simbad_view = _tool_endpoint('lookup_simbad')
lookup_jpl_horizons_view = _tool_endpoint('lookup_jpl_horizons')
