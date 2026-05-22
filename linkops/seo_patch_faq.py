"""Deterministic paste-ready FAQ answers and manual-review routing for SEO patches."""

from __future__ import annotations

import re

from linkops.content_optimization_model import ContentOptimizationReport
from linkops.content_optimizer import (
    apply_brand_capitalization,
    capitalize_brand,
    extract_comparison_entities,
    is_comparison_query,
)
from linkops.gsc_intent import INTENT_REVIEW

# Must never appear under "## Paste-Ready Changes" in Markdown output.
PASTE_READY_FORBIDDEN_SUBSTRINGS = (
    "add a concise answer after editorial review",
    "todo",
    "placeholder",
    "fill in later",
    "editorial review needed",
)

_PRICING_TERMS = re.compile(
    r"\b(cost|price|pricing|plan|plans|free|paid|per\s+user|monthly|annually)\b",
    re.IGNORECASE,
)

_NUMBER_CLAIM = re.compile(
    r"\$\s*\d|(?:\d+\s*(?:%|percent))|(?:\b\d+\s*/\s*month)|(?:\b\d+\s+users?\b)",
    re.IGNORECASE,
)


def is_pricing_or_current_data_question(question: str) -> bool:
    """True when the FAQ should not receive a paste-ready answer without verification."""
    return bool(_PRICING_TERMS.search(question))


def manual_review_reason(question: str) -> str:
    """Human-readable reason for skipping paste-ready FAQ."""
    ql = question.lower()
    if is_pricing_or_current_data_question(question):
        return (
            f'Pricing-related FAQ skipped: "{question}" because current pricing '
            "should be verified before publishing."
        )
    if "best alternative" in ql:
        return (
            f'Alternative-related FAQ needs editorial review: "{question}" '
            "if no safe internal comparison target is available."
        )
    return f'FAQ skipped for manual review: "{question}".'


def _product_from_question(question: str, report: ContentOptimizationReport) -> str:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9.]*", question)
    for tok in tokens:
        branded = capitalize_brand(tok)
        if branded != tok.title() or tok.lower() in {"webex", "clickup", "trello", "zoom", "slack"}:
            return branded
    title = report.target_url.rstrip("/").split("/")[-1].replace("-", " ")
    first = title.split()[0] if title else "this tool"
    return capitalize_brand(first)


def _review_alternative_answer(product: str) -> str:
    return (
        f"Small businesses that find {product} too complex may also compare Zoom, Google Meet, "
        f"Microsoft Teams, and other video meeting tools. The best alternative depends on whether "
        f"the team needs simple meetings, business calling, webinars, or deeper Microsoft or "
        f"Google Workspace integration."
    )


def _comparison_answer(question: str, keyword: str, query_intent: str) -> str | None:
    entities = extract_comparison_entities(keyword)
    if not entities:
        return None
    left, right = entities
    ql = question.lower()
    if "better than" in ql or "better for small teams" in ql:
        return (
            f"Neither {left} nor {right} is better for every small team. {left} often fits teams "
            f"that want flexible views and deeper customization. {right} often fits teams that "
            f"want a simpler board-style workflow. Compare setup effort, daily workflow, and cost "
            f"comfort before switching."
        )
    if "easier" in ql:
        return (
            f"Ease of use depends on how your team works. {right} is often quicker to learn for "
            f"simple task boards, while {left} can feel heavier at first but offers more structure "
            f"for growing teams. Run a short pilot with real tasks before committing."
        )
    if "main difference" in ql:
        return (
            f"The main difference is scope: {left} supports broader work management with tasks, "
            f"docs, and goals in one place, while {right} focuses on visual boards and cards. "
            f"Choose based on whether the team needs a full workspace or a lightweight tracker."
        )
    if "should a small business use" in ql:
        return (
            f"A small business should use {left} when it needs flexible projects, docs, and goals "
            f"in one system. It should use {right} when it wants a simple, visual way to track "
            f"work without heavy setup. Many teams outgrow bare boards as process complexity grows."
        )
    return None


