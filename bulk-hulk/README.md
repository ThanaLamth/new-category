# Bulk Hulk Workflow

This folder contains the bulk scheduling workflow used for the `BULK HULK` Google Sheet.

## Files

- `bulk-hulk-sheet-post.mjs`: schedules posts from the sheet and pushes content to WordPress
- `bulk-hulk-sheet-links-to-paste.csv`: row-to-permalink mapping for pasting full slugs back into the sheet

## Ubuntu Setup

Requirements:

- Ubuntu with `node` 18+ installed
- outbound internet access

Run:

```bash
git clone https://github.com/ThanaLamth/new-category.git
cd new-category/bulk-hulk
node bulk-hulk-sheet-post.mjs --rows=197 --dry-run
```

Schedule specific rows:

```bash
node bulk-hulk-sheet-post.mjs --rows=187,188,197
```

Schedule everything allowed by the script:

```bash
node bulk-hulk-sheet-post.mjs
```

Output:

- results are written to `bulk-hulk-sheet-post-results.json` in this same folder

## Current Behavior

- If a doc has `Meta Title/Title`, that value is used for SEO title and slug
- If a doc has only `H1`, the `H1` is used for SEO title and slug
- `H1` remains the visible heading inside the article
- `Meta Description` is used for excerpt
- keyword lists are sent as focus keywords
- images are uploaded as centered Gutenberg image blocks with caption and alt text
