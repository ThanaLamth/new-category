import argparse
import csv
import gzip
import html
import re
from collections import Counter


KEEP_DIRECT = {
    "CMC": ("cmc", "", "/cmc", "Keep", "Kept as separate commercial/distribution category"),
    "Sponsored Articles": (
        "sponsored-articles",
        "",
        "/sponsored-articles",
        "Keep",
        "Kept as separate sponsored/commercial category",
    ),
    "Press Release": (
        "press-release",
        "",
        "/press-release",
        "Keep",
        "Kept as separate PR/commercial category",
    ),
    "Press Releases": (
        "press-release",
        "",
        "/press-release",
        "Merge",
        "Merged legacy press-releases into /press-release",
    ),
}


OLD_CATEGORY_ACTIONS = {
    "Altcoin News": "Reclassify by narrative angle",
    "Bitcoin News": "Reclassify by narrative angle",
    "News": "Reclassify by narrative angle",
    "Crypto News": "Reclassify by narrative angle",
    "CMC": "Keep",
    "Sponsored Articles": "Keep",
    "Press Release": "Keep",
    "Press Releases": "Merge into /press-release",
    "Crypto 101": "Remove as category",
    "Blockchain Technology": "Remove as category",
    "Cryptocurrencies": "Convert to tags / migrate",
    "Services": "Remove as category",
    "Ripple": "Convert to tag",
    "Crypto Exchanges": "Map editorial stories to /power/exchanges",
    "Ethereum": "Convert to tag",
    "Blockchain Event": "Do not keep as core category",
    "Crypto Wallets": "Remove as category",
    "EOS": "Convert to tag",
    "Litecoin": "Convert to tag",
    "Bitcoin Cash": "Convert to tag",
    "Cardano": "Convert to tag",
    "Binance Coin (BNB)": "Convert to tag",
    "Stellar": "Convert to tag",
    "Monero": "Convert to tag",
    "Analysis": "Reclassify by narrative angle",
    "Binance": "Reclassify by narrative angle",
    "Learn Crypto": "Remove as category",
    "Binance Exchange": "Merge into /power/exchanges",
    "Pin Post": "Remove and use featured flag",
    "Mining": "Convert to tag",
}


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def classify(text: str, old_categories: list[str], tags: list[str]) -> tuple[str, str, str, str, str]:
    lower = text.lower()
    old_set = set(old_categories)

    for cat, result in KEEP_DIRECT.items():
        if cat in old_set:
            return result

    if contains_any(
        lower,
        [
            "fraud",
            "scam",
            "rug pull",
            "stole",
            "stolen",
            "hack",
            "hacked",
            "embezzlement",
            "money laundering",
            "theft",
            "ponzi",
            "seized funds",
            "arrested",
            "sentenced",
        ],
    ):
        return "investigations", "fraud", "/investigations/fraud", "Reclassify", "Fraud / scam / enforcement angle"

    if contains_any(
        lower,
        [
            "collapsed",
            "collapse",
            "bankrupt",
            "bankruptcy",
            "implosion",
            "liquidation",
            "shut down",
            "chapter 11",
            "insolvency",
            "wiped out",
        ],
    ):
        return "investigations", "collapse", "/investigations/collapse", "Reclassify", "Collapse / failure angle"

    if contains_any(
        lower,
        [
            "controversy",
            "backlash",
            "criticized",
            "criticism",
            "under fire",
            "uproar",
            "faces questions",
            "accused",
            "sparks debate",
            "sparks concern",
        ],
    ):
        return "investigations", "controversy", "/investigations/controversy", "Reclassify", "Controversy angle"

    if contains_any(
        lower,
        [
            "sec",
            "lawsuit",
            "court",
            "judge",
            "regulation",
            "regulatory",
            "bill ",
            "compliance",
            "legal battle",
            "legal dispute",
            "charges filed",
            "appeal",
        ],
    ):
        return "conflicts", "regulation", "/conflicts/regulation", "Reclassify", "Regulation conflict angle"

    if contains_any(
        lower,
        [
            "dispute",
            "feud",
            "clash",
            "battle with",
            "sues",
            "sued",
            "terminates partnership",
            "conflict with",
            "split from",
            "war with",
            "standoff",
        ],
    ):
        return "conflicts", "company", "/conflicts/company", "Reclassify", "Company conflict angle"

    if contains_any(
        lower,
        [
            "decentralization debate",
            "community split",
            "governance fight",
            "ideological",
            "maximalist",
            "censorship",
            "values clash",
            "philosophical divide",
        ],
    ):
        return "conflicts", "ideology", "/conflicts/ideology", "Reclassify", "Ideology conflict angle"

    if contains_any(
        lower,
        [
            "founder",
            "ceo",
            "co-founder",
            "creator",
            "satoshi",
            "charles hoskinson",
            "vitalik",
            "cz",
            "sam bankman-fried",
            "justin sun",
            "elon musk",
        ],
    ):
        return "people", "founders", "/people/founders", "Reclassify", "Founder / executive profile angle"

    if contains_any(
        lower,
        [
            "influencer",
            "analyst says",
            "trader says",
            "youtube",
            "x post",
            "tweeted",
            "social media figure",
            "promoter",
            "commentator",
        ],
    ):
        return "people", "influencers", "/people/influencers", "Reclassify", "Influencer / personality angle"

    if contains_any(
        lower,
        [
            "institution",
            "blackrock",
            "fidelity",
            "bank",
            "asset manager",
            "sovereign",
            "government",
            "treasury",
            "central bank",
            "etf issuer",
        ],
    ):
        return "people", "institutions", "/people/institutions", "Reclassify", "Institutional actor angle"

    if contains_any(
        lower,
        [
            "exchange",
            "binance",
            "coinbase",
            "kraken",
            "bybit",
            "okx",
            "bitfinex",
            "huobi",
            "listing",
            "delisting",
        ],
    ) or "crypto exchanges" in {c.lower() for c in old_set}:
        return "power", "exchanges", "/power/exchanges", "Reclassify", "Exchange power / market influence angle"

    if contains_any(
        lower,
        [
            "venture capital",
            "vc",
            "a16z",
            "paradigm",
            "funding round",
            "raises",
            "raised",
            "backed by",
            "investor",
            "seed round",
        ],
    ):
        return "power", "vcs", "/power/vcs", "Reclassify", "VC / capital power angle"

    if contains_any(
        lower,
        [
            "regulator",
            "sec",
            "cftc",
            "fca",
            "esma",
            "lawmakers",
            "congress",
            "justice department",
            "regulatory body",
        ],
    ):
        return "power", "regulators", "/power/regulators", "Reclassify", "Regulator power angle"

    if contains_any(
        lower,
        [
            "dramatic surge",
            "crash",
            "panic",
            "shock",
            "fear and greed",
            "whale moves",
            "liquidated",
            "sell-off",
            "soars",
            "plunges",
            "breakout drama",
        ],
    ):
        return "stories", "market-drama", "/stories/market-drama", "Reclassify", "Market drama story angle"

    if contains_any(
        lower,
        [
            "company saga",
            "returns to",
            "comes back",
            "relaunch",
            "restructuring",
            "long-running saga",
            "chapter in",
            "expands into",
            "partnership saga",
        ],
    ):
        return "stories", "company-sagas", "/stories/company-sagas", "Reclassify", "Company saga angle"

    if contains_any(
        lower,
        [
            "rise and fall",
            "boom and bust",
            "surged then fell",
            "token collapse",
            "from hype to",
            "meteoric rise",
            "project downfall",
        ],
    ):
        return "stories", "project-rise-fall", "/stories/project-rise-fall", "Reclassify", "Project rise/fall angle"

    if "blockchain event" in {c.lower() for c in old_set}:
        return "people", "institutions", "/people/institutions", "Reclassify", "Event-driven institutional angle fallback"
    if "analysis" in {c.lower() for c in old_set}:
        return "stories", "market-drama", "/stories/market-drama", "Reclassify", "Legacy analysis fallback"
    if "binance" in {c.lower() for c in old_set} or "binance exchange" in {c.lower() for c in old_set}:
        return "power", "exchanges", "/power/exchanges", "Reclassify", "Legacy Binance category fallback"

    return "stories", "market-drama", "/stories/market-drama", "Manual review", "Broad fallback; review manually"


