"""Deterministic internal-link suggestion scoring (no external AI)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from linkops.content_model import ContentItem
from linkops.html_tools import extract_headings, normalize_internal_url

# Topic clusters: cluster name -> specific topical terms (multi-word phrases first).
TOPIC_CLUSTERS: dict[str, list[str]] = {
    "communication": [
        "communication", "communications", "chat", "messaging", "message",
        "slack", "microsoft teams", "zoom", "meet", "google meet", "webex",
        "video", "meeting", "meetings", "call", "calls", "remote", "hybrid",
        "async", "distributed", "collaboration", "workspace",
    ],
    "project_management": [
        "project management", "project", "projects", "asana", "monday",
        "monday.com", "clickup", "trello", "planning", "roadmap", "timeline",
        "milestones",
    ],
    "task_management": [
        "task management", "task", "tasks", "to-do", "todo", "kanban",
        "owner", "due date", "priority", "backlog",
    ],
    "workflow_management": [
        "workflow", "workflows", "process", "processes", "approval", "handoff",
        "automation", "automations", "recurring",
    ],
    "productivity": [
        "productivity", "focus", "notes", "docs", "documents", "calendar",
        "workspace", "collaboration",
    ],
    "freelancers": [
        "freelancer", "freelancers", "solo", "client work", "clients",
    ],
}

# Generic editorial terms — must not drive strong topical relevance or cluster assignment.
DOMAIN_STOPWORDS = frozenset(
    "best tools tool small teams team review guide comparison business businesses "
    "software work working use using also across actually always based broader one "
    "which better".split()
)

BASIC_STOP_WORDS = frozenset(
    "a an the and or for to of in on at by with from is are was were be been "
    "your you our we it this that these those how what when where why".split()
)

COMMUNICATION_HEADING_TERMS = [
    "communication", "remote", "video meeting", "video meetings", "meeting",
    "meetings", "chat", "messaging", "slack", "zoom", "microsoft teams",
    "google meet", "webex", "google workspace", "collaboration",
]

KNOWN_COMMUNICATION_TOOLS = [
    "slack", "zoom", "microsoft teams", "google meet", "webex",
    "google workspace", "teams",
]

EXCLUDED_COMMERCIAL_FOR_COMMUNICATION = frozenset(
    {"project_management", "task_management", "workflow_management"}
)

SECONDARY_ALLOWED: dict[str, set[str]] = {
    "communication": {"productivity"},
    "project_management": {"task_management", "workflow_management"},
    "task_management": {"project_management", "workflow_management"},
    "workflow_management": {"task_management", "project_management"},
    "productivity": {"communication", "freelancers"},
    "freelancers": {"productivity", "task_management"},
}

CORE_PAGE_SLUGS = frozenset(
    {
        "",
        "home",
        "blog",
        "contact",
        "contact-us",
        "about",
        "about-us",
    }
)

CORE_PAGE_TITLE_TERMS = frozenset(
    {
        "home",
        "blog",
        "contact",
        "contact us",
        "about",
        "about us",
    }
)

POLICY_PAGE_SLUG_TERMS = (
    "privacy",
    "privacy-policy",
    "terms",
    "terms-of-service",
    "terms-and-conditions",
    "editorial-policy",
    "affiliate-disclosure",
)

POLICY_PAGE_TITLE_TERMS = (
    "privacy policy",
    "terms of service",
    "terms and conditions",
    "editorial policy",
    "affiliate disclosure",
)

PAGE_TYPE_PREFERENCE_BOOST = {
    "review": 5.0,
    "comparison": 5.0,
    "category_guide": 3.0,
    "article": 2.0,
    "core_page": -25.0,
    "policy_legal": -50.0,
}

# Cluster compatibility: primary target cluster -> strong/medium/penalized cluster sets.
CLUSTER_COMPATIBILITY: dict[str, dict[str, str | set[str]]] = {
    "communication": {
        "strong": "communication",
        "medium": {"productivity"},
        "penalize": EXCLUDED_COMMERCIAL_FOR_COMMUNICATION,
    },
    "project_management": {
        "strong": "project_management",
        "medium": {"task_management", "workflow_management"},
        "penalize": {"communication"},
    },
    "task_management": {
        "strong": "task_management",
        "medium": {"project_management", "workflow_management"},
        "penalize": set(),
    },
    "workflow_management": {
        "strong": "workflow_management",
        "medium": {"task_management", "project_management"},
        "penalize": set(),
    },
    "productivity": {
        "strong": "productivity",
        "medium": {"communication", "freelancers"},
        "penalize": set(),
    },
    "freelancers": {
        "strong": "freelancers",
        "medium": {"productivity", "task_management"},
        "penalize": set(),
    },
}

MIN_ACCEPT_SCORE = 18.0
STRONG_SCORE_THRESHOLD = 35.0
STRICT_MIN_ACCEPT_SCORE = 28.0
STRICT_STRONG_SCORE_THRESHOLD = 45.0
STRONG_INTERNAL_SUPPORT_THRESHOLD = 7


def _link_record_str(link: object, key: str) -> str | None:
    """Read a string field from a link dict or object-like record; never raises."""
    try:
        if isinstance(link, dict):
            value = link.get(key)
        else:
            value = getattr(link, key, None)
            if value is None and hasattr(link, "__getitem__"):
                try:
                    value = link[key]  # type: ignore[index]
                except (KeyError, TypeError, IndexError):
                    value = None
        if value is None:
            return None
        text = str(value).strip()
        return text or None
    except Exception:
        return None


def item_links_to_target(item: ContentItem, target_url: str) -> bool:
    """True if any existing internal link on item points at target_url (normalized)."""
    target_norm = normalize_internal_url(target_url)
    if not target_norm:
        return False
    for link in item.existing_internal_links or []:
        try:
            raw = _link_record_str(link, "normalized_url")
            if not raw:
                raw = _link_record_str(link, "href")
            if not raw:
                continue
            link_norm = normalize_internal_url(raw)
            if link_norm and link_norm == target_norm:
                return True
        except Exception:
            continue
    return False


def _pages_already_linking_to_target(
    catalog: list[ContentItem],
    target_url: str,
) -> list[ContentItem]:
    return [c for c in catalog if item_links_to_target(c, target_url)]


def _pages_not_linking_to_target(
    catalog: list[ContentItem],
    target_url: str,
    exclude_url: str | None = None,
) -> list[ContentItem]:
    target_norm = normalize_internal_url(target_url)
    if not target_norm:
        return list(catalog)
    exclude_norm = normalize_internal_url(exclude_url) if exclude_url else None
    result: list[ContentItem] = []
    for item in catalog:
        item_norm = item.normalized_url()
        if item_norm == target_norm or item_norm == exclude_norm:
            continue
        if not item_links_to_target(item, target_url):
            result.append(item)
    return result


@dataclass
class Suggestion:
    source_title: str
    source_url: str
    target_url: str
    score: float
    reason: str
    suggested_anchor_text: str
    suggested_insertion_sentence: str
    suggested_location_hint: str
    target_already_linked: bool
    risk_level: str  # low | medium | high
    strength: str = "medium"  # strong | medium
    page_type: str = "article"


@dataclass
class RejectedCandidate:
    source_title: str
    source_url: str
    score: float
    reason: str


@dataclass
class SuggestionReport:
    suggestions: list[Suggestion]
    strong: list[Suggestion]
    medium: list[Suggestion]
    rejected: list[RejectedCandidate]
    already_linking: list[ContentItem]
    related_already_linking: list[ContentItem]
    target_item: ContentItem | None
    target_clusters: list[str]
    target_primary_cluster: str | None
    target_secondary_clusters: list[str]
    core_pages_excluded: list[str]
    already_linking_quality_note: str
    final_recommendation: str
    strict_mode: bool


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _tokenize(text: str, *, exclude_domain: bool = True) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    stop = BASIC_STOP_WORDS | (DOMAIN_STOPWORDS if exclude_domain else frozenset())
    return {w for w in words if len(w) > 2 and w not in stop}


def _meaningful_tokens(text: str) -> set[str]:
    return _tokenize(text, exclude_domain=True)


def _paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n+", text)
    if len(parts) <= 1:
        parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _term_in_text(term: str, text: str) -> bool:
    term = term.lower().strip()
    if not term:
        return False
    if " " in term:
        return term in text
    if term in DOMAIN_STOPWORDS:
        return False
    return bool(re.search(rf"\b{re.escape(term)}\b", text))


def detect_clusters(
    text: str,
    title: str = "",
    slug: str = "",
    keyword: str | None = None,
) -> set[str]:
    """Assign topical clusters using specific terms; generic words alone do not assign."""
    blob = _normalize_text(f"{title} {slug.replace('-', ' ')} {text} {keyword or ''}")
    clusters: set[str] = set()

    for cluster_name, terms in TOPIC_CLUSTERS.items():
        for term in sorted(terms, key=len, reverse=True):
            if _term_in_text(term, blob):
                clusters.add(cluster_name)
                break

    return clusters


def detect_primary_clusters(
    title: str = "",
    slug: str = "",
    keyword: str | None = None,
) -> set[str]:
    """Assign primary clusters from target metadata only (title, slug, keyword)."""
    blob = _normalize_text(f"{title} {slug.replace('-', ' ')} {keyword or ''}")
    clusters: set[str] = set()

    for cluster_name, terms in TOPIC_CLUSTERS.items():
        for term in sorted(terms, key=len, reverse=True):
            if _term_in_text(term, blob):
                clusters.add(cluster_name)
                break

    return clusters


def detect_secondary_clusters(content: str, primary_clusters: set[str]) -> set[str]:
    """Weak secondary cluster hints from full content; never adds commercial clusters for communication."""
    if not primary_clusters or not content:
        return set()

    allowed: set[str] = set()
    for primary in primary_clusters:
        allowed |= SECONDARY_ALLOWED.get(primary, set())
    if not allowed:
        return set()

    blob = _normalize_text(content[:5000])
    secondary: set[str] = set()
    for cluster_name in allowed:
        terms = TOPIC_CLUSTERS.get(cluster_name, [])
        for term in sorted(terms, key=len, reverse=True):
            if _term_in_text(term, blob):
                secondary.add(cluster_name)
                break

    secondary -= primary_clusters
    if "communication" in primary_clusters:
        secondary -= EXCLUDED_COMMERCIAL_FOR_COMMUNICATION
    return secondary


def _primary_cluster(clusters: set[str], keyword: str | None = None) -> str | None:
    if not clusters:
        return None
    priority = [
        "communication",
        "project_management",
        "task_management",
        "workflow_management",
        "productivity",
        "freelancers",
    ]
    if keyword:
        kw_clusters = detect_primary_clusters(title=keyword, keyword=keyword)
        for name in priority:
            if name in kw_clusters:
                return name
    for name in priority:
        if name in clusters:
            return name
    return next(iter(clusters))


def _heading_blob(item: ContentItem) -> str:
    headings = extract_headings(item.content_html)
    heading_text = " ".join(headings.get("h1", []) + headings.get("h2", []))
    return _normalize_text(f"{item.title} {item.slug.replace('-', ' ')} {heading_text}")


def _has_communication_heading_relevance(item: ContentItem) -> bool:
    blob = _heading_blob(item)
    for term in COMMUNICATION_HEADING_TERMS:
        if _term_in_text(term, blob):
            return True
    return False


def _known_communication_tool_in_headings(item: ContentItem) -> bool:
    blob = _heading_blob(item)
    for tool in KNOWN_COMMUNICATION_TOOLS:
        if _term_in_text(tool, blob):
            return True
    return False


def _has_heading_cluster_match(item: ContentItem, cluster: str) -> bool:
    blob = _heading_blob(item)
    terms = TOPIC_CLUSTERS.get(cluster, [])
    for term in sorted(terms, key=len, reverse=True):
        if _term_in_text(term, blob):
            return True
    return False


def _has_communication_h2_section(item: ContentItem) -> bool:
    headings = extract_headings(item.content_html)
    for heading in headings.get("h2", []):
        heading_lower = heading.lower()
        for term in COMMUNICATION_HEADING_TERMS:
            if term in heading_lower:
                return True
    return False


def classify_page_type(item: ContentItem) -> str:
    """Classify a page as article, review, comparison, category guide, core, or policy/legal."""
    slug = item.slug.lower().strip("/")
    title = _normalize_text(item.title)
    slug_text = slug.replace("-", " ")

    for term in POLICY_PAGE_TITLE_TERMS:
        if term in title:
            return "policy_legal"
    for term in POLICY_PAGE_SLUG_TERMS:
        if term in slug or term.replace("-", " ") in slug_text:
            return "policy_legal"

    if slug in CORE_PAGE_SLUGS or title in CORE_PAGE_TITLE_TERMS:
        return "core_page"
    for term in CORE_PAGE_TITLE_TERMS:
        if term == title or title.startswith(f"{term} "):
            return "core_page"

    if " vs " in title or "-vs-" in slug or slug.endswith("-vs-asana") or " vs " in slug_text:
        return "comparison"
    if "review" in title or slug.endswith("-review") or " review" in slug_text:
        return "review"
    if title.startswith("best ") or slug.startswith("best-"):
        return "category_guide"
    return "article"


def is_core_page(item: ContentItem) -> bool:
    return classify_page_type(item) == "core_page"


def is_policy_page(item: ContentItem) -> bool:
    return classify_page_type(item) == "policy_legal"


def _phrase_in_text(phrase: str, text: str) -> bool:
    phrase = _normalize_text(phrase)
    if not phrase:
        return False
    if " " in phrase:
        return phrase in _normalize_text(text)
    return phrase in _meaningful_tokens(text)


def _meaningful_title_tokens(item: ContentItem | None) -> set[str]:
    if not item:
        return set()
    return _meaningful_tokens(f"{item.title} {item.slug.replace('-', ' ')}")


def _is_excluded_commercial_for_communication(
    source: ContentItem,
    target_primary: str | None,
) -> bool:
    if target_primary != "communication":
        return False
    source_primary = detect_primary_clusters(source.title, source.slug)
    if not (source_primary & EXCLUDED_COMMERCIAL_FOR_COMMUNICATION):
        return False
    if _has_communication_heading_relevance(source):
        return False
    if _known_communication_tool_in_headings(source):
        return False
    if _has_communication_h2_section(source):
        return False
    return True


def _has_strong_heading_relevance(
    source: ContentItem,
    target_primary: str | None,
) -> bool:
    if target_primary == "communication":
        return (
            _has_communication_heading_relevance(source)
            or _known_communication_tool_in_headings(source)
        )
    if not target_primary:
        return False
    return _has_heading_cluster_match(source, target_primary)


def _cluster_compatibility_score(
    target_primary: str | None,
    source_clusters: set[str],
    source: ContentItem,
) -> tuple[float, list[str], str]:
    """Return adjustment score, reason fragments, and match tier (strong|medium|weak|penalized)."""
    if not target_primary or not source_clusters:
        return 0.0, [], "weak"

    rules = CLUSTER_COMPATIBILITY.get(target_primary)
    if not rules:
        return 0.0, [], "weak"

    strong_cluster = rules["strong"]
    medium_clusters: set[str] = rules["medium"]
    penalize_clusters: set[str] = rules["penalize"]

    if strong_cluster in source_clusters:
        if target_primary == "communication" and not _has_strong_heading_relevance(source, target_primary):
            return 8.0, ["communication cluster but only body-level overlap"], "medium"
        return 35.0, [f"shared {strong_cluster.replace('_', ' ')} cluster"], "strong"

    overlap_medium = source_clusters & medium_clusters
    if overlap_medium:
        if target_primary == "communication":
            if _has_strong_heading_relevance(source, target_primary) or _has_communication_h2_section(source):
                label = ", ".join(sorted(c.replace("_", " ") for c in overlap_medium))
                return 15.0, [f"partial cluster match ({label}) with heading-level communication relevance"], "medium"
            return -10.0, ["productivity/collaboration page without heading-level communication relevance"], "penalized"
        label = ", ".join(sorted(c.replace("_", " ") for c in overlap_medium))
        return 12.0, [f"related cluster ({label})"], "medium"

    overlap_penalized = source_clusters & penalize_clusters
    if overlap_penalized:
        if target_primary == "communication":
            if _has_communication_h2_section(source) and _has_strong_heading_relevance(source, target_primary):
                label = ", ".join(sorted(c.replace("_", " ") for c in overlap_penalized))
                return 5.0, [f"cross-cluster ({label}) with dedicated communication section in H2"], "medium"
            label = ", ".join(sorted(c.replace("_", " ") for c in overlap_penalized))
            return -30.0, [f"unrelated cluster ({label}) without title/slug/H2 communication relevance"], "penalized"
        label = ", ".join(sorted(c.replace("_", " ") for c in overlap_penalized))
        return -30.0, [f"unrelated cluster ({label})"], "penalized"

    if source_clusters - {target_primary}:
        return -15.0, ["no cluster compatibility"], "penalized"

    return 0.0, [], "weak"


def _score_candidate(
    candidate: ContentItem,
    target_item: ContentItem | None,
    target_primary: str | None,
    target_secondary: set[str],
    target_keyword: str | None,
    page_type: str,
) -> tuple[float, list[str], str, bool, bool]:
    """Return score, reason parts, match tier, generic-only flag, and heading relevance."""
    score = 0.0
    reasons: list[str] = []
    generic_only = True

    cand_title = candidate.title
    cand_content = candidate.plain_text[:5000]
    source_primary = detect_primary_clusters(candidate.title, candidate.slug)
    source_secondary = detect_secondary_clusters(cand_content, source_primary)
    source_clusters = source_primary | source_secondary
    heading_relevant = _has_strong_heading_relevance(candidate, target_primary)
    heading_blob = _heading_blob(candidate)

    score += PAGE_TYPE_PREFERENCE_BOOST.get(page_type, 0.0)
    if page_type in ("review", "comparison", "category_guide"):
        reasons.append(f"preferred page type ({page_type.replace('_', ' ')})")
        generic_only = False

    # Exact target keyword phrase in source headings (strong boost).
    if target_keyword:
        kw_norm = _normalize_text(target_keyword)
        if kw_norm and _phrase_in_text(kw_norm, heading_blob):
            score += 30.0
            reasons.append("exact target keyword phrase in source title/slug/H2")
            generic_only = False
        elif kw_norm and _phrase_in_text(kw_norm, cand_content):
            score += 10.0
            reasons.append("target keyword phrase in source body only (heading match preferred)")
            generic_only = False

    # Meaningful target title tokens in source headings (medium boost).
    target_tokens = _meaningful_title_tokens(target_item)
    heading_tokens = _meaningful_tokens(heading_blob)
    content_tokens = _meaningful_tokens(cand_content)
    title_overlap = target_tokens & heading_tokens
    content_overlap = target_tokens & content_tokens

    if title_overlap:
        boost = 12.0 * min(len(title_overlap), 3)
        score += boost
        reasons.append(
            f"target title terms in source title/slug/H2: {', '.join(sorted(title_overlap)[:4])}"
        )
        generic_only = False
    elif content_overlap:
        boost = 4.0 * min(len(content_overlap), 3)
        score += boost
        reasons.append(
            f"target title terms in source body only: {', '.join(sorted(content_overlap)[:4])}"
        )

    target_all = ({target_primary} if target_primary else set()) | target_secondary
    shared_clusters = target_all & source_clusters
    if shared_clusters and heading_relevant:
        label = ", ".join(sorted(c.replace("_", " ") for c in shared_clusters))
        score += 25.0
        reasons.append(f"shared cluster match with heading relevance: {label}")
        generic_only = False
    elif shared_clusters:
        label = ", ".join(sorted(c.replace("_", " ") for c in shared_clusters))
        score += 8.0
        reasons.append(f"shared cluster match in body only: {label}")

    compat_score, compat_reasons, match_tier = _cluster_compatibility_score(
        target_primary, source_clusters, candidate
    )
    score += compat_score
    reasons.extend(compat_reasons)

    if target_primary and _has_heading_cluster_match(candidate, target_primary):
        score += 18.0
        reasons.append(f"source title/slug/H2 discusses {target_primary.replace('_', ' ')} topics")
        generic_only = False
    elif target_primary and _paragraph_has_cluster_terms(cand_content, target_primary):
        score += 6.0
        reasons.append(f"source body mentions {target_primary.replace('_', ' ')} terms (not heading-level)")

    if target_item:
        all_target = set(re.findall(r"[a-z0-9]+", _normalize_text(target_item.title)))
        all_source = set(re.findall(r"[a-z0-9]+", heading_blob))
        generic_shared = (all_target & all_source) & DOMAIN_STOPWORDS
        if generic_shared and generic_only:
            score += min(len(generic_shared), 2) * 0.5
            reasons.append(
                f"generic overlap only ({', '.join(sorted(generic_shared)[:4])})"
            )

    link_count = len(candidate.existing_internal_links)
    if 1 <= link_count <= 8:
        score += 3.0
    elif link_count == 0:
        score += 1.0

    if not reasons:
        reasons.append("weak topical match")

    return score, reasons, match_tier, generic_only, heading_relevant


def _paragraph_has_cluster_terms(content: str, cluster: str) -> bool:
    terms = TOPIC_CLUSTERS.get(cluster, [])
    for para in _paragraphs(content):
        para_lower = para.lower()
        for term in terms:
            if _term_in_text(term, para_lower):
                return True
    return False


def _risk_level(
    score: float,
    match_tier: str,
    generic_only: bool,
    shared_clusters: set[str],
    target_primary: str | None,
    heading_relevant: bool,
    page_type: str,
    include_core_pages: bool,
    strong_threshold: float,
) -> str:
    if page_type == "policy_legal":
        return "high"
    if page_type == "core_page":
        if not include_core_pages:
            return "high"
        return "medium"

    if generic_only and not shared_clusters:
        return "high"
    if match_tier == "penalized":
        return "high"

    if target_primary == "communication" and not heading_relevant:
        if match_tier == "medium" or score >= MIN_ACCEPT_SCORE:
            return "medium"
        return "high"

    if match_tier == "strong" and score >= strong_threshold and heading_relevant:
        return "low"
    if match_tier == "strong" and heading_relevant:
        return "low" if score >= MIN_ACCEPT_SCORE else "medium"
    if match_tier == "medium":
        return "medium"
    if generic_only:
        return "high"
    if score >= MIN_ACCEPT_SCORE:
        return "medium"
    return "high"


def _anchor_text(target_item: ContentItem | None, target_url: str) -> str:
    if target_item and target_item.title:
        return target_item.title.strip()
    slug = target_url.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").title()


def _insertion_sentence(
    target_title: str,
    target_url: str,
    target_primary: str | None,
) -> str:
    if target_primary == "communication":
        return (
            f"If your team works remotely or across locations, you may also want to compare "
            f"[{target_title}]({target_url})."
        )
    if target_primary == "project_management":
        return (
            f"If your team needs a broader project management comparison, read "
            f"[{target_title}]({target_url})."
        )
    if target_primary == "task_management":
        return (
            f"If your team is evaluating task management options, read "
            f"[{target_title}]({target_url})."
        )
    if target_primary == "workflow_management":
        return (
            f"If your team is comparing workflow tools, read "
            f"[{target_title}]({target_url})."
        )
    return (
        f"If your team is comparing broader options, read "
        f"[{target_title}]({target_url})."
    )


def _location_hint(candidate: ContentItem) -> str:
    if candidate.excerpt_html:
        return "Near the introduction or first comparison section, after the opening context."
    if "comparison" in candidate.plain_text.lower()[:500]:
        return "After the first tool comparison or feature summary paragraph."
    if "conclusion" in candidate.plain_text.lower()[-800:]:
        return "Before the conclusion section, in a related-tools or next-steps paragraph."
    return "Mid-article where a related-tool or category cross-link fits naturally."


def _related_already_linking(
    already: list[ContentItem],
    target_primary: str | None,
    target_secondary: set[str],
) -> list[ContentItem]:
    target_all = ({target_primary} if target_primary else set()) | target_secondary
    if not target_all:
        return []
    related: list[ContentItem] = []
    for page in already:
        page_primary = detect_primary_clusters(page.title, page.slug)
        page_secondary = detect_secondary_clusters(page.plain_text[:3000], page_primary)
        if (page_primary | page_secondary) & target_all:
            related.append(page)
            continue
        if target_primary == "communication" and _has_communication_heading_relevance(page):
            related.append(page)
    return related


def _short_tool_name(title: str) -> str:
    cleaned = title.replace(" Review", "").replace(" for Small Businesses", "")
    cleaned = cleaned.replace(" for Small Teams", "")
    return cleaned.strip()


def _determine_final_recommendation(
    suggestions: list[Suggestion],
    strict_mode: bool,
    related_count: int,
) -> str:
    strong_low = [s for s in suggestions if s.strength == "strong" and s.risk_level == "low"]

    if strict_mode and related_count >= STRONG_INTERNAL_SUPPORT_THRESHOLD:
        if not strong_low:
            return "No new links needed"
        if len(strong_low) <= 2:
            tool_names = " or ".join(_short_tool_name(s.source_title) for s in strong_low)
            return (
                f"No new links are necessary unless you want one optional link from {tool_names}."
            )
        return "Review manually"

    if not suggestions:
        return "No new links needed"
    if strong_low and len(strong_low) == len(suggestions):
        return "Add only these links"
    if strong_low:
        return "Review manually"
    return "Review manually"


def _already_linking_quality_note(
    already_count: int,
    related_count: int,
    strict_mode: bool,
) -> str:
    if strict_mode:
        return (
            f"Target already has strong internal support ({related_count} topically related pages "
            f"already linking; {already_count} total). Additional links may not be necessary."
        )
    if related_count:
        return f"{already_count} pages already link to target ({related_count} topically related)."
    return f"{already_count} pages already link to target."


def generate_suggestions(
    catalog: list[ContentItem],
    target_url: str,
    target_keyword: str | None = None,
    max_suggestions: int = 8,
    include_high_risk: bool = False,
    include_core_pages: bool = False,
) -> SuggestionReport:
    target_norm = normalize_internal_url(target_url)
    if not target_norm:
        raise ValueError(f"Target URL is not a valid WorkToolsLab internal URL: {target_url}")

    target_item = next((c for c in catalog if c.normalized_url() == target_norm), None)
    already = _pages_already_linking_to_target(catalog, target_url)
    candidates = _pages_not_linking_to_target(catalog, target_url, exclude_url=target_norm)

    target_text = target_item.plain_text if target_item else ""
    target_title = target_item.title if target_item else ""
    target_slug = target_item.slug if target_item else target_norm.rstrip("/").split("/")[-1]

    target_primary_set = detect_primary_clusters(target_title, target_slug, target_keyword)
    target_primary = _primary_cluster(target_primary_set, target_keyword)
    target_secondary = detect_secondary_clusters(target_text, target_primary_set)
    target_clusters = sorted(target_primary_set | target_secondary)
    target_anchor = _anchor_text(target_item, target_url)

    related = _related_already_linking(already, target_primary, target_secondary)
    strict_mode = len(related) >= STRONG_INTERNAL_SUPPORT_THRESHOLD
    min_accept_score = STRICT_MIN_ACCEPT_SCORE if strict_mode else MIN_ACCEPT_SCORE
    strong_threshold = STRICT_STRONG_SCORE_THRESHOLD if strict_mode else STRONG_SCORE_THRESHOLD
    effective_max = min(max_suggestions, 2) if strict_mode else max_suggestions

    accepted: list[tuple[float, str, str, str, bool, ContentItem, str]] = []
    rejected: list[RejectedCandidate] = []
    core_pages_excluded: list[str] = []

    for cand in candidates:
        page_type = classify_page_type(cand)

        if is_policy_page(cand):
            rejected.append(
                RejectedCandidate(
                    source_title=cand.title,
                    source_url=cand.url,
                    score=0.0,
                    reason="policy/legal page excluded from internal link suggestions",
                )
            )
            continue

        if is_core_page(cand) and not include_core_pages:
            core_pages_excluded.append(cand.title)
            rejected.append(
                RejectedCandidate(
                    source_title=cand.title,
                    source_url=cand.url,
                    score=0.0,
                    reason="core utility page excluded by default (use --include-core-pages to review)",
                )
            )
            continue

        if _is_excluded_commercial_for_communication(cand, target_primary):
            rejected.append(
                RejectedCandidate(
                    source_title=cand.title,
                    source_url=cand.url,
                    score=0.0,
                    reason=(
                        "unrelated project/task/workflow page for communication target "
                        "without title/slug/H2 communication relevance"
                    ),
                )
            )
            continue

        score, reason_parts, match_tier, generic_only, heading_relevant = _score_candidate(
            cand,
            target_item,
            target_primary,
            target_secondary,
            target_keyword,
            page_type,
        )
        source_primary = detect_primary_clusters(cand.title, cand.slug)
        source_secondary = detect_secondary_clusters(cand.plain_text[:5000], source_primary)
        source_clusters = source_primary | source_secondary
        target_all = ({target_primary} if target_primary else set()) | target_secondary
        shared = target_all & source_clusters
        risk = _risk_level(
            score,
            match_tier,
            generic_only,
            shared,
            target_primary,
            heading_relevant,
            page_type,
            include_core_pages,
            strong_threshold,
        )
        reason = "; ".join(reason_parts)

        if risk == "high" and not include_high_risk:
            rejected.append(
                RejectedCandidate(
                    source_title=cand.title,
                    source_url=cand.url,
                    score=round(score, 1),
                    reason=f"high risk — {reason}",
                )
            )
            continue

        if score < min_accept_score:
            rejected.append(
                RejectedCandidate(
                    source_title=cand.title,
                    source_url=cand.url,
                    score=round(score, 1),
                    reason=f"score below threshold ({min_accept_score}) — {reason}",
                )
            )
            continue

        if match_tier == "penalized" and risk != "low":
            rejected.append(
                RejectedCandidate(
                    source_title=cand.title,
                    source_url=cand.url,
                    score=round(score, 1),
                    reason=f"incompatible cluster — {reason}",
                )
            )
            continue

        if target_primary == "communication" and not heading_relevant and risk == "low":
            risk = "medium"

        strength = "strong" if risk == "low" and match_tier == "strong" else "medium"
        accepted.append((score, reason, risk, strength, match_tier == "strong", cand, page_type))

    accepted.sort(key=lambda x: (-x[0], -int(x[4]), x[5].title))

    suggestions: list[Suggestion] = []
    strong: list[Suggestion] = []
    medium: list[Suggestion] = []

    for sc, reason, risk, strength, _, cand, page_type in accepted[:effective_max]:
        sug = Suggestion(
            source_title=cand.title,
            source_url=cand.url,
            target_url=target_norm,
            score=round(sc, 1),
            reason=reason,
            suggested_anchor_text=target_anchor,
            suggested_insertion_sentence=_insertion_sentence(
                target_anchor, target_norm, target_primary
            ),
            suggested_location_hint=_location_hint(cand),
            target_already_linked=False,
            risk_level=risk,
            strength=strength,
            page_type=page_type,
        )
        suggestions.append(sug)
        if strength == "strong":
            strong.append(sug)
        else:
            medium.append(sug)

    already_note = _already_linking_quality_note(len(already), len(related), strict_mode)
    final_recommendation = _determine_final_recommendation(suggestions, strict_mode, len(related))

    return SuggestionReport(
        suggestions=suggestions,
        strong=strong,
        medium=medium,
        rejected=rejected,
        already_linking=already,
        related_already_linking=related,
        target_item=target_item,
        target_clusters=target_clusters,
        target_primary_cluster=target_primary,
        target_secondary_clusters=sorted(target_secondary),
        core_pages_excluded=sorted(core_pages_excluded),
        already_linking_quality_note=already_note,
        final_recommendation=final_recommendation,
        strict_mode=strict_mode,
    )
