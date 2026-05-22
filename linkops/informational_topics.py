"""Informational and mixed project/task topic detection and paste-ready templates."""

from __future__ import annotations

import re

from linkops.gsc_intent import INTENT_INFORMATIONAL

_MIXED_PROJECT_TASK_RE = re.compile(
    r"(?i)"
    r"(?:project\s+(?:and|&)\s+task\s+management"
    r"|task\s+(?:and|&)\s+project\s+management"
    r"|project\s+management\s+and\s+task\s+management"
    r"|task\s+management\s+and\s+project\s+management"
    r"|project\s+(?:vs\.?|versus)\s+task\s+management"
    r"|task\s+(?:vs\.?|versus)\s+project\s+management)"
)

_PRODUCT_CATEGORY_RE = re.compile(
    r"\b(tools|software|apps|platforms|suites|solutions)\b",
    re.IGNORECASE,
)

MIXED_PROJECT_TASK_INTRO = (
    "Small teams often need both project management and task management: project management "
    "helps organize larger goals, while task management helps clarify the individual actions, "
    "owners, and deadlines needed to complete the work."
)

MIXED_PROJECT_TASK_HEADINGS: list[str] = [
    "Project and Task Management: What Small Teams Should Know",
    "Project Management vs Task Management for Small Teams",
    "How Project and Task Management Work Together",
]

MIXED_PROJECT_TASK_FAQ: list[str] = [
    "What is the difference between project management and task management?",
    "Do small teams need both project management and task management?",
    "Can one tool handle both projects and tasks?",
    "When should a small team use task management instead of project management?",
    "What should small teams look for in project and task management tools?",
]

TASK_VS_PROJECT_SLUG = "task-management-vs-project-management"
TASK_VS_PROJECT_URL = "https://worktoolslab.com/task-management-vs-project-management/"


def is_mixed_project_task_topic(keyword: str) -> bool:
    """True for informational phrases about project vs task management together."""
    return bool(_MIXED_PROJECT_TASK_RE.search(keyword.strip()))


def is_unnatural_best_category(keyword: str) -> bool:
    """Keywords that should not use 'best [keyword]' product-roundup templates."""
    kw = keyword.strip()
    if not kw:
        return False
    if kw.lower().startswith("best "):
        return False
    if is_mixed_project_task_topic(kw):
        return True
    lower = kw.lower()
    if " and " in lower and "management" in lower and not _PRODUCT_CATEGORY_RE.search(kw):
        return True
    if (
        len(kw.split()) >= 3
        and "management" in lower
        and not _PRODUCT_CATEGORY_RE.search(kw)
        and not re.search(r"\bvs\.?\b|\bversus\b", lower)
    ):
        return True
    return False


def should_skip_best_faq_templates(keyword: str, query_intent: str) -> bool:
    """Skip generic 'What is the best X' / 'Who is Best X best for' FAQ stems."""
    if is_mixed_project_task_topic(keyword) or is_unnatural_best_category(keyword):
        return True
    if query_intent == INTENT_INFORMATIONAL and is_unnatural_best_category(keyword):
        return True
    if query_intent == INTENT_INFORMATIONAL and not _PRODUCT_CATEGORY_RE.search(keyword):
        if not keyword.strip().lower().startswith("best "):
            return True
    return False


def mixed_project_task_faq_answer(question: str) -> str | None:
    """Deterministic paste-ready answers for mixed project/task FAQ questions."""
    ql = question.lower()
    if "difference between project management and task management" in ql:
        return (
            "Project management focuses on planning and coordinating larger goals, timelines, "
            "milestones, and team responsibilities. Task management focuses on the individual "
            "actions, owners, due dates, and status updates needed to complete that work."
        )
    if "need both project management and task management" in ql:
        return (
            "Many small teams need both. Project management helps the team see the bigger goal, "
            "while task management helps everyone understand the next actions, responsibilities, "
            "and deadlines."
        )
    if "one tool handle both projects and tasks" in ql:
        return (
            "Yes. Many tools can support both project management and task management if they offer "
            "task ownership, due dates, project views, status tracking, and enough structure for "
            "the team's workflow."
        )
    if "task management instead of project management" in ql:
        return (
            "A small team should focus on task management when the main problem is daily execution, "
            "unclear ownership, missed follow-ups, or scattered to-do lists rather than complex "
            "project planning."
        )
    if "look for in project and task management tools" in ql:
        return (
            "Small teams should look for clear task ownership, simple due dates, project views, "
            "collaboration features, workflow visibility, and an interface the team can use "
            "consistently."
        )
    return None


def related_task_vs_project_link_note(catalog_urls: list[str], target_url: str) -> str | None:
    """Optional internal link note when a related comparison article exists in cache."""
    target_norm = target_url.rstrip("/").lower()
    for url in catalog_urls:
        norm = url.rstrip("/").lower()
        if TASK_VS_PROJECT_SLUG in norm and norm != target_norm:
            return (
                "Consider linking the phrase task management vs project management to "
                f"{url if url.endswith('/') else url + '/'} if it fits naturally."
            )
    if any(TASK_VS_PROJECT_SLUG in u for u in catalog_urls):
        if TASK_VS_PROJECT_URL.rstrip("/").lower() != target_norm:
            return (
                "Consider linking the phrase task management vs project management to "
                f"{TASK_VS_PROJECT_URL} if it fits naturally."
            )
    return None
