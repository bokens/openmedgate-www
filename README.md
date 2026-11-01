# OpenMedGate website

Source and infrastructure of [openmedgate.com](https://openmedgate.com): a static site built with Hugo, served by AWS CloudFront from a private S3 bucket.

OpenMedGate is an initiative, not a company, a product or an open-source project. The text on the site follows a canon kept outside this repository; see [AGENTS.md](AGENTS.md) for the rules that apply to any change of wording.

## Structure

```text
archetypes/blog.md            front matter for a new post
assets/css/site.css           the whole stylesheet (Hugo pipes minify and fingerprint it)
assets/js/site.js             theme toggle, mobile navigation, reveal on scroll, copy link
assets/images/founders/       founder portraits; Hugo resizes them to WebP at build time
blog-inbox/                   where approved posts arrive (README.md describes the procedure)
config/_default/              config.toml, languages.toml (en, pl), params.toml, menus.<lang>.toml
content/<lang>/_index.md      start page front matter
content/<lang>/blog/<slug>/   one page bundle per post and language, linked by translationKey
data/site/<lang>.yaml         all copy of the start page
data/authors.yaml             author profiles for the blog and the founders section
i18n/<lang>.toml              interface strings
layouts/                      baseof, index, blog/list, blog/single, 404 and partials
scripts/blog/ingest.py        converts an inbox folder into page bundles
static/fonts/                 self-hosted woff2 (Fraunces, IBM Plex Sans, IBM Plex Mono; SIL OFL)
static/images/signatories/    signatory logos, colour and white variants
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

## Blog

Posts are page bundles: `content/pl/blog/<slug>/index.md` with its photos, and `content/en/blog/<slug>/index.md` for the English version, both with the same `translationKey`. The English URL can differ through `slug` in the English front matter. Front matter fields: `title`, `lead`, `date`, `draft`, `authors` (keys of `data/authors.yaml`), `category` (`method`, `mechanism`, `evidence`, `standards`, `procedures`), optional `cover` and `coverAlt`, optional `sources` (a list shown under the post), optional `updated`.

Posts arrive in `blog-inbox/`; [blog-inbox/README.md](blog-inbox/README.md) is the procedure and `scripts/blog/ingest.py` does the mechanical part. Drafts (`draft: true`) appear only with `hugo server -D`.

## Design

- Paper, ink and one signal colour (vermilion). Tokens are the custom properties at the top of `assets/css/site.css`; the dark theme redefines them under `[data-theme="dark"]`.
- Fraunces for display, IBM Plex Sans for text, IBM Plex Mono for references, dates, labels and numbers.
- The mark is two brackets, the right one swung open; it is inline SVG in `layouts/partials/logo.html` and `static/favicon.svg`.
- The theme follows the system preference and can be switched in the header; the choice is kept in `localStorage`.
- No cookies, no analytics, no third-party scripts or fonts.

Items in `data/site/*.yaml` flagged `placeholder: true` carry a visible badge while `showPlaceholderBadges` is on in `params.toml`. Switch it off, or remove the flags, once the content is final.

## Hosting

`terraform/main.tf` describes the S3 bucket `openmedgate-com`, the CloudFront distribution with the `openmedgate.com` and `www` aliases, the ACM certificate in `us-east-1` and the Route 53 records in the hosted zone `Z01408102MYKXZKFCO74L`. The domain was bought at OVH and is delegated to Route 53. Terraform state lives in the `quantummed-terraform-state-bucket` bucket under `openmedgate-com/terraform.tfstate`. Infrastructure changes are made by the infrastructure owner; content work does not run `terraform apply`.

## Fonts

The woff2 files in `static/fonts/` are subsets (Latin and Latin Extended) of Fraunces, IBM Plex Sans and IBM Plex Mono, all under the SIL Open Font License 1.1 (`static/fonts/OFL.txt`).
