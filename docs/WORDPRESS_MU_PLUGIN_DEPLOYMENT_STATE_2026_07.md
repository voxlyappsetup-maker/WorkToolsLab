# WordPress MU Plugin Deployment State — WorkToolsLab

**Date:** 2026-07-06 (initial) · **P0-7 sync:** 2026-07-10
**Status:** Live plugins deployed manually by owner; repository mirrors synchronized to verified live implementation.

---

## Purpose

Preserve canonical copies of custom Must-Use plugins that control WorkToolsLab author box rendering and Rank Math / Kadence author identity behavior.

---

## Live deployment

| Item | Path |
|------|------|
| **WordPress MU plugins directory** | `/wp-content/mu-plugins/` |
| **Author Box plugin** | `worktoolslab-author-box.php` — **unchanged** |
| **Author Links plugin** | `worktoolslab-author-links.php` — **updated live 2026-07-10** |
| **Author Box version** | 1.1.0 (inline CSS version on Author Box) |

**Deployment method:** Manual upload/edit in hosting file manager (SiteGround) — **not** automated from this repository.

**P0-7 note:** Live `worktoolslab-author-links.php` was manually updated on SiteGround; SiteGround cache purged after fix. Repository mirror synchronized in commit for this closeout.

---

## Repository mirrors

| Repository path | Live path | Sync status |
|-----------------|-----------|-------------|
| `wordpress/mu-plugins/worktoolslab-author-box.php` | `wp-content/mu-plugins/worktoolslab-author-box.php` | Unchanged |
| `wordpress/mu-plugins/worktoolslab-author-links.php` | `wp-content/mu-plugins/worktoolslab-author-links.php` | **Synchronized 2026-07-10** — exact verified live implementation |

---

## Author Box plugin behavior (mirror spec — unchanged)

- Renders on **singular posts only** (`is_singular('post')`).
- **Author name** links to `https://worktoolslab.com/about/hayssam-dennaoui/`.
- **View all posts** links to `get_author_posts_url()`.
- **Bio** from WordPress user description (`get_the_author_meta('description')`).
- Enqueues Kadence `author-box.min.css` + inline CSS (`worktoolslab-author-box`, v1.1.0).
- Appended via `the_content` filter (Kadence built-in author box disabled on live site).

---

## Author Links plugin behavior (mirror spec — P0-7 update)

### Kadence (preserved)

- `kadence_author_use_profile_link` → `true` (priority 999).

### Dedicated author profile page (`/about/hayssam-dennaoui/`)

Deterministic four-entity graph via `rank_math/json_ld` filter (priority 99):

| Entity key | @type | @id |
|------------|-------|-----|
| `worktoolslab_organization` | Organization | `/#organization` |
| `worktoolslab_website` | WebSite | `/#website` |
| `worktoolslab_author_profile_page` | ProfilePage | `/about/hayssam-dennaoui/#webpage` |
| `worktoolslab_author_profile_person` | Person | `/about/hayssam-dennaoui/` |

- **No Article/BlogPosting** on profile page.
- ProfilePage `mainEntity` → Hayssam Person.
- WebSite `publisher` → Organization `#organization`.
- Person `worksFor` → Organization `#organization`.
- Optional Gravatar ImageObject (96px) when avatar available.

### All other pages (preserved normalization)

- Normalize existing Hayssam **Person** entities (`@id`, `url`, `jobTitle`, `description`, `worksFor`, `sameAs`).
- Normalize **Article / BlogPosting / NewsArticle** `author` → canonical profile `@id`.
- **Does not** rebuild Rank Math's full graph on non-profile pages.

### Canonical URLs (live)

| Role | URL |
|------|-----|
| Hayssam profile | https://worktoolslab.com/about/hayssam-dennaoui/ |
| WorkToolsLab Organization | https://worktoolslab.com/#organization |
| WorkToolsLab WebSite | https://worktoolslab.com/#website |
| Author archive (separate, not redirected) | https://worktoolslab.com/author/hayssam-dennaoui/ |

### Rank Math configuration (live — owner change)

- **Local SEO → Person or Company:** **Organization** (changed from Person).
- **Default Article schema:** removed from dedicated profile page.

---

## Sync rules

1. **Repository changes do not deploy automatically** to WordPress.
2. Before replacing live files, **back up** current MU plugins on the server.
3. After editing either copy, **diff live vs repository** and align intentionally.
4. Document material live-only hotfixes in closeout records or this file.
5. No secrets, API keys, or credentials belong in these plugins.

---

## P0-7 validation (live)

| Check | Result |
|-------|--------|
| Google TEST LIVE URL | **1 valid Profile page item** (Jul 10, 2026, 5:17 PM) |
| Mixed `#person` Person+Organization | **Absent** after fix |
| Indexing requested | Once — do not repeat |
| Google Index tab reprocessed | **Pending** — not claimed |

**Closeout:** `docs/P0_7_PUBLISHER_PROFILEPAGE_SCHEMA_LIVE_FIX_2026_07.md`

---

## Related docs

- `docs/AUTHOR_BYLINE_SCHEMA_IMPLEMENTATION_2026_07.md`
- `docs/P0_A_AUTHORITY_LIVE_IMPLEMENTATION_RECORD_2026_07.md`
- `docs/P0_7_PUBLISHER_PROFILEPAGE_SCHEMA_LIVE_FIX_2026_07.md`
