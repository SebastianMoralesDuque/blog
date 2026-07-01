# Proposal: Blog Automatizado

## Intent

Crear un blog automatizado en `blog.sebastianmorales.sbs` que publique 2 posts diarios con análisis crítico de noticias tech desde la perspectiva del materialismo marxista. El contenido generado 100% por IA (Ollama) sin revisión humana, con SEO optimizado para buscadores tradicionales y agentes de IA.

## Scope

### In Scope
- Proyecto Astro + MDX con Tailwind CSS
- Content Collections con schema para blog posts
- Script Python de generación de contenido (Ollama API)
- Fuentes de noticias: HackerNews API + RSS feeds (TechCrunch, The Verge, ArsTechnica)
- Cron job diario (2 publicaciones)
- Umami analytics integrado
- SEO: sitemap, RSS, JSON-LD Schema.org, llms.txt
- Página /about con links (LinkedIn, GitHub, email)
- Despliegue via Coolify + Gitea

### Out of Scope
- Revisión humana de contenido (100% automatizado)
- Sistema de comentarios
- Newsletter
- Monetización
- Múltiples autores

## Capabilities

### New Capabilities
- `blog-core`: Estructura Astro, layouts, componentes, Content Collections
- `content-automation`: Script Python, Ollama API, fuentes de noticias, cron job
- `seo-traditional`: Sitemap, RSS feed, JSON-LD, meta tags
- `seo-ai-agents`: llms.txt, llms-full.txt
- `analytics`: Integración Umami
- `personal-brand`: Página /about con links profesionales

### Modified Capabilities
None — proyecto nuevo.

## Approach

1. **Inicializar proyecto Astro** con template de blog, MDX, Tailwind
2. **Configurar Content Collections** con schema: title, description, pubDate, author, tags, source
3. **Crear script Python** que:
   - Fetch noticias de HackerNews API + RSS feeds
   - Selecciona las más relevantes
   - Genera análisis con Ollama (prompt con tono materialista marxista)
   - Guarda como MDX en `src/content/blog/`
   - Git push automático
4. **Configurar cron** para ejecutar 2x/día
5. **Integrar Umami** con script tag + `data-astro-rerun`
6. **Crear llms.txt** y JSON-LD para SEO
7. **Crear página /about** con links profesionales
8. **Desplegar en Coolify** con variables de entorno

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `/home/ubuntu/projects/blog/` | New | Proyecto completo Astro |
| Gitea `sebastianmorales/blog` | New | Repo privado |
| Coolify | Modified | Nuevo servicio desplegado |
| Cron system | Modified | 2 jobs diarios para generación |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Contenido de baja calidad | High | Prompt optimizado, selección cuidadosa de noticias |
| Penalización SEO por AI slop | Medium | Contenido con análisis genuino, no solo resúmenes |
| Ollama caído o modelo no disponible | Low | Health check en script, fallback a modelo alternativo |
| Repositorio lleno de posts | Low | Limpieza periódica de posts antiguos (>90 días) |

## Rollback Plan

1. Detener cron job: `crontab -e` → comentar las líneas
2. Detener servicio en Coolify
3. El código queda en Gitea, reversible en cualquier momento
4. Posts generados se pueden eliminar del repo

## Dependencies

- Ollama corriendo en `127.0.0.1:11434`
- Gitea accesible para push
- Coolify configurado para auto-deploy on push
- Umami funcionando para analytics

## Success Criteria

- [ ] Blog desplegado en `blog.sebastianmorales.sbs`
- [ ] 2 posts publicados automáticamente por día
- [ ] Umami registrando visitas
- [ ] Sitemap y RSS funcionando
- [ ] JSON-LD válido (testear con Google Rich Results)
- [ ] llms.txt accesible en raíz del dominio
- [ ] Página /about con todos los links