def parse_posts(path: str):
    text = gzip.open(path, "rt", encoding="utf-8", errors="replace").read()
    for match in re.finditer(r"<item>(.*?)</item>", text, re.S):
        block = match.group(1)
        post_type = re.search(r"<wp:post_type><!\[CDATA\[(.*?)\]\]></wp:post_type>", block, re.S)
        if not post_type or post_type.group(1) != "post":
            continue
        title = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", block, re.S)
        link = re.search(r"<link>(.*?)</link>", block, re.S)
        status = re.search(r"<wp:status><!\[CDATA\[(.*?)\]\]></wp:status>", block, re.S)
        post_id = re.search(r"<wp:post_id>(.*?)</wp:post_id>", block, re.S)
        content = re.search(r"<content:encoded><!\[CDATA\[(.*?)\]\]></content:encoded>", block, re.S)
        old_categories = [
            html.unescape(m.group(1).strip())
            for m in re.finditer(
                r'<category\s+domain="category"[^>]*><!\[CDATA\[(.*?)\]\]></category>',
                block,
                re.S,
            )
        ]
        tags = [
            html.unescape(m.group(1).strip())
            for m in re.finditer(
                r'<category\s+domain="post_tag"[^>]*><!\[CDATA\[(.*?)\]\]></category>',
                block,
                re.S,
            )
        ]
        title_text = html.unescape(title.group(1).strip()) if title else ""
        content_text = html.unescape(content.group(1)) if content else ""
        analysis_text = " \n".join(
            [title_text, content_text, " ".join(old_categories), " ".join(tags)]
        )
        yield {
            "post_id": post_id.group(1).strip() if post_id else "",
            "title": title_text,
            "url": html.unescape(link.group(1).strip()) if link else "",
            "status": status.group(1).strip() if status else "",
            "old_categories": old_categories,
            "tags": tags,
            "analysis_text": analysis_text,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=False)
    args = parser.parse_args()

    rows = []
    category_counts = Counter()
    for post in parse_posts(args.input):
        primary, sub, path, action, note = classify(
            post["analysis_text"], post["old_categories"], post["tags"]
        )
        category_counts[path] += 1
        old_actions = sorted(
            {OLD_CATEGORY_ACTIONS.get(cat, "Review") for cat in post["old_categories"]}
        )
        rows.append(
            {
                "post_id": post["post_id"],
                "status": post["status"],
                "title": post["title"],
                "url": post["url"],
                "old_categories": " | ".join(post["old_categories"]),
                "old_tags": " | ".join(post["tags"]),
                "old_category_actions": " | ".join(old_actions),
                "suggested_new_primary_category": primary,
                "suggested_new_subcategory": sub,
                "suggested_new_category_path": path,
                "action": action,
                "notes": note,
            }
        )

    rows.sort(
        key=lambda r: (
            r["suggested_new_category_path"],
            r["status"],
            r["title"].lower(),
        )
    )

    fieldnames = [
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
    ]
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    if args.summary:
        with open(args.summary, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["suggested_new_category_path", "post_count"])
            for path, count in sorted(category_counts.items()):
                writer.writerow([path, count])


if __name__ == "__main__":
    main()
