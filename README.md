# TokenTopNews Category Remap

This repo contains the first-pass category migration outputs for TokenTopNews.

Files:

- `tokentopnews-category-remap-2026-04-02.csv`
- `tokentopnews-category-remap-summary-2026-04-02.csv`
- `tokentopnews-category-manual-review-2026-04-02.csv`
- `map_tokentopnews_categories.py`
- `build_tokentopnews_manual_review.py`

Notes:

- The WordPress export had XML issues, so parsing was done by `item` block instead of strict XML parsing.
- The remap output is heuristic and should be reviewed before applying changes in WordPress.
- The manual review file highlights posts that are more likely to need human review.
