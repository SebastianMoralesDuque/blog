# AGENTS.md

## What This Repo Is

Static blog (Astro 5 + MDX + Tailwind) with automated content pipeline. Publishes 2 AI-generated posts/day via Ollama. Deployed to Coolify via GitHub Actions webhook.

**Site:** https://blog.sebastianmorales.sbs
**Content perspective:** Critical tech analysis from historical materialism framework.

## Commands

```bash
npm run build      # Build static site (only verification step available)
npm run dev        # Local dev server
```

No lint, typecheck, or test framework configured. `npm run build` is the only CI-equivalent check.

## Deployment (Coolify)

- **Trigger:** Push to `main` → GitHub Actions → Coolify webhook
- **Webhook:** `http://143.47.45.158:9000/deploy` (hardcoded in `.github/workflows/deploy.yml`)
- **Coolify UUID:** `zzhjq78rmhdl4aw6d0vdn3rz`
- **Build:** Dockerfile multi-stage (Node 20 Alpine builder → nginx Alpine)
- **No runtime env vars needed for static build** — Umami analytics values are baked into `Dockerfile` (lines 9-10)

## Content Pipeline

- `scripts/generate_post.py` — fetches HN + RSS, generates via Ollama, commits+pushes MDX
- Runs via cron: `0 8,20 * * *` on the VPS (not in CI)
- Posts land in `src/content/blog/` as `YYYY-MM-DD-slug.mdx`
- Images served via Pollinations.ai CDN URLs (no local storage)
- Prompt template: `scripts/prompt_template.txt`

## Credentials (set in Coolify dashboard, NOT in repo)

| Variable | Purpose | Default/Example |
|----------|---------|-----------------|
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Model name | `minimax-m3:cloud` |
| `SITE_URL` | Canonical site URL | `https://blog.sebastianmorales.sbs` |
| `FILEBROWSER_URL` | File Browser instance | `https://files.sebastianmorales.sbs` |
| `FILEBROWSER_USER` | File Browser username | `sebas` |
| `FILEBROWSER_PASS` | File Browser password | (secret) |
| `UMAMI_WEBSITE_ID` | Umami analytics ID | `6626ec48-ab22-4b2c-a57b-b047721d9263` |
| `UMAMI_SCRIPT_URL` | Umami script URL | `https://analytics.sebastianmorales.sbs/script.js` |

**IMPORTANT:** Never commit `.env`, `.env.*`, `credentials.json`, or `secrets/` — all gitignored.

## Key Architecture Decisions

- **Static site, no server runtime** — all content baked at build time
- **Ollama on VPS** — not in Docker, runs on host at 127.0.0.1:11434
- **Pollinations.ai for images** — free, no API key, CDN-served URLs
- **File Browser** at `files.sebastianmorales.sbs` — optional backup for images, not used for public serving
- **nginx in Docker** — handles SPA routing, static caching, RSS/llms.txt content types

## Content Schema

Blog posts (`src/content/blog/*.mdx`) require these frontmatter fields:

```yaml
title: string
description: string
pubDate: date
author: string (default: "Sebastian Morales")
tags: string[]
source: string
image: string (optional)
draft: boolean (default: false)
```

Schema defined in `src/content.config.ts`.

## Gotchas

- `.env.example` exists but no `.env` file on the VPS — cron script uses defaults from code
- The `generate_post.py` script auto-commits and pushes to `main`, which triggers Coolify deploy
- Blog generation log: `blog-generation.log` (gitignored)
- `openspec/` directory contains SDD artifacts — do not modify without understanding SDD workflow
- Dark mode via `class` strategy in Tailwind (`tailwind.config.mjs`)
