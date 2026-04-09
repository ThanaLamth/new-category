import { execFileSync } from "node:child_process";
import { writeFile } from "node:fs/promises";

const SHEET_CSV_URL =
  "https://docs.google.com/spreadsheets/d/1henfW4prbK61maDEwLGA9mkgJkbJxllH0UM5Z9-J6hM/export?format=csv&gid=205384556";

const siteConfigs = {
  Coincu: {
    baseUrl: "https://coincu.com",
    username: "Elena Ivanova",
    appPassword: "xP0tJ6W3YoQqbvoFYuNV0arb",
    categories: [39400, 12416],
    timezoneOffsetHours: 7,
  },
  Kanalcoin: {
    baseUrl: "https://www.kanalcoin.com",
    username: "Aisha Khan",
    appPassword: "Jc2Y9VCjp0B8yLmJZT89PfGJ",
    categories: [245, 837],
    timezoneOffsetHours: 4,
  },
  Tokentopnews: {
    baseUrl: "https://tokentopnews.com",
    username: "Kaelynmonroe",
    appPassword: "zvqryQdJNeq3XtM9tSQ42uPZ",
    categories: [604, 605],
    timezoneOffsetHours: 4,
  },
  Bitcoininfonews: {
    baseUrl: "https://bitcoininfonews.com",
    username: "Diego Martinez",
    appPassword: "Uo1PKG5lkLnWghIj3qPPYuFh",
    categories: [572, 1192],
    timezoneOffsetHours: 4,
  },
  Theccpress: {
    baseUrl: "https://theccpress.com",
    username: "adriana",
    appPassword: "euVZ40tHNPjjAyJd268b9YVw",
    categories: [2189, 2192],
    timezoneOffsetHours: 4,
  },
  "coinlive.me": {
    baseUrl: "https://coinlive.me",
    username: "Akita",
    appPassword: "QlBxP7Dcp6xdFnFnFbZDU55N",
    categories: [11517, 11518],
    timezoneOffsetHours: 4,
  },
  coinlineup: {
    baseUrl: "https://coinlineup.com",
    username: "rohancryptowrites",
    appPassword: "AOtnQDnljU00vyf61FSfGLuM",
    categories: [370, 371],
    timezoneOffsetHours: 4,
  },
};

const targetRows = new Set(
  (process.argv
    .find((arg) => arg.startsWith("--rows="))
    ?.replace("--rows=", "")
    .split(",")
    .filter(Boolean)
    .map((value) => Number(value.trim())) ?? [])
);
const dryRun = process.argv.includes("--dry-run");

function docIdFromUrl(url) {
  const match = url.match(/\/document\/d\/([^/]+)/);
  if (!match) throw new Error(`Could not parse doc id from ${url}`);
  return match[1];
}

