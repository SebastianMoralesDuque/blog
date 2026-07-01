# Blog Core Specification

## Purpose

Define the Astro project structure, layouts, components, and Content Collections for the blog.

## Requirements

### Requirement: Project Structure

The system MUST use Astro with MDX integration and Tailwind CSS.

#### Scenario: Project initialization

- GIVEN a fresh Astro project
- WHEN `npm create astro@latest` is executed with blog template
- THEN the project MUST include `@astrojs/mdx` and `@astrojs/tailwind` integrations
- AND `astro.config.mjs` MUST configure both integrations

### Requirement: Content Collections

The system MUST define a `blog` content collection with Zod schema.

#### Scenario: Blog post schema validation

- GIVEN a blog post MDX file in `src/content/blog/`
- WHEN the file is processed by the content collection
- THEN the frontmatter MUST include: title (string), description (string), pubDate (date), author (string), tags (array of strings), source (string)
- AND invalid frontmatter MUST cause a build error

#### Scenario: MDX support

- GIVEN a blog post with `.mdx` extension
- WHEN the file contains JSX components
- THEN the components MUST render correctly in the output

### Requirement: Layout System

The system MUST provide a base layout and a blog post layout.

#### Scenario: Base layout renders common elements

- GIVEN any page using the base layout
- WHEN the page is rendered
- THEN it MUST include `<head>` with meta tags, Umami script, and JSON-LD
- AND it MUST include a header with site title and navigation
- AND it MUST include a footer with copyright and links

#### Scenario: Blog post layout renders article metadata

- GIVEN a blog post using the post layout
- WHEN the page is rendered
- THEN it MUST display: title, publication date, author, tags, and reading time
- AND the content MUST be rendered in a readable typography style

### Requirement: Responsive Design

The system MUST be fully responsive across mobile, tablet, and desktop.

#### Scenario: Mobile viewport

- GIVEN a user on a 375px viewport
- WHEN they load any page
- THEN all content MUST be readable without horizontal scrolling
- AND navigation MUST collapse to a mobile menu

### Requirement: Cognitive UX Design

The system MUST use design patterns that encourage reading and engagement.

#### Scenario: Typography for readability

- GIVEN a blog post page
- WHEN the user reads the content
- THEN the font size MUST be at least 16px
- AND line height MUST be 1.6-1.8
- AND content width MUST be max 70ch for optimal reading

#### Scenario: Visual hierarchy

- GIVEN a blog post page
- WHEN the user scans the page
- THEN headings MUST have clear visual distinction
- AND blockquotes MUST be visually distinct
- AND code blocks MUST have syntax highlighting
