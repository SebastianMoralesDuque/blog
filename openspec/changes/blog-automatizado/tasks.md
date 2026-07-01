# Tasks: Blog Automatizado

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1200-1500 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 |
| Delivery strategy | ask-always |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Project setup + Astro core | PR 1 | Base project, layouts, index |
| 2 | Content system + SEO | PR 2 | Collections, sitemap, RSS, llms |
| 3 | Automation pipeline | PR 3 | Python script + cron |
| 4 | Analytics + Personal brand | PR 4 | Umami + about page |

---

## Phase 1: Project Foundation

- [x] 1.1 Initialize Astro project: `npm create astro@latest blog -- --template minimal`
- [x] 1.2 Install dependencies: `@astrojs/mdx`, `@astrojs/tailwind`, `@astrojs/sitemap`
- [x] 1.3 Configure `astro.config.mjs` with integrations
- [x] 1.4 Create `src/content.config.ts` with blog collection schema
- [x] 1.5 Create `.env.example` with all environment variables
- [x] 1.6 Create `src/layouts/BaseLayout.astro` with head, nav, footer slots
- [x] 1.7 Create `src/components/Header.astro` with responsive navigation
- [x] 1.8 Create `src/components/Footer.astro` with professional links
- [x] 1.9 Create `src/pages/index.astro` with post list

## Phase 2: Content System + SEO

- [x] 2.1 Create `src/layouts/PostLayout.astro` with article metadata
- [x] 2.2 Create `src/pages/rss.xml.ts` with RSS 2.0 feed
- [x] 2.3 Add JSON-LD to BaseLayout for Blog schema
- [x] 2.4 Add JSON-LD to PostLayout for BlogPosting schema
- [x] 2.5 Add Open Graph and Twitter Card meta tags
- [x] 2.6 Create `public/robots.txt` with sitemap reference
- [x] 2.7 Create `public/llms.txt` with site description
- [x] 2.8 Create `public/llms-full.txt` (generated at build)
- [x] 2.9 Add canonical URLs to all pages

## Phase 3: Automation Pipeline

- [x] 3.1 Create `scripts/generate_post.py` with Ollama API integration
- [x] 3.2 Add HackerNews API fetch logic
- [x] 3.3 Add RSS feed fetch logic (feedparser)
- [x] 3.4 Add story selection algorithm
- [x] 3.5 Add content generation with prompt template
- [x] 3.6 Create `scripts/prompt_template.txt` with Marxist analysis prompt
- [x] 3.7 Add MDX file generation with frontmatter
- [x] 3.8 Add git automation (add, commit, push)
- [x] 3.9 Add error handling and retry logic
- [x] 3.10 Create `scripts/requirements.txt` with Python dependencies
- [ ] 3.11 Configure cron job (08:00 and 20:00 UTC)

## Phase 4: Analytics + Personal Brand

- [x] 4.1 Add Umami script to BaseLayout with `data-astro-rerun`
- [x] 4.2 Configure Umami via environment variables
- [x] 4.3 Create `src/pages/about.astro` with bio and professional links
- [x] 4.4 Add LinkedIn, GitHub, and email links
- [x] 4.5 Add about page to header navigation
- [x] 4.6 Add about page to footer navigation

## Phase 5: Testing + Verification

- [x] 5.1 Test `npm run build` succeeds
- [ ] 5.2 Validate sitemap.xml output
- [ ] 5.3 Validate RSS feed output
- [ ] 5.4 Validate JSON-LD with Google Rich Results
- [ ] 5.5 Test Python script with mock APIs
- [ ] 5.6 Test responsive design on mobile viewport
- [ ] 5.7 Verify Umami tracking in production

## Phase 6: Deployment

- [ ] 6.1 Create Gitea repo `sebastianmorales/blog` (private)
- [ ] 6.2 Push initial commit
- [ ] 6.3 Configure Coolify with the repo
- [ ] 6.4 Set environment variables in Coolify
- [ ] 6.5 Verify auto-deploy on push
- [ ] 6.6 Configure cron job on server
- [ ] 6.7 Verify first content generation
