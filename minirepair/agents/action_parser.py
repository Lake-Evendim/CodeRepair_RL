"""Extract structured JSON actions from LLM free-text output."""

from __future__ import annotations

import re

from minirepair.env.action_schema import Action, ParseError, parse_action


def extract_json_candidates(text: str) -> list[str]:
    """Extract JSON object candidates from LLM output.

    Handles: raw JSON, markdown code blocks (```json ... ``` / ``` ... ```),
    and JSON embedded in surrounding thought text.
    """
    candidates: list[str] = []

    # 1. Try markdown code blocks first (highest priority)
    code_block_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)```", re.DOTALL)
    for match in code_block_pattern.finditer(text):
        block = match.group(1).strip()
        if block.startswith("{"):
            candidates.append(block)

    # 2. Try finding bare JSON objects with brace matching
    for i, ch in enumerate(text):
        if ch == "{":
            depth = 0
            for j in range(i, len(text)):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                if depth == 0:
                    candidates.append(text[i : j + 1])
                    break

    return candidates


def extract_action_from_llm_output(text: str) -> Action | ParseError:
    """Extract an Action from LLM output text.

    Tries multiple JSON candidates and returns the first valid Action.
    Falls back to ParseError if no valid action is found.
    """
    candidates = extract_json_candidates(text)

    last_error: ParseError | None = None
    for candidate in candidates:
        result = parse_action(candidate)
        if isinstance(result, Action):
            return result
        last_error = result

    if last_error is not None:
        return last_error

    return ParseError(error="No JSON object found in LLM output", raw_input=text[:500])
