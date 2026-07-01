# SEO for AI Agents Specification

## Purpose

Define SEO features targeting AI agents and LLMs: llms.txt files.

## Requirements

### Requirement: llms.txt File

The system MUST include a llms.txt file at the site root.

#### Scenario: llms.txt structure

- GIVEN the site is deployed
- WHEN `llms.txt` is fetched
- THEN it MUST be valid Markdown format
- AND it MUST include: H1 (site name), blockquote (site description), H2 sections for: About, Content, Author, Optional
- AND it MUST NOT exceed 3000 tokens

#### Scenario: llms.txt content accuracy

- GIVEN the llms.txt file exists
- WHEN an AI agent reads it
- THEN it MUST accurately describe the site's purpose
- AND it MUST list the most important pages
- AND it MUST include author information

### Requirement: llms-full.txt File

The system MAY include a llms-full.txt file with complete content.

#### Scenario: llms-full.txt generation

- GIVEN blog posts exist
- WHEN the build runs
- THEN `llms-full.txt` MUST be generated at the root
- AND it MUST include full text of all posts
- AND it MUST be formatted as clean Markdown

### Requirement: Semantic HTML

The system MUST use semantic HTML5 elements for better AI parsing.

#### Scenario: Article elements

- GIVEN a blog post page
- WHEN the HTML is rendered
- THEN the post content MUST be wrapped in `<article>` tags
- AND headings MUST use proper hierarchy (h1, h2, h3)
- AND paragraphs MUST use `<p>` tags
- AND lists MUST use `<ul>` or `<ol>` tags

### Requirement: Clean URL Structure

The system MUST use clean, readable URLs.

#### Scenario: Post URL format

- GIVEN a blog post with title "Apple Vision Pro Analysis"
- WHEN published on 2026-07-01
- THEN the URL MUST be `/blog/2026-07-01-apple-vision-pro-analysis`
- AND the URL MUST be lowercase with hyphens
