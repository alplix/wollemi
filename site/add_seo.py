"""Add SEO tags (canonical, Open Graph, Twitter Card, JSON-LD, favicon links, robots) to every language version
of the site, using each file's own already-translated <title>/description -- run AFTER site/translate_site.py.

Usage: python site/add_seo.py

BASE_URL points at the real deployment: wollemi.athena.org.tr.
"""
import os
import re

from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://wollemi.athena.org.tr"

FILES = [
    ("index.html", "en", "en_US"),
    ("index.tr.html", "tr", "tr_TR"),
    ("index.de.html", "de", "de_DE"),
    ("index.fr.html", "fr", "fr_FR"),
    ("index.es.html", "es", "es_ES"),
    ("index.ru.html", "ru", "ru_RU"),
    ("index.zh.html", "zh", "zh_CN"),
]


def process(fname, lang, og_locale):
    path = os.path.join(HERE, fname)
    if not os.path.exists(path):
        print("skip (missing):", fname)
        return
    soup = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")
    head = soup.find("head")
    title_tag = soup.find("title")
    title = title_tag.get_text().strip() if title_tag else "Wollemi"
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
    url = f"{BASE_URL}/{fname}" if fname != "index.html" else f"{BASE_URL}/"
    image = f"{BASE_URL}/assets/img/blender_deployed.jpg"

    for tag in head.find_all(["link", "meta", "script"]):
        if tag.name == "link" and tag.get("rel") in ("canonical", "icon", "apple-touch-icon"):
            tag.decompose()
        elif tag.name == "meta" and (tag.get("property", "").startswith(("og:", "twitter:")) or tag.get("name") == "twitter:card" or tag.get("name") == "robots"):
            tag.decompose()
        elif tag.name == "script" and tag.get("type") == "application/ld+json":
            tag.decompose()

    def add_meta(**attrs):
        t = soup.new_tag("meta", attrs=attrs)
        head.append(t)

    def add_link(**attrs):
        t = soup.new_tag("link", attrs=attrs)
        head.append(t)

    add_meta(name="robots", content="index, follow")
    add_link(rel="canonical", href=url)
    add_link(rel="icon", type="image/png", sizes="32x32", href="assets/favicon-32.png")
    add_link(rel="icon", type="image/png", sizes="192x192", href="assets/favicon-192.png")
    add_link(rel="apple-touch-icon", sizes="180x180", href="assets/favicon-180.png")

    add_meta(property="og:type", content="website")
    add_meta(property="og:title", content=title)
    add_meta(property="og:description", content=desc)
    add_meta(property="og:url", content=url)
    add_meta(property="og:image", content=image)
    add_meta(property="og:locale", content=og_locale)
    for fname2, lang2, og2 in FILES:
        if lang2 != lang:
            add_meta(property="og:locale:alternate", content=og2)

    add_meta(name="twitter:card", content="summary_large_image")
    add_meta(name="twitter:title", content=title)
    add_meta(name="twitter:description", content=desc)
    add_meta(name="twitter:image", content=image)

    ld = {
        "@context": "https://schema.org",
        "@type": "ResearchProject",
        "name": "Wollemi",
        "url": url,
        "description": desc,
        "image": image,
        "inLanguage": lang,
    }
    import json
    script = soup.new_tag("script", type="application/ld+json")
    script.string = json.dumps(ld, ensure_ascii=False, indent=2)
    head.append(script)

    open(path, "w", encoding="utf-8").write(str(soup))
    print("updated", fname)


def main():
    for fname, lang, og_locale in FILES:
        process(fname, lang, og_locale)


if __name__ == "__main__":
    main()
