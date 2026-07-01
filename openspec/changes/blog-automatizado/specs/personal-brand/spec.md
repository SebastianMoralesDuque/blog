# Personal Brand Specification

## Purpose

Define the "About" page and professional links for personal brand promotion.

## Requirements

### Requirement: About Page

The system MUST include a dedicated `/about` page.

#### Scenario: About page content

- GIVEN a user navigates to `/about`
- WHEN the page loads
- THEN it MUST display: name, photo/avatar, brief bio (2-3 paragraphs)
- AND the bio MUST describe professional background and interests
- AND the page MUST include a call-to-action section

#### Scenario: About page design

- GIVEN the about page is rendered
- WHEN a user views it
- THEN the layout MUST be visually distinct from blog posts
- AND it MUST use a two-column layout (text + links) on desktop

### Requirement: Professional Links

The system MUST display clickable professional links.

#### Scenario: LinkedIn link

- GIVEN the about page is rendered
- WHEN the user sees the links section
- THEN there MUST be a LinkedIn link
- AND it MUST open in a new tab
- AND it MUST use the LinkedIn icon or text label

#### Scenario: GitHub link

- GIVEN the about page is rendered
- WHEN the user sees the links section
- THEN there MUST be a GitHub link
- AND it MUST open in a new tab
- AND it MUST use the GitHub icon or text label

#### Scenario: Email link

- GIVEN the about page is rendered
- WHEN the user sees the links section
- THEN there MUST be an email link: `dev@sebastianmorales.sbs`
- AND it MUST use `mailto:` protocol
- AND it MUST open the user's email client

### Requirement: Navigation Integration

The system MUST include the about page in site navigation.

#### Scenario: Header navigation

- GIVEN any page on the blog
- WHEN the header is rendered
- THEN it MUST include a link to `/about`
- AND the link MUST be visible on both desktop and mobile

#### Scenario: Footer navigation

- GIVEN any page on the blog
- WHEN the footer is rendered
- THEN it MUST include a link to `/about`
- AND it MUST include the professional links as icons

### Requirement: SEO for About Page

The system MUST optimize the about page for search engines.

#### Scenario: About page meta tags

- GIVEN the about page is rendered
- WHEN the `<head>` is generated
- THEN it MUST include: title "About - Sebastian Morales"
- AND description MUST include professional keywords
- AND Open Graph tags MUST be present
