# AGENTS.md: openmedgate.com website

Source and infrastructure of openmedgate.com, a static Hugo site. [README.md](README.md) describes the structure; its Cloudflare Pages section is outdated.

## Hosting

- The live site is served by AWS CloudFront from the private S3 bucket `openmedgate-com`, with DNS in Route 53 (`terraform/main.tf`).
- Pushing to GitHub does not deploy anything. Publishing is a separate upload.

## Commands

- `hugo server -D`: local preview at http://localhost:1313, including drafts.
- `hugo --minify`: production build in `public/` (generated, not committed).
- Publishing: `upload_www_content.sh` builds, mirrors `public/` to S3 with `--delete` and invalidates CloudFront, using the AWS SSO profile `quantummed-www-editor`. Its `DISTRIBUTION_ID` is empty; look it up with `aws cloudfront list-distributions --profile quantummed-www-editor --query "DistributionList.Items[?Aliases.Items[?@=='openmedgate.com']].Id"` before the first upload.

## Where things are

- Start-page copy: `data/site/en.yaml` and `data/site/pl.yaml`; interface strings: `i18n/`; menus: `config/_default/menus.<lang>.toml`. Layouts hold no copy.
- Items flagged `placeholder: true` in the data files carry a visible badge while `showPlaceholderBadges` is on in `config/_default/params.toml`. Replace the text and remove the flag together.
- Blog posts: page bundles under `content/<lang>/blog/<slug>/`, linked by `translationKey`. When the operator says a new post has arrived, or `blog-inbox/` holds a post folder, follow [blog-inbox/README.md](blog-inbox/README.md) step by step.
- Design tokens and every style: `assets/css/site.css`. Fonts are self-hosted in `static/fonts/`; do not add third-party scripts, fonts or trackers.

## What the site is

OpenMedGate is an initiative, not a company, a product or an open-source project. The canon that defines it lives outside this repository, in QuantumMed-Shared (`01-Products/OpenMedGate/OpenMedGate-Overview.md`). Read it before writing or changing any text. The rules that follow from it:

- No sales: no calls to contact a company, no lead forms, no links to commercial offers.
- Signatory companies appear in one fixed place on the site, as signatories of the principles, never under a piece that points at a specific company.
- "Open" means open interfaces and open standards. Never promise to release code, and never publish dates or countdowns for it.
- Company names appear only as quotations from public procurement documents. Never name hospitals, patients or private conversations.
- Every number carries its denominator, source, period and method.
- State principles without geography, so they read internationally; Polish procedures are evidence, not the frame.

## Rules

- This repository is public. Commit only text that is ready to be read by anyone; internal notes and canon documents stay outside it.
- Publish only after the operator explicitly approves it in the current session, and check the live site afterwards.
- Publish only from a clean `main` that is pushed, so the site always matches the repository.
- Never edit `public/`; it is generated.
- Do not store secrets or credentials.
