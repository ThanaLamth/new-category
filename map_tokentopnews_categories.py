import argparse
import csv
import gzip
import html
import re
from collections import Counter


OLD_CATEGORY_ACTIONS = {
    "Blockchain Event": "Delete old category",
    "Blockchain Events": "Delete old category",
    "CMC": "Keep",
    "Crypto Insights": "Reclassify",
    "Bitcoin Price Prediction": "Delete old category",
    "Crypto Topics": "Delete old category",
    "Airdrop News": "Reclassify",
    "CBDC News": "Reclassify",
    "Cloud Mining": "Delete old category",
    "Crypto Presales": "Delete old category",
    "Crypto Regulation": "Reclassify",
    "Press Release": "Keep",
    "Sponsored Articles": "Keep",
    "Cryptocurrency News": "Reclassify",
    "Altcoins": "Reclassify",
    "Bitcoin": "Convert asset category to tag",
    "Cardano": "Convert asset category to tag",
    "Dogecoin": "Reclassify",
    "Ethereum": "Convert asset category to tag",
    "Ripple": "Convert asset category to tag",
    "Solana": "Convert asset category to tag",
    "TRON": "Convert asset category to tag",
    "Finance & Cryptocurrency": "Reclassify",
    "Knowledge": "Delete old category",
    "Learn Crypto": "Delete old category",
    "Top Projects": "Delete old category",
    "Uncategorized": "Delete old category",
}


