#!/usr/bin/env python3
"""
Blog Content Generator
Generates blog posts using Ollama AI from tech news sources.
Runs 2x daily via cron (08:00 and 20:00 UTC).
"""

import os
import sys
import json
import re
import subprocess
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
import feedparser

# Paths (must be before logging)
PROJECT_ROOT = Path(__file__).parent.parent

# Configure logging
LOG_PATH = os.getenv('BLOG_LOG_PATH', str(PROJECT_ROOT / 'blog-generation.log'))
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_PATH, mode='a'),
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'minimax-m3:cloud')
SITE_URL = os.getenv('SITE_URL', 'https://blog.sebastianmorales.sbs')

# Paths
BLOG_CONTENT_DIR = PROJECT_ROOT / 'src' / 'content' / 'blog'
PROMPT_TEMPLATE_PATH = PROJECT_ROOT / 'scripts' / 'prompt_template.txt'

# News sources
HACKERNEWS_API = 'https://hacker-news.firebaseio.com/v0'
RSS_FEEDS = [
    'https://techcrunch.com/feed/',
    'https://www.theverge.com/rss/index.xml',
    'https://feeds.arstechnica.com/arstechnica/index',
]


def fetch_hackernews_stories(limit: int = 10) -> list[dict]:
    """Fetch top stories from HackerNews API."""
    try:
        resp = requests.get(f'{HACKERNEWS_API}/topstories.json', timeout=10)
        resp.raise_for_status()
        story_ids = resp.json()[:limit]

        stories = []
        for story_id in story_ids:
            try:
                story_resp = requests.get(f'{HACKERNEWS_API}/item/{story_id}.json', timeout=5)
                story_resp.raise_for_status()
                story = story_resp.json()
                if story and story.get('title'):
                    stories.append({
                        'title': story['title'],
                        'url': story.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                        'source': 'HackerNews',
                        'score': story.get('score', 0),
                    })
            except Exception as e:
                logger.warning(f'Failed to fetch HN story {story_id}: {e}')
                continue

        logger.info(f'Fetched {len(stories)} stories from HackerNews')
        return stories
    except Exception as e:
        logger.error(f'Failed to fetch HackerNews: {e}')
        return []


def fetch_rss_feeds(limit_per_feed: int = 5) -> list[dict]:
    """Fetch stories from RSS feeds."""
    stories = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:limit_per_feed]:
                stories.append({
                    'title': entry.get('title', 'Untitled'),
                    'url': entry.get('link', ''),
                    'source': feed.feed.get('title', feed_url),
                    'description': entry.get('summary', '')[:200],
                })
            logger.info(f'Fetched {len(feed.entries[:limit_per_feed])} stories from {feed.feed.get("title", feed_url)}')
        except Exception as e:
            logger.warning(f'Failed to fetch RSS feed {feed_url}: {e}')
            continue

    return stories


def select_stories(stories: list[dict], count: int = 4) -> list[dict]:
    """Select the most relevant stories for analysis."""
    # Deduplicate by title similarity
    seen_titles = set()
    unique_stories = []

    for story in stories:
        # Simple dedup by normalized title
        normalized = re.sub(r'[^a-z0-9]', '', story['title'].lower())
        if normalized not in seen_titles:
            seen_titles.add(normalized)
            unique_stories.append(story)

    # Sort by score (if available) and take top N
    scored = [s for s in unique_stories if 'score' in s]
    unscored = [s for s in unique_stories if 'score' not in s]
    scored.sort(key=lambda x: x['score'], reverse=True)

    selected = (scored + unscored)[:count]
    logger.info(f'Selected {len(selected)} stories for generation')
    return selected


def load_prompt_template() -> str:
    """Load the prompt template from file."""
    if PROMPT_TEMPLATE_PATH.exists():
        return PROMPT_TEMPLATE_PATH.read_text()
    else:
        # Default prompt
        return """Eres un analista de tecnología con formación en materialismo histórico.
Escribe un artículo de blog sobre esta noticia tecnológica.

Título de la noticia: {title}
Fuente: {source}
Contexto: {context}

Requisitos:
- Título llamativo pero preciso (8-15 palabras)
- Análisis crítico desde el materialismo marxista
- Enfoque en relaciones de poder, propiedad de medios de producción, explotación laboral, concentración de capital
- Menciona empresas específicas y sus estructuras de poder
- Conecta con tendencias históricas del capitalismo
- Tono: riguroso pero accesible
- 800-1200 palabras
- Incluir palabras clave SEO naturales
- Termina con una conclusión que invite a la reflexión

Formato de salida:
TITLE: [título del artículo]
DESCRIPTION: [descripción meta de 1-2 oraciones]
TAGS: [tag1, tag2, tag3]
CONTENT: [contenido del artículo en MDX]"""


