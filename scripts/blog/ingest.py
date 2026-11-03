#!/usr/bin/env python3
"""Turn an approved post from blog-inbox/<folder>/ into Hugo page bundles.

Usage:
    python scripts/blog/ingest.py blog-inbox/2026-11-10-slug [--dry-run] [--date 2026-11-10T09:00]

Reads pl.md (required) and en.md (optional), applies the conversions listed in
blog-inbox/README.md, copies the photos with ASCII names and writes
content/pl/blog/<slug>/index.md and content/en/blog/<slug>/index.md.
Nothing is written until every check has passed. Standard library only.
"""
import argparse
import datetime
import pathlib
import re
import shutil
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
CATEGORIES = {"method", "mechanism", "evidence", "standards", "procedures", "series"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
POLISH = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


def fail(msg):
    print(f"STOP: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------- minimal YAML front matter ----------

def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        inner = value[1:-1]
        return inner.replace("''", "'") if value[0] == "'" else inner.replace('\\"', '"')
    return value


def parse_front_matter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    block, body = text[3:end].strip("\n"), text[end + 4:].lstrip("\n")
    meta, key = {}, None
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and key:
            meta.setdefault(key, []).append(unquote(stripped[2:]))
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if raw == "":
            meta[key] = []
        elif raw.startswith("[") and raw.endswith("]"):
            meta[key] = [unquote(x) for x in raw[1:-1].split(",") if x.strip()]
        else:
            meta[key] = unquote(raw)
    return meta, body


def load_authors():
    ids = []
    for line in (ROOT / "data" / "authors.yaml").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([a-z0-9-]+):\s*$", line)
        if m:
            ids.append(m.group(1))
    return ids


# ---------- body conversion ----------

def ascii_name(name):
    path = pathlib.Path(name)
    stem = unicodedata.normalize("NFKD", path.stem.translate(POLISH)).encode("ascii", "ignore").decode()
    stem = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "image"
    return f"{stem}{path.suffix.lower()}"


def convert_body(body, notes, images):
    """Return the converted body. `images` collects {ascii name: original name}."""
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and re.match(r"^#\s+", lines[0]):
        lines.pop(0)
        notes.append("removed the leading '# Title' line")
    text = "\n".join(lines)

    n = len(re.findall(r"%%.*?%%", text, flags=re.S)) + len(re.findall(r"<!--.*?-->", text, flags=re.S))
    if n:
        text = re.sub(r"[ \t]*%%.*?%%[ \t]*", "", text, flags=re.S)
        text = re.sub(r"[ \t]*<!--.*?-->[ \t]*", "", text, flags=re.S)
        notes.append(f"removed {n} comment(s)")

    tag_re = r"(?<![\w#&/])#(?!#)([^\W\d_][\w\-/]*)(?=[\s.,;:)]|$)"
    tags = sorted(set(re.findall(tag_re, text, flags=re.M)))
    if tags:
        text = re.sub(r"[ \t]?" + tag_re, "", text, flags=re.M)
        notes.append("removed tag(s): " + ", ".join(tags))

    if re.search(r"^#\s+", text, flags=re.M):
        text = re.sub(r"^(#{1,5})(\s+)", lambda m: "#" + m.group(1) + m.group(2), text, flags=re.M)
        notes.append("shifted headings one level down")

    def embed(m):
        target, _, extra = m.group(1).partition("|")
        desc = "" if re.fullmatch(r"\s*\d+\s*", extra or "") else (extra or "").strip()
        name = ascii_name(target.strip())
        images.setdefault(name, target.strip())
        return f"![{desc}]({name})"

    text = re.sub(r"!\[\[([^\]]+)\]\]", embed, text)

    def img(m):
        target = m.group(2).strip()
        if re.match(r"^https?://", target):
            return m.group(0)
        name = ascii_name(target)
        images.setdefault(name, target)
        return f"![{m.group(1)}]({name}{m.group(3)})"

    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)((?:\s+\"[^\"]*\")?)\)", img, text)

    if re.search(r"\[\[", text):
        text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
        text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
        notes.append("turned internal links into plain text")

    out = []
    for line in text.splitlines():
        m = re.match(r"^>\s*\[!\w+\][+-]?\s*(.*)$", line)
        if m:
            title = m.group(1).strip()
            if title:
                out.append(f"> {title}")
                out.append(">")
            notes.append("converted a callout into a quote")
            continue
        out.append(line)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip("\n") + "\n"

    for pattern, what in ((r"\[\^", "footnotes"), (r"^<(?!br\s*/?>)[a-zA-Z]", "raw HTML"), (r"!\[\[", "embedded notes")):
        if re.search(pattern, text, flags=re.M):
            notes.append(f"ASK THE OPERATOR: the body contains {what}, which do not render")
    return text


# ---------- output ----------

def q(value):
    return "'" + str(value).replace("'", "''") + "'"


def front_matter(meta, lang, date, slug, en_slug, updated):
    lines = ["---", f"title: {q(meta['title'])}"]
    if lang == "en" and en_slug and en_slug != slug:
        lines.append(f"slug: {q(en_slug)}")
    lines += [f"lead: {q(meta.get('lead', ''))}", f"date: {date}"]
    if updated:
        lines.append(f"updated: {updated}")
    lines += ["draft: false", "authors:"]
    lines += [f"  - {a}" for a in meta["authors"]]
    lines.append(f"category: {meta['category']}")
    if meta.get("cover"):
        lines.append(f"cover: {ascii_name(meta['cover'])}")
        lines.append(f"coverAlt: {q(meta.get('coverAlt', ''))}")
    lines.append(f"translationKey: {slug}")
    if meta.get("sources"):
        lines.append("sources:")
        lines += [f"  - {q(s)}" for s in meta["sources"]]
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def normalise_time(value, flag):
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", value):
        value += ":00"
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value):
        fail(f"{flag} must look like 2026-11-10T09:00 (Warsaw time)")
    return value


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--date", help="publication time, Warsaw time, e.g. 2026-11-10T09:00")
    ap.add_argument("--updated", help="set when republishing a live post, e.g. 2026-11-12T10:00")
    args = ap.parse_args()

    folder = pathlib.Path(args.folder)
    if not folder.is_dir():
        fail(f"{folder} is not a folder")
    pl_file = folder / "pl.md"
    if not pl_file.is_file():
        fail("pl.md is missing")
    authors = load_authors()

    pl_meta, pl_body = parse_front_matter(pl_file.read_text(encoding="utf-8"))
    if pl_meta.get("status") != "approved":
        fail("pl.md is not approved")
    for key in ("title", "lead", "category", "authors", "slug"):
        if not pl_meta.get(key):
            fail(f"pl.md has no {key}")
    if pl_meta["category"] not in CATEGORIES:
        fail(f"category must be one of {sorted(CATEGORIES)}")
    if isinstance(pl_meta["authors"], str):
        pl_meta["authors"] = [pl_meta["authors"]]
    unknown = [a for a in pl_meta["authors"] if a not in authors]
    if unknown:
        fail(f"unknown author(s): {', '.join(unknown)}; add a profile to data/authors.yaml first")
    slug = pl_meta["slug"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        fail("slug must be lowercase ASCII letters, digits and hyphens")
    if not pl_body.strip():
        fail("pl.md has no body")

    en_meta, en_body = None, None
    en_file = folder / "en.md"
    if en_file.is_file():
        en_meta, en_body = parse_front_matter(en_file.read_text(encoding="utf-8"))
        if en_meta.get("status") != "approved":
            fail("en.md exists but is not approved")
        for key in ("title", "lead"):
            if not en_meta.get(key):
                fail(f"en.md has no {key}")
        if not en_body.strip():
            fail("en.md has no body")
        for key in ("category", "authors", "cover", "sources"):
            en_meta[key] = pl_meta.get(key)
        en_meta["coverAlt"] = en_meta.get("coverAlt") or pl_meta.get("coverAlt", "")
        en_slug = en_meta.get("slug") or slug
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", en_slug):
            fail("the English slug must be lowercase ASCII letters, digits and hyphens")
    else:
        en_slug = None
        print("NOTE: no en.md; ask the operator whether to publish the Polish version alone.")

    date = normalise_time(args.date or datetime.datetime.now().strftime("%Y-%m-%dT%H:%M"), "--date")
    updated = normalise_time(args.updated, "--updated") if args.updated else None

    # Convert everything first; write only when every check has passed.
    plan = []
    for lang, meta, body in (("pl", pl_meta, pl_body), ("en", en_meta, en_body)):
        if meta is None:
            continue
        notes, images = [], {}
        text = convert_body(body, notes, images)
        if meta.get("cover"):
            images.setdefault(ascii_name(meta["cover"]), meta["cover"])
        for dst, src in images.items():
            candidates = [folder / src] + [f for f in folder.iterdir() if f.is_file() and ascii_name(f.name) == dst]
            found = next((c for c in candidates if c.is_file()), None)
            if found is None:
                fail(f"photo {src} is missing from {folder}")
            if found.suffix.lower() not in IMAGE_EXT:
                fail(f"{found.name} is not an image")
            images[dst] = found
        target = ROOT / "content" / lang / "blog" / slug
        fm = front_matter(meta, lang, date, slug, en_slug if lang == "en" else None, updated)
        plan.append((lang, target, fm + text, notes, images))

    for lang, target, content, notes, images in plan:
        if not args.dry_run:
            target.mkdir(parents=True, exist_ok=True)
            (target / "index.md").write_text(content, encoding="utf-8")
            for dst, src in images.items():
                shutil.copyfile(src, target / dst)
        print(f"[{lang}] {'would write' if args.dry_run else 'wrote'} {target.relative_to(ROOT)}")
        for n in notes:
            print(f"   - {n}")
        for dst, src in images.items():
            print(f"   - photo {src.name} -> {dst}")
    print("Next: hugo server -D, check each language against its source, then wait for approval.")


if __name__ == "__main__":
    main()