COMMERCIAL = {
    "CMC": ("cmc", "", "/cmc", "Kept from old CMC category"),
    "Sponsored Articles": (
        "sponsored-articles",
        "",
        "/sponsored-articles",
        "Kept from old Sponsored Articles category",
    ),
    "Press Release": (
        "press-release",
        "",
        "/press-release",
        "Kept from old Press Release category",
    ),
}


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def classify(text: str, old_categories: list[str], tags: list[str]) -> tuple[str, str, str, str, str]:
    text = text.lower()
    tag_text = " ".join(tags).lower()
    old_set = set(old_categories)

    for cat, result in COMMERCIAL.items():
        if cat in old_set:
            primary, sub, path, note = result
            return primary, sub, path, OLD_CATEGORY_ACTIONS.get(cat, "Keep"), note

    if contains_any(
        text,
        [
            "weekly recap",
            "week in review",
            "top stories this week",
            "this week in crypto",
            "weekly roundup",
            "weekly-recap",
            "top stories",
        ],
    ):
        return "weekly-recap", "top-stories", "weekly-recap/top-stories", "Reclassify", "Weekly recap/top stories pattern"

    if contains_any(
        text,
        [
            "etf inflow",
            "etf outflow",
            "net inflow",
            "net outflow",
            "funding rate",
            "open interest",
            "bitfinex longs",
            "bitfinex",
            "liquidation",
            "short squeeze",
            "long squeeze",
            "leverage",
            "resistance level",
        ],
    ):
        return "insights", "liquidity", "insights/liquidity", "Reclassify", "Liquidity / positioning signal"

    if contains_any(
        text,
        [
            "on-chain",
            "realized price",
            "exchange reserve",
            "exchange balances",
            "whale accumulation",
            "sopr",
            "mvrv",
            "supply in profit",
            "supply in loss",
            "dormancy",
            "utxo",
        ],
    ):
        return "insights", "on-chain", "insights/on-chain", "Reclassify", "On-chain metric signal"

    if contains_any(
        text,
        [
            "institutional",
            "corporate treasury",
            "reserve",
            "sovereign",
            "tokenized equities",
            "tokenized equity",
            "fundrise",
            "vcx",
            "blackrock",
            "microstrategy",
            "strategy bought",
            "treasury strategy",
            "el salvador",
            "openai",
            "anthropic",
            "spacex",
        ],
    ):
        return "insights", "institutional", "insights/institutional", "Reclassify", "Institutional / treasury / fund signal"

    if contains_any(
        text,
        [
            "airdrop",
            " ai ",
            "ai-crypto",
            "artificial intelligence",
            "ai agent",
            "openai",
            "anthropic",
            "llm",
        ],
    ):
        return "trends", "ai-crypto", "trends/ai-crypto", "Reclassify", "AI-crypto trend signal"

    if contains_any(
        text,
        [
            "defi",
            "dex",
            "staking",
            "restaking",
            "yield farming",
            "liquidity pool",
            "amm",
            "borrow and lend",
            "lending protocol",
        ],
    ):
        return "trends", "defi", "trends/defi", "Reclassify", "DeFi trend signal"

    if "dogecoin" in text or contains_any(
        text,
        ["memecoin", "meme coin", "pepe", "shib", "doge", "bonk", "floki"]
    ):
        return "trends", "memecoins", "trends/memecoins", "Reclassify", "Memecoin trend signal"

    if contains_any(text, ["altcoin season", "altseason", "altcoins rally", "altcoin rally", "capital rotation into altcoins"]):
        return "narratives", "altcoin-season", "narratives/altcoin-season", "Reclassify", "Altcoin season narrative"

    if contains_any(
        text,
        [
            "ethereum ecosystem",
            "layer 2",
            "layer-2",
            "l2",
            "rollup",
            "restaking",
            "ethereum scaling",
            "eth ecosystem",
        ],
    ):
        return "narratives", "ethereum-ecosystem", "narratives/ethereum-ecosystem", "Reclassify", "Ethereum ecosystem narrative"

    if contains_any(
        text,
        [
            "bitcoin cycle",
            "halving",
            "fear & greed",
            "fear and greed",
            "capitulation",
            "accumulation phase",
            "bull market",
            "bear market",
            "cycle top",
            "cycle bottom",
        ],
    ):
        return "narratives", "bitcoin-cycle", "narratives/bitcoin-cycle", "Reclassify", "Bitcoin cycle narrative"

    if contains_any(text, ["cross-market", "correlation with stocks", "crypto and stocks", "bitcoin and gold"]):
        return "narratives", "cross-market", "narratives/cross-market", "Reclassify", "Cross-market narrative"

    if contains_any(
        text,
        [
            "federal reserve",
            "fed ",
            "fed's",
            "fomc",
            "interest rate",
            "rate cut",
            "rate hike",
            "inflation",
            "cpi",
            "pce",
            "treasury yield",
            "payrolls",
            "unemployment",
        ],
    ):
        return "macro", "fed", "macro/fed", "Reclassify", "Fed / inflation / rates signal"

    if contains_any(
        text,
        [
            "global liquidity",
            "m2",
            "money supply",
            "balance sheet",
            "quantitative tightening",
            "quantitative easing",
            "liquidity cycle",
            "central bank liquidity",
            "dollar liquidity",
        ],
    ):
        return "macro", "global-liquidity", "macro/global-liquidity", "Reclassify", "Global liquidity signal"

    if contains_any(
        text,
        [
            "oil price",
            "crude oil",
            "nasdaq",
            "s&p 500",
            "stocks",
            "equities",
            "gold price",
            "dollar index",
            "risk-on",
            "risk off",
        ],
    ) and contains_any(text, ["bitcoin", "btc", "crypto", "ethereum", "xrp", "solana"]):
        return "macro", "crypto-macro", "macro/crypto-macro", "Reclassify", "Macro plus crypto cross-market signal"

    regulation_terms = [
        "securities and exchange commission",
        "regulation",
        "regulatory",
        "bill c-",
        "election law",
        "compliance",
        "legal challenge",
        "ban on crypto",
        "crypto donation",
        "department of justice",
        "lawsuit against",
        "sec lawsuit",
        "court ruling",
        "judge ruled",
        "cbdc",
    ]
    if "crypto regulation" in old_set or "cbdc news" in {c.lower() for c in old_set} or contains_any(text, regulation_terms):
        return "macro", "regulation", "macro/regulation", "Reclassify", "Regulation or legal-policy signal"

    if "dogecoin" in old_set:
        return "trends", "memecoins", "trends/memecoins", "Reclassify", "Old Dogecoin category fallback"
    if "altcoins" in {c.lower() for c in old_set}:
        return "narratives", "altcoin-season", "narratives/altcoin-season", "Reclassify", "Old Altcoins category fallback"
    if "bitcoin" in {c.lower() for c in old_set} or "bitcoin" in tag_text or "btc" in tag_text:
        return "narratives", "bitcoin-cycle", "narratives/bitcoin-cycle", "Reclassify", "Bitcoin asset fallback"
    if "ethereum" in {c.lower() for c in old_set} or "ethereum" in tag_text or "eth" in tag_text:
        return "narratives", "ethereum-ecosystem", "narratives/ethereum-ecosystem", "Reclassify", "Ethereum asset fallback"
    if contains_any(tag_text, ["xrp", "ripple", "solana", "cardano", "tron"]):
        return "insights", "", "insights", "Reclassify", "Asset-tag fallback into broad insights"
    if "crypto insights" in {c.lower() for c in old_set}:
        return "insights", "", "insights", "Reclassify", "Old Crypto Insights fallback"

    return "insights", "", "insights", "Manual review", "Broad fallback; review manually"


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
        if post["status"] == "trash":
            continue
        primary, sub, path, action, note = classify(
            post["analysis_text"], post["old_categories"], post["tags"]
        )
        category_counts[path] += 1
        old_actions = sorted(
            {
                OLD_CATEGORY_ACTIONS.get(cat, "Review")
                for cat in post["old_categories"]
            }
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
