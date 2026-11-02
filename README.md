# OpenMedGate website

Source and infrastructure of [openmedgate.com](https://openmedgate.com): a static site built with Hugo, served by AWS CloudFront from a private S3 bucket.

OpenMedGate is a movement for open interfaces in healthcare: not a company, not a product, not an open-source project. The text on the site follows a canon kept outside this repository; see [AGENTS.md](AGENTS.md) for the rules that apply to any change of wording.

## Structure

```text
archetypes/blog.md            front matter for a new post
asset-sources/media/          render script and provenance of the two video loops
assets/css/site.css           the whole stylesheet (Hugo pipes minify and fingerprint it)
assets/js/site.js             navigation, reveal on scroll, videos, mechanism diagram, dot matrix, copy link
assets/images/founders/       founder portraits; Hugo resizes them to WebP at build time
blog-inbox/                   where approved posts arrive (README.md describes the procedure)
config/_default/              config.toml, languages.toml (en, pl), params.toml, menus.<lang>.toml
content/<lang>/_index.md      start page front matter
content/<lang>/blog/<slug>/   one page bundle per post and language, linked by translationKey
data/site/<lang>.yaml         all copy of the start page
data/authors.yaml             author profiles for the blog and the founders section
i18n/<lang>.toml              interface strings
layouts/                      baseof, index, blog/list, blog/single, 404 and partials (diagram, icons, cards)
scripts/blog/ingest.py        converts an inbox folder into page bundles
static/fonts/                 self-hosted woff2 (Manrope, IBM Plex Mono; SIL OFL)
static/media/                 rendered video loops and their posters
static/images/signatories/    signatory logos, white and colour variants
terraform/main.tf             S3, CloudFront, ACM and Route 53
upload_www_content.sh         build and deploy
```

## Commands

```bash
hugo server -D          # preview with drafts at http://localhost:1313
hugo --minify           # production build in public/ (generated, not committed)
./upload_www_content.sh # build, mirror public/ to S3 with --delete, invalidate CloudFront
```

The upload uses the AWS SSO profile `quantummed-www-editor`. When its session has expired, run `aws sso login --profile quantummed-www-editor`. The script's `DISTRIBUTION_ID` is empty; look it up once with:

```bash
aws cloudfront list-distributions --profile quantummed-www-editor \
  --query "DistributionList.Items[?Aliases.Items[?@=='openmedgate.com']].Id" --output text
```

Pushing to GitHub does not deploy anything.

## Languages

English is the default language and lives at the root; Polish lives under `/pl/`. The language switch links to the translation of the current page when one exists and to the other language's start page otherwise. Interface strings are in `i18n/`, start-page copy in `data/site/`, menus in `config/_default/menus.<lang>.toml`.

## Start page

Hero with a video loop, a marquee of standards, three observations, the interactive mechanism diagram (today and with open interfaces; it cycles on its own until the visitor takes over), six postulates, evidence (dot matrix of the current review, three numbers, the registry, the method), founders, signatories on a second video loop and the latest findings.

The copy follows the owner's writing rules: full sentences, no "not X but Y" contrasts, no triads, no closing aphorisms, no sentence fragments as headlines.

Items in `data/site/*.yaml` flagged `placeholder: true` carry a visible badge while `showPlaceholderBadges` is on in `params.toml`. The dot matrix fills to `data-filled` on the `[data-matrix]` element once a number exists; without it, it shimmers as a placeholder.

## Blog

Posts are page bundles: `content/pl/blog/<slug>/index.md` with its photos, and `content/en/blog/<slug>/index.md` for the English version, both with the same `translationKey`. The English URL can differ through `slug` in the English front matter. Front matter fields: `title`, `lead`, `date`, `draft`, `authors` (keys of `data/authors.yaml`), `category` (`method`, `mechanism`, `evidence`, `standards`, `procedures`), optional `cover` and `coverAlt`, optional `sources`, optional `updated`. A post without a cover gets a generated one, coloured by category.

Posts arrive in `blog-inbox/`; [blog-inbox/README.md](blog-inbox/README.md) is the procedure and `scripts/blog/ingest.py` does the mechanical part. Drafts (`draft: true`) appear only with `hugo server -D`.

## Design

- Night bands with motion and white sections; one signal colour, mint `#17e39a`. Red is semantic and means closed. Tokens are the custom properties at the top of `assets/css/site.css`.
- Manrope for everything, IBM Plex Mono for labels, references and numbers.
- The mark is two brackets, the right one swung open; inline SVG in `layouts/partials/logo.html`, also `static/favicon.svg` and `static/apple-touch-icon.png`.
- Videos play only while visible and never autoplay for visitors who prefer reduced motion; the posters show instead. See `asset-sources/media/SOURCE.md`.
- No cookies, no analytics, no third-party scripts or fonts.

## Hosting

`terraform/main.tf` describes the S3 bucket `openmedgate-com`, the CloudFront distribution with the `openmedgate.com` and `www` aliases, the ACM certificate in `us-east-1` and the Route 53 records in the hosted zone `Z01408102MYKXZKFCO74L`. The domain was bought at OVH and is delegated to Route 53. Terraform state lives in the `quantummed-terraform-state-bucket` bucket under `openmedgate-com/terraform.tfstate`. Infrastructure changes are made by the infrastructure owner; content work does not run `terraform apply`.

## Fonts

The woff2 files in `static/fonts/` are subsets (Latin and Latin Extended) of Manrope and IBM Plex Mono, both under the SIL Open Font License 1.1 (`static/fonts/OFL.txt`).