function htmlDecode(text) {
  return text
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&rsquo;/g, "'")
    .replace(/&lsquo;/g, "'")
    .replace(/&rdquo;/g, '"')
    .replace(/&ldquo;/g, '"')
    .replace(/&ndash;/g, "-")
    .replace(/&mdash;/g, "-")
    .replace(/&#39;/g, "'")
    .replace(/&#8217;/g, "'")
    .replace(/&#8211;/g, "-")
    .replace(/&#8212;/g, "-")
    .replace(/&#8230;/g, "...")
    .replace(/&#([0-9]+);/g, (_, code) => String.fromCharCode(Number(code)));
}

function stripTags(text) {
  return htmlDecode(text.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim());
}

function cleanGoogleRedirects(html) {
  return html.replace(/href="https:\/\/www\.google\.com\/url\?q=([^"&]+)[^"]*"/g, (_, encoded) => {
    const decoded = decodeURIComponent(encoded);
    return `href="${decoded.replace(/"/g, "&quot;")}"`;
  });
}

function normalizeLabelText(text) {
  return stripTags(text).replace(/\s+/g, " ").trim().toLowerCase();
}

function stripLabelValue(text, label) {
  const normalizedLabel = label.toLowerCase();
  const normalizedText = text.trim();
  if (!normalizedText.toLowerCase().startsWith(normalizedLabel)) return "";
  return normalizedText.slice(label.length).replace(/^[:\s-]+/, "").trim();
}

function removeLabeledParagraphs(contentHtml, labels) {
  return contentHtml.replace(/<p[^>]*>[\s\S]*?<\/p>/gi, (paragraphHtml) => {
    const paragraphText = normalizeLabelText(paragraphHtml);
    return labels.some((label) => paragraphText.startsWith(label.toLowerCase()))
      ? ""
      : paragraphHtml;
  });
}

function removeMetaParagraphs(contentHtml) {
  return removeLabeledParagraphs(contentHtml, [
    "Meta Title/Title",
    "Meta Title",
    "SEO Title",
    "Title",
    "Meta Description",
    "Keywords",
    "Keyword",
    "Keyword List",
    "Focus Keywords",
    "Focus Keyword",
    "Focus Keyphrase",
  ]).trim();
}

function extractLabeledParagraph(contentHtml, labels) {
  const paragraphs = [...contentHtml.matchAll(/<p[^>]*>([\s\S]*?)<\/p>/gi)];
  for (const match of paragraphs) {
    const paragraphText = stripTags(match[1]).replace(/\s+/g, " ").trim();
    for (const label of labels) {
      const value = stripLabelValue(paragraphText, label);
      if (value) return value;
    }
  }
  return "";
}

function extractMetaTitle(contentHtml) {
  return extractLabeledParagraph(contentHtml, [
    "Meta Title/Title",
    "Meta Title",
    "SEO Title",
    "Title",
  ]);
}

function extractMetaDescription(contentHtml) {
  return extractLabeledParagraph(contentHtml, ["Meta Description"]);
}

function extractFocusKeywords(contentHtml) {
  const raw = extractLabeledParagraph(contentHtml, [
    "Keywords",
    "Keyword",
    "Keyword List",
    "Focus Keywords",
    "Focus Keyword",
    "Focus Keyphrase",
  ]);
  if (!raw) return [];
  return raw
    .split(/,|\||;|\n/)
    .map((item) => item.replace(/^used\s*:\s*/i, "").trim())
    .filter(Boolean);
}

function extractFirstH1(contentHtml) {
  const match = contentHtml.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
  if (!match) throw new Error("No H1 found in document export");
  return stripTags(match[1]);
}

function removeFirstH1(contentHtml) {
  return contentHtml.replace(/<h1[^>]*>[\s\S]*?<\/h1>/i, "").trim();
}

function sanitizeContentHtml(contentHtml) {
  return contentHtml
    .replace(/<span[^>]*>/gi, "")
    .replace(/<\/span>/gi, "")
    .replace(/<p[^>]*>/gi, "<p>")
    .replace(/<(p|h2|h3|h4|ul|ol|li)[^>]*>/gi, "<$1>")
    .replace(/<a [^>]*href="([^"]+)"[^>]*>/gi, '<a href="$1">')
    .replace(/<img([^>]*?)style="[^"]*"([^>]*?)>/gi, "<img$1$2>")
    .replace(/<img([^>]*?)src="data:image\/[^"]+"([^>]*?)>/gi, "<img$1$2>")
    .replace(/<p>\s*<\/p>/gi, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function normalizeBodyHtml(rawHtml) {
  const bodyMatch = rawHtml.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  if (!bodyMatch) throw new Error("No body found in document export");
  return cleanGoogleRedirects(bodyMatch[1]).trim();
}

function utcGmtIsoFromLocalOffset(datetime, offsetHours) {
  const [datePart, timePart] = datetime.split(" ");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute, second] = timePart.split(":").map(Number);
  const ms = Date.UTC(year, month - 1, day, hour - offsetHours, minute, second);
  return new Date(ms).toISOString().replace(".000Z", "");
}

function slugifyTitle(title) {
  return htmlDecode(title)
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");
}

function escapeHtmlAttr(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function parseDataUrl(src) {
  const match = src.match(/^data:(image\/[a-zA-Z0-9.+-]+);base64,([\s\S]+)$/);
  if (!match) throw new Error("Unsupported image data URL");
  return {
    mime: match[1],
    buffer: Buffer.from(match[2], "base64"),
  };
}

async function uploadMedia(site, row, title, imageIndex, src) {
  const { mime, buffer } = parseDataUrl(src);
  const ext = mime.split("/")[1]?.replace("jpeg", "jpg") || "png";
  const filename = `bulk-hulk-row-${row.row}-${imageIndex}.${ext}`;
  const auth = Buffer.from(`${site.username}:${site.appPassword}`, "utf8").toString("base64");
  const res = await fetch(`${site.baseUrl}/wp-json/wp/v2/media`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${auth}`,
      "Content-Type": mime,
      "Content-Disposition": `attachment; filename="${filename}"`,
    },
    body: buffer,
  });

  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Non-JSON media response from ${row.site}: ${text.slice(0, 500)}`);
  }

  if (!res.ok) {
    throw new Error(`Failed media upload for row ${row.row} on ${row.site}: ${res.status} ${JSON.stringify(data)}`);
  }

  return data;
}

function imageAltText(title, index, total) {
  return total > 1 ? `${title} image ${index}` : title;
}

async function processEmbeddedImages(site, row, title, html) {
  const matches = [...html.matchAll(/(<a [^>]*href="([^"]+)"[^>]*>\s*)?(?:<span[^>]*>\s*)*<img[^>]*src="(data:image\/[^"]+)"[^>]*>(?:\s*<\/span>)*(?:\s*<\/a>)?/gi)];
  if (matches.length === 0) {
    return { html, featuredMediaId: null };
  }
  const firstHrefMatch = html.match(/<a [^>]*href="([^"]+)"[^>]*>/i);
  const fallbackHref = firstHrefMatch ? htmlDecode(firstHrefMatch[1]) : "";

  let output = "";
  let cursor = 0;
  let featuredMediaId = null;

  for (let i = 0; i < matches.length; i += 1) {
    const match = matches[i];
    const fullMatch = match[0];
    const href = match[2] ? htmlDecode(match[2]) : fallbackHref;
    const src = match[3];
    const start = match.index ?? 0;
    const end = start + fullMatch.length;

    output += html.slice(cursor, start);
    cursor = end;

    const media = await uploadMedia(site, row, title, i + 1, src);
    if (!featuredMediaId) featuredMediaId = media.id;

    const alt = escapeHtmlAttr(imageAltText(title, i + 1, matches.length));
    const imgTag = `<img src="${escapeHtmlAttr(media.source_url)}" alt="${alt}" class="wp-image-${media.id}"/>`;
    const wrappedImg = href ? `<a href="${escapeHtmlAttr(href)}">${imgTag}</a>` : imgTag;
    output += `\n<!-- wp:image {"id":${media.id},"linkDestination":"custom","align":"center","className":"wp-block-image size-full"} -->\n<figure class="wp-block-image aligncenter size-full">${wrappedImg}<figcaption class="wp-element-caption"> </figcaption></figure>\n<!-- /wp:image -->\n`;
  }

  output += html.slice(cursor);
  return { html: output, featuredMediaId };
}

async function fetchDocPayload(docUrl) {
  const docId = docIdFromUrl(docUrl);
  const exportUrl = `https://docs.google.com/document/d/${docId}/export?format=html`;
  const res = await fetch(exportUrl);
  if (!res.ok) {
    throw new Error(`Failed to fetch doc export ${docId}: ${res.status} ${res.statusText}`);
  }

  const rawHtml = await res.text();
  const bodyHtml = normalizeBodyHtml(rawHtml);
  const h1 = extractFirstH1(bodyHtml);
  const seoTitle = extractMetaTitle(bodyHtml);
  const excerpt = extractMetaDescription(bodyHtml);
  const focusKeywords = extractFocusKeywords(bodyHtml);
  const contentWithoutMeta = removeMetaParagraphs(bodyHtml);
  const contentHtml = seoTitle ? contentWithoutMeta : removeFirstH1(contentWithoutMeta);

  return {
    title: seoTitle || h1,
    seoTitle,
    h1,
    excerpt,
    focusKeywords,
    contentHtml: `${contentHtml}\n\n`,
  };
}

async function loadSheetRows() {
  const rowSelector =
    targetRows.size > 0
      ? [...targetRows].sort((a, b) => a - b).join(",")
      : "";
  const psScript = `
$WarningPreference = 'SilentlyContinue'
$url = '${SHEET_CSV_URL}'
$csv = (Invoke-WebRequest -UseBasicParsing $url -TimeoutSec 60).Content | ConvertFrom-Csv
$targets = '${rowSelector}'
if ($targets) {
  $numbers = $targets.Split(',') | ForEach-Object { [int]$_ }
} else {
  $numbers = 2..($csv.Count + 1)
}
$rows = foreach ($n in $numbers) {
  $r = $csv[$n - 2]
  if ($null -eq $r) { continue }
  [pscustomobject]@{
    row = $n
    docUrl = $r.'Article Link'
    scheduleUtcPlus4 = $r.'Time to post'
    existingLink = $r.'Link'
    site = $r.'SITE'
    disclaimer = $r.'Disclaimer'
  }
}
$rows | ConvertTo-Json -Depth 3 -Compress
`;
  const output = execFileSync(
    "powershell",
    ["-NoProfile", "-Command", psScript],
    { encoding: "utf8", maxBuffer: 10 * 1024 * 1024 }
  );
  const parsed = JSON.parse(output);
  const rows = Array.isArray(parsed) ? parsed : [parsed];
  return rows.filter((row) => row.docUrl && row.scheduleUtcPlus4 && row.site);
}

async function savePost(row, payload) {
  const site = siteConfigs[row.site];
  if (!site) throw new Error(`Missing site config for ${row.site}`);

  const auth = Buffer.from(`${site.username}:${site.appPassword}`, "utf8").toString("base64");
  const displayTitle = payload.h1 || payload.title;
  const processed = await processEmbeddedImages(site, row, displayTitle, payload.contentHtml);
  const slug = slugifyTitle(payload.title);
  const dateGmt = utcGmtIsoFromLocalOffset(
    row.scheduleUtcPlus4,
    site.timezoneOffsetHours ?? 4
  );
  const postBody = {
    title: payload.title,
    content: `${sanitizeContentHtml(processed.html)}${row.disclaimer}`,
    status: "future",
    date: row.scheduleUtcPlus4,
    date_gmt: dateGmt,
    categories: site.categories,
    slug,
  };
  if (payload.excerpt) {
    postBody.excerpt = payload.excerpt;
  }
  if (processed.featuredMediaId) {
    postBody.featured_media = processed.featuredMediaId;
  }

  const endpoint = `${site.baseUrl}/wp-json/wp/v2/posts`;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: {
      Authorization: `Basic ${auth}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(postBody),
  });

  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Non-JSON response from ${row.site}: ${text.slice(0, 500)}`);
  }

  if (!res.ok) {
    throw new Error(`Failed saving post for row ${row.row} on ${row.site}: ${res.status} ${JSON.stringify(data)}`);
  }

  const seoWarnings = [];
  const rankMathResult = await updateRankMathMeta(site, auth, data.id, payload, slug).catch((error) => {
    seoWarnings.push(`rankmath: ${error instanceof Error ? error.message : String(error)}`);
    return null;
  });
  const yoastResult = await updateYoastMeta(site, auth, data.id, payload).catch((error) => {
    seoWarnings.push(`yoast: ${error instanceof Error ? error.message : String(error)}`);
    return null;
  });

  return {
    row: row.row,
    site: row.site,
    id: data.id,
    status: data.status,
    link: data.link,
    permalink: `${site.baseUrl}/${slug}/`,
    slug,
    date_gmt: data.date_gmt,
    title: data.title?.rendered ?? payload.title,
    featured_media: data.featured_media,
    seo_title: payload.seoTitle || payload.title,
    h1: payload.h1,
    focus_keywords: payload.focusKeywords,
    seo_warnings: seoWarnings,
    rankmath: rankMathResult,
    yoast: yoastResult,
  };
}

async function updateRankMathMeta(site, auth, postId, payload, slug) {
  const meta = {
    rank_math_title: payload.seoTitle || payload.title,
    rank_math_description: payload.excerpt || "",
    rank_math_focus_keyword: (payload.focusKeywords || []).join(", "),
    rank_math_permalink: slug,
  };
  const res = await fetch(`${site.baseUrl}/wp-json/rankmath/v1/updateMeta`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${auth}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      objectType: "post",
      objectID: postId,
      meta,
    }),
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${text.slice(0, 400)}`);
  }
  return text ? JSON.parse(text) : { ok: true };
}

async function updateYoastMeta(site, auth, postId, payload) {
  const yoastMeta = {
    _yoast_wpseo_title: payload.seoTitle || payload.title,
    _yoast_wpseo_metadesc: payload.excerpt || "",
    _yoast_wpseo_focuskw: (payload.focusKeywords || []).join(", "),
  };
  const res = await fetch(`${site.baseUrl}/wp-json/wp/v2/posts/${postId}`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${auth}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      meta: yoastMeta,
    }),
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${text.slice(0, 400)}`);
  }
  return text ? JSON.parse(text) : { ok: true };
}

async function main() {
  const rows = await loadSheetRows();
  const results = [];

  for (const row of rows) {
    const payload = await fetchDocPayload(row.docUrl);
    const summary = {
      row: row.row,
      site: row.site,
      scheduleUtcPlus4: row.scheduleUtcPlus4,
      date_gmt: utcGmtIsoFromLocalOffset(
        row.scheduleUtcPlus4,
        siteConfigs[row.site]?.timezoneOffsetHours ?? 4
      ),
      title: payload.title,
      seoTitle: payload.seoTitle,
      h1: payload.h1,
      excerpt: payload.excerpt,
      focusKeywords: payload.focusKeywords,
    };

    if (dryRun) {
      results.push({ ...summary, mode: "dry-run" });
      continue;
    }

    try {
      const created = await savePost(row, payload);
      results.push({ ...summary, ...created, mode: "posted" });
    } catch (error) {
      results.push({
        ...summary,
        mode: "failed",
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  const outPath = "C:\\Users\\admin\\bulk-hulk-sheet-post-results.json";
  await writeFile(outPath, JSON.stringify(results, null, 2), "utf8");
  console.log(JSON.stringify({ dryRun, outPath, results }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
