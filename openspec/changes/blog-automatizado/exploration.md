# Exploration: Blog Automatizado

## Current State

Proyecto nuevo desde cero. No hay codebase existente. El usuario tiene infraestructura completa en el VPS:
- Ollama corriendo en `127.0.0.1:11434` (modelo: `minimax-m3:cloud`, configurable via env)
- Umami self-hosted en `analytics.sebastianmorales.sbs`
- Coolify para despliegue
- Gitea para hosting de repos
- Tailscale VPN

## Affected Areas

Todo es nuevo. No hay archivos existentes que se afecten.

## Approaches

### Approach 1: Astro + Script Python para automatización

**Arquitectura:**
```
blog/
├── src/
│   ├── content/blog/          # Posts MDX
│   ├── components/            # Componentes Astro
│   ├── layouts/               # Layouts
│   └── pages/                 # Páginas
├── scripts/
│   └── generate_post.py       # Script de generación con Ollama
├── public/
│   ├── llms.txt               # SEO para agentes IA
│   └── llms-full.txt          # Contenido completo
├── openspec/                  # Artefactos SDD
└── .env                       # Variables de entorno
```

**Automatización:** Cron job diario → Python script → Ollama genera contenido → Git push → Coolify redespliega

- Pros: Simple, debuggeable, separación clara entre generación y publicación
- Cons: Requiere Python en el servidor, dos sistemas para mantener
- Effort: Medium

### Approach 2: Astro + Node.js script

**Arquitectura:** Similar a Approach 1 pero con Node.js/TypeScript en lugar de Python

- Pros: Stack unificado (JS/TS), mejor integración con ecosistema Astro
- Cons: Más complejo para scraping de noticias
- Effort: Medium

### Approach 3: Astro con SSR + API route para generación

**Arquitectura:** Astro en modo híbrido/SSR, con endpoint API que genera contenido on-demand

- Pros: Generación bajo demanda, más flexible
- Cons: Complejo, requiere servidor corriendo, overkill para blog estático
- Effort: High

## Recommendation

**Approach 1 (Astro + Python)** es el mejor porque:
1. Python tiene mejor ecosistema para scraping y procesamiento de noticias
2. Separación clara: generación (Python) ≠ publicación (Astro)
3. Fácil de debuggear y mantener
4. El usuario ya tiene Python en el servidor

## Key Research Findings

### Astro Content Collections
- Usar `glob` loader con Zod schema para blog posts
- Soporte MDX nativo para contenido enriquecido
- Schema recomendado: title, description, pubDate, author, image, tags

### Ollama API
- Endpoint: `http://127.0.0.1:11434/api/generate`
- Modelo configurable via env var `OLLAMA_MODEL`
- Soporta streaming y respuesta completa
- Web search integrado disponible (`options.web_search: true`)

### Umami Integration
- Script tag simple: `<script defer data-website-id="ID" src="https://analytics.sebastianmorales.sbs/script.js"></script>`
- Paquete `@yeskunall/astro-umami` disponible (6.3K weekly downloads)
- IMPORTANTE: Con View Transitions de Astro, usar `data-astro-rerun` para tracking correcto

### SEO para Agentes IA (llms.txt)
- **ESTADO ACTUAL (2026):** Estándar propuesto, NO soportado por LLMs principales (Ahrefs, junio 2026)
- Solo ~2% de sitios tienen llms.txt válido (Ahrefs dataset 1M sitios)
- Google NO usa llms.txt para búsqueda
- **Recomendación:** Crearlo como experimento de bajo costo, pero NO obsesionarse
- Priorizar fundamentos: HTML semántico, datos estructurados, contenido claro
- JSON-LD con Schema.org SÍ es relevante para SEO tradicional

### Schema.org JSON-LD para Blog
```json
{
  "@context": "https://schema.org",
  "@type": "Blog",
  "name": "Crítica Tecnológica",
  "url": "https://blog.sebastianmorales.sbs",
  "author": {
    "@type": "Person",
    "name": "Sebastian Morales"
  }
}
```

## Risks

1. **Calidad del contenido IA** — Sin supervisión humana, el contenido puede ser genérico o incorrecto
2. **Penalización SEO** — Google degrada contenido generado masivamente sin valor agregado
3. **Reputación** — Poner nombre propio en contenido político automatizado tiene riesgos
4. **Mantenimiento** — Modelos de Ollama cambian frecuentemente, puede requerir ajustes
5. **Scalability** — Ollama local tiene límites de rendimiento

## Open Questions

1. ¿Qué fuentes de noticias usar? (HackerNews, TechCrunch RSS, scraping custom)
2. ¿Frecuencia exacta de publicación? (1 post/día, múltiples?)
3. ¿Revisión humana o 100% automatizado?
4. ¿Dominio exacto: `blog.sebastianmorales.sbs`?
5. ¿Estilo visual del blog? (tema Astro existente o custom?)

## Ready for Proposal

**Yes** — La exploración es suficiente para avanzar a propuesta. Las.open questions deben resolverse en la fase de propuesta con el usuario.
