"""Claude extraction call: turn raw meeting note text into structured action items.

The prompt and tool schema below are copied verbatim from CLAUDE.md and must not
be modified without the user's explicit sign-off.
"""

import anthropic

from config import ANTHROPIC_API_KEY, EXTRACTION_MODEL

EXTRACTION_PROMPT = """Extract action items from this meeting note. For each item, identify the task, who owns it, any due date, and priority.

Rules:
- If no owner is stated, set assignee to "unassigned"
- If no due date is stated, omit due_date
- If the note contains no actionable items, return an empty action_items array and explain why in the flags field
- If the note appears to duplicate an earlier one (same title, same date, near-identical content), flag it in the flags field rather than guessing
- Priority defaults to "normal" unless urgency is explicit
- Only set priority to "urgent" or "high" if the note contains explicit urgency language (e.g. "urgent", "ASAP", "critical", a tight deadline). Otherwise use "normal".
- Always respond by calling the create_action_items tool
- Set flag_type to "none" unless something needs human review, otherwise choose the closest of: possible_duplicate, no_action_items, ambiguous_owner, other

Meeting note:
{{Google_Doc_Text_Content}}"""

CREATE_ACTION_ITEMS_TOOL = {
    "name": "create_action_items",
    "description": "Record the structured action items extracted from a meeting note.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Short task title, imperative form, e.g. 'Send Q3 report to finance'",
                        },
                        "assignee": {
                            "type": "string",
                            "description": "Name of the person responsible, or 'unassigned' if not stated in the note",
                        },
                        "due_date": {
                            "type": "string",
                            "description": "ISO 8601 date (YYYY-MM-DD) if mentioned in the note",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["urgent", "high", "normal", "low"],
                        },
                        "description": {
                            "type": "string",
                            "description": "One or two sentences of context for the task",
                        },
                    },
                    "required": ["title", "assignee", "priority"],
                },
            },
            "flag_type": {
                "type": "string",
                "enum": [
                    "none",
                    "possible_duplicate",
                    "no_action_items",
                    "ambiguous_owner",
                    "other",
                ],
                "description": "Category of concern with this extraction, if any. Use 'none' if nothing needs review.",
            },
            "flags": {
                "type": "string",
                "description": "Human-readable explanation of the concern. Empty string if flag_type is 'none'.",
            },
        },
        "required": ["action_items", "flag_type", "flags"],
    },
}


def extract_action_items(doc_text: str) -> dict:
    """Call claude-haiku-4-5 with the fixed prompt and forced tool call.

    Returns the tool_use input dict: {action_items, flag_type, flags}.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = EXTRACTION_PROMPT.replace("{{Google_Doc_Text_Content}}", doc_text)

    response = client.messages.create(
        model=EXTRACTION_MODEL,
        max_tokens=4096,
        tools=[CREATE_ACTION_ITEMS_TOOL],
        tool_choice={"type": "tool", "name": "create_action_items"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_action_items":
            return block.input

    raise RuntimeError(
        f"Expected a create_action_items tool call, got stop_reason={response.stop_reason!r}"
    )