def generate_content(story: dict, prompt_template: str) -> Optional[dict]:
    """Generate blog post content using Ollama API."""
    prompt = prompt_template.format(
        title=story['title'],
        source=story['source'],
        context=story.get('description', story.get('url', '')),
    )

    try:
        resp = requests.post(
            f'{OLLAMA_BASE_URL}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False,
            },
            timeout=180,  # 3 minutes timeout
        )
        resp.raise_for_status()
        response_text = resp.json().get('response', '')

        if not response_text:
            logger.error('Empty response from Ollama')
            return None

        # Parse the response
        parsed = parse_generated_content(response_text)
        if parsed:
            parsed['source_url'] = story.get('url', '')
            parsed['source_name'] = story.get('source', 'Unknown')
        return parsed

    except requests.exceptions.Timeout:
        logger.error('Ollama request timed out')
        return None
    except Exception as e:
        logger.error(f'Failed to generate content: {e}')
        return None


def parse_generated_content(text: str) -> Optional[dict]:
    """Parse the structured output from Ollama."""
    try:
        # Extract fields
        title_match = re.search(r'TITLE:\s*(.+?)(?:\n|$)', text)
        desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?:\n|$)', text)
        tags_match = re.search(r'TAGS:\s*(.+?)(?:\n|$)', text)
        content_match = re.search(r'CONTENT:\s*(.*)', text, re.DOTALL)

        if not all([title_match, desc_match, content_match]):
            logger.error('Failed to parse generated content')
            return None

        title = title_match.group(1).strip()
        description = desc_match.group(1).strip()
        tags_str = tags_match.group(1).strip() if tags_match else ''
        content = content_match.group(1).strip()

        # Parse tags
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        if not tags:
            tags = ['tecnología', 'análisis', 'materialismo']

        # Generate slug from title
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        slug = slug[:50]  # Limit length

        return {
            'title': title,
            'description': description,
            'tags': tags,
            'content': content,
            'slug': slug,
        }
    except Exception as e:
        logger.error(f'Failed to parse content: {e}')
        return None


def create_mdx_file(post_data: dict) -> Path:
    """Create MDX file for the blog post."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime('%Y-%m-%d')
    filename = f"{date_str}-{post_data['slug']}.mdx"
    filepath = BLOG_CONTENT_DIR / filename

    # Ensure directory exists
    BLOG_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    # Create MDX content — escape inner quotes for valid YAML
    safe_title = post_data['title'].replace('"', '\\"')
    safe_desc = post_data['description'].replace('"', '\\"')
    frontmatter = f"""---
title: "{safe_title}"
description: "{safe_desc}"
pubDate: {now.isoformat()}
author: "Sebastian Morales"
tags: {json.dumps(post_data['tags'])}
source: "{post_data['source_name']}"
draft: false
---

"""
    content = frontmatter + post_data['content']

    filepath.write_text(content, encoding='utf-8')
    logger.info(f'Created post: {filepath}')
    return filepath


def git_commit_and_push(filepath: Path, title: str):
    """Commit and push the new post to git."""
    try:
        # Stage the file
        subprocess.run(
            ['git', 'add', str(filepath)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )

        # Commit
        commit_msg = f"blog: add {title}"
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )

        # Push
        subprocess.run(
            ['git', 'push', 'origin', 'main'],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )

        logger.info(f'Pushed to git: {commit_msg}')
    except subprocess.CalledProcessError as e:
        logger.error(f'Git operation failed: {e}')
        raise


def main():
    """Main entry point."""
    logger.info('Starting blog content generation')

    # Fetch stories from all sources
    hn_stories = fetch_hackernews_stories(limit=10)
    rss_stories = fetch_rss_feeds(limit_per_feed=5)
    all_stories = hn_stories + rss_stories

    if not all_stories:
        logger.error('No stories fetched from any source')
        sys.exit(1)

    # Select top stories
    selected = select_stories(all_stories, count=4)

    # Load prompt template
    prompt_template = load_prompt_template()

    # Generate posts (2 per run)
    generated = 0
    for story in selected[:2]:
        logger.info(f'Generating post for: {story["title"]}')

        post_data = generate_content(story, prompt_template)
        if post_data:
            filepath = create_mdx_file(post_data)
            git_commit_and_push(filepath, post_data['title'])
            generated += 1
        else:
            logger.warning(f'Failed to generate content for: {story["title"]}')

    logger.info(f'Generation complete. Created {generated} posts.')
    return generated


if __name__ == '__main__':
    main()
