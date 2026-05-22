"""Read-only content optimization analysis from WordPress and GSC caches."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from linkops.content_model import ContentItem
from linkops.content_optimization_model import (
    ALIGNMENT_ALIGNED,
    ALIGNMENT_MISALIGNED,
    ALIGNMENT_PARTIAL,
    COVERAGE_EXACT,
    COVERAGE_MISSING,
    COVERAGE_PARTIAL,
    COVERAGE_STRONG,
    COVERAGE_WEAK,
    CoverageField,
    ContentOptimizationReport,
    FaqAnalysis,
    GscQueryMetrics,
    HeadingAnalysis,
    IntroAnalysis,
    InternalLinkSupport,
    LINK_SUPPORT_MODERATE,
    LINK_SUPPORT_STRONG,
    LINK_SUPPORT_UNKNOWN,
    LINK_SUPPORT_WEAK,
    REC_CONTENT,
    REC_FAQ_OPTIMIZATION,
    REC_INTERNAL_LINKS,
    REC_LIGHT,
    REC_MONITOR,
    REC_NO_CHANGE,
    REC_REVIEW_MANUAL,
    REC_TITLE_META,
    TitleMetaSuggestions,
)
from linkops.suggestion_engine import detect_primary_clusters
from linkops.gsc_intent import (
    INTENT_BROAD_BEST,
    INTENT_COMPARISON,
    INTENT_HOW_TO,
    INTENT_INFORMATIONAL,
    INTENT_REVIEW,
    INTENT_UNKNOWN,
    PAGE_COMPARISON,
    PAGE_GUIDE,
    PAGE_REVIEW,
    PAGE_ROUNDUP,
    PAGE_UNKNOWN,
    detect_gsc_page_type,
    detect_query_intent,
)
from linkops.gsc_model import GscCache
from linkops.html_tools import extract_headings, html_to_plain_text, normalize_internal_url
from linkops.link_analyzer import pages_already_linking

READ_ONLY_NOTICE = (
    "This report is read-only. LinkOps does not modify WordPress, publish content, "
    "or call external APIs. Apply suggestions manually after editorial review."
)

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "for",
        "to",
        "of",
        "in",
        "on",
        "and",
        "or",
        "is",
        "are",
        "with",
        "your",
        "my",
        "our",
    }
)

_FAQ_HEADING_MARKERS = (
    "faq",
    "frequently asked",
    "questions and answers",
    "common questions",
)

_TITLE_CASE_SMALL_WORDS = frozenset(
    {"a", "an", "the", "and", "or", "but", "for", "nor", "on", "at", "to", "by", "in", "of", "with", "vs"}
)

_STRONG_COVERAGE = frozenset({COVERAGE_EXACT, COVERAGE_PARTIAL, COVERAGE_STRONG})

_COMPARISON_FAQ_MIN_STRONG = 3

_GSC_RELATED_MIN_OVERLAP = 0.45

_CORE_COVERAGE_FIELDS = (
    "title",
    "slug",
    "h1",
    "headings",
    "first_100_words",
    "first_150_words",
    "body",
)

_QUESTION_STARTER_RE = re.compile(
    r"^(what|which|who|when|where|why|how|is|are|do|does|should|can)\b",
    re.IGNORECASE,
)

_INTRO_NO_SENTENCE = "No intro sentence needed."

# Longest phrases first when matching inside text.
BRAND_CAPITALIZATION: dict[str, str] = {
    "cisco webex": "Cisco Webex",
    "microsoft teams": "Microsoft Teams",
    "google workspace": "Google Workspace",
    "google meet": "Google Meet",
    "monday.com": "Monday.com",
    "clickup": "ClickUp",
    "trello": "Trello",
    "asana": "Asana",
    "monday": "Monday.com",
    "notion": "Notion",
    "slack": "Slack",
    "zoom": "Zoom",
    "webex": "Webex",
    "todoist": "Todoist",
    "basecamp": "Basecamp",
    "smartsheet": "Smartsheet",
    "airtable": "Airtable",
    "jira": "Jira",
    "linear": "Linear",
    "hubspot": "HubSpot",
    "salesforce": "Salesforce",
}

_COMPARISON_SPLIT_RE = re.compile(r"\s+vs\.?\s+|\s+versus\s+", re.IGNORECASE)
_COMPARISON_SIGNAL_RE = re.compile(
    r"\bvs\.?\b|\bversus\b|\bcompare\b|\bcomparison\b",
    re.IGNORECASE,
)

_TOPIC_FAQ_TEMPLATES: dict[str, list[str]] = {
    "collaboration": [
        "What are the best collaboration tools for small teams?",
        "What should small teams look for in collaboration tools?",
        "Do small teams need collaboration tools?",
        "What is the easiest collaboration tool for small teams?",
        "What is the difference between collaboration tools and communication tools?",
    ],
    "project_management": [
        "What is the best project management software for small teams?",
        "What should small teams look for in project management software?",
        "Do small teams need project management software?",
        "What is the easiest project management software for small teams?",
        "What is the difference between project management tools and project management software?",
    ],
    "communication": [
        "What are the best communication tools for small businesses?",
        "What should small businesses look for in communication tools?",
        "Do remote teams need communication tools?",
        "What is the easiest communication tool for small teams?",
        "What is the difference between communication tools and collaboration tools?",
    ],
    "workflow_management": [
        "What are the best workflow management tools for small teams?",
        "What should small teams look for in workflow management tools?",
        "Do small teams need workflow management software?",
        "What is the easiest workflow management tool for small teams?",
        "What is the difference between workflow management and project management?",
    ],
    "task_management": [
        "What are the best task management tools for small teams?",
        "What should small teams look for in task management tools?",
        "Do small teams need task management software?",
        "What is the easiest task management tool for small teams?",
        "What is the difference between task management and project management?",
    ],
}

_TOPIC_INTRO_SENTENCES: dict[str, str] = {
    "collaboration": (
        "Good collaboration tools for small teams should help people communicate clearly, "
        "share work, manage files, and stay aligned without adding unnecessary complexity."
    ),
    "project_management": (
        "The best project management software for small teams should help with task ownership, "
        "deadlines, collaboration, and project visibility without adding unnecessary complexity."
    ),
    "communication": (
        "The best communication tools for small teams should make meetings, messaging, and "
        "remote coordination reliable without adding unnecessary complexity."
    ),
    "workflow_management": (
        "Good workflow management tools for small teams should clarify handoffs, approvals, "
        "and recurring processes without adding unnecessary bureaucracy."
    ),
    "task_management": (
        "Good task management tools for small teams should make ownership, due dates, and "
        "status visible without adding unnecessary complexity."
    ),
}


def strip_leading_best(keyword: str) -> str:
    """Remove a leading 'best ' so titles/questions do not repeat it."""
    k = keyword.strip()
    if k.lower().startswith("best "):
        return k[5:].strip()
    return k


def capitalize_brand(term: str) -> str:
    """Return editorial brand capitalization for a single tool name or phrase."""
    raw = term.strip().rstrip(".")
    lower = raw.lower()
    if lower in BRAND_CAPITALIZATION:
        return BRAND_CAPITALIZATION[lower]
    for phrase, branded in sorted(BRAND_CAPITALIZATION.items(), key=lambda x: -len(x[0])):
        if " " in phrase and phrase in lower:
            return lower.replace(phrase, branded)
    if "." in raw:
        return raw.title()
    return smart_title_case(raw)


def apply_brand_capitalization(text: str) -> str:
    """Apply known brand casing to a phrase (longest multi-word matches first)."""
    result = text
    for phrase, branded in sorted(BRAND_CAPITALIZATION.items(), key=lambda x: -len(x[0])):
        result = re.sub(re.escape(phrase), branded, result, flags=re.IGNORECASE)
    return result


def is_comparison_query(keyword: str, query_intent: str) -> bool:
    """True when the query is a tool-vs-tool or explicit comparison search."""
    if query_intent == INTENT_COMPARISON:
        return True
    return bool(_COMPARISON_SIGNAL_RE.search(keyword))


def parse_comparison_parts(keyword: str) -> tuple[str, str] | None:
    """Split 'clickup vs trello' into left/right tool name strings."""
    parts = _COMPARISON_SPLIT_RE.split(keyword.strip(), maxsplit=1)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        return parts[0].strip(), parts[1].strip()
    return None


def extract_comparison_entities(keyword: str) -> tuple[str, str] | None:
    """Return branded entity names for a comparison keyword."""
    parts = parse_comparison_parts(keyword)
    if not parts:
        return None
    return capitalize_brand(parts[0]), capitalize_brand(parts[1])


def _faq_normalize_for_match(text: str) -> str:
    """Normalize FAQ text for semantic comparison (case and brand insensitive)."""
    t = apply_brand_capitalization(text)
    t = t.lower()
    t = re.sub(r"[^\w\s.]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _faq_both_entities(text: str, left: str, right: str) -> bool:
    norm = _faq_normalize_for_match(text)
    left_keys = {_faq_normalize_for_match(left), left.lower(), left.lower().replace(".com", "")}
    right_keys = {_faq_normalize_for_match(right), right.lower(), right.lower().replace(".com", "")}
    left_hit = any(k and k in norm for k in left_keys)
    right_hit = any(k and k in norm for k in right_keys)
    return left_hit and right_hit


def _comparison_faq_pattern_types(text: str, left: str, right: str) -> set[str]:
    """Canonical comparison FAQ pattern types present in a question."""
    norm = _faq_normalize_for_match(text)
    if not _faq_both_entities(norm, left, right):
        return set()
    types: set[str] = set()
    if re.search(r"better than", norm):
        types.add("better_than")
    if re.search(r"easier to use than|easier.*than", norm):
        types.add("easier_than")
    if re.search(r"which is better|which.*better", norm) or (
        " vs " in norm and "better" in norm
    ):
        types.add("which_better")
    if re.search(r"main difference between|difference between", norm):
        types.add("main_difference")
    if re.search(r"should.*(use|choose)", norm) and " or " in norm:
        types.add("should_use_or")
    if " or " in norm and re.search(r"for small (teams|business)", norm):
        types.add("or_for_teams")
    return types


def count_strong_comparison_faqs(faq_items: list[str], left: str, right: str) -> int:
    """Count FAQ items that match at least one strong comparison pattern."""
    return sum(1 for item in faq_items if _comparison_faq_pattern_types(item, left, right))


def classify_faq_coverage(
    keyword: str,
    query_intent: str,
    faq_items: list[str],
) -> tuple[str, str]:
    """Classify FAQ coverage; comparison queries use entity-aware pattern scoring."""
    if is_comparison_query(keyword, query_intent):
        entities = extract_comparison_entities(keyword)
        if entities:
            left, right = entities
            strong_count = count_strong_comparison_faqs(faq_items, left, right)
            if strong_count >= _COMPARISON_FAQ_MIN_STRONG:
                return (
                    COVERAGE_STRONG,
                    f"strong comparison FAQ coverage ({strong_count} questions)",
                )
    blob = " ".join(faq_items)
    if not blob.strip():
        return COVERAGE_MISSING, "no FAQ-style headings detected"
    return classify_coverage(keyword, blob)


def format_comparison_phrase(keyword: str) -> str:
    """Editorial 'ClickUp vs Trello' style phrase with correct brand casing."""
    parts = parse_comparison_parts(keyword)
    if parts:
        left, right = parts
        return f"{capitalize_brand(left)} vs {capitalize_brand(right)}"
    return apply_brand_capitalization(smart_title_case(strip_leading_best(keyword)))


def comparison_seo_titles(keyword: str) -> list[str]:
    """Natural SEO title options for comparison queries (never prefixed with Best)."""
    phrase = format_comparison_phrase(keyword)
    return [
        f"{phrase} for Small Teams",
        f"{phrase}: Which Is Better for Small Teams?",
        f"{phrase} Comparison for Small Teams",
    ]


def smart_best_title(keyword: str, query_intent: str = "") -> str:
    """Title-case a keyword without duplicating 'Best'; skip Best for comparisons."""
    k = keyword.strip()
    if is_comparison_query(k, query_intent):
        return format_comparison_phrase(k)
    if k.lower().startswith("best "):
        return smart_title_case(apply_brand_capitalization(k))
    return smart_title_case(f"Best {apply_brand_capitalization(strip_leading_best(k))}")


def keyword_to_natural_question_phrase(keyword: str) -> str:
    """Natural question stem for FAQ suggestions (no 'best best')."""
    core = strip_leading_best(keyword)
    if re.search(r"\b(tools|software|apps|platforms)\b", core, re.IGNORECASE):
        return f"What are the best {core}"
    return f"What is the best {core}"


def detect_content_topic(keyword: str, item: ContentItem) -> str:
    """Topic for FAQ/intro templates; collaboration is distinct from communication."""
    slug_title = f"{item.slug.replace('-', ' ')} {item.title}".lower()
    kw = keyword.lower()
    blob = f"{kw} {slug_title}"

    if "collaboration" in blob:
        return "collaboration"
    if "communication" in blob:
        return "communication"
    if "workflow" in blob:
        return "workflow_management"
    if "task-management" in item.slug or "task management" in blob:
        return "task_management"
    if "project-management" in item.slug or "project management" in blob:
        return "project_management"

    clusters = detect_primary_clusters(title=item.title, slug=item.slug, keyword=keyword)
    priority = (
        "communication",
        "project_management",
        "task_management",
        "workflow_management",
        "productivity",
        "freelancers",
    )
    for name in priority:
        if name in clusters:
            if name == "communication" and "collaboration" in blob:
                return "collaboration"
            return name
    return "project_management"


def _normalize_phrase(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _keyword_tokens(keyword: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", keyword.lower()) if t not in _STOPWORDS and len(t) > 1]


def _phrase_in_text(phrase: str, text: str) -> bool:
    if not phrase or not text:
        return False
    return _normalize_phrase(phrase) in _normalize_phrase(text)


def _token_overlap_ratio(keyword: str, text: str) -> float:
    tokens = _keyword_tokens(keyword)
    if not tokens:
        return 0.0
    blob = _normalize_phrase(text)
    hits = sum(1 for t in tokens if t in blob)
    return hits / len(tokens)


def smart_title_case(text: str) -> str:
    """Natural English title case; keep short prepositions/articles lowercase."""
    if not text.strip():
        return text

    def _case_segment(segment: str) -> str:
        words = segment.split()
        if not words:
            return segment
        out: list[str] = []
        for i, word in enumerate(words):
            core = re.sub(r"[^a-zA-Z0-9]+", "", word)
            lower = core.lower()
            if not core:
                out.append(word)
                continue
            if i == 0 or i == len(words) - 1 or lower not in _TITLE_CASE_SMALL_WORDS:
                repl = core[0].upper() + core[1:].lower() if len(core) > 1 else core.upper()
                out.append(word.replace(core, repl, 1))
            else:
                out.append(word.replace(core, lower, 1))
        return " ".join(out)

    if ":" in text:
        parts = text.split(":", 1)
        return f"{_case_segment(parts[0].strip())}: {_case_segment(parts[1].strip())}"
    return _case_segment(text)


def classify_coverage(keyword: str, text: str) -> tuple[str, str]:
    """Return coverage status and short detail for a text field."""
    if not text or not text.strip():
        return COVERAGE_MISSING, "field empty"
    if _phrase_in_text(keyword, text):
        return COVERAGE_EXACT, "exact phrase present"
    ratio = _token_overlap_ratio(keyword, text)
    if ratio >= 0.75:
        return COVERAGE_PARTIAL, f"strong token overlap ({ratio:.0%})"
    if ratio >= 0.45:
        return COVERAGE_WEAK, f"partial token overlap ({ratio:.0%})"
    return COVERAGE_MISSING, "keyword not detected"


def classify_heading_coverage(
    keyword: str,
    h2_list: list[str],
    h3_list: list[str],
) -> tuple[str, str, bool]:
    """Return status, detail, and whether exact phrase appears in H2/H3."""
    combined = h2_list + h3_list
    if not combined:
        return COVERAGE_MISSING, "no H2/H3 headings found", False
    if any(_phrase_in_text(keyword, h) for h in combined):
        return COVERAGE_EXACT, "exact phrase present in H2/H3", True
    text = " ".join(combined)
    status, detail = classify_coverage(keyword, text)
    return status, detail, False


def compute_intent_alignment(query_intent: str, page_type: str) -> str:
    """Map query intent and page type to alignment label."""
    aligned = {
        (INTENT_BROAD_BEST, PAGE_ROUNDUP),
        (INTENT_COMPARISON, PAGE_COMPARISON),
        (INTENT_REVIEW, PAGE_REVIEW),
        (INTENT_HOW_TO, PAGE_GUIDE),
    }
    partial = {
        (INTENT_INFORMATIONAL, PAGE_ROUNDUP),
        (INTENT_INFORMATIONAL, PAGE_GUIDE),
        (INTENT_BROAD_BEST, PAGE_GUIDE),
        (INTENT_UNKNOWN, PAGE_ROUNDUP),
        (INTENT_UNKNOWN, PAGE_UNKNOWN),
    }
    pair = (query_intent, page_type)
    if pair in aligned:
        return ALIGNMENT_ALIGNED
    if pair in partial:
        return ALIGNMENT_PARTIAL
    misaligned_pairs = {
        (INTENT_BROAD_BEST, PAGE_REVIEW),
        (INTENT_BROAD_BEST, PAGE_COMPARISON),
        (INTENT_REVIEW, PAGE_ROUNDUP),
        (INTENT_COMPARISON, PAGE_ROUNDUP),
        (INTENT_HOW_TO, PAGE_ROUNDUP),
        (INTENT_HOW_TO, PAGE_REVIEW),
    }
    if pair in misaligned_pairs:
        return ALIGNMENT_MISALIGNED
    if query_intent == INTENT_BROAD_BEST and page_type in (PAGE_REVIEW, PAGE_COMPARISON, PAGE_GUIDE):
        return ALIGNMENT_MISALIGNED
    if query_intent == INTENT_REVIEW and page_type != PAGE_REVIEW:
        return ALIGNMENT_MISALIGNED
    if query_intent == INTENT_COMPARISON and page_type != PAGE_COMPARISON:
        return ALIGNMENT_MISALIGNED
    if query_intent == INTENT_HOW_TO and page_type != PAGE_GUIDE:
        return ALIGNMENT_MISALIGNED
    return ALIGNMENT_PARTIAL


def find_item_by_url(catalog: list[ContentItem], target_url: str) -> ContentItem | None:
    target_norm = normalize_internal_url(target_url)
    if not target_norm:
        return None
    for item in catalog:
        if item.normalized_url() == target_norm:
            return item
    return None


def _first_n_words(text: str, n: int) -> str:
    words = text.split()
    return " ".join(words[:n]) if words else ""


def _is_comparison_link_fragment(heading: str) -> bool:
    """Exclude internal-link comparison titles mistaken for FAQ questions."""
    h = heading.strip()
    hl = h.lower()
    if " vs " not in hl and " versus " not in hl:
        return False
    if re.match(r"^[a-z]{1,4}\s+vs\b", hl):
        return True
    if not h.endswith("?"):
        return True
    if not _QUESTION_STARTER_RE.match(h):
        return True
    return False


def _is_valid_faq_heading(heading: str, in_faq_section: bool) -> bool:
    h = heading.strip()
    if not h or h.lower() in {"faq", "faqs"}:
        return False
    if _is_comparison_link_fragment(h):
        return False
    hl = h.lower()
    if any(m in hl for m in _FAQ_HEADING_MARKERS) and h.lower() != "faq":
        return True
    if in_faq_section:
        return h.endswith("?") or _QUESTION_STARTER_RE.match(h)
    if h.endswith("?"):
        return _QUESTION_STARTER_RE.match(h) is not None
    return _QUESTION_STARTER_RE.match(h) is not None


def _extract_faq_items(content_html: str, headings: dict[str, list[str]]) -> list[str]:
    """FAQ headings only — not anchor text or comparison link titles."""
    items: list[str] = []
    in_faq_section = False

    if content_html:
        soup = BeautifulSoup(content_html, "html.parser")
        for tag in soup.find_all(["h2", "h3"]):
            text = tag.get_text(strip=True)
            if not text:
                continue
            tl = text.lower()
            if any(m in tl for m in _FAQ_HEADING_MARKERS):
                in_faq_section = True
                if tl not in {"faq", "faqs"} and _is_valid_faq_heading(text, True):
                    items.append(text)
                continue
            if _is_valid_faq_heading(text, in_faq_section):
                items.append(text)
    else:
        for level in ("h2", "h3"):
            for h in headings.get(level, []):
                if _is_valid_faq_heading(h, False):
                    items.append(h)

    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:20]


def _heading_relevant(keyword: str, heading: str) -> bool:
    return _token_overlap_ratio(keyword, heading) >= 0.4 or _phrase_in_text(keyword, heading)


def _generate_intro_sentence(
    keyword: str,
    query_intent: str,
    page_type: str,
    topic: str,
) -> str:
    kw = keyword.strip().rstrip(".")
    if query_intent == INTENT_REVIEW or page_type == PAGE_REVIEW:
        brand = _keyword_tokens(kw)
        product = capitalize_brand(brand[0]) if brand else "this tool"
        return (
            f"This {product} review for small businesses covers pricing, meeting quality, "
            f"ease of use, and whether it is worth it for day-to-day team communication."
        )
    if is_comparison_query(kw, query_intent) or page_type == PAGE_COMPARISON:
        phrase = format_comparison_phrase(kw)
        return (
            f"Choosing between {phrase} for a small team comes down to workflow complexity, "
            f"pricing, and how clearly each platform handles tasks, deadlines, and collaboration."
        )
    if query_intent == INTENT_HOW_TO:
        core = strip_leading_best(kw)
        return (
            f"To improve {core}, start with a simple workflow your team can follow every week: "
            f"clear ownership, visible deadlines, and one shared place for updates."
        )
    return _TOPIC_INTRO_SENTENCES.get(topic, _TOPIC_INTRO_SENTENCES["project_management"])


def _generate_heading_suggestions(
    keyword: str,
    query_intent: str,
    topic: str,
    existing: list[str],
    max_suggestions: int,
) -> list[str]:
    title_line = smart_best_title(keyword, query_intent)
    core = smart_title_case(apply_brand_capitalization(strip_leading_best(keyword)))
    candidates: list[str] = []
    if is_comparison_query(keyword, query_intent):
        phrase = format_comparison_phrase(keyword)
        candidates = [
            f"{phrase}: Quick Verdict",
            f"{phrase}: Main Differences",
            f"{phrase} for Small Teams",
        ]
    elif query_intent == INTENT_BROAD_BEST:
        if topic == "collaboration":
            candidates = [
                title_line,
                smart_title_case(f"How to Choose {strip_leading_best(keyword)}"),
                smart_title_case(f"What Small Teams Should Look for in {strip_leading_best(keyword)}"),
                smart_title_case("Collaboration Tools vs Communication Tools for Small Teams"),
            ]
        elif topic == "communication":
            candidates = [
                title_line,
                smart_title_case(f"How to Choose {strip_leading_best(keyword)}"),
                smart_title_case("Communication Tools vs Collaboration Tools for Small Teams"),
            ]
        elif topic == "project_management":
            candidates = [
                title_line,
                smart_title_case(
                    "Project Management Tools vs Project Management Software for Small Teams"
                ),
                smart_title_case("How to Choose Project Management Software for a Small Team"),
                smart_title_case(f"What Small Teams Should Look for in {core}"),
            ]
        else:
            candidates = [
                title_line,
                smart_title_case(f"How to Choose {strip_leading_best(keyword)}"),
                smart_title_case(f"What Small Teams Should Look for in {core}"),
            ]
    elif query_intent == INTENT_REVIEW:
        brand = _keyword_tokens(keyword)
        product = capitalize_brand(brand[0]) if brand else smart_best_title(keyword, query_intent).split()[0]
        candidates = [
            smart_title_case(f"Is {product} Good for Small Businesses?"),
            smart_title_case(f"{product} Pricing and Plans for Small Teams"),
            smart_title_case(f"Pros and Cons of {product} for Small Business Use"),
            smart_title_case(f"Who Should Use {product}?"),
        ]
    elif query_intent == INTENT_HOW_TO:
        candidates = [
            smart_title_case(f"How to {strip_leading_best(keyword)}"),
            "Step-by-Step Setup for Small Teams",
            "Common Mistakes to Avoid",
        ]
    else:
        candidates = [
            f"{title_line}: Overview",
            "What You Need to Know",
            "Practical Recommendations",
        ]

    existing_lower = {h.lower() for h in existing}
    out: list[str] = []
    for c in candidates:
        if c.lower() not in existing_lower:
            out.append(c)
        if len(out) >= max_suggestions:
            break
    return out


def _generate_faq_suggestions(
    keyword: str,
    query_intent: str,
    topic: str,
    existing: list[str],
    max_suggestions: int,
) -> list[str]:
    kw = keyword.strip().rstrip("?")
    if is_comparison_query(kw, query_intent):
        entities = extract_comparison_entities(kw)
        if entities:
            left, right = entities
            candidates = [
                f"Is {left} better than {right}?",
                f"Is {right} easier to use than {left}?",
                f"Which is better for small teams, {left} or {right}?",
                f"What is the main difference between {left} and {right}?",
                f"Should a small business use {left} or {right}?",
            ]
            existing_types: set[str] = set()
            for ex in existing:
                existing_types |= _comparison_faq_pattern_types(ex, left, right)
            filtered: list[str] = []
            for c in candidates:
                cand_types = _comparison_faq_pattern_types(c, left, right)
                if cand_types and cand_types & existing_types:
                    continue
                filtered.append(c)
            candidates = filtered
        else:
            phrase = format_comparison_phrase(kw)
            candidates = [
                f"Which is better for small teams in {phrase}?",
                f"What is the main difference in {phrase}?",
                "Which option is easier for a small team to adopt?",
                "Which tool has better pricing for small businesses?",
            ]
    elif query_intent == INTENT_REVIEW:
        brand = _keyword_tokens(kw)
        product = capitalize_brand(brand[0]) if brand else "this tool"
        candidates = [
            f"Is {product} good for small businesses?",
            f"Is {product} good for small business video meetings and calling?",
            f"Is {product} worth it for a small business?",
            f"What is the best alternative to {product} for small businesses?",
            f"How much does {product} cost for a small team?",
        ]
    elif query_intent == INTENT_BROAD_BEST:
        candidates = list(_TOPIC_FAQ_TEMPLATES.get(topic, _TOPIC_FAQ_TEMPLATES["project_management"]))
    else:
        candidates = [
            f"{keyword_to_natural_question_phrase(kw)}?",
            f"Who is {smart_best_title(kw, query_intent)} best for?",
            "What should I consider before choosing?",
        ]

    existing_blob = " ".join(existing).lower()
    out: list[str] = []
    for c in candidates:
        if "best best" in c.lower():
            continue
        if c.lower() not in existing_blob:
            out.append(c)
        if len(out) >= max_suggestions:
            break
    return out


def _slug_recommendation(item: ContentItem, keyword: str) -> str:
    """Safe slug guidance for published URLs — never casually suggest replacing indexed slugs."""
    slug_status, _ = classify_coverage(keyword, item.slug.replace("-", " "))
    if slug_status in (COVERAGE_EXACT, COVERAGE_PARTIAL):
        return "Keep current slug"
    return "Review manually; changing published slugs can affect SEO and redirects"


def _build_title_meta(
    keyword: str,
    item: ContentItem,
    query_intent: str,
    topic: str,
) -> TitleMetaSuggestions:
    if query_intent == INTENT_REVIEW:
        brand = _keyword_tokens(keyword)
        product = capitalize_brand(brand[0]) if brand else smart_best_title(keyword, query_intent)
        seo_title = smart_title_case(f"{product} Review for Small Businesses: Is It Worth It?")
        meta = (
            f"Read our {product} review for small businesses: pricing, pros and cons, "
            f"and whether it fits your team's meetings and communication needs."
        )[:158]
        focus = f"{product.lower()} review small business"
    elif is_comparison_query(keyword, query_intent):
        phrase = format_comparison_phrase(keyword)
        seo_title = comparison_seo_titles(keyword)[0]
        meta = (
            f"Compare {phrase} for small teams, including ease of use, features, "
            f"workflows, project management, and which tool fits best."
        )[:158]
        focus = keyword.lower().strip()
    else:
        seo_title = smart_title_case(f"{smart_best_title(keyword, query_intent)}: Practical Guide")
        topic_hint = topic.replace("_", " ")
        meta = (
            f"Find the best {topic_hint} options for small teams: features, pricing, and "
            f"practical recommendations without unnecessary complexity."
        )[:158]
        focus = strip_leading_best(keyword).lower()
        if not focus.startswith("best "):
            focus = f"best {focus}"

    if len(meta) > 160:
        meta = meta[:157] + "..."
    return TitleMetaSuggestions(
        seo_title=seo_title,
        meta_description=meta,
        focus_keyword=focus,
        slug_recommendation=_slug_recommendation(item, keyword),
    )


def _gsc_row_to_metrics(row, *, matched_via: str, match_note: str) -> GscQueryMetrics:
    return GscQueryMetrics(
        query=row.query,
        clicks=row.clicks,
        impressions=row.impressions,
        ctr=row.ctr,
        position=row.position,
        available=True,
        matched_via=matched_via,
        match_note=match_note,
    )


def _queries_for_target_page(
    gsc_cache: GscCache,
    target_norm: str,
) -> list[str]:
    """Distinct queries in GSC cache associated with the target page URL."""
    found: list[str] = []
    seen: set[str] = set()
    for qp in gsc_cache.query_pages:
        page_norm = normalize_internal_url(qp.page)
        if page_norm == target_norm and qp.query.lower().strip() not in seen:
            seen.add(qp.query.lower().strip())
            found.append(qp.query)
    return found


def _lookup_gsc_metrics(
    gsc_cache: GscCache | None,
    lookup_query: str,
    target_url: str,
) -> GscQueryMetrics | None:
    if not gsc_cache:
        return None
    q_norm = _normalize_phrase(lookup_query)
    target_norm = normalize_internal_url(target_url)

    for row in gsc_cache.queries:
        if _normalize_phrase(row.query) == q_norm:
            return _gsc_row_to_metrics(row, matched_via="exact", match_note="")

    page_queries = _queries_for_target_page(gsc_cache, target_norm) if target_norm else []
    candidates: list[tuple[float, object, bool]] = []

    for row in gsc_cache.queries:
        overlap = _token_overlap_ratio(lookup_query, row.query)
        on_page = row.query in page_queries or any(
            _normalize_phrase(row.query) == _normalize_phrase(pq) for pq in page_queries
        )
        if on_page:
            overlap = max(overlap, _GSC_RELATED_MIN_OVERLAP)
        if overlap >= _GSC_RELATED_MIN_OVERLAP:
            score = overlap + (0.25 if on_page else 0.0) + (row.impressions / 10000.0)
            candidates.append((score, row, on_page))

    if not candidates and page_queries:
        for pq in page_queries:
            for row in gsc_cache.queries:
                if _normalize_phrase(row.query) == _normalize_phrase(pq):
                    return _gsc_row_to_metrics(
                        row,
                        matched_via="related",
                        match_note=f"GSC metrics matched from related query: {row.query}",
                    )

    if candidates:
        candidates.sort(key=lambda x: -x[0])
        best_row = candidates[0][1]
        note = ""
        if _normalize_phrase(best_row.query) != q_norm:
            note = f"GSC metrics matched from related query: {best_row.query}"
        return _gsc_row_to_metrics(
            best_row,
            matched_via="related" if note else "exact",
            match_note=note,
        )
    return None


def _inbound_link_support(catalog: list[ContentItem], target_url: str, keyword: str) -> InternalLinkSupport:
    linking = pages_already_linking(catalog, target_url)
    count = len(linking)
    if count >= 5:
        level = LINK_SUPPORT_STRONG
    elif count >= 2:
        level = LINK_SUPPORT_MODERATE
    elif count >= 1:
        level = LINK_SUPPORT_WEAK
    else:
        level = LINK_SUPPORT_WEAK
    cmd = (
        f'python -m linkops.cli suggest --target-url "{target_url}" '
        f'--target-keyword "{keyword}" --max-suggestions 8'
    )
    notes = f"{count} catalog page(s) already link to this target."
    if count == 0:
        notes = "No inbound internal links detected in WordPress cache."
    return InternalLinkSupport(
        inbound_count=count,
        support_level=level,
        next_suggest_command=cmd,
        notes=notes,
    )


def _aggregate_coverage_status(fields: list[CoverageField]) -> dict[str, str]:
    return {f.field_name: f.status for f in fields}


def _coverage_is_strong(coverage_map: dict[str, str]) -> bool:
    """True when title/slug/intro/body/headings/FAQ are in good shape."""
    return (
        coverage_map.get("title") in _STRONG_COVERAGE
        and coverage_map.get("slug") in _STRONG_COVERAGE
        and coverage_map.get("first_150_words") == COVERAGE_EXACT
        and coverage_map.get("body") in _STRONG_COVERAGE
        and coverage_map.get("headings") in _STRONG_COVERAGE
        and coverage_map.get("faq") in _STRONG_COVERAGE
    )


def _core_coverage_strong(coverage_map: dict[str, str]) -> bool:
    return all(coverage_map.get(f) in _STRONG_COVERAGE for f in _CORE_COVERAGE_FIELDS)


def _faq_coverage_sufficient(coverage_map: dict[str, str]) -> bool:
    return coverage_map.get("faq") in (COVERAGE_EXACT, COVERAGE_STRONG)


def _only_faq_gap(coverage_map: dict[str, str]) -> bool:
    """Core fields strong but FAQ still needs work."""
    return _core_coverage_strong(coverage_map) and not _faq_coverage_sufficient(coverage_map)


def _comparison_page_well_covered(
    keyword: str,
    query_intent: str,
    coverage_map: dict[str, str],
    link_support: str,
) -> bool:
    if not is_comparison_query(keyword, query_intent):
        return False
    return (
        _core_coverage_strong(coverage_map)
        and _faq_coverage_sufficient(coverage_map)
        and link_support == LINK_SUPPORT_STRONG
    )


def _has_material_content_gaps(coverage_map: dict[str, str]) -> bool:
    if _only_faq_gap(coverage_map):
        return False
    check_fields = ("title", "slug", "first_150_words", "headings", "body")
    return any(coverage_map.get(f) in (COVERAGE_MISSING, COVERAGE_WEAK) for f in check_fields)


def _compute_overall_recommendation(
    *,
    keyword: str,
    query_intent: str,
    coverage_map: dict[str, str],
    intent_alignment: str,
    gsc: GscQueryMetrics | None,
    link_support: str,
) -> tuple[str, list[str], str]:
    priority: list[str] = []
    strong = _coverage_is_strong(coverage_map)
    material_gaps = _has_material_content_gaps(coverage_map)

    if intent_alignment == ALIGNMENT_MISALIGNED:
        priority.append("Review page type vs query intent before heavy optimization.")
        rationale = "Query intent and page type do not align; manual editorial review is safer than bulk edits."
        return REC_REVIEW_MANUAL, priority, rationale

    if (
        gsc
        and gsc.available
        and gsc.clicks == 0
        and gsc.impressions >= 20
        and 8 <= gsc.position <= 20
        and not material_gaps
    ):
        priority.append("On-page coverage is solid; prioritize title/meta CTR and indexing.")
        rationale = (
            f"GSC shows position {gsc.position:.1f} with zero clicks — title/meta and SERP presentation "
            "are the main levers, not major content rewrites."
        )
        return REC_TITLE_META, priority, rationale

    if _comparison_page_well_covered(keyword, query_intent, coverage_map, link_support):
        priority.append("Monitor GSC performance; comparison page is well covered.")
        rationale = (
            "Core comparison coverage, FAQ coverage, and internal link support are strong. "
            "Monitor GSC performance before making more edits."
        )
        if gsc and gsc.available and 20 < gsc.position <= 90:
            return REC_MONITOR, priority, rationale
        return REC_NO_CHANGE, priority, rationale

    if _only_faq_gap(coverage_map):
        priority.append("Improve FAQ coverage only.")
        rationale = (
            "Title, slug, intro, headings, and body are already strong; FAQ is the main remaining gap."
        )
        if link_support == LINK_SUPPORT_STRONG:
            return REC_FAQ_OPTIMIZATION, priority, rationale
        return REC_LIGHT, priority, rationale

    if strong and link_support == LINK_SUPPORT_STRONG:
        if gsc and gsc.available and 20 < gsc.position <= 90:
            priority.append("Strong coverage and internal links; monitor position movement.")
            rationale = (
                f"Content and internal links are already strong; GSC position {gsc.position:.1f} "
                "suggests monitoring rather than heavy optimization."
            )
            return REC_MONITOR, priority, rationale
        priority.append("No urgent on-page or internal-link changes detected.")
        rationale = "Title, slug, intro, body, headings, FAQ, and internal links are already in good shape."
        return REC_NO_CHANGE, priority, rationale

    if material_gaps:
        priority.append("Add or strengthen target keyword in title, intro, headings, and FAQ.")
        rationale = "One or more important coverage areas are weak or missing the target keyword."
        return REC_CONTENT, priority, rationale

    if link_support in (LINK_SUPPORT_WEAK, LINK_SUPPORT_UNKNOWN):
        priority.append("Build internal link support from related articles.")
        rationale = "Content coverage is acceptable, but inbound internal links are limited."
        return REC_INTERNAL_LINKS, priority, rationale

    if strong and gsc and gsc.available and 20 < gsc.position <= 90:
        priority.append("Coverage is strong; monitor GSC position and CTR.")
        rationale = (
            f"On-page coverage is already strong for position {gsc.position:.1f}; "
            "prefer monitoring or light tweaks over a full content rewrite."
        )
        return REC_MONITOR, priority, rationale

    weak_any = any(coverage_map.get(f) == COVERAGE_WEAK for f in coverage_map)
    if weak_any:
        priority.append("Light copy tweaks may improve topical clarity.")
        rationale = "Some fields show only partial keyword overlap; light edits may help."
        return REC_LIGHT, priority, rationale

    priority.append("Monitor GSC position and CTR; no urgent on-page changes detected.")
    rationale = "No material content gaps detected; continue monitoring performance."
    return REC_NO_CHANGE, priority, rationale


def _build_content_gaps(
    coverage: list[CoverageField],
    headings: HeadingAnalysis,
    faq: FaqAnalysis,
    coverage_map: dict[str, str],
) -> list[str]:
    if _only_faq_gap(coverage_map):
        return ["Improve FAQ coverage only."]

    gaps: list[str] = []
    skip_heading_gap = not headings.keyword_in_h2_recommended and not headings.missing_opportunities
    for field in coverage:
        if field.field_name == "headings" and skip_heading_gap:
            continue
        if field.field_name == "faq":
            continue
        if field.status in (COVERAGE_MISSING, COVERAGE_WEAK):
            gaps.append(f"Improve {field.field_name}: {field.detail}")
    for h in headings.missing_opportunities[:1]:
        gaps.append(h)
    faq_field = coverage_map.get("faq")
    if faq_field in (COVERAGE_MISSING, COVERAGE_WEAK) and faq.suggestions:
        gaps.append("Improve FAQ coverage with question-style H2/H3 headings.")
    return gaps


def _executive_summary(
    keyword: str,
    overall: str,
    intent_alignment: str,
    gsc: GscQueryMetrics | None,
    rationale: str,
) -> str:
    parts = [f"Target keyword «{keyword}» — overall recommendation: {overall}."]
    parts.append(f"Intent alignment: {intent_alignment}.")
    if gsc and gsc.available:
        gsc_line = (
            f"GSC: {gsc.impressions} impressions, {gsc.clicks} clicks, avg position {gsc.position:.1f}."
        )
        if gsc.match_note:
            gsc_line += f" {gsc.match_note}"
        parts.append(gsc_line)
    else:
        parts.append("GSC metrics not available for this query (import gsc-import to enrich).")
    parts.append(f"Why this recommendation: {rationale}")
    return " ".join(parts)


def analyze_content_optimization(
    catalog: list[ContentItem],
    target_url: str,
    target_keyword: str,
    *,
    gsc_query: str | None = None,
    gsc_cache: GscCache | None = None,
    max_faq_suggestions: int = 5,
    max_heading_suggestions: int = 5,
) -> ContentOptimizationReport:
    """Build a full content optimization report for one target page."""
    item = find_item_by_url(catalog, target_url)
    if item is None:
        raise ValueError(
            f"Target URL not found in WordPress content cache: {target_url}\n"
            "Run: python -m linkops.cli fetch"
        )

    keyword = target_keyword.strip()
    gsc_lookup = (gsc_query or keyword).strip()
    topic = detect_content_topic(keyword, item)
    query_intent = detect_query_intent(keyword)
    page_type = detect_gsc_page_type(item)
    intent_alignment = compute_intent_alignment(query_intent, page_type)

    plain = item.plain_text or html_to_plain_text(item.content_html)
    headings_raw = extract_headings(item.content_html)
    all_headings = headings_raw["h1"] + headings_raw["h2"] + headings_raw["h3"]
    intro_100 = _first_n_words(plain, 100)
    intro_150 = _first_n_words(plain, 150)
    slug_text = item.slug.replace("-", " ")

    heading_status, heading_detail, exact_in_headings = classify_heading_coverage(
        keyword, headings_raw["h2"], headings_raw["h3"]
    )

    coverage = [
        CoverageField("title", *classify_coverage(keyword, item.title)),
        CoverageField("slug", *classify_coverage(keyword, slug_text)),
        CoverageField(
            "h1",
            *classify_coverage(keyword, " ".join(headings_raw["h1"]) or item.title),
        ),
        CoverageField("headings", heading_status, heading_detail),
        CoverageField("first_100_words", *classify_coverage(keyword, intro_100)),
        CoverageField("first_150_words", *classify_coverage(keyword, intro_150)),
        CoverageField("body", *classify_coverage(keyword, plain)),
    ]

    faq_existing = _extract_faq_items(item.content_html, headings_raw)
    faq_status, faq_detail = classify_faq_coverage(keyword, query_intent, faq_existing)
    coverage.append(CoverageField("faq", faq_status, faq_detail))

    exact_early = _phrase_in_text(keyword, intro_150[: max(len(intro_150) // 2, 80)])
    answers_intent = intent_alignment == ALIGNMENT_ALIGNED or _token_overlap_ratio(keyword, intro_150) >= 0.5
    too_generic = _token_overlap_ratio(keyword, intro_150) < 0.35 and not exact_early
    needs_direct = not (exact_early and answers_intent and not too_generic)
    paste_sentence = (
        _generate_intro_sentence(keyword, query_intent, page_type, topic)
        if needs_direct
        else _INTRO_NO_SENTENCE
    )

    intro = IntroAnalysis(
        word_count=len(intro_150.split()),
        exact_keyword_early=exact_early,
        answers_intent=answers_intent,
        too_generic=too_generic,
        needs_direct_sentence=needs_direct,
        paste_ready_sentence=paste_sentence,
        notes=[
            "Exact keyword in first 150 words." if exact_early else "Exact keyword not in opening 150 words.",
            "Intro aligns with detected query intent." if answers_intent else "Intro may not directly answer search intent.",
        ],
    )

    relevant = [h for h in all_headings if _heading_relevant(keyword, h)]
    missing_ops: list[str] = []
    heading_suggestions: list[str] = []
    keyword_h2_rec = False

    if exact_in_headings:
        keyword_h2_rec = False
    elif heading_status == COVERAGE_PARTIAL:
        missing_ops.append(
            "Consider one H2 with a close variant of the target keyword (exact phrase not yet in H2/H3)."
        )
        heading_suggestions = _generate_heading_suggestions(
            keyword, query_intent, topic, all_headings, 1
        )[:1]
        keyword_h2_rec = False
    elif heading_status in (COVERAGE_MISSING, COVERAGE_WEAK):
        missing_ops.append("Add one H2 that includes the target keyword or a close variant.")
        heading_suggestions = _generate_heading_suggestions(
            keyword, query_intent, topic, all_headings, 1
        )[:1]
        keyword_h2_rec = True
    else:
        keyword_h2_rec = False

    headings = HeadingAnalysis(
        h1=headings_raw["h1"],
        h2=headings_raw["h2"],
        h3=headings_raw["h3"],
        relevant_headings=relevant,
        missing_opportunities=missing_ops,
        keyword_in_h2_recommended=keyword_h2_rec,
        suggestions=heading_suggestions,
    )

    faq_suggestions = _generate_faq_suggestions(
        keyword, query_intent, topic, faq_existing, max_faq_suggestions
    )
    faq_note = ""
    if faq_status == COVERAGE_STRONG:
        faq_note = "strong comparison coverage detected"
    faq = FaqAnalysis(
        existing_faq_items=faq_existing,
        suggestions=faq_suggestions,
        coverage_note=faq_note,
    )

    title_meta = _build_title_meta(keyword, item, query_intent, topic)
    gsc_metrics = _lookup_gsc_metrics(gsc_cache, gsc_lookup, target_url)
    internal = _inbound_link_support(catalog, target_url, keyword)
    coverage_map = _aggregate_coverage_status(coverage)
    overall, priority, rationale = _compute_overall_recommendation(
        keyword=keyword,
        query_intent=query_intent,
        coverage_map=coverage_map,
        intent_alignment=intent_alignment,
        gsc=gsc_metrics,
        link_support=internal.support_level,
    )

    content_gaps = _build_content_gaps(coverage, headings, faq, coverage_map)
    target_norm = normalize_internal_url(target_url) or target_url
    next_commands = [
        internal.next_suggest_command,
        f'python -m linkops.cli optimize --target-url "{target_norm}/" --target-keyword "{keyword}"',
    ]
    if gsc_cache is None:
        next_commands.append("python -m linkops.cli gsc-import --queries-csv .\\exports\\gsc_queries.csv")

    return ContentOptimizationReport(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        target_url=target_norm + "/" if not target_url.endswith("/") else target_url,
        target_keyword=keyword,
        gsc_query=gsc_lookup,
        query_intent=query_intent,
        page_type=page_type,
        intent_alignment=intent_alignment,
        coverage=coverage,
        intro=intro,
        headings=headings,
        faq=faq,
        title_meta=title_meta,
        content_gaps=content_gaps,
        internal_links=internal,
        overall_recommendation=overall,
        priority_actions=priority,
        recommendation_rationale=rationale,
        executive_summary=_executive_summary(
            keyword, overall, intent_alignment, gsc_metrics, rationale
        ),
        gsc_metrics=gsc_metrics,
        next_commands=next_commands,
        request_indexing_urls=[target_norm + "/"],
    )
