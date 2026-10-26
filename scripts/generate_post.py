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
import shutil
import subprocess
import logging
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
import feedparser

# Paths (must be before logging)
PROJECT_ROOT = Path(__file__).parent.parent

# Configure logging. In cron, stdout is redirected to the same log file, so we
# only add the console handler when running interactively to avoid duplicates.
LOG_PATH = os.getenv('BLOG_LOG_PATH', str(PROJECT_ROOT / 'blog-generation.log'))
_handlers = [logging.FileHandler(LOG_PATH, mode='a')]
if sys.stdout.isatty():
    _handlers.append(logging.StreamHandler(sys.stdout))
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    force=True,
    handlers=_handlers,
)
logger = logging.getLogger(__name__)

# Configuration from environment
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
SITE_URL = os.getenv('SITE_URL', 'https://blog.sebastianmorales.sbs')

# Optional forced model (for testing) and last-resort local fallback.
FORCED_MODEL = os.getenv('OLLAMA_MODEL', '').strip()
LOCAL_MODEL = os.getenv('OLLAMA_LOCAL_MODEL', 'granite4.1:3b').strip()

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


# Preferred order: quality first. The list is verified against Ollama at runtime
# and cached for the whole process so we don't probe the same models four times.
PREFERRED_CLOUD_MODELS = [
    'gpt-oss:120b-cloud',
    'nemotron-3-nano:30b-cloud',
    'gpt-oss:20b-cloud',
    'gemma4:31b-cloud',
    'gemma4:cloud',
]
_FREE_MODELS_CACHE: Optional[list[str]] = None


def discover_free_cloud_models() -> list[str]:
    """Discover free cloud models available in Ollama (cached per process)."""
    global _FREE_MODELS_CACHE
    if _FREE_MODELS_CACHE is not None:
        return _FREE_MODELS_CACHE

    try:
        resp = requests.get(f'{OLLAMA_BASE_URL}/api/tags', timeout=10)
        resp.raise_for_status()
        all_models = resp.json().get('models', [])
    except Exception as e:
        logger.warning(f'Could not fetch Ollama model list: {e}')
        _FREE_MODELS_CACHE = []
        return []

    cloud_models = [
        m['name'] for m in all_models
        if m['name'].endswith(':cloud') or m['name'].endswith('-cloud')
    ]
    if not cloud_models:
        logger.info('No cloud models found in Ollama')
        _FREE_MODELS_CACHE = []
        return []

    def model_sort_key(name: str) -> tuple:
        try:
            return (PREFERRED_CLOUD_MODELS.index(name), name)
        except ValueError:
            return (len(PREFERRED_CLOUD_MODELS), name)

    cloud_models.sort(key=model_sort_key)
    logger.info(f'Found {len(cloud_models)} cloud models: {cloud_models}')

    working = []
    for model in cloud_models:
        try:
            test_resp = requests.post(
                f'{OLLAMA_BASE_URL}/api/generate',
                json={'model': model, 'prompt': 'Say OK', 'stream': False},
                timeout=20,
            )
            test_resp.raise_for_status()
            data = test_resp.json()
            if data.get('response'):
                working.append(model)
                logger.info(f'Cloud model {model} is FREE and working')
            else:
                logger.info(f'Cloud model {model} returned empty (likely paid)')
        except Exception as e:
            error_msg = str(e)
            if 'subscription' in error_msg or '402' in error_msg:
                logger.info(f'Cloud model {model} requires subscription (paid)')
            else:
                logger.warning(f'Cloud model {model} error: {error_msg[:80]}')

    logger.info(f'Free cloud models available: {working}')
    _FREE_MODELS_CACHE = working
    return working


def get_models_to_try() -> list[str]:
    """Return the ordered list of models for generation/review."""
    if FORCED_MODEL:
        return [FORCED_MODEL]
    models = list(discover_free_cloud_models())
    if LOCAL_MODEL and LOCAL_MODEL not in models:
        models.append(LOCAL_MODEL)
    return models


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
        return """Eres un analista de tecnología independiente.
Escribe un artículo de blog sobre esta noticia tecnológica.

Título de la noticia: {title}
Fuente: {source}
Contexto: {context}

Requisitos:
- Título llamativo pero preciso (8-15 palabras)
- Análisis crítico de la industria tecnológica
- Enfoque en relaciones de poder, concentración de capital, y dinámicas económicas reales
- Menciona empresas específicas y sus estructuras de poder
- Conecta con tendencias históricas de la industria
- Tono: riguroso pero accesible, como un periodista independiente
- 800-1200 palabras
- Incluir palabras clave SEO naturales
- Termina con una conclusión que invite a la reflexión

Formato de salida:
TITLE: [título del artículo]
DESCRIPTION: [descripción meta de 1-2 oraciones]
TAGS: [tag1, tag2, tag3]
CONTENT: [contenido del artículo en MDX]"""


