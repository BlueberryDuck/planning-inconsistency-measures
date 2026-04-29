"""PDDL pipeline: Preprocess (strip costs) and Translate (plasp -> TranslatedProblem).

Preprocess removes action-cost elements that plasp rejects but that don't
affect reachability/mutex/sequencing measures. Translate runs plasp over a
preprocessed PDDL pair and yields a context-managed `TranslatedProblem`
holding the resulting `.lp` path and its provenance flag.
"""

import logging
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranslatedProblem:
    """An ASP problem ready for Brave reasoning.

    Either the result of plasp Translate (`needs_bridge=True`, `_cleanup` set
    to remove the temp dir) or a hand-written `.lp` test scenario
    (`needs_bridge=False`, `_cleanup=None`). Used as a context manager so
    cleanup is hard to forget.
    """

    path: Path
    needs_bridge: bool = False
    translate_s: float = 0.0
    _cleanup: Callable[[], None] | None = field(default=None, repr=False)

    def __enter__(self) -> "TranslatedProblem":
        return self

    def __exit__(self, *exc: object) -> None:
        if self._cleanup is not None:
            self._cleanup()


def translate_pddl(
    domain_path: Path | str, problem_path: Path | str
) -> TranslatedProblem:
    """Run plasp Translate over a PDDL pair; return a context-managed TranslatedProblem.

    Strips action costs first, runs plasp in a temp dir, and wires temp-dir
    removal as the returned TranslatedProblem's cleanup. Raises RuntimeError
    on plasp failure; the temp dir is removed before the exception propagates.

    Use as a context manager so cleanup is hard to forget:
        with translate_pddl(domain, problem) as translated:
            ...
    """
    domain_path = Path(domain_path)
    problem_path = Path(problem_path)
    logger.info(
        "Translating PDDL via plasp: %s + %s", domain_path.name, problem_path.name
    )

    t0 = time.monotonic()
    domain_text = strip_costs(domain_path.read_text())
    problem_text = strip_costs(problem_path.read_text())

    tmpdir = tempfile.mkdtemp()
    tmp = Path(tmpdir)
    try:
        (tmp / "domain.pddl").write_text(domain_text)
        (tmp / "problem.pddl").write_text(problem_text)

        result = subprocess.run(
            ["plasp", "translate", str(tmp / "domain.pddl"), str(tmp / "problem.pddl")],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"plasp translation failed for {domain_path} + {problem_path}: "
                f"{result.stderr.strip()}"
            )

        plasp_lp = tmp / "instance.lp"
        plasp_lp.write_text(result.stdout)
    except BaseException:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise

    return TranslatedProblem(
        path=plasp_lp,
        needs_bridge=True,
        translate_s=time.monotonic() - t0,
        _cleanup=lambda: shutil.rmtree(tmpdir, ignore_errors=True),
    )


_KEYWORD_RULES: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (kw, re.compile(rf"\(\s*{re.escape(kw)}\b", re.IGNORECASE))
    for kw in (":functions", ":metric", "increase", "decrease")
)

_FUNCTION_ASSIGNMENT_RULE: tuple[str, re.Pattern[str]] = (
    "function-assignments",
    re.compile(r"\(\s*=\s*\("),
)


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
    stripped: list[str] = []

    prev = text
    text = re.sub(r":action-costs\s*", "", text)
    if text != prev:
        stripped.append(":action-costs")

    for label, opener in (*_KEYWORD_RULES, _FUNCTION_ASSIGNMENT_RULE):
        prev = text
        text = _splice_balanced_sexpr(text, opener)
        if text != prev:
            stripped.append(label)

    if stripped:
        logger.debug("Stripped cost elements: %s", ", ".join(stripped))

    return text


def _splice_balanced_sexpr(text: str, opener: re.Pattern[str]) -> str:
    """Splice out every S-expression whose opening matches `opener`.

    The match must include the leading `(`; this function then walks
    forward to the balancing `)` and removes the whole span. On unmatched
    parens, the remainder of the text is preserved verbatim — load-bearing
    for malformed PDDL fragments encountered during preprocessing.
    """
    out: list[str] = []
    i = 0
    while i < len(text):
        match = opener.search(text, i)
        if not match:
            out.append(text[i:])
            break

        out.append(text[i : match.start()])
        depth = 0
        j = match.start()
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
            out.append(text[match.start() :])
            i = len(text)

    return "".join(out)
