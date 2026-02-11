# OpenMedGate Website

Static website for [openmedgate.com](https://openmedgate.com) built with Hugo.

## Stack

- **Generator:** Hugo (static site generator)
- **Styling:** TailwindCSS (via CDN for dev, build for prod)
- **Interactivity:** Alpine.js
- **Forms:** HubSpot embed
- **Booking:** Calendly embed
- **Hosting:** Cloudflare Pages

## Quick Start

### Prerequisites

- [Hugo](https://gohugo.io/installation/) (extended version)
- Node.js 18+ (for Tailwind build - optional)

### Development

```bash
# Clone repo
git clone https://github.com/bokens/openmedgate-www.git
cd openmedgate-www

# Start dev server
hugo server -D

# Open http://localhost:1313
```

### Build

```bash
hugo --minify
# Output in /public
```

## Project Structure

```
openmedgate-www/
├── config/
│   └── _default/
│       ├── config.toml      # Main Hugo config
│       ├── languages.toml   # i18n (EN/PL/DE)
│       └── params.toml      # Site parameters
├── content/
│   ├── en/                  # English content
│   ├── pl/                  # Polish content
│   └── de/                  # German content
├── i18n/                    # UI translations
├── layouts/
│   ├── _default/            # Base layouts
│   ├── partials/            # Reusable components
│   └── index.html           # Homepage
├── static/
│   ├── images/
│   ├── _headers             # Cloudflare headers
│   └── _redirects           # Cloudflare redirects
└── README.md
```

## Configuration

### HubSpot Integration

1. Get your Portal ID and Form ID from HubSpot
2. Update `config/_default/params.toml`:

```toml
hubspotPortalId = "YOUR_PORTAL_ID"
hubspotFormId = "YOUR_FORM_ID"
```

### Calendly Integration

1. Get your Calendly URL
2. Update `config/_default/params.toml`:

```toml
calendlyURL = "https://calendly.com/your-link"
```

### Countdown Campaign

Configure the open-sourcing countdown in `params.toml`:

```toml
countdownEnabled = true
countdownTargetDate = "2026-08-01T00:00:00Z"
```

### Adding Content

Content is in Markdown files under `content/{lang}/`:

- `content/en/_index.md` - English homepage
- `content/pl/_index.md` - Polish homepage
- `content/de/_index.md` - German homepage

## Deployment (Cloudflare Pages)

### Setup

1. Connect your GitHub repo to Cloudflare Pages
2. Configure build settings:
   - **Build command:** `hugo --minify`
   - **Build output directory:** `public`
   - **Environment variable:** `HUGO_VERSION` = `0.128.0`

### Custom Domain

1. Add `openmedgate.com` in Cloudflare Pages settings
2. Configure DNS:
   - CNAME `@` → `openmedgate-www.pages.dev`
   - Or use Cloudflare DNS proxy

### Domain Redirects (301)

For other OMG domains (.eu, .io, .org), set up redirect rules in Cloudflare:

1. Go to domain's Cloudflare dashboard
2. Rules → Redirect Rules
3. Add rule: `*` → `https://openmedgate.com` (301)

## Features

### Implemented ✅

- [x] Multi-language (EN/PL/DE)
- [x] Language switcher (auto-detect + manual)
- [x] Dark/light mode
- [x] Cookie consent (GDPR)
- [x] HubSpot form embed
- [x] Calendly embed
- [x] Countdown timer
- [x] Segment picker (Hospital/AI Vendor/Developer/Public Sector)
- [x] Responsive (mobile-first)
- [x] SEO (meta tags, OG tags, sitemap, robots.txt)
- [x] Cloudflare Pages ready

### TODO 📋

- [ ] Add actual content (manifest, how it works, etc.)
- [ ] Add logo and images
- [ ] Replace Tailwind CDN with build (optional, for performance)
- [ ] Add privacy policy, terms, imprint pages
- [ ] Connect HubSpot (real Portal/Form IDs)
- [ ] Connect Calendly (real URL)
- [ ] Add social links

## License

Proprietary - OpenMedGate