def call_ollama(prompt: str, model: str) -> Optional[str]:
    """Call Ollama API with a specific model. Returns response text or None."""
    try:
        resp = requests.post(
            f'{OLLAMA_BASE_URL}/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
            },
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json().get('response', '')
    except requests.exceptions.Timeout:
        logger.warning(f'Ollama request timed out for model {model}')
        return None
    except Exception as e:
        logger.warning(f'Model {model} failed: {e}')
        return None


def generate_content(story: dict, prompt_template: str) -> Optional[dict]:
    """Generate blog post content with automatic model fallback."""
    prompt = prompt_template.format(
        title=story['title'],
        source=story['source'],
        context=story.get('description', story.get('url', '')),
    )

    models_to_try = get_models_to_try()

    for model in models_to_try:
        logger.info(f'Trying model: {model}')
        response_text = call_ollama(prompt, model)

        if response_text:
            parsed = parse_generated_content(response_text)
            if parsed:
                parsed['source_url'] = story.get('url', '')
                parsed['source_name'] = story.get('source', 'Unknown')
                parsed['raw_response'] = response_text
                logger.info(f'Success with model: {model}')
                return parsed
            else:
                logger.warning(f'Model {model} returned unparseable content, trying next...')
        else:
            logger.warning(f'Model {model} returned empty response, trying next...')

    logger.error('All models failed')
    return None


def parse_generated_content(text: str) -> Optional[dict]:
    """Parse the structured output from Ollama."""
    try:
        # Some models leak their reasoning before the real structured output.
        # Use the LAST occurrence of each header so the final answer wins.
        title_matches = re.findall(r'TITLE:\s*(.+?)(?:\n|DESCRIPTION:)', text, re.DOTALL)
        desc_matches = re.findall(r'DESCRIPTION:\s*(.+?)(?:\n|TAGS:)', text, re.DOTALL)
        tags_matches = re.findall(r'TAGS:\s*(.+?)(?:\n|CONTENT:)', text, re.DOTALL)
        content_idx = text.rfind('CONTENT:')

        if not title_matches or not desc_matches or content_idx == -1:
            logger.error('Failed to parse generated content')
            return None

        title = title_matches[-1].strip()
        description = desc_matches[-1].strip()
        tags_str = tags_matches[-1].strip() if tags_matches else ''
        content = text[content_idx + len('CONTENT:'):].strip()

        # Remove IMAGE_PROMPT and MERMAID lines from content
        content = re.sub(r'\n?IMAGE_PROMPT:\s*.+?\n', '\n', content)
        content = re.sub(r'\n?MERMAID:\s*.+?\n', '\n', content, flags=re.DOTALL)

        # Remove mermaid code blocks from content (they'll be injected separately)
        content = re.sub(r'\n?```mermaid\n.*?\n```\n?', '\n', content, flags=re.DOTALL)

        # Also remove mermaid code without fences (sometimes LLM includes raw mermaid)
        # Remove lines that are clearly mermaid arrow syntax (A --> B, A -.-> B, etc.)
        # but preserve lines that merely mention --> in prose (e.g. HTML comments)
        mermaid_arrow_re = re.compile(r'^\s*\w[\w\s]*\s*[-.=>]+\s*\w')
        lines = content.split('\n')
        lines = [line for line in lines if not mermaid_arrow_re.match(line)]
        content = '\n'.join(lines)

        content = content.strip()

        # Parse tags
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        if not tags:
            tags = ['tecnología', 'análisis', 'industria']

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


