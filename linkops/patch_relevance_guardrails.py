"""Deterministic relevance guardrails for paste-ready SEO patch suggestions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from linkops.content_model import ContentItem
from linkops.gsc_intent import (
    INTENT_BROAD_BEST,
    INTENT_COMPARISON,
    INTENT_HOW_TO,
    INTENT_INFORMATIONAL,
    INTENT_REVIEW,
    PAGE_COMPARISON,
    PAGE_GUIDE,
    PAGE_REVIEW,
    PAGE_ROUNDUP,
    detect_gsc_page_type,
    detect_query_intent,
)

_COMPARISON_SPLIT_RE = re.compile(r"\s+vs\.?\s+|\s+versus\s+", re.IGNORECASE)

BRAND_CAPITALIZATION: dict[str, str] = {
    "clickup": "ClickUp",
    "trello": "Trello",
    "asana": "Asana",
    "monday.com": "Monday.com",
    "notion": "Notion",
    "slack": "Slack",
    "zoom": "Zoom",
    "webex": "Webex",
    "microsoft teams": "Microsoft Teams",
    "google meet": "Google Meet",
}
from linkops.informational_topics import (
    MIXED_PROJECT_TASK_FAQ,
    MIXED_PROJECT_TASK_HEADINGS,
    MIXED_PROJECT_TASK_INTRO,
    is_mixed_project_task_topic,
)

_COMPARISON_SIGNAL_RE = re.compile(
    r"\bvs\.?\b|\bversus\b|\bcompare\b|\bcomparison\b",
    re.IGNORECASE,
)

_CONCEPT_VOCAB = frozenset(
    {
        "project",
        "projects",
        "task",
        "tasks",
        "workflow",
        "management",
        "productivity",
        "communication",
        "collaboration",
        "planning",
        "goals",
        "work",
    }
)

def parse_comparison_parts(keyword: str) -> tuple[str, str] | None:
    parts = _COMPARISON_SPLIT_RE.split(keyword.strip(), maxsplit=1)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        return parts[0].strip(), parts[1].strip()
    return None


_BRAND_TERMS = frozenset(BRAND_CAPITALIZATION.keys()) | {
    "teamwork",
    "teamwork.com",
    "monday",
    "notion",
    "basecamp",
    "smartsheet",
    "airtable",
    "jira",
    "linear",
    "hubspot",
    "salesforce",
    "todoist",
}

_VIDEO_MEETING_BLOCK_PHRASES = (
    "video meeting",
    "video meetings",
    "business calling",
    "calling features",
    "google meet",
    "microsoft teams",
    "cisco webex",
)

_VIDEO_MEETING_PRODUCT_MARKERS = (
    "webex",
    "zoom",
    "google meet",
    "microsoft teams",
    "cisco webex",
)

_PM_SOFTWARE_PHRASES = (
    "project management software",
    "best project management software",
    "project management tools for small teams",
    "project management tool for small teams",
)

_PRODUCTIVITY_INTRO = (
    "Good team productivity tools help a small team track tasks, share files, communicate "
    "clearly, coordinate calendars, take notes, and reduce constant switching between apps."
)

_PRODUCTIVITY_FAQ = [
    "What are the best productivity tools for small teams?",
    "What should small teams look for in productivity tools?",
    "Do small teams need separate apps for tasks, docs, and communication?",
    "What is the easiest productivity setup for a small team?",
    "How do productivity tools reduce tool switching for small teams?",
]

_PRODUCTIVITY_HEADINGS = [
    "Best Productivity Tools for Small Teams: What to Compare",
    "How to Choose Team Productivity Tools for a Small Team",
    "Task Tracking, Communication, and Docs in One Productivity Stack",
]

_CONCEPT_COMPARISON_FAQ = [
    "What is the difference between a project and a task?",
    "Can a task be part of a project?",
    "Do small teams need project management or task management?",
    "When should a small team focus on tasks instead of full project planning?",
    "What should small teams look for when balancing projects and tasks?",
]

_CONCEPT_COMPARISON_HEADINGS = [
    "Project vs Task: What Small Teams Should Know",
    "What Is the Difference Between a Project and a Task?",
    "Project Management vs Task Management for Small Teams",
]

_CONCEPT_COMPARISON_INTRO = (
    "A project is a larger body of work with a goal, timeline, and coordinated tasks. "
    "A task is a single actionable step with an owner and due date. Small teams need "
    "both project-level clarity and task-level follow-through to avoid scattered work."
)

_TRELLO_FREELANCER_REVIEW_FAQ = [
    "Is Trello good for freelancers?",
    "Is Trello good for tracking client work on a board?",
    "What are the best Trello alternatives for freelancers?",
    "How do freelancers use Trello for client projects and deadlines?",
    "Is Trello worth it for a solo freelancer or micro-team?",
]

_TRELLO_FREELANCER_REVIEW_INTRO = (
    "A Trello review for freelancers should focus on Kanban boards, client project visibility, "
    "simple task tracking, and whether Trello stays lightweight enough for solo or small "
    "freelance workflows."
)

_GENERIC_REVIEW_FAQ = [
    "Is {product} good for small businesses?",
    "Is {product} worth it for a small business?",
    "What are the best alternatives to {product} for small businesses?",
    "What should small businesses look for in {product}?",
    "How much does {product} cost for a small team?",
]

_FAKE_PRODUCT_COMPARISON_RE = re.compile(
    r"^is\s+\w+\s+better\s+than\s+\w+\??$|^is\s+\w+\s+easier\s+to\s+use\s+than\s+\w+\??$",
    re.IGNORECASE,
)


@dataclass
class PatchContext:
    keyword: str
    comparison_kind: str  # none | software_comparison | concept_comparison
    page_kind: str  # review | roundup | guide | comparison | informational | unknown
    topic: str
    product_name: str = ""
    force_manual_review: bool = False
    manual_review_reason: str = ""
    future_article_title: str = ""
    allow_video_meeting_templates: bool = False
    allow_pm_software_wording: bool = True


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _is_concept_side(term: str) -> bool:
    raw = term.lower().strip().rstrip(".")
    if raw.replace(".com", "") in _BRAND_TERMS or raw in _BRAND_TERMS:
        return False
    if raw in ("teamwork", "teamwork.com"):
        return False
    tokens = re.findall(r"[a-z]+", raw)
    if not tokens:
        return False
    return all(t in _CONCEPT_VOCAB for t in tokens)


def is_concept_comparison(keyword: str) -> bool:
    """True when a vs/versus query compares concepts, not software products."""
    kw = keyword.strip()
    if is_mixed_project_task_topic(kw) and not _COMPARISON_SIGNAL_RE.search(kw):
        return False
    if not _COMPARISON_SIGNAL_RE.search(kw):
        return False
    parts = parse_comparison_parts(kw)
    if not parts:
        return False
    left, right = parts
    return _is_concept_side(left) and _is_concept_side(right)


def is_software_comparison(keyword: str, query_intent: str = "") -> bool:
    """True for branded tool-vs-tool comparisons (ClickUp vs Trello, Monday.com vs Asana)."""
    if is_concept_comparison(keyword):
        return False
    if query_intent == INTENT_COMPARISON:
        return True
    if _COMPARISON_SIGNAL_RE.search(keyword):
        parts = parse_comparison_parts(keyword)
        if parts and not (_is_concept_side(parts[0]) and _is_concept_side(parts[1])):
            return True
    return False


def is_teamwork_vs_asana_query(keyword: str) -> bool:
    parts = parse_comparison_parts(keyword)
    if not parts:
        return False
    left, right = _normalize(parts[0]), _normalize(parts[1])
    return ("teamwork" in left or left == "teamwork") and "asana" in right


def is_misrouted_branded_comparison(keyword: str, item: ContentItem | None) -> bool:
    """Detect queries that should not patch a different comparison article."""
    if not item or not is_teamwork_vs_asana_query(keyword):
        return False
    slug = item.slug.lower()
    wrong_slugs = (
        "asana-vs-clickup",
        "clickup-vs-asana",
        "clickup-vs-trello",
        "notion-vs-trello",
    )
    if any(s in slug for s in wrong_slugs):
        return True
    if "teamwork" not in slug and "asana" in slug and "vs" in slug:
        return True
    return False


def _is_video_meeting_review_context(keyword: str, item: ContentItem | None) -> bool:
    """True for review pages about video/calling tools (Webex, Zoom, Meet, Teams)."""
    slug = item.slug.lower() if item else ""
    title = item.title.lower() if item else ""
    blob = f"{keyword.lower()} {slug} {title}"
    if "video-meeting" in slug or "video meeting" in blob:
        return True
    if "review" not in slug and "review" not in keyword.lower():
        return False
    return any(marker in blob for marker in _VIDEO_MEETING_PRODUCT_MARKERS)


def detect_patch_topic(keyword: str, item: ContentItem | None) -> str:
    """Topic for patch templates (broader than legacy detect_content_topic)."""
    kw = keyword.lower()
    slug = item.slug.lower() if item else ""
    title = item.title.lower() if item else ""
    blob = f"{kw} {slug} {title}"

    if "video-meeting" in slug or "video meeting" in blob:
        return "video_meeting"
    if _is_video_meeting_review_context(keyword, item):
        return "video_meeting"
    if "freelancer" in blob or "freelance" in slug:
        return "freelancer"
    if "productivity" in blob and "project-management" not in slug:
        return "productivity"
    if "collaboration" in blob:
        return "collaboration"
    if "communication" in blob:
        return "communication"
    if "workflow" in blob:
        return "workflow_management"
    if "task-management" in slug or ("task management" in blob and "project-management" not in slug):
        return "task_management"
    if "project-management" in slug or "project management" in blob:
        return "project_management"
    if item:
        from linkops.content_optimizer import detect_content_topic as _legacy_topic

        return _legacy_topic(keyword, item)
    return "project_management"


def _detect_page_kind(
    keyword: str,
    query_intent: str,
    page_type: str,
    item: ContentItem | None,
) -> str:
    if page_type == PAGE_REVIEW or query_intent == INTENT_REVIEW:
        return "review"
    if page_type == PAGE_ROUNDUP or query_intent == INTENT_BROAD_BEST:
        return "roundup"
    if page_type == PAGE_GUIDE or query_intent == INTENT_HOW_TO:
        return "guide"
    if page_type == PAGE_COMPARISON or is_software_comparison(keyword, query_intent):
        return "comparison"
    if is_concept_comparison(keyword):
        return "guide"
    if query_intent == INTENT_INFORMATIONAL:
        return "informational"
    if item and "review" in item.slug:
        return "review"
    return "informational"


def _capitalize_brand(term: str) -> str:
    from linkops.content_optimizer import capitalize_brand

    return capitalize_brand(term)


def _keyword_tokens(keyword: str) -> list[str]:
    from linkops.content_optimizer import _keyword_tokens

    return _keyword_tokens(keyword)


def _extract_product_name(keyword: str, item: ContentItem | None) -> str:
    if item and "review" in item.slug:
        tokens = _keyword_tokens(item.title) or _keyword_tokens(keyword)
        if tokens:
            return _capitalize_brand(tokens[0])
    tokens = _keyword_tokens(keyword)
    if tokens:
        return _capitalize_brand(tokens[0])
    return ""


def classify_patch_context(
    keyword: str,
    *,
    query_intent: str = "",
    page_type: str = "",
    topic: str = "",
    item: ContentItem | None = None,
) -> PatchContext:
    """Build patch relevance context for a target page and keyword."""
    kw = keyword.strip()
    query_intent = query_intent or detect_query_intent(kw)
    page_type = page_type or (detect_gsc_page_type(item) if item else "")
    topic = topic or detect_patch_topic(kw, item)
    product = _extract_product_name(kw, item)

    if is_concept_comparison(kw):
        comparison_kind = "concept_comparison"
    elif is_software_comparison(kw, query_intent):
        comparison_kind = "software_comparison"
    else:
        comparison_kind = "none"

    page_kind = _detect_page_kind(kw, query_intent, page_type, item)
    allow_video = topic == "video_meeting" or _is_video_meeting_review_context(kw, item)
    allow_pm = topic in (
        "project_management",
        "task_management",
        "workflow_management",
    ) or (
        item is not None
        and "project-management" in item.slug.lower()
        and topic != "productivity"
    )

    ctx = PatchContext(
        keyword=kw,
        comparison_kind=comparison_kind,
        page_kind=page_kind,
        topic=topic,
        product_name=product,
        allow_video_meeting_templates=allow_video,
        allow_pm_software_wording=allow_pm,
    )

    if is_misrouted_branded_comparison(kw, item):
        ctx.force_manual_review = True
        ctx.manual_review_reason = (
            f'Query "{kw}" is a Teamwork.com vs Asana branded comparison. '
            "Do not apply paste-ready patches to a different comparison article "
            "(for example Asana vs ClickUp). "
            'Suggested future article title: "Teamwork vs Asana for Small Teams".'
        )
        ctx.future_article_title = "Teamwork vs Asana for Small Teams"
    return ctx


def block_incompatible_patch_suggestion(text: str, ctx: PatchContext) -> bool:
    """Return True if the suggestion should be blocked."""
    lower = text.lower()
    if ctx.comparison_kind == "concept_comparison":
        if _FAKE_PRODUCT_COMPARISON_RE.match(text.strip()):
            return True
        if re.search(r"\bis\s+\w+\s+better\s+than\b", lower) and not re.search(
            r"difference between", lower
        ):
            if not any(
                p in lower
                for p in (
                    "project management",
                    "task management",
                    "project and task",
                    "project vs task",
                )
            ):
                return True
    if not ctx.allow_video_meeting_templates:
        if any(term in lower for term in _VIDEO_MEETING_BLOCK_PHRASES):
            return True
        if re.search(r"\bzoom\b", lower) and "alternative" in lower:
            return True
    if not ctx.allow_pm_software_wording and ctx.topic == "productivity":
        if any(phrase in lower for phrase in _PM_SOFTWARE_PHRASES):
            return True
    if ctx.force_manual_review:
        return True
    return False


def filter_patch_faqs(questions: list[str], ctx: PatchContext) -> list[str]:
    """Remove or replace incompatible FAQ suggestions."""
    if ctx.force_manual_review:
        return []
    out: list[str] = []
    for q in questions:
        if not block_incompatible_patch_suggestion(q, ctx):
            out.append(q)
    return out


def filter_patch_headings(headings: list[str], ctx: PatchContext) -> list[str]:
    return [h for h in headings if not block_incompatible_patch_suggestion(h, ctx)]


def filter_patch_intro(intro: str, ctx: PatchContext) -> str:
    if block_incompatible_patch_suggestion(intro, ctx):
        return ""
    return intro


def concept_comparison_faq_candidates() -> list[str]:
    return list(_CONCEPT_COMPARISON_FAQ)


def concept_comparison_heading_candidates() -> list[str]:
    return list(_CONCEPT_COMPARISON_HEADINGS)


def concept_comparison_intro() -> str:
    return _CONCEPT_COMPARISON_INTRO


def concept_comparison_faq_answer(question: str) -> str | None:
    """Paste-ready answers for concept comparison FAQ questions."""
    ql = question.lower()
    if "difference between a project and a task" in ql:
        return (
            "A project is a larger body of work with a goal, timeline, and coordinated tasks. "
            "A task is a single actionable step with an owner and due date."
        )
    if "task be part of a project" in ql:
        return "Yes. Tasks are usually the smaller units of work inside a project."
    if "project management or task management" in ql:
        return (
            "Many small teams need both. Project management clarifies the bigger goal; "
            "task management keeps daily actions and deadlines visible."
        )
    if "focus on tasks instead" in ql:
        return (
            "Focus on task management when daily execution, ownership, and follow-ups "
            "are the main problem rather than complex multi-phase planning."
        )
    if "balancing projects and tasks" in ql:
        return (
            "Look for clear project views, simple task ownership, due dates, status tracking, "
            "and a workflow the team can maintain consistently."
        )
    from linkops.informational_topics import mixed_project_task_faq_answer

    return mixed_project_task_faq_answer(question)


def guarded_faq_candidates(ctx: PatchContext) -> list[str]:
    """Primary FAQ template list for a patch context."""
    if ctx.force_manual_review:
        return []
    if is_mixed_project_task_topic(ctx.keyword):
        return list(MIXED_PROJECT_TASK_FAQ)
    if ctx.comparison_kind == "concept_comparison":
        return list(_CONCEPT_COMPARISON_FAQ)
    if ctx.page_kind == "review":
        product = ctx.product_name or "this tool"
        if ctx.topic == "video_meeting":
            return [
                f"Is {product} good for small businesses?",
                f"Is {product} good for small business video meetings and calling?",
                f"Is {product} worth it for a small business?",
                f"What is the best alternative to {product} for small businesses?",
                f"How much does {product} cost for a small team?",
            ]
        if ctx.topic == "freelancer" or "trello" in (ctx.product_name or "").lower():
            return list(_TRELLO_FREELANCER_REVIEW_FAQ)
        return [
            t.format(product=product) for t in _GENERIC_REVIEW_FAQ if "{product}" in t
        ]
    if ctx.topic == "productivity":
        return list(_PRODUCTIVITY_FAQ)
    if is_mixed_project_task_topic(ctx.keyword):
        return list(MIXED_PROJECT_TASK_FAQ)
    return []


def guarded_intro_sentence(ctx: PatchContext) -> str | None:
    """Return a guarded intro sentence when templates apply, else None."""
    if ctx.force_manual_review:
        return None
    if is_mixed_project_task_topic(ctx.keyword):
        return MIXED_PROJECT_TASK_INTRO
    if ctx.comparison_kind == "concept_comparison":
        return _CONCEPT_COMPARISON_INTRO
    if ctx.page_kind == "review":
        if ctx.topic == "freelancer" or "trello" in (ctx.product_name or "").lower():
            return _TRELLO_FREELANCER_REVIEW_INTRO
        if ctx.topic == "video_meeting" and ctx.product_name:
            p = _capitalize_brand(ctx.product_name)
            return (
                f"This {p} review for small businesses covers pricing, meeting quality, "
                f"ease of use, and whether it is worth it for day-to-day video meetings."
            )
    if ctx.topic == "productivity":
        return _PRODUCTIVITY_INTRO
    if is_mixed_project_task_topic(ctx.keyword):
        return MIXED_PROJECT_TASK_INTRO
    return None


def guarded_heading_candidates(ctx: PatchContext) -> list[str]:
    if ctx.force_manual_review:
        return []
    if is_mixed_project_task_topic(ctx.keyword):
        return list(MIXED_PROJECT_TASK_HEADINGS)
    if ctx.comparison_kind == "concept_comparison":
        return list(_CONCEPT_COMPARISON_HEADINGS)
    if ctx.topic == "productivity":
        return list(_PRODUCTIVITY_HEADINGS)
    if is_mixed_project_task_topic(ctx.keyword):
        return list(MIXED_PROJECT_TASK_HEADINGS)
    return []
