# Estado Actual — Blog Automatizado

**Fecha:** 2026-07-01
**Última actualización:** 2026-07-01 17:00 UTC

---

## Resumen

Blog automatizado en `blog.sebastianmorales.sbs` que publica 2 posts diarios con análisis crítico de noticias tech desde la perspectiva del materialismo marxista. Contenido generado 100% por IA (Ollama) sin revisión humana.

---

## Estado de Implementación

### ✅ Completado

| Componente | Estado | Archivos |
|------------|--------|----------|
| **Proyecto Astro** | ✅ Listo | `astro.config.mjs`, `package.json`, `tsconfig.json` |
| **Content Collections** | ✅ Listo | `src/content.config.ts` |
| **Layouts** | ✅ Listo | `src/layouts/BaseLayout.astro`, `src/layouts/PostLayout.astro` |
| **Componentes** | ✅ Listo | `src/components/Header.astro`, `src/components/Footer.astro` |
| **Páginas** | ✅ Listo | `src/pages/index.astro`, `src/pages/about.astro` |
| **RSS Feed** | ✅ Listo | `src/pages/rss.xml.ts` |
| **SEO Tradicional** | ✅ Listo | JSON-LD, Open Graph, Twitter Cards, canonical URLs |
| **SEO Agentes IA** | ✅ Listo | `public/llms.txt`, `public/llms-full.txt` |
| **robots.txt** | ✅ Listo | `public/robots.txt` |
| **Automatización** | ✅ Listo | `scripts/generate_post.py`, `scripts/prompt_template.txt` |
| **Umami Analytics** | ✅ Listo | Integrado en BaseLayout |
| **Post de ejemplo** | ✅ Listo | `src/content/blog/2026-07-01-apple-vision-pro-*.mdx` |

### ⏳ Pendiente

| Tarea | Estado | Notas |
|-------|--------|-------|
| **Verificar primera generación** | ⏳ Pendiente | Próxima ejecución: 20:00 UTC hoy |

---

## Stack Técnico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Framework | Astro | ^5.7.10 |
| Content | MDX | ^4.2.6 |
| Estilos | Tailwind CSS | ^3.4.17 |
| Typography | @tailwindcss/typography | ^0.5.15 |
| SEO | @astrojs/sitemap | ^3.3.1 |
| RSS | @astrojs/rss | latest |
| AI | Ollama API | local (127.0.0.1:11434) |
| Modelo | minimax-m3:cloud | configurable via env |
| Analytics | Umami | self-hosted |
| Despliegue | Coolify | auto-deploy on push |

---

## Commits

| PR | Commit | Descripción | Fecha |
|----|--------|-------------|-------|
| PR 1 | `a494bc2` | Fundación Astro (layouts, nav, index) | 2026-07-01 |
| PR 2 | `39ee013` | Contenido + SEO (RSS, llms.txt, robots.txt, JSON-LD) | 2026-07-01 |
| PR 3 | `a41dc20` | Automatización (Python script + Ollama) | 2026-07-01 |
| PR 4 | `0c4b0f4` | Analytics + Marca (Umami + /about) | 2026-07-01 |
| PR 5 | `038bc8c` | Dockerfile + nginx config (producción) | 2026-07-01 |

---

## Variables de Entorno (para Coolify)

```bash
# Ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=minimax-m3:cloud

# Umami Analytics
UMAMI_WEBSITE_ID=<obtener de analytics.sebastianmorales.sbs>
UMAMI_SCRIPT_URL=https://analytics.sebastianmorales.sbs/script.js

# Site
SITE_URL=https://blog.sebastianmorales.sbs
```

---

## Cron Job (configurado)

```bash
# Ejecutar a las 08:00 y 20:00 UTC
0 8,20 * * * cd /home/ubuntu/projects/blog && /usr/bin/python3 scripts/generate_post.py >> /home/ubuntu/projects/blog/blog-generation.log 2>&1
```

**Estado:** ✅ Configurado en crontab del VPS

---

## Estructura del Proyecto

```
/home/ubuntu/projects/blog/
├── astro.config.mjs          # Configuración Astro
├── package.json              # Dependencias
├── tsconfig.json             # TypeScript config
├── tailwind.config.mjs       # Configuración Tailwind
├── Dockerfile                # Build multi-etapa (Node + nginx)
├── nginx.conf                # Configuración nginx
├── .env.example              # Variables de entorno
├── .gitignore                # Archivos ignorados
├── src/
│   ├── content.config.ts     # Schema de Content Collections
│   ├── content/
│   │   └── blog/             # Posts MDX
│   ├── components/
│   │   ├── Header.astro      # Navegación
│   │   └── Footer.astro      # Footer con links
│   ├── layouts/
│   │   ├── BaseLayout.astro  # Layout base
│   │   └── PostLayout.astro  # Layout de posts
│   ├── pages/
│   │   ├── index.astro       # Página principal
│   │   ├── about.astro       # Página sobre mí
│   │   └── rss.xml.ts        # Feed RSS
│   └── styles/
│       └── global.css        # Estilos globales
├── public/
│   ├── llms.txt              # SEO para agentes IA
│   ├── llms-full.txt         # Contenido completo
│   └── robots.txt            # Reglas crawlers
├── scripts/
│   ├── generate_post.py      # Script de generación
│   ├── prompt_template.txt   # Template prompt
│   └── requirements.txt      # Dependencias Python
└── openspec/                 # Artefactos SDD
    ├── config.yaml
    └── changes/blog-automatizado/
        ├── exploration.md
        ├── proposal.md
        ├── design.md
        ├── tasks.md
        └── specs/
```

---

## Próximos Pasos

1. ✅ **Verificar que el blog carga** en `blog.sebastianmorales.sbs` — HTTP 200
2. ✅ **Verificar RSS feed** en `blog.sebastianmorales.sbs/rss.xml` — Funcionando
3. ✅ **Verificar llms.txt** en `blog.sebastianmorales.sbs/llms.txt` — Funcionando
4. ✅ **Verificar analytics** en Umami dashboard — Umami configurado y funcionando
5. ⏳ **Esperar primera generación** — Próxima ejecución: 20:00 UTC hoy
6. ⏳ **Verificar posts generados** en el blog
7. ⏳ **Monitorear calidad** del contenido generado

---

## Notas

- El post de ejemplo (`apple-vision-pro-explotacion-digital.mdx`) es solo para testing, puede eliminarse después del despliegue
- El modelo `minimax-m3:cloud` es configurable via env var `OLLAMA_MODEL`
- Umami está configurado para no trackear en modo desarrollo
- El script de generación tiene retry automático si Ollama falla

---

## Despliegue

**URL:** https://blog.sebastianmorales.sbs
**UUID Coolify:** `zzhjq78rmhdl4aw6d0vdn3rz`
**Repo:** https://github.com/SebastianMoralesDuque/blog (público)
**Build:** Dockerfile multi-etapa (Node.js builder + nginx alpine)
**Traefik:** Auto-configurado via Coolify Docker labels

**Commits desplegados:** `038bc8c` (HEAD)
**Último deploy:** 2026-07-01 21:47 UTC
