import argparse
import csv
import gzip
import html
import re
from collections import Counter


KEEP_DIRECT = {
    "CMC": ("cmc", "", "/cmc", "Keep", "Kept as separate distribution/commercial layer"),
    "Sponsored Articles": (
        "sponsored-articles",
        "",
        "/sponsored-articles",
        "Keep",
        "Kept as separate sponsored/commercial layer",
    ),
    "Press Release": (
        "press-release",
        "",
        "/press-release",
        "Keep",
        "Kept as separate PR/commercial layer",
    ),
}


OLD_CATEGORY_ACTIONS = {
    "Blockchain Events": "Reclassify",
    "Blockchain Event": "Reclassify",
    "CMC": "Keep",
    "Guides": "Keep",
    "Bitcoin": "Reclassify",
    "bitcoin": "Reclassify",
    "Blockchain": "Reclassify",
    "Crypto Trading": "Reclassify",
    "Cryptocurrency": "Merge into /guides/crypto-basics",
    "Crypto Basics": "Reclassify",
    "Markets": "Keep",
    "Crypto Market": "Merge into /markets",
    "Forex": "Delete",
    "Stock Market": "Delete",
    "Mining": "Merge into /guides",
    "News": "Keep",
    "Crypto": "Delete broad duplicate category",
    "Crypto Regulations": "Merge into /news/regulation",
    "Regulation": "Reclassify",
    "NFT": "Reclassify or tag",
    "Shiba Inu Coin": "Convert to tag",
    "Sponsored Articles": "Keep",
    "Stories": "Delete",
    "Tools": "Delete",
    "Top Projects": "Reclassify",
    "Uncategorized": "Delete and reassign",
    "Altcoins": "Reclassify",
    "Ethereum": "Reclassify",
    "ethereum": "Reclassify",
    "Xrp": "Reclassify",
    "exchanges": "Reclassify",
    "bank": "Reclassify",
}


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def classify(text: str, old_categories: list[str], tags: list[str]) -> tuple[str, str, str, str, str]:
    lower = text.lower()
    old_set = set(old_categories)

    for cat, result in KEEP_DIRECT.items():
        if cat in old_set:
            return result

    if "top projects" in {c.lower() for c in old_set} or contains_any(
        lower,
        [
            "top projects",
            "best crypto projects",
            "top blockchain projects",
            "top altcoin projects",
            "project round-up",
        ],
    ):
        return "projects", "top-projects", "/projects/top-projects", "Reclassify", "Top projects content"

    if contains_any(
        lower,
        [
            "project review",
            "reviewed project",
            "token review",
            "project assessment",
            "platform review",
            "is it legit",
        ],
    ):
        return "projects", "reviews", "/projects/reviews", "Reclassify", "Project review content"

    if contains_any(
        lower,
        [
            "new project",
            "new token project",
            "emerging project",
            "new crypto project",
            "upcoming project",
            "new blockchain project",
        ],
    ):
        return "projects", "new-projects", "/projects/new-projects", "Reclassify", "New project discovery content"

    if "guides" in {c.lower() for c in old_set} or contains_any(
        lower,
        [
            "what is crypto",
            "what is cryptocurrency",
            "how to buy crypto",
            "how to start with crypto",
            "beginner guide",
            "beginners guide",
            "crypto basics",
            "what is bitcoin",
            "what is ethereum",
        ],
    ):
        if contains_any(lower, ["wallet", "seed phrase", "private key", "cold wallet", "hot wallet"]):
            return "guides", "wallets", "/guides/wallets", "Reclassify", "Wallet explainer content"
        if contains_any(lower, ["defi", "dex", "lending protocol", "yield farming", "staking", "restaking"]):
            return "guides", "defi", "/guides/defi", "Reclassify", "DeFi explainer content"
        if contains_any(lower, ["crypto trading", "trading strategy", "technical analysis", "candlestick", "stop loss"]):
            return "guides", "crypto-trading", "/guides/crypto-trading", "Reclassify", "Trading guide content"
        if contains_any(lower, ["blockchain", "smart contract", "consensus", "layer 1", "layer 2"]):
            return "guides", "blockchain", "/guides/blockchain", "Reclassify", "Blockchain explainer content"
        if contains_any(lower, ["security", "hack", "scam", "phishing", "wallet safety", "protect your crypto"]):
            return "guides", "security", "/guides/security", "Reclassify", "Security guide content"
        if contains_any(lower, ["altcoin", "altcoins", "dogecoin", "shiba inu", "xrp", "solana", "cardano"]):
            return "guides", "altcoins", "/guides/altcoins", "Reclassify", "Altcoin explainer content"
        return "guides", "crypto-basics", "/guides/crypto-basics", "Reclassify", "General crypto basics guide"

    if "markets" in {c.lower() for c in old_set} or contains_any(
        lower,
        [
            "price prediction",
            "price outlook",
            "market trend",
            "price analysis",
            "technical analysis",
            "resistance level",
            "support level",
            "market volatility",
            "bullish momentum",
            "bearish momentum",
            "etf inflows",
            "liquidation",
        ],
    ):
        if contains_any(lower, [" xrp ", "xrp/", "ripple", "ripple (xrp)", "xrp price"]):
            return "markets", "xrp", "/markets/xrp", "Reclassify", "XRP market/price analysis"
        if contains_any(lower, [" ethereum ", "eth ", "eth/", "ethereum price"]):
            return "markets", "ethereum", "/markets/ethereum", "Reclassify", "Ethereum market/price analysis"
        return "markets", "bitcoin", "/markets/bitcoin", "Reclassify", "Bitcoin or broad crypto market analysis"

    if "news" in {c.lower() for c in old_set} or "crypto" in {c.lower() for c in old_set}:
        if contains_any(lower, ["exchange", "binance", "coinbase", "kraken", "bybit", "okx", "listing"]):
            return "news", "exchanges", "/news/exchanges", "Reclassify", "Exchange/news coverage"
        if contains_any(lower, ["bank", "banks", "banking", "jpmorgan", "goldman sachs", "bank of america"]):
            return "news", "bank", "/news/bank", "Reclassify", "Banking/finance news"
        if contains_any(lower, ["regulation", "regulatory", "sec", "lawsuit", "compliance", "bill ", "legal"]):
            return "news", "regulation", "/news/regulation", "Reclassify", "Regulation news"
        if contains_any(lower, ["event", "conference", "summit", "expo", "blockchain week", "consensus 202"]):
            return "news", "blockchain-events", "/news/blockchain-events", "Reclassify", "Blockchain event news"
        if contains_any(lower, [" ethereum ", "eth ", "ethereum/", "ethereum price"]):
            return "news", "ethereum", "/news/ethereum", "Reclassify", "Ethereum news"
        if contains_any(lower, ["altcoin", "altcoins", "dogecoin", "shiba", "solana", "cardano", "xrp", "ripple"]):
            return "news", "altcoins", "/news/altcoins", "Reclassify", "Altcoin news"
        return "news", "bitcoin", "/news/bitcoin", "Reclassify", "Bitcoin or general crypto news"

    if "blockchain" in {c.lower() for c in old_set}:
        return "guides", "blockchain", "/guides/blockchain", "Reclassify", "Old Blockchain category"
    if "crypto trading" in {c.lower() for c in old_set}:
        return "guides", "crypto-trading", "/guides/crypto-trading", "Reclassify", "Old Crypto Trading category"
    if "crypto basics" in {c.lower() for c in old_set}:
        return "guides", "crypto-basics", "/guides/crypto-basics", "Reclassify", "Old Crypto Basics category"
    if "altcoins" in {c.lower() for c in old_set}:
        return "news", "altcoins", "/news/altcoins", "Reclassify", "Old Altcoins category"
    if "ethereum" in {c.lower() for c in old_set}:
        return "news", "ethereum", "/news/ethereum", "Reclassify", "Old Ethereum category"
    if "xrp" in {c.lower() for c in old_set}:
        return "markets", "xrp", "/markets/xrp", "Reclassify", "Old XRP category"
    if "bitcoin" in {c.lower() for c in old_set}:
        return "news", "bitcoin", "/news/bitcoin", "Reclassify", "Old Bitcoin category"

    return "news", "bitcoin", "/news/bitcoin", "Manual review", "Broad fallback; review manually"


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
