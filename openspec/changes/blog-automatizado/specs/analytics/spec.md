# Analytics Specification

## Purpose

Define Umami analytics integration for tracking blog visits and user behavior.

## Requirements

### Requirement: Umami Integration

The system MUST integrate Umami analytics via script tag.

#### Scenario: Script injection

- GIVEN the site is deployed
- WHEN any page loads
- THEN the `<head>` MUST include the Umami tracking script
- AND the script MUST use `defer` attribute
- AND the script MUST reference `data-website-id` from environment variable
- AND the script URL MUST point to `analytics.sebastianmorales.sbs`

#### Scenario: View Transitions compatibility

- GIVEN a user navigates between pages using View Transitions
- WHEN the transition completes
- THEN the Umami script MUST track the new page view
- AND the script tag MUST include `data-astro-rerun` attribute

### Requirement: Environment Configuration

The system MUST configure Umami via environment variables.

#### Scenario: Environment variables

- GIVEN the system reads Umami configuration
- WHEN the env vars are not set
- THEN it MUST use defaults: website ID from `UMAMI_WEBSITE_ID` env var
- AND script URL from `UMAMI_SCRIPT_URL` env var (default: `https://analytics.sebastianmorales.sbs/script.js`)

### Requirement: Privacy Compliance

The system MUST respect user privacy.

#### Scenario: Do Not Track

- GIVEN a user has enabled Do Not Track in their browser
- WHEN they visit the blog
- THEN the Umami script MUST respect the DNT setting
- AND no tracking data MUST be collected

### Requirement: Development Mode

The system MUST handle analytics differently in development.

#### Scenario: Development environment

- GIVEN the site is running in development mode (`npm run dev`)
- WHEN pages load
- THEN the Umami script MUST NOT be injected
- AND analytics data MUST NOT be collected
