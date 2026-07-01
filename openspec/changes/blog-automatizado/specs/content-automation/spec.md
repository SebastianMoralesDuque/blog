# Content Automation Specification

## Purpose

Define the automated pipeline that generates 2 blog posts per day using Ollama AI and news sources.

## Requirements

### Requirement: News Source Integration

The system MUST fetch news from multiple sources daily.

#### Scenario: HackerNews API fetch

- GIVEN the automation script runs
- WHEN fetching from HackerNews API
- THEN it MUST retrieve top stories from `https://hacker-news.firebaseio.com/v0/topstories.json`
- AND it MUST fetch at least 10 stories
- AND each story MUST include: title, URL, score, author

#### Scenario: RSS feed fetch

- GIVEN the automation script runs
- WHEN fetching from RSS feeds
- THEN it MUST parse feeds from TechCrunch, The Verge, and ArsTechnica
- AND each item MUST include: title, link, description, publication date

#### Scenario: Source reliability

- GIVEN a news source is unavailable
- WHEN the fetch fails
- THEN the script MUST log the error
- AND continue with available sources
- AND NOT crash or stop execution

### Requirement: Content Selection

The system MUST select the most relevant stories for analysis.

#### Scenario: Story selection algorithm

- GIVEN a list of fetched stories
- WHEN selecting stories for analysis
- THEN the system MUST prioritize by: recency (last 24h), relevance to tech industry, engagement potential
- AND select at least 4 stories (to generate 2 posts from 2 sources each)
- AND avoid duplicate topics

### Requirement: AI Content Generation

The system MUST generate blog posts using Ollama API.

#### Scenario: Post generation

- GIVEN a selected news story
- WHEN the generation script runs
- THEN it MUST call Ollama API at `OLLAMA_BASE_URL`
- AND use model specified in `OLLAMA_MODEL` env var
- AND generate a post with: title (8-15 words), analysis (800-1200 words), conclusion
- AND the analysis MUST use materialist Marxist framework
- AND the tone MUST be rigorous but accessible

#### Scenario: Model unavailability

- GIVEN Ollama is unreachable or model is missing
- WHEN the generation script runs
- THEN it MUST log the error
- AND retry once after 60 seconds
- AND skip this generation cycle if retry fails
- AND NOT write empty or malformed posts

#### Scenario: Environment variable configuration

- GIVEN the system reads `OLLAMA_BASE_URL` and `OLLAMA_MODEL`
- WHEN the env vars are not set
- THEN it MUST use defaults: `http://127.0.0.1:11434` and `minimax-m3:cloud`

### Requirement: Post Persistence

The system MUST save generated posts as MDX files.

#### Scenario: MDX file creation

- GIVEN a generated blog post
- WHEN saving to filesystem
- THEN it MUST create a file at `src/content/blog/YYYY-MM-DD-{slug}.mdx`
- AND the frontmatter MUST include: title, description, pubDate, author ("Sebastian Morales"), tags, source
- AND the content MUST be valid MDX

#### Scenario: Git automation

- GIVEN a new post is saved
- WHEN the script completes
- THEN it MUST stage all new files
- AND commit with message: "blog: add {title}"
- AND push to origin main

### Requirement: Scheduling

The system MUST run 2 times per day.

#### Scenario: Cron execution

- GIVEN the cron job is configured
- WHEN it runs at 08:00 and 20:00 UTC
- THEN the script MUST execute
- AND generate exactly 1 post per run (2 total per day)
- AND logs MUST be written to `/var/log/blog-generation.log`

### Requirement: Prompt Engineering

The system MUST use a structured prompt for content generation.

#### Scenario: System prompt

- GIVEN a news story to analyze
- WHEN the prompt is sent to Ollama
- THEN it MUST include: role definition (materialist Marxist analyst), output format, word count target, tone guidelines
- AND the prompt MUST be configurable via a template file
