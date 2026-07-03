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
import time
import urllib.parse
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

# File Browser configuration
FILEBROWSER_URL = os.getenv('FILEBROWSER_URL', 'https://files.sebastianmorales.sbs')
FILEBROWSER_USER = os.getenv('FILEBROWSER_USER', 'sebas')
FILEBROWSER_PASS = os.getenv('FILEBROWSER_PASS', '')

# Pollinations.ai configuration
POLLINATIONS_BASE = 'https://image.pollinations.ai/prompt'
DEFAULT_IMAGE = 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&h=675&fit=crop'

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


def login_filebrowser() -> Optional[str]:
    """Get JWT token from File Browser."""
    if not FILEBROWSER_USER or not FILEBROWSER_PASS:
        logger.info('File Browser credentials not configured, skipping')
        return None
    
    try:
        resp = requests.post(
            f'{FILEBROWSER_URL}/api/login',
            json={
                'username': FILEBROWSER_USER,
                'password': FILEBROWSER_PASS,
            },
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.text.strip().strip('"')
        logger.info('Logged in to File Browser')
        return token
    except Exception as e:
        logger.error(f'Failed to login to File Browser: {e}')
        return None


def download_pollinations_image(prompt: str, output_path: str, width: int = 1200, height: int = 675) -> bool:
    """Download image from Pollinations.ai with retry."""
    encoded_prompt = urllib.parse.quote(prompt)
    url = f'{POLLINATIONS_BASE}/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true'

    for attempt in range(3):
        try:
            logger.info(f'Downloading image from Pollinations (attempt {attempt + 1})')
            resp = requests.get(url, timeout=60, stream=True)
            resp.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = os.path.getsize(output_path)
            if file_size > 1000:  # At least 1KB
                logger.info(f'Downloaded image: {output_path} ({file_size} bytes)')
                return True
            else:
                logger.warning(f'Downloaded file too small: {file_size} bytes')
                os.remove(output_path)

        except Exception as e:
            logger.warning(f'Pollinations download attempt {attempt + 1} failed: {e}')
            if attempt < 2:
                time.sleep(5)

    # Fallback to default image
    logger.warning('Using default fallback image')
    try:
        resp = requests.get(DEFAULT_IMAGE, timeout=30, stream=True)
        resp.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f'Failed to download fallback image: {e}')
        return False


def upload_to_filebrowser(local_path: str, remote_path: str, token: str) -> Optional[str]:
    """Upload image to File Browser. Returns public URL."""
    try:
        with open(local_path, 'rb') as f:
            file_data = f.read()

        resp = requests.post(
            f'{FILEBROWSER_URL}/api/resources/{remote_path}?override=true',
            headers={'X-Auth': token},
            data=file_data,
            timeout=30,
        )
        resp.raise_for_status()

        public_url = f'{FILEBROWSER_URL}/files/{remote_path}'
        logger.info(f'Uploaded to File Browser: {public_url}')
        return public_url

    except Exception as e:
        logger.error(f'Failed to upload to File Browser: {e}')
        return None


def parse_image_prompts(text: str) -> dict:
    """Extract IMAGE_PROMPT and MERMAID from LLM output."""
    result = {
        'image_prompts': [],
        'mermaid': None,
    }

    # Extract IMAGE_PROMPTs
    image_matches = re.findall(r'IMAGE_PROMPT:\s*(.+?)(?=\n(?:IMAGE_PROMPT:|MERMAID:|$))', text, re.DOTALL)
    for match in image_matches[:2]:  # Max 2
        prompt = match.strip()
        if prompt:
            result['image_prompts'].append(prompt)

    # Extract MERMAID
    mermaid_match = re.search(r'MERMAID:\s*(.+?)(?=\n\n|\Z)', text, re.DOTALL)
    if mermaid_match:
        mermaid_code = mermaid_match.group(1).strip()
        # Clean up mermaid code - remove markdown code fences if present
        mermaid_code = re.sub(r'^```mermaid\s*', '', mermaid_code)
        mermaid_code = re.sub(r'\s*```$', '', mermaid_code)
        if mermaid_code:
            result['mermaid'] = mermaid_code

    logger.info(f'Parsed {len(result["image_prompts"])} image prompts, mermaid: {bool(result["mermaid"])}')
    return result


