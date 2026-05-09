import feedparser
import re

FEED_URL = "https://prayush.hashnode.dev/rss.xml"
README_PATH = "README.md"
START_MARKER = "<!-- BLOG-POST-LIST:START -->"
END_MARKER = "<!-- BLOG-POST-LIST:END -->"

feed = feedparser.parse(FEED_URL)
latest = feed.entries[0]

post_md = f"📝 [{latest.title}]({latest.link})"

with open(README_PATH, "r") as f:
    content = f.read()

new_section = f"{START_MARKER}\n{post_md}\n{END_MARKER}"
updated = re.sub(
    rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
    new_section,
    content,
    flags=re.DOTALL
)

with open(README_PATH, "w") as f:
    f.write(updated)

print(f"Updated with: {latest.title}")
