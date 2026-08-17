#!/usr/bin/env python3
"""Update README.md with the latest Hashnode blog post.

Fetches the publication RSS feed and rewrites the region between the
BLOG-POST-LIST markers with a link to the most recent post.

RSS is used deliberately: Hashnode's GraphQL Public API now requires a paid
Pro plan for every request (including reads), whereas the RSS feed is free.

The feed sits behind Cloudflare. From most networks it returns clean XML, but
a CI runner can occasionally be served an anti-bot HTML challenge instead. So
we retry, send a realistic browser User-Agent, and — crucially — fail *loudly*
with diagnostics rather than dying on a cryptic XML ParseError.
"""
import re
import sys
import xml.etree.ElementTree as ET

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

README_PATH = "README.md"
FEED_URL = "https://prayush.hashnode.dev/rss.xml"
START_MARKER = "<!-- BLOG-POST-LIST:START -->"
END_MARKER = "<!-- BLOG-POST-LIST:END -->"

HEADERS = {
    # A real browser UA + Accept header; some CDNs reject obvious bot clients.
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
}


def fail(msg, *, body=None):
    """Emit a GitHub Actions error annotation and exit non-zero."""
    print(f"::error::update_blog: {msg}", file=sys.stderr)
    if body is not None:
        snippet = " ".join(body[:300].split())
        print(f"  response began with: {snippet!r}", file=sys.stderr)
    sys.exit(1)


def fetch_feed():
    session = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=1.5,  # waits ~0s, 1.5s, 3s, 6s between attempts
        status_forcelist=(403, 429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        resp = session.get(FEED_URL, headers=HEADERS, timeout=30)
    except requests.RequestException as exc:
        fail(f"request to {FEED_URL} failed: {exc}")

    ctype = resp.headers.get("content-type", "unknown")
    print(f"GET {FEED_URL} -> HTTP {resp.status_code} ({ctype})")

    if resp.status_code != 200:
        fail(f"unexpected status {resp.status_code}", body=resp.text)

    # Cloudflare / anti-bot challenge pages come back as HTML, not XML.
    if "xml" not in ctype.lower() and not resp.text.lstrip().startswith("<?xml"):
        fail(f"expected XML, got content-type {ctype!r} "
             "(likely a Cloudflare anti-bot page, not the feed)", body=resp.text)

    return resp.content


def latest_post(feed_bytes):
    try:
        root = ET.fromstring(feed_bytes)
    except ET.ParseError as exc:
        fail(f"could not parse feed XML: {exc}",
             body=feed_bytes.decode("utf-8", "replace"))

    item = root.find("./channel/item")  # first <item> == newest post
    if item is None:
        fail("feed parsed but contained no <item> elements")

    title = (item.findtext("title") or "").strip()
    url = (item.findtext("link") or "").strip()
    if not title or not url:
        fail(f"latest item missing title/link (title={title!r}, url={url!r})")

    return title, url


def update_readme(title, url):
    with open(README_PATH, encoding="utf-8") as f:
        content = f.read()

    if START_MARKER not in content or END_MARKER not in content:
        fail(f"markers not found in {README_PATH}: "
             f"expected {START_MARKER} ... {END_MARKER}")

    new_section = f"{START_MARKER}\n📝 [{title}]({url})\n{END_MARKER}"
    # Replace via a function so backslashes/\g<> in the title aren't treated
    # as regex backreferences in the replacement string.
    updated = re.sub(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        lambda _match: new_section,
        content,
        flags=re.DOTALL,
    )

    if updated == content:
        print(f"README already current — latest post: {title}")
        return

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"Updated README with latest post: {title}")


def main():
    title, url = latest_post(fetch_feed())
    update_readme(title, url)


if __name__ == "__main__":
    main()
