"""
Astrid Chat Engine - Vellum-powered

Calls the deployed "astrid-agent" workflow on Vellum's platform via execute_workflow().
Every execution traces in app.vellum.ai → workflow sandbox → Executions tab.

Django's job: parse the request, call Vellum, return the response.
The intelligence lives in Vellum.
"""

import json
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from vellum import Vellum
from vellum.client.types import (
    ChatMessageRequest,
    WorkflowRequestChatHistoryInputRequest,
    WorkflowOutputString,
)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Vellum(api_key=os.environ["VELLUM_API_KEY"])
    return _client


def _to_chat_message_requests(messages: list) -> list[ChatMessageRequest]:
    """Convert frontend message format to Vellum ChatMessageRequest objects.

    Frontend sends: [{"role": "user", "content": "..."}, ...]
    """
    role_map = {
        "user": "USER",
        "assistant": "ASSISTANT",
        "system": "SYSTEM",
    }
    return [
        ChatMessageRequest(
            role=role_map.get(msg.get("role", "user"), "USER"),
            text=msg.get("content", ""),
        )
        for msg in messages
    ]


@csrf_exempt
@require_POST
def chat_view(request):
    """
    POST /api/chat/
    Body: { "messages": [{ "role": "user", "content": "What's visible tonight?" }] }
    Returns: { "response": "..." }
    """
    try:
        body = json.loads(request.body)
        messages = body.get("messages", [])

        if not messages:
            return JsonResponse({"error": "No messages provided"}, status=400)

        chat_history = _to_chat_message_requests(messages)

        result = _get_client().execute_workflow(
            workflow_deployment_name="astrid-agent",
            inputs=[
                WorkflowRequestChatHistoryInputRequest(
                    name="chat_history",
                    value=chat_history,
                )
            ],
        )

        # Find the "response" output in the result
        for output in result.data.outputs:
            if output.name == "response" and isinstance(output, WorkflowOutputString):
                return JsonResponse({"response": output.value})

        return JsonResponse(
            {"error": "No response output found in workflow result"},
            status=500,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