def validate_post(post_data: dict) -> dict:
    """Programmatic validation. Returns {valid, issues, fixed}."""
    issues = []
    fixed = dict(post_data)

    # Check for CJK characters
    cjk_chars = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', post_data['content'])
    if cjk_chars:
        issues.append(f'Found {len(cjk_chars)} CJK characters in content')

    # Check title is not empty
    if not post_data.get('title', '').strip():
        issues.append('Title is empty')

    # Check description is not empty
    if not post_data.get('description', '').strip():
        issues.append('Description is empty')

    # Check content length
    word_count = len(post_data.get('content', '').split())
    if word_count < 200:
        issues.append(f'Content too short: {word_count} words')
    elif word_count > 2000:
        issues.append(f'Content too long: {word_count} words')

    # Check tags
    if not post_data.get('tags'):
        fixed['tags'] = ['tecnología', 'análisis', 'industria']
        issues.append('Tags empty, using defaults')

    logger.info(f'Validation: {len(issues)} issues found')
    return {
        'valid': len(issues) == 0 or (len(issues) == 1 and 'CJK characters' not in issues[0]),
        'issues': issues,
        'fixed': fixed,
    }


def review_post(post_data: dict) -> dict:
    """LLM-based review with automatic model fallback."""
    review_prompt = """Eres un editor profesional de contenido en español. Revisa este artículo de blog y corrige cualquier problema.

Problemas a buscar y corregir:
1. Caracteres en otros idiomas (chino, japonés, etc.) mezclados con español → reemplaza por la traducción correcta al español
2. Gramática y ortografía incorrectas
3. Contenido incoherente o repetitivo
4. Formato MDX roto (etiquetas mal cerradas, etc.)
5. Tags que no sean relevantes al contenido

IMPORTANTE:
- Solo corrige si hay problemas reales
- Si el artículo está bien, devuelve "valid": true sin cambios
- El contenido DEBE permanecer en español
- NO cambies el estilo ni el tono del análisis

Devuelve ÚNICAMENTE un JSON válido (sin markdown, sin explicaciones):
{{
  "valid": true/false,
  "issues": ["problema 1", "problema 2"],
  "corrected_title": "título corregido solo si era necesario",
  "corrected_description": "descripción corregida solo si era necesaria",
  "corrected_content": "contenido corregido solo si era necesario",
  "corrected_tags": ["tags"] solo si era necesario
}}

Si no hay correcciones, devuelve: {{"valid": true, "issues": [], "corrected_title": null, "corrected_description": null, "corrected_content": null, "corrected_tags": null}}

ARTÍCULO:
TITLE: {title}
DESCRIPTION: {description}
TAGS: {tags}
CONTENT: {content}"""

    prompt = review_prompt.format(
        title=post_data['title'],
        description=post_data['description'],
        tags=', '.join(post_data.get('tags', [])),
        content=post_data['content'],
    )

    models_to_try = get_models_to_try()

    for model in models_to_try:
        response_text = call_ollama(prompt, model)
        if not response_text:
            continue

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                review_result = json.loads(json_match.group())
                logger.info(f'Review OK with {model}: valid={review_result.get("valid")}')
                return review_result
            except json.JSONDecodeError:
                logger.warning(f'Model {model} returned invalid JSON for review')
                continue

    logger.warning('All models failed for review, skipping')
    return {'valid': True, 'issues': []}


def generate_content_with_review(story: dict, prompt_template: str) -> Optional[dict]:
    """Generate content with validation and LLM review."""
    post_data = generate_content(story, prompt_template)
    if not post_data:
        return None

    # Step 1: Programmatic validation
    validation = validate_post(post_data)
    post_data = validation['fixed']

    if not validation['valid']:
        logger.warning(f'Post rejected by validation: {validation["issues"]}')
        return None

    # Step 2: LLM review and corrections
    review = review_post(post_data)

    if review.get('corrected_title'):
        logger.info(f'Review: correcting title')
        post_data['title'] = review['corrected_title']
    if review.get('corrected_description'):
        logger.info(f'Review: correcting description')
        post_data['description'] = review['corrected_description']
    if review.get('corrected_content'):
        logger.info(f'Review: correcting content ({len(review["corrected_content"])} chars)')
        post_data['content'] = review['corrected_content']
    if review.get('corrected_tags'):
        logger.info(f'Review: correcting tags')
        post_data['tags'] = review['corrected_tags']

    if review.get('issues'):
        logger.info(f'Review issues: {review["issues"]}')

    return post_data


QUARANTINE_DIR = PROJECT_ROOT / '.quarantine'


def sanitize_mdx(content: str) -> str:
    """Fix common MDX syntax errors produced by LLMs."""
    # Autolinks like <https://example.com> are invalid in MDX.
    content = re.sub(r'<(https?://[^>\s]+)>', r'\1', content)
    # Leaked reasoning tags.
    content = content.replace('</think>', '')
    # Remove leaked structured-output headers if they ended up inside the body.
    content = re.sub(
        r'^(?:TITLE|DESCRIPTION|TAGS|CONTENT):.*\n?',
        '',
        content,
        flags=re.MULTILINE,
    )
    return content.strip()


