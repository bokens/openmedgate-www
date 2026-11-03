#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'HELP'
Usage: ./upload_www_content.sh [--dry-run]

Build the site with Hugo, mirror public/ to the openmedgate.com S3 bucket and
invalidate the CloudFront distribution. Remote files absent from public/ are
deleted. The distribution is found by its openmedgate.com alias.

  --dry-run  Build and preview the S3 changes without uploading or invalidating.
  --help     Show this help.

AWS_PROFILE selects the AWS CLI profile (default: quantummed-www-editor).
HELP
}

DRY_RUN=false
case "${1:-}" in
  "") ;;
  --dry-run) DRY_RUN=true ;;
  --help|-h) usage; exit 0 ;;
  *) usage >&2; exit 1 ;;
esac

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export AWS_PROFILE="${AWS_PROFILE:-quantummed-www-editor}"
export AWS_PAGER=""
BUCKET_NAME="openmedgate-com"
DOMAIN_NAME="openmedgate.com"
REGION="eu-central-1"

for tool in aws hugo; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Required command is missing: %s\n' "$tool" >&2
    exit 1
  fi
done

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  printf 'AWS session unavailable for profile %s. Run: aws sso login --profile %s\n' "$AWS_PROFILE" "$AWS_PROFILE" >&2
  exit 1
fi

printf 'Building the site...\n'
(cd "$PROJECT_DIR" && hugo --minify --cleanDestinationDir --quiet)

# Do not mirror an incomplete build with --delete.
for page in index.html pl/index.html blog/index.html; do
  if [[ ! -s "$PROJECT_DIR/public/$page" ]]; then
    printf 'Missing or empty public/%s; upload cancelled.\n' "$page" >&2
    exit 1
  fi
done

DISTRIBUTION_ID="$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Aliases.Items[?@=='${DOMAIN_NAME}']].Id | [0]" --output text)"
if [[ ! "$DISTRIBUTION_ID" =~ ^[A-Z0-9]+$ ]]; then
  printf 'CloudFront distribution for %s not found (got: %s).\n' "$DOMAIN_NAME" "$DISTRIBUTION_ID" >&2
  exit 1
fi

SYNC_OPTIONS=(
  --delete
  --no-follow-symlinks
  --cache-control "public,max-age=300"
  --exclude ".DS_Store" --exclude "*/.DS_Store"
  --region "$REGION"
)
if [[ "$DRY_RUN" == true ]]; then
  SYNC_OPTIONS+=(--dryrun)
fi

printf 'Source: %s/public/\nDestination: s3://%s/\nCloudFront: %s\nProfile: %s\n' "$PROJECT_DIR" "$BUCKET_NAME" "$DISTRIBUTION_ID" "$AWS_PROFILE"
aws s3 sync "$PROJECT_DIR/public/" "s3://$BUCKET_NAME/" "${SYNC_OPTIONS[@]}"

if [[ "$DRY_RUN" == true ]]; then
  printf 'Dry run complete. Nothing uploaded, no invalidation requested.\n'
  exit 0
fi

INVALIDATION_ID="$(aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" --paths '/*' \
  --query 'Invalidation.Id' --output text)"
printf 'Files uploaded. CloudFront invalidation %s requested.\nWebsite: https://%s\n' "$INVALIDATION_ID" "$DOMAIN_NAME"