def _topic_answer(question: str, topic: str) -> str | None:
    ql = question.lower()
    if topic == "collaboration":
        if "best collaboration tools" in ql:
            return (
                "Strong collaboration tools for small teams combine messaging, file sharing, "
                "task visibility, and light coordination. The best fit depends on whether the "
                "team is remote, hybrid, or mostly in-office."
            )
        if "look for" in ql:
            return (
                "Small teams should look for easy onboarding, clear permissions, reliable notifications, "
                "and integrations with email or chat tools they already use."
            )
        if "need collaboration" in ql:
            return (
                "Most small teams benefit from some collaboration tooling once work spans more than "
                "one person or one inbox. Even lean teams gain from shared files and clear task ownership."
            )
        if "easiest" in ql:
            return (
                "The easiest collaboration tool is usually the one the team already knows—often Slack, "
                "Microsoft Teams, or a simple shared workspace—rather than the most feature-rich option."
            )
        if "difference between collaboration" in ql:
            return (
                "Collaboration tools focus on working together on shared work—files, tasks, and projects. "
                "Communication tools focus on meetings and messaging. Many products blend both; choose "
                "based on whether the pain is coordination or conversation."
            )
    if topic == "project_management":
        if "best project management" in ql:
            return (
                "Good project management software for small teams clarifies who owns each task, "
                "what is due next, and how work rolls up to a shared goal without heavy admin."
            )
        if "look for" in ql:
            return (
                "Look for simple boards or lists, due dates, assignees, comments, and reporting that "
                "matches how the team actually plans work—not enterprise features you will not use."
            )
        if "need project management" in ql:
            return (
                "Teams that miss deadlines, lose tasks in email, or juggle multiple clients usually "
                "benefit from lightweight project management even with fewer than ten people."
            )
        if "easiest" in ql:
            return (
                "The easiest tool is often a familiar board-style app with minimal configuration. "
                "Pilot one real client project before rolling it out site-wide."
            )
        if "difference between project management tools" in ql:
            return (
                "Project management tools coordinate projects and timelines; project management "
                "software usually adds workflows, permissions, and reporting in one product."
            )
    return None


def generate_safe_faq_answer(
    question: str,
    report: ContentOptimizationReport,
    *,
    topic: str = "",
) -> str | None:
    """Return a paste-ready FAQ answer, or None if the question must be manual-only."""
    q = apply_brand_capitalization(question.strip())
    if is_pricing_or_current_data_question(q):
        return None

    ql = q.lower()
    product = _product_from_question(q, report)

    if report.query_intent == INTENT_REVIEW:
        if "best alternative" in ql:
            return _review_alternative_answer(product)
        if "worth it" in ql:
            return (
                f"Whether {product} is worth it depends on how often the team uses video meetings, "
                f"whether calling features matter, and how it compares with tools the business "
                f"already pays for. Compare core features and admin effort—not list price alone."
            )
        if "video meeting" in ql or "calling" in ql:
            return (
                f"{product} can suit small businesses that rely on video meetings and calling, "
                f"especially teams that want one platform for meetings and business phone features. "
                f"Confirm licensing, admin setup, and integrations match how the team already works."
            )
        if "good for small business" in ql:
            return (
                f"{product} can work for small businesses when its meeting, calling, and admin "
                f"capabilities match day-to-day needs. Compare it with familiar options such as "
                f"Zoom, Google Meet, or Microsoft Teams before switching."
            )

    if is_comparison_query(report.target_keyword, report.query_intent):
        ans = _comparison_answer(q, report.target_keyword, report.query_intent)
        if ans:
            return ans

    if topic:
        ans = _topic_answer(q, topic)
        if ans:
            return ans

    if ql.startswith("what are the best") or ql.startswith("what is the best"):
        phrase = report.target_keyword.strip()
        return (
            f"Good options for «{phrase}» depend on team size, budget comfort, and tools you "
            f"already use. Compare onboarding effort, daily workflow fit, and support needs—not "
            f"feature count alone."
        )
    if "who is" in ql and "best for" in ql:
        return (
            "This type of page is best for small teams comparing practical options before they "
            "commit to a new tool. Readers should leave with clear tradeoffs, not a single "
            "one-size-fits-all pick."
        )
    if "consider before choosing" in ql:
        return (
            "Before choosing, list must-have features, team size, integrations with email or chat, "
            "and how much admin time you can spend on setup and training."
        )

    return None


def answer_is_paste_safe(answer: str) -> bool:
    """Reject answers that contain banned placeholder language or unsafe numeric claims."""
    lower = answer.lower()
    if any(b in lower for b in PASTE_READY_FORBIDDEN_SUBSTRINGS):
        return False
    if _NUMBER_CLAIM.search(answer):
        return False
    return True