def validate_build() -> tuple[bool, str]:
    """Run the real Astro build. Returns (ok, error_output)."""
    npm_bin = os.getenv('NPM_BIN') or shutil.which('npm') or 'npm'
    try:
        result = subprocess.run(
            [npm_bin, 'run', 'build'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except Exception as e:
        return False, f'Build could not run: {e}'
    if result.returncode == 0:
        return True, ''
    output = (result.stdout or '') + '\n' + (result.stderr or '')
    return False, output[-5000:]


def quarantine_post(filepath: Path, error: str) -> Path:
    """Move a post that fails the build out of the content directory."""
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    dest = QUARANTINE_DIR / filepath.name
    shutil.move(str(filepath), str(dest))
    (QUARANTINE_DIR / f'{filepath.stem}.error.log').write_text(error, encoding='utf-8')
    logger.error(f'Post moved to quarantine: {dest}')
    return dest


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

    # Use first image as OG image, fallback to default
    og_image = image_urls[0] if image_urls else DEFAULT_IMAGE

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

    content = frontmatter + sanitize_mdx(content_with_images)

    filepath.write_text(content, encoding='utf-8')
    logger.info(f'Created post: {filepath}')
    return filepath


def git_commit_and_push(filepath: Path, title: str):
    """Commit and push the new post to git."""
    commit_msg = f"blog: add {title}"
    try:
        # Sync first so the new commit is applied on top of the remote branch.
        pull_result = subprocess.run(
            ['git', 'pull', '--rebase', '--autostash', 'origin', 'main'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if pull_result.returncode != 0:
            logger.error(f'git pull --rebase failed: {pull_result.stderr[-500:]}')
            raise RuntimeError('git pull failed; refusing to commit on a diverged branch')

        subprocess.run(
            ['git', 'add', str(filepath)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )
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


FORBIDDEN_IMAGE_TERMS = ['purple', 'fuchsia', 'neon', 'cyberpunk', 'dystopian', 'dark cinematic', 'chiaroscuro', 'glow', 'glowing']


def process_images(post_data: dict, story: dict) -> tuple[list[str], Optional[str]]:
    """Process images for a post: parse prompts, generate Pollinations URLs."""
    # Parse image prompts from raw response
    raw_response = post_data.get('raw_response', '')
    prompts = parse_image_prompts(raw_response)

    # Filter out prompts with forbidden terms (match prompt_template.txt rules)
    filtered_prompts = []
    for prompt in prompts['image_prompts']:
        lower = prompt.lower()
        if any(term in lower for term in FORBIDDEN_IMAGE_TERMS):
            logger.warning(f'Rejected image prompt (forbidden term): {prompt[:60]}...')
            continue
        filtered_prompts.append(prompt)

    if not filtered_prompts:
        logger.warning('No valid image prompts after filtering, using default fallback image')
        return [DEFAULT_IMAGE], prompts['mermaid']

    # Generate Pollinations URLs directly (they are public and free)
    image_urls = []
    for prompt in filtered_prompts[:2]:  # Max 2 images
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

        try:
            post_data = generate_content_with_review(story, prompt_template)
            if post_data:
                # Idempotency check: skip if a post with this slug already exists
                date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                expected_filename = f"{date_str}-{post_data['slug']}.mdx"
                if (BLOG_CONTENT_DIR / expected_filename).exists():
                    logger.warning(f'Post already exists, skipping: {expected_filename}')
                    continue

                # Process images
                image_urls, mermaid_code = process_images(post_data, story)

                # Create MDX file
                filepath = create_mdx_file(post_data, image_urls, mermaid_code)

                # Never commit a post that breaks the Astro build.
                ok, build_error = validate_build()
                if not ok:
                    quarantine_post(filepath, build_error)
                    logger.error(
                        f'Build validation failed for {filepath.name}; post quarantined. '
                        f'Error tail: {build_error[-1500:]}'
                    )
                    continue

                # Git commit and push (GitHub Actions triggers the Coolify deploy)
                git_commit_and_push(filepath, post_data['title'])
                generated += 1
            else:
                logger.warning(f'Failed to generate content for: {story["title"]}')
        except Exception as e:
            logger.error(f'Error processing story "{story["title"]}": {e}', exc_info=True)
            continue

    logger.info(f'Generation complete. Created {generated} posts.')
    return generated


if __name__ == '__main__':
    main()
