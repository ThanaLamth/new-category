import argparse
import csv


HIGH_RISK_PATHS = {
    "macro/regulation",
    "insights/institutional",
    "insights/liquidity",
}


def needs_manual_review(row: dict[str, str]) -> tuple[bool, list[str]]:
    reasons = []
    title = (row.get("title") or "").strip()
    old_categories = (row.get("old_categories") or "").strip()
    path = (row.get("suggested_new_category_path") or "").strip()
    notes = (row.get("notes") or "").strip()
    status = (row.get("status") or "").strip()

    if status != "publish":
        reasons.append("not-published")
    if not title:
        reasons.append("missing-title")
    if title.lower() in {"tess", "tessttt"}:
        reasons.append("test-title")
    if not old_categories or old_categories == "Uncategorized":
        reasons.append("uncategorized-or-empty")
    if " | " in old_categories:
        reasons.append("multiple-old-categories")
    if path in HIGH_RISK_PATHS:
        reasons.append(f"high-risk-target:{path}")
    if "fallback" in notes.lower():
        reasons.append("fallback-rule")
    if row.get("action") == "Manual review":
        reasons.append("manual-review-rule")

    return bool(reasons), reasons


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = []
    with open(args.input, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            flagged, reasons = needs_manual_review(row)
            if not flagged:
                continue
            row["manual_review_reasons"] = " | ".join(reasons)
            rows.append(row)

    rows.sort(
        key=lambda r: (
            r["manual_review_reasons"],
            r["suggested_new_category_path"],
            r["title"].lower(),
        )
    )

    fieldnames = list(rows[0].keys()) if rows else [
        "post_id",
        "status",
        "title",
        "url",
        "old_categories",
        "old_tags",
        "old_category_actions",
        "suggested_new_primary_category",
        "suggested_new_subcategory",
        "suggested_new_category_path",
        "action",
        "notes",
        "manual_review_reasons",
    ]
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
