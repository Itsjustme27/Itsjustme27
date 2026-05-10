import requests
import re

README_PATH = "README.md"
START_MARKER = "<!-- BLOG-POST-LIST:START -->"
END_MARKER = "<!-- BLOG-POST-LIST:END -->"

query = """
{
  publication(host: "prayush.hashnode.dev") {
    posts(first: 1) {
      edges {
        node {
          title
          url
        }
      }
    }
  }
}
"""

response = requests.post(
    "https://gql.hashnode.com",
    json={"query": query},
    headers={"Content-Type": "application/json"}
)

data = response.json()
post = data["data"]["publication"]["posts"]["edges"][0]["node"]
post_md = f"📝 [{post['title']}]({post['url']})"

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

print(f"Updated with: {post['title']}")