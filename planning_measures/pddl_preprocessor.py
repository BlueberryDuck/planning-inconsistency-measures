"""PDDL preprocessor that strips action-cost elements.

Many IPC benchmark domains declare (:functions (total-cost) - number) and
use (increase (total-cost) N) in effects. These are irrelevant to
inconsistency measure computation but cause plasp to reject the file.
This module removes cost-related elements so plasp can parse the domain.
"""

import logging
import re

logger = logging.getLogger(__name__)


def strip_costs(pddl_text: str) -> str:
    """Remove action-cost elements from PDDL text.

    Strips:
      - :action-costs from :requirements
      - (:functions ...) section (single or multi-line)
      - (increase ...) and (decrease ...) effect terms
      - All numeric function value assignments, e.g. (= (total-cost) 0)
      - (:metric ...) specification
    """
    text = pddl_text
    stripped = []

    prev = text
    text = re.sub(r":action-costs\s*", "", text)
    if text != prev:
        stripped.append(":action-costs")

    for keyword in (":functions", ":metric", "increase", "decrease"):
        prev = text
        text = _remove_sexp(text, keyword)
        if text != prev:
            stripped.append(keyword)

    prev = text
    text = _remove_function_assignments(text)
    if text != prev:
        stripped.append("function-assignments")

    if stripped:
        logger.debug("Stripped cost elements: %s", ", ".join(stripped))

    return text


def _remove_function_assignments(text: str) -> str:
    """Remove (= (function-name ...) value) assignments from PDDL text.

    Matches patterns like (= (total-cost) 0) or (= (road-length c1 c2) 22).
    """
    result = []
    i = 0
    while i < len(text):
        # Look for (= (
        match = re.search(r"\(\s*=\s*\(", text[i:])
        if not match:
            result.append(text[i:])
            break

        # Add text before the match
        result.append(text[i : i + match.start()])

        # Find matching closing paren for the outer (= ...)
        pos = i + match.start()
        depth = 0
        j = pos
        while j < len(text):
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    i = j + 1
                    break
            j += 1
        else:
            result.append(text[pos:])
            i = len(text)

    return "".join(result)


def _remove_sexp(text: str, keyword: str) -> str:
    """Remove all S-expressions starting with (keyword ...) from text.

    Handles nested parentheses correctly.
    """
    result = []
    i = 0
    while i < len(text):
        # Look for opening paren followed by keyword
        match = re.search(rf"\(\s*{re.escape(keyword)}\b", text[i:], re.IGNORECASE)
        if not match:
            result.append(text[i:])
            break

        # Add text before the match
        result.append(text[i : i + match.start()])

        # Find matching closing paren
        pos = i + match.start()
        depth = 0
        j = pos
        while j < len(text):
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    # Skip this entire S-expression
                    i = j + 1
                    break
            j += 1
        else:
            # Unmatched parens, keep remainder as-is
            result.append(text[pos:])
            i = len(text)

    return "".join(result)
