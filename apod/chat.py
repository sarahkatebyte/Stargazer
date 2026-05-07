"""
Astrid Chat Engine - Vellum-powered

The agentic loop now runs as a Vellum Workflow:
  - LLM calls go through Vellum's inference API
  - Tool schemas are auto-generated from function signatures
  - Every conversation is traced in the Vellum dashboard
  - Model swaps happen in Vellum, not in this code

Django's job here is simple: parse the request, run the workflow, return the response.
"""

import json
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from vellum import ChatMessage, StringChatMessageContent

from .astrid import AstridWorkflow
from .astrid.inputs import Inputs


def _to_chat_messages(messages: list) -> list[ChatMessage]:
    """Convert frontend message format to Vellum ChatMessage objects.

    Frontend sends: [{"role": "user", "content": "..."}, ...]
    Vellum expects: ChatMessage(role="USER", content="...")
    """
    role_map = {
        "user": "USER",
        "assistant": "ASSISTANT",
        "system": "SYSTEM",
    }
    return [
        ChatMessage(
            role=role_map.get(msg.get("role", "user"), "USER"),
            content=StringChatMessageContent(value=msg.get("content", "")),
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

        chat_history = _to_chat_messages(messages)
        workflow = AstridWorkflow()
        event = workflow.run(inputs=Inputs(chat_history=chat_history))

        if event.name == "workflow.execution.fulfilled":
            return JsonResponse({
                "response": event.outputs.response,
            })
        else:
            return JsonResponse(
                {"error": "Workflow execution failed"},
                status=500,
            )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
