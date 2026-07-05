# WordPress MU Plugin Deployment State — WorkToolsLab

**Date:** 2026-07-06  
**Status:** Live plugins deployed manually by owner; repository mirrors added for version control.

---

## Purpose

Preserve canonical copies of custom Must-Use plugins that control WorkToolsLab author box rendering and Rank Math / Kadence author identity behavior.

---

## Live deployment

| Item | Path |
|------|------|
| **WordPress MU plugins directory** | `/wp-content/mu-plugins/` |
| **Author Box plugin** | `worktoolslab-author-box.php` |
| **Author Links plugin** | `worktoolslab-author-links.php` |
| **Version (both)** | 1.1.0 (inline CSS version on Author Box) |

**Deployment method:** Manual upload/edit in hosting file manager or SFTP — **not** automated from this repository.

---

## Repository mirrors

| Repository path | Live path |
|-----------------|-----------|
| `wordpress/mu-plugins/worktoolslab-author-box.php` | `wp-content/mu-plugins/worktoolslab-author-box.php` |
| `wordpress/mu-plugins/worktoolslab-author-links.php` | `wp-content/mu-plugins/worktoolslab-author-links.php` |

---

## Author Box plugin behavior (mirror spec)

- Renders on **singular posts only** (`is_singular('post')`).
- **Author name** links to `https://worktoolslab.com/about/hayssam-dennaoui/`.
- **View all posts** links to `get_author_posts_url()`.
- **Bio** from WordPress user description (`get_the_author_meta('description')`).
- Enqueues Kadence `author-box.min.css` + inline CSS (`worktoolslab-author-box`, v1.1.0).
- Appended via `the_content` filter (Kadence built-in author box disabled on live site).

---

## Author Links plugin behavior (mirror spec)

- `kadence_author_use_profile_link` → `true`.
- **No** global `author_link` override forcing archive URLs (removed in live update).
- `rank_math/json_ld` filter normalizes:
  - Hayssam **Person** `@id` / `url` → dedicated profile URL
  - `jobTitle` → Editor
  - `worksFor` → WorkToolsLab
  - `sameAs` → LinkedIn
  - **BlogPosting / Article / NewsArticle** `author` → profile `@id`
  - **Profile page** → ProfilePage + `mainEntity` Person where applicable
  - Adds Person entity on profile page if missing

**Does not modify:** Rank Math publisher / site `#person` Knowledge Graph entity (Organization vs Person+Organization).

---

## Sync rules

1. **Repository changes do not deploy automatically** to WordPress.
2. Before replacing live files, **back up** current MU plugins on the server.
3. After editing either copy, **diff live vs repository** and align intentionally.
4. Document material live-only hotfixes in `docs/P0_A_AUTHORITY_LIVE_IMPLEMENTATION_RECORD_2026_07.md` or this file.
5. No secrets, API keys, or credentials belong in these plugins.

---

## Future deployment options (not implemented)

- SFTP sync script documented in repo
- CI deploy to staging
- Version bump comment in plugin header when behavior changes

---

## Related docs

- `docs/AUTHOR_BYLINE_SCHEMA_IMPLEMENTATION_2026_07.md`
- `docs/P0_A_AUTHORITY_LIVE_IMPLEMENTATION_RECORD_2026_07.md`
