"""
Astrid Chat Engine

This is a mini agent runtime. It does exactly what Vellum's platform does:
1. Accept user messages
2. Send them to Claude with tool definitions
3. When Claude calls a tool, execute it against Stargazer's data
4. Feed results back to Claude
5. Return the synthesized response

The agentic loop: Claude decides WHICH tools to call and in WHAT order.
We just execute and relay. This is the core pattern behind every AI agent
framework - LangChain, CrewAI, Vellum - they all do this loop.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import anthropic

# Load tool definitions and system prompt once at module level
SKILL_DIR = Path(__file__).resolve().parent.parent / 'skill'
SCRIPTS_DIR = SKILL_DIR / 'scripts'

with open(SKILL_DIR / 'TOOLS.json') as f:
    TOOL_DEFINITIONS = json.load(f)

with open(SKILL_DIR / 'SKILL.md') as f:
    SYSTEM_PROMPT = f.read()

# Convert our tool format to Anthropic's format
# The WHY: Anthropic's API expects tools in a specific shape with
# "input_schema" (JSON Schema). Our TOOLS.json uses "parameters".
# This adapter bridges the gap - same pattern as an ORM translating
# your model to SQL.
ANTHROPIC_TOOLS = []
for tool in TOOL_DEFINITIONS:
    anthropic_tool = {
        'name': tool['name'],
        'description': tool['description'],
        'input_schema': tool.get('parameters', {})
    }
    # Tools with no parameters need a valid JSON schema
    if not anthropic_tool['input_schema']:
        anthropic_tool['input_schema'] = {'type': 'object', 'properties': {}}
    ANTHROPIC_TOOLS.append(anthropic_tool)


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Execute a Stargazer tool by running its Python script as a subprocess.

    The WHY: Each tool is a standalone Python script that reads JSON from
    argv and prints JSON to stdout. This is the Unix philosophy -
    small programs that do one thing, communicate via text streams.
    Running as subprocess also isolates failures - if SIMBAD times out,
    it doesn't crash the chat endpoint.
    """
    script_path = SCRIPTS_DIR / f'{tool_name}.py'

    if not script_path.exists():
        return json.dumps({'error': f'Unknown tool: {tool_name}'})

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), json.dumps(tool_input)],
            capture_output=True,
            text=True,
            timeout=15,  # 15 second timeout per tool
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


def run_agent_loop(messages: list, max_turns: int = 6) -> dict:
    """
    The agentic loop. This is the heart of every agent framework.

    1. Send messages to Claude
    2. If Claude responds with text -> done, return it
    3. If Claude responds with tool_use -> execute the tools, append results, go to step 1
    4. Repeat up to max_turns (bounded loop - same pattern as your ingestion agent)

    The WHY behind bounded loops: Without a limit, a confused model could
    call tools forever (costing money and time). Your ingestion agent uses
    8 turns. We use 6 here because chat should feel snappy.
    """
    client = anthropic.Anthropic()  # Reads ANTHROPIC_API_KEY from env

    for turn in range(max_turns):
        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=ANTHROPIC_TOOLS,
            messages=messages,
        )

        # If Claude just wants to talk (no tool calls), we're done
        if response.stop_reason == 'end_turn':
            # Extract text from content blocks
            text_parts = [
                block.text for block in response.content
                if block.type == 'text'
            ]
            return {
                'response': '\n'.join(text_parts),
                'tool_calls': [],
                'turns_used': turn + 1,
            }

        # If Claude wants to use tools, execute them and continue the loop
        if response.stop_reason == 'tool_use':
            # Append Claude's response (with tool_use blocks) to messages
            messages.append({
                'role': 'assistant',
                'content': [block.model_dump() for block in response.content]
            })

            # Execute each tool call and build the results message
            tool_results = []
            tool_calls_made = []

            for block in response.content:
                if block.type == 'tool_use':
                    tool_result = execute_tool(block.name, block.input)
                    tool_results.append({
                        'type': 'tool_result',
                        'tool_use_id': block.id,
                        'content': tool_result,
                    })
                    tool_calls_made.append({
                        'tool': block.name,
                        'input': block.input,
                        'result_preview': tool_result[:200],
                    })

            # Append tool results to messages and loop back
            messages.append({
                'role': 'user',
                'content': tool_results,
            })

    # If we hit max_turns, return whatever we have
    text_parts = [
        block.text for block in response.content
        if block.type == 'text'
    ]
    return {
        'response': '\n'.join(text_parts) if text_parts else "I'm still thinking about that - could you try rephrasing?",
        'tool_calls': [],
        'turns_used': max_turns,
    }


@csrf_exempt
@require_POST
def chat_view(request):
    """
    POST /api/chat/
    Body: { "messages": [{ "role": "user", "content": "What's visible tonight?" }] }

    Returns: { "response": "...", "turns_used": 2 }
    """
    try:
        body = json.loads(request.body)
        messages = body.get('messages', [])

        if not messages:
            return JsonResponse({'error': 'No messages provided'}, status=400)

        result = run_agent_loop(messages)
        return JsonResponse(result)

    except anthropic.AuthenticationError:
        return JsonResponse({'error': 'API key not configured'}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
