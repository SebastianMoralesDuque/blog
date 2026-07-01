# SEO Traditional Specification

## Purpose

Define traditional SEO features: sitemap, RSS feed, JSON-LD structured data, and meta tags.

## Requirements

### Requirement: Sitemap Generation

The system MUST generate an XML sitemap automatically.

#### Scenario: Sitemap includes all posts

- GIVEN blog posts exist in the collection
- WHEN the build runs
- THEN `sitemap.xml` MUST be generated at the root
- AND it MUST include all published posts
- AND each entry MUST include: lastmod, changefreq, priority

#### Scenario: Sitemap excludes drafts

- GIVEN a post with `draft: true` in frontmatter
- WHEN the build runs
- THEN that post MUST NOT appear in the sitemap

### Requirement: RSS Feed

The system MUST provide an RSS feed for blog subscribers.

#### Scenario: RSS feed generation

- GIVEN blog posts exist
- WHEN the build runs
- THEN `rss.xml` MUST be generated at the root
- AND it MUST include: title, link, description, pubDate for each post
- AND the feed MUST be valid RSS 2.0

### Requirement: JSON-LD Structured Data

The system MUST include Schema.org JSON-LD for blog and posts.

#### Scenario: Blog-level structured data

- GIVEN any page on the blog
- WHEN the page loads
- THEN the `<head>` MUST contain a JSON-LD script with `@type: Blog`
- AND it MUST include: name, description, url, author

#### Scenario: Post-level structured data

- GIVEN a blog post page
- WHEN the page loads
- THEN the `<head>` MUST contain a JSON-LD script with `@type: BlogPosting`
- AND it MUST include: headline, author, datePublished, description, keywords

### Requirement: Meta Tags

The system MUST include proper meta tags for social sharing and SEO.

#### Scenario: Open Graph tags

- GIVEN any page
- WHEN the page loads
- THEN the `<head>` MUST include: og:title, og:description, og:type, og:url, og:image
- AND og:image MUST default to a fallback image if no post image

#### Scenario: Twitter Card tags

- GIVEN any page
- WHEN the page loads
- THEN the `<head>` MUST include: twitter:card, twitter:title, twitter:description

#### Scenario: Canonical URLs

- GIVEN any page
- WHEN the page loads
- THEN the `<head>` MUST include a canonical URL pointing to the current page

### Requirement: robots.txt

The system MUST include a robots.txt file.

#### Scenario: robots.txt content

- GIVEN the site is deployed
- WHEN `robots.txt` is fetched
- THEN it MUST allow crawling of all pages
- AND it MUST reference the sitemap URL
