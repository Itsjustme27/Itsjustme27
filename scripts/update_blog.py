import requests
import re
import xml.etree.ElementTree as ET

README_PATH = "README.md"
START_MARKER = "<!-- BLOG-POST-LIST:START -->"
END_MARKER = "<!-- BLOG-POST-LIST:END -->"

response = requests.get("https://prayush.hashnode.dev/rss.xml")
response.raise_for_status()

root = ET.fromstring(response.content)
item = root.find("./channel/item")  # first post

title = item.findtext("title")
url = item.findtext("link")

post_md = f"📝 [{title}]({url})"

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

print(f"Updated with: {title}")