"""
Astrid Chat Engine - Vellum-powered

Calls the deployed "astrid-agent" workflow on Vellum's platform via execute_workflow().
Every execution traces in app.vellum.ai → workflow sandbox → Executions tab.

Observability:
  - external_id: a per-request UUID passed to Vellum, linking Django logs to Vellum traces
  - execution_id: Vellum's trace ID, logged alongside the external_id for cross-service correlation
  - Structured logging via Django's logger - searchable in Railway's log stream

Django's job: parse the request, call Vellum, return the response.
The intelligence lives in Vellum.
"""

import json
import logging
import os
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from vellum import Vellum
from vellum.client.types import (
    ChatMessageRequest,
    WorkflowOutputString,
    WorkflowRequestChatHistoryInputRequest,
)

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Vellum(api_key=os.environ["VELLUM_API_KEY"])
    return _client


def _to_chat_message_requests(messages: list) -> list[ChatMessageRequest]:
    """Convert frontend message format to Vellum ChatMessageRequest objects."""
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
    Returns: { "response": "...", "trace_id": "<vellum_execution_id>" }
    """
    # Correlation ID: ties this Django request to its Vellum trace
    external_id = str(uuid.uuid4())

    try:
        body = json.loads(request.body)
        messages = body.get("messages", [])

        if not messages:
            return JsonResponse({"error": "No messages provided"}, status=400)

        chat_history = _to_chat_message_requests(messages)
        last_message = messages[-1].get("content", "")[:100]

        logger.info(
            "astrid.request",
            extra={
                "external_id": external_id,
                "message_count": len(messages),
                "last_message_preview": last_message,
            },
        )

        result = _get_client().execute_workflow(
            workflow_deployment_name="astrid-agent",
            external_id=external_id,
            inputs=[
                WorkflowRequestChatHistoryInputRequest(
                    name="chat_history",
                    value=chat_history,
                )
            ],
        )

        logger.info(
            "astrid.response",
            extra={
                "external_id": external_id,
                "execution_id": result.execution_id,
                "output_count": len(result.data.outputs),
            },
        )

        for output in result.data.outputs:
            if output.name == "response" and isinstance(output, WorkflowOutputString):
                return JsonResponse({
                    "response": output.value,
                    "trace_id": result.execution_id,
                })

        return JsonResponse(
            {"error": "No response output found in workflow result"},
            status=500,
        )

    except json.JSONDecodeError:
        logger.error("astrid.error", extra={"external_id": external_id, "error": "invalid_json"})
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(
            "astrid.error",
            extra={"external_id": external_id, "error": str(e)},
            exc_info=True,
        )
        return JsonResponse({"error": str(e)}, status=500)
