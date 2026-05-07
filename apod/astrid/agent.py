"""
AstridAgent - the core ToolCallingNode.

This replaces the hand-rolled agentic loop in chat.py.
Vellum handles:
  - The LLM call (via their inference API)
  - Tool schema generation (from function signatures)
  - The iteration loop (up to max_prompt_iterations)
  - Execution tracing (visible in Vellum dashboard)

We just hand it the system prompt, the tools, and the chat history.
"""

from pathlib import Path
from typing import List

from vellum import (
    ChatMessage,
    ChatMessagePromptBlock,
    PlainTextPromptBlock,
    PromptParameters,
    RichTextPromptBlock,
    VariablePromptBlock,
)
from vellum.workflows.nodes.displayable.tool_calling_node.node import ToolCallingNode

from .inputs import Inputs
from .tools import (
    get_celestial_bodies,
    get_todays_apod,
    get_visible_tonight,
    lookup_jpl_horizons,
    lookup_simbad,
)

# Load system prompt once at import time
_SKILL_MD = Path(__file__).resolve().parent.parent.parent / 'skill' / 'SKILL.md'
SYSTEM_PROMPT = _SKILL_MD.read_text()


class AstridAgent(ToolCallingNode):
    ml_model = "bfba1721-9299-4627-bbf6-b0192be66158"  # claude-sonnet-4-6 (Vellum workspace UUID)

    prompt_inputs = {
        "chat_history": Inputs.chat_history,
    }

    blocks = [
        ChatMessagePromptBlock(
            chat_role="SYSTEM",
            blocks=[
                RichTextPromptBlock(
                    blocks=[PlainTextPromptBlock(text=SYSTEM_PROMPT)]
                )
            ],
        ),
        VariablePromptBlock(input_variable="chat_history"),
    ]

    parameters = PromptParameters(
        temperature=0.7,
        max_tokens=1024,
    )

    max_prompt_iterations = 6

    functions = [
        get_celestial_bodies,
        get_todays_apod,
        get_visible_tonight,
        lookup_simbad,
        lookup_jpl_horizons,
    ]

    class Outputs(ToolCallingNode.Outputs):
        text: str
        chat_history: List[ChatMessage]
