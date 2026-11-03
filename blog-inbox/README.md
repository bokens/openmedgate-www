# Blog inbox

Approved posts are copied here, one folder per post. An agent working in this repository turns each one into a blog post, shows it to the operator and publishes it after the operator approves it. Everything in this folder except this file is ignored by git.

## What arrives

```text
blog-inbox/RRRR-MM-DD-<slug>/
  pl.md          Polish version (required)
  en.md          English version (optional)
  *.jpg, *.png   photos the posts use
```

From `pl.md` the procedure reads `status`, the fields both languages share (`category`, `authors`, `cover`, `coverAlt`, `slug`, `sources`) and the Polish `title`, `lead` and body. From `en.md` it reads `status`, the English `title`, `lead`, `slug` and body. Other fields belong to the source repository and are never copied.

Valid values: `category` is `method`, `mechanism`, `evidence`, `standards`, `procedures` or `series` (the “One bid” series); `authors` are the keys of `data/authors.yaml`. A new author needs a profile there first; ask the operator for it.

## Procedure

1. **Check the source.** `pl.md` has `status: approved`, a title, a lead, a body, a valid category, valid authors and a slug. If `en.md` exists, it also has `status: approved`, a title, a lead and a body. If anything is missing, stop and tell the operator; do not fill it in yourself.
2. **Find what is already done.** `<slug>` is the `slug` from `pl.md`.
   - No `content/pl/blog/<slug>/`: continue with step 3.
   - The folder is untracked or has uncommitted changes: an earlier run stopped before approval; continue with step 5.
   - The folder is committed but https://openmedgate.com/pl/blog/<slug>/ does not show the post: continue with step 7.
   - The post is live: this is an update. Go through every step and pass `--updated` in step 3.
3. **Convert.** `python scripts/blog/ingest.py blog-inbox/<folder> --dry-run`, then without `--dry-run`. The script writes `content/pl/blog/<slug>/index.md`, `content/en/blog/<slug>/index.md` when `en.md` exists, and copies the photos with lowercase ASCII names. `--date` sets the publication time in Warsaw time; the default is now. Nothing publishes on its own, so a future date means the post appears only with the first deployment on or after that date; tell the operator.
4. **Report the conversions.** The script changes only what the rules below allow and prints each change. Report every one of them. If it prints `ASK THE OPERATOR`, stop and ask.
   - a leading `# Title` line is removed, since the title comes from the front matter;
   - if the body uses `#` for sections, every heading moves one level down;
   - `![[photo.png]]` or `![[photo.png|description]]` becomes `![description](photo.png)`; a number after `|` is an Obsidian display width and is dropped;
   - a link to another note keeps only its text, since internal notes are not public;
   - a callout (`> [!note] Title`, also `[!note]-` and `[!note]+`) becomes a plain quote: the marker goes, a title stays as the quote's first paragraph, and a `>` line separates it from the content;
   - comments (`%% … %%`, `<!-- … -->`) and tags (`#tag`) are removed.

   Never rewrite, shorten, reorder, translate or add text. Raw HTML, footnotes and embedded notes do not render: ask the operator what to do with them.
5. **Preview.** Run `hugo server -D` and give the operator http://localhost:1313/pl/blog/<slug>/, plus http://localhost:1313/blog/<English slug>/ when there is an English version. Check each language against its source: the same number of headings, bold passages, italics, links, list items, quotes, table rows and photos, every photo in the same place, and the visible text matching the source word for word apart from the changes reported in step 4. Obsidian shows a single line break as a new line; the website joins such lines into one paragraph. Where the source relies on single line breaks, ask whether they should be separate paragraphs.
6. **Wait for approval.** Continue only after the operator explicitly approves this post in this session.
7. **Publish.** Stop the preview server. Commit only `content/*/blog/<slug>/`, with the message `blog: <Polish title>`, push to `main`, then run `./upload_www_content.sh` (see AGENTS.md for the distribution id).
8. **Verify and report.** The Polish address and the English one, if there is one, answer 200 and show the title and every photo, and the post is listed on https://openmedgate.com/pl/blog/ and https://openmedgate.com/blog/. Then delete `blog-inbox/<folder>/` and give the operator the addresses.
