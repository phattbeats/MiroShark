"""
Repair orphaned tool messages before they reach the LLM.

The OpenAI chat-completion spec says every {"role": "tool", "tool_call_id": X}
message must be immediately preceded by an {"role": "assistant", "tool_calls":
[{..."id": X...}]} message. OpenAI tolerates violations. MiniMax does not, and
returns "invalid params, tool result's tool id(...) not found (2013)".

CAMEL-AI sometimes loses the assistant turn between rounds. This patch wraps
ScoreBasedContextCreator.create_context: after CAMEL builds the messages array,
we walk it and synthesize a placeholder assistant turn in front of any
orphaned tool messages so the conversation passes MiniMax's validator.

Loaded automatically via a .pth file in site-packages.
"""
from camel.memories.context_creators.score_based import (
    ScoreBasedContextCreator,
)

_original_create_context = ScoreBasedContextCreator.create_context


def _repair_orphan_tool_messages(messages):
    repaired = []
    for msg in messages:
        if msg.get("role") == "tool":
            tool_call_id = msg.get("tool_call_id")
            prev = repaired[-1] if repaired else None
            needs_synth = True
            if prev and prev.get("role") == "assistant":
                tool_calls = prev.get("tool_calls") or []
                if any(
                    tc.get("id") == tool_call_id for tc in tool_calls
                ):
                    needs_synth = False
            if needs_synth and tool_call_id:
                repaired.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": "synthesized_recovery",
                            "arguments": "{}",
                        },
                    }],
                })
        repaired.append(msg)
    return repaired


def _patched_create_context(self, records):
    messages, total_tokens = _original_create_context(self, records)
    return _repair_orphan_tool_messages(messages), total_tokens


ScoreBasedContextCreator.create_context = _patched_create_context