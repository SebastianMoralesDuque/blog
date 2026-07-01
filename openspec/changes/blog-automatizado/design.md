# Design: Blog Automatizado

## Technical Approach

Proyecto nuevo con Astro + MDX para el blog, Python script para automatización, y despliegue via Coolify. La separación entre generación (Python) y publicación (Astro) permite independencia y facilidad de debug.

## Architecture Decisions

### Decision: Framework principal

**Choice**: Astro con MDX
**Alternatives**: Next.js, Hugo, Jekyll
**Rationale**: Astro tiene el mejor rendimiento para content-heavy sites, soporte nativo de MDX, Content Collections con validación Zod, y zero JavaScript by default. Next.js es overkill para un blog estático.

### Decision: Lenguaje de automatización

**Choice**: Python
**Alternatives**: Node.js/TypeScript, Bash
**Rationale**: Python tiene mejor ecosistema para scraping (feedparser, requests), es más legible para scripts de generación, y el usuario ya lo tiene disponible. Node.js sería más consistente con Astro pero más complejo para este caso de uso.

### Decision: Generación de contenido

**Choice**: Ollama API local con modelo configurable
**Alternatives**: OpenAI API, Claude API, modelos locales sin API
**Rationale**: Ollama es gratuito, corre localmente, y el modelo es configurable via env var. Sin dependencia de APIs externas ni costos recurrentes.

### Decision: Fuentes de noticias

**Choice**: HackerNews API + RSS feeds (TechCrunch, The Verge, ArsTechnica)
**Alternatives**: Web scraping directo, APIs de pago
**Rationale**: HackerNews API es gratuita y confiable. RSS feeds son estándar y fáciles de parsear. Web scraping es frágil y viola ToS.

### Decision: Diseño UX cognitivo

**Choice**: Tema custom con tipografía optimizada para lectura
**Alternatives**: Tema existente (Astro Paper, Astro Nano)
**Rationale**: Un tema custom permite control total sobre la experiencia de lectura: tipografía (16px+, line-height 1.6-1.8), ancho máximo 70ch, contraste adecuado, y elementos visuales que retienen al lector.

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                    CRON (2x/día)                        │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              Python Script (generate_post.py)           │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ HackerNews  │  │ RSS Feeds    │  │ Ollama API    │  │
│  │ API         │  │ (3 sources)  │  │ (generate)    │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                │                   │          │
│         └────────┬───────┘                   │          │
│                  │                           │          │
│                  ▼                           │          │
│         ┌────────────────┐                   │          │
│         │ Select Stories │───────────────────┘          │
│         └────────┬───────┘                              │
│                  │                                      │
│                  ▼                                      │
│         ┌────────────────┐                              │
│         │ Generate Post  │                              │
│         │ (Ollama API)   │                              │
│         └────────┬───────┘                              │
│                  │                                      │
│                  ▼                                      │
│         ┌────────────────┐                              │
│         │ Save as MDX    │                              │
│         └────────┬───────┘                              │
│                  │                                      │
│                  ▼                                      │
│         ┌────────────────┐                              │
│         │ Git Push       │                              │
│         └────────────────┘                              │
└─────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              Coolify (auto-deploy on push)              │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Astro Build                        │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐│    │
│  │  │ Content  │ │ Sitemap  │ │ RSS Feed         ││    │
│  │  │ Collect. │ │ Generate │ │ Generate         ││    │
│  │  └──────────┘ └──────────┘ └──────────────────┘│    │
│  └─────────────────────────────────────────────────┘    │
│                  │                                      │
│                  ▼                                      │
│         ┌────────────────┐                              │
│         │ Static Output  │                              │
│         │ (blog.seb...)  │                              │
│         └────────────────┘                              │
└─────────────────────────────────────────────────────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `astro.config.mjs` | Create | Configuración Astro con MDX + Tailwind |
| `src/content.config.ts` | Create | Content Collection schema con Zod |
| `src/content/blog/*.mdx` | Create | Posts generados automáticamente |
| `src/layouts/BaseLayout.astro` | Create | Layout base con head, nav, footer |
| `src/layouts/PostLayout.astro` | Create | Layout de post con metadata |
| `src/pages/index.astro` | Create | Página principal (listado de posts) |
| `src/pages/about.astro` | Create | Página sobre mí con links |
| `src/pages/rss.xml.ts` | Create | RSS feed endpoint |
| `src/components/Header.astro` | Create | Navegación principal |
| `src/components/Footer.astro` | Create | Footer con links profesionales |
| `public/llms.txt` | Create | SEO para agentes IA |
| `public/robots.txt` | Create | Reglas para crawlers |
| `scripts/generate_post.py` | Create | Script de generación con Ollama |
| `scripts/prompt_template.txt` | Create | Template para prompt de generación |
| `.env.example` | Create | Variables de entorno de ejemplo |
| `package.json` | Create | Dependencias del proyecto |

## Interfaces / Contracts

### Ollama API Contract

```python
# Request
POST http://127.0.0.1:11434/api/generate
{
    "model": "minimax-m3:cloud",
    "prompt": "<prompt from template>",
    "stream": false
}

# Response
{
    "model": "minimax-m3:cloud",
    "response": "<generated content>",
    "done": true
}
```

### MDX Frontmatter Schema

```typescript
// src/content.config.ts
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const blog = defineCollection({
    loader: glob({ pattern: "**/*.mdx", base: "./src/content/blog" }),
    schema: z.object({
        title: z.string(),
        description: z.string(),
        pubDate: z.coerce.date(),
        author: z.string().default('Sebastian Morales'),
        tags: z.array(z.string()),
        source: z.string(),
        image: z.string().optional(),
    })
});

export const collections = { blog };
```

### Environment Variables

```bash
# Ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=minimax-m3:cloud

# Umami
UMAMI_WEBSITE_ID=<your-website-id>
UMAMI_SCRIPT_URL=https://analytics.sebastianmorales.sbs/script.js

# Site
SITE_URL=https://blog.sebastianmorales.sbs
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Content collection schema validation | Test frontmatter parsing |
| Unit | Python script: news fetching | Mock API responses |
| Unit | Python script: content generation | Mock Ollama API |
| Integration | Build process | `npm run build` succeeds |
| Integration | Sitemap generation | Validate XML output |
| Integration | RSS feed generation | Validate RSS 2.0 |
| E2E | Page rendering | Check all pages load |
| E2E | Navigation | Links work correctly |
| E2E | Responsive | Mobile viewport test |

## Migration / Rollout

No migration required — proyecto nuevo.

### Rollout Plan

1. Crear repo en Gitea: `sebastianmorales/blog` (privado)
2. Inicializar proyecto Astro localmente
3. Push initial commit
4. Configurar Coolify con el repo
5. Configurar variables de entorno en Coolify
6. Verificar despliegue automático
7. Configurar cron job en el servidor
8. Verificar primera generación de contenido

## Open Questions

- [ ] ¿Qué tema de Astro usar como base? (Recomendación: Astro Paper o custom desde cero)
- [ ] ¿Cuántos posts mantener visibles? (Últimos 30? Todos?)
- [ ] ¿Necesita paginación en el listado principal?