def inject_images_into_content(content: str, image_urls: list[str], mermaid_code: Optional[str]) -> str:
    """Inject images and mermaid diagram into content."""
    lines = content.split('\n')
    new_lines = []
    image_index = 0
    heading_count = 0

    for line in lines:
        new_lines.append(line)

        # Insert image after every 2-3 headings
        if line.startswith('## ') and image_index < len(image_urls):
            heading_count += 1
            if heading_count % 2 == 0:  # Every 2 headings
                new_lines.append('')
                new_lines.append(f'![Imagen del artículo]({image_urls[image_index]})')
                new_lines.append('')
                image_index += 1

    # Insert remaining images at end if not all used
    while image_index < len(image_urls):
        new_lines.append('')
        new_lines.append(f'![Imagen del artículo]({image_urls[image_index]})')
        new_lines.append('')
        image_index += 1

    # Insert mermaid diagram before conclusion if exists and not already in content
    if mermaid_code and '```mermaid' not in content:
        conclusion_idx = len(new_lines)
        for i in range(len(new_lines) - 1, -1, -1):
            if '## Conclusión' in new_lines[i] or '## Conclu' in new_lines[i]:
                conclusion_idx = i
                break

        new_lines.insert(conclusion_idx, '')
        new_lines.insert(conclusion_idx + 1, '```mermaid')
        new_lines.insert(conclusion_idx + 2, mermaid_code)
        new_lines.insert(conclusion_idx + 3, '```')
        new_lines.insert(conclusion_idx + 4, '')

    return '\n'.join(new_lines)


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
            parsed['raw_response'] = response_text
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
        # Extract fields - use a more robust parsing approach
        # Find TITLE: everything until next field or newline
        title_match = re.search(r'TITLE:\s*(.+?)(?:\n|DESCRIPTION:)', text, re.DOTALL)
        desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?:\n|TAGS:)', text, re.DOTALL)
        tags_match = re.search(r'TAGS:\s*(.+?)(?:\n|CONTENT:)', text, re.DOTALL)
        content_match = re.search(r'CONTENT:\s*(.*)', text, re.DOTALL)

        if not all([title_match, desc_match, content_match]):
            logger.error('Failed to parse generated content')
            return None

        title = title_match.group(1).strip()
        description = desc_match.group(1).strip()
        tags_str = tags_match.group(1).strip() if tags_match else ''
        content = content_match.group(1).strip()

        # Remove IMAGE_PROMPT and MERMAID lines from content
        content = re.sub(r'\n?IMAGE_PROMPT:\s*.+?\n', '\n', content)
        content = re.sub(r'\n?MERMAID:\s*.+?\n', '\n', content, flags=re.DOTALL)
        
        # Remove mermaid code blocks from content (they'll be injected separately)
        content = re.sub(r'\n?```mermaid\n.*?\n```\n?', '\n', content, flags=re.DOTALL)
        
        # Also remove mermaid code without fences (sometimes LLM includes raw mermaid)
        # Remove any line that contains --> (mermaid arrow syntax)
        lines = content.split('\n')
        lines = [line for line in lines if '-->' not in line]
        content = '\n'.join(lines)
        
        content = content.strip()

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


def create_mdx_file(post_data: dict, image_urls: list[str], mermaid_code: Optional[str]) -> Path:
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

    # Use first image as OG image
    og_image = image_urls[0] if image_urls else ''

    frontmatter = f"""---
title: "{safe_title}"
description: "{safe_desc}"
pubDate: {now.isoformat()}
author: "Sebastian Morales"
tags: {json.dumps(post_data['tags'])}
source: "{post_data['source_name']}"
image: "{og_image}"
draft: false
---

"""

    # Inject images into content
    content_with_images = inject_images_into_content(post_data['content'], image_urls, mermaid_code)

    content = frontmatter + content_with_images

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


def process_images(post_data: dict, story: dict) -> tuple[list[str], Optional[str]]:
    """Process images for a post: parse prompts, generate Pollinations URLs."""
    # Parse image prompts from raw response
    raw_response = post_data.get('raw_response', '')
    prompts = parse_image_prompts(raw_response)

    if not prompts['image_prompts']:
        logger.warning('No image prompts found in response')
        return [], prompts['mermaid']

    # Generate Pollinations URLs directly (they are public and free)
    image_urls = []
    for prompt in prompts['image_prompts'][:2]:  # Max 2 images
        encoded = urllib.parse.quote(prompt)
        seed = hash(prompt) % 100000
        url = f'{POLLINATIONS_BASE}/{encoded}?width=1200&height=675&model=flux&nologo=true&seed={seed}'
        image_urls.append(url)
        logger.info(f'Generated image URL: {url[:80]}...')

    return image_urls, prompts['mermaid']


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
            # Process images
            image_urls, mermaid_code = process_images(post_data, story)

            # Create MDX file
            filepath = create_mdx_file(post_data, image_urls, mermaid_code)

            # Git commit and push
            git_commit_and_push(filepath, post_data['title'])
            generated += 1
        else:
            logger.warning(f'Failed to generate content for: {story["title"]}')

    logger.info(f'Generation complete. Created {generated} posts.')
    return generated


if __name__ == '__main__':
    main()
