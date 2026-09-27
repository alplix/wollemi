"""Build translated copies of site/index.html using the Tilvar translation API (https://tilvar.athena.org.tr),
with hreflang links and a language switcher wired between all versions.

Usage:
  TILVAR_API_KEY=... python site/translate_site.py

Writes site/index.<lang>.html for each target language plus updates site/index.html itself with hreflang tags,
a language switcher and (once, via --seo) the SEO meta block. Caches translations in site/.translate_cache.json
so re-running after a content change only translates what's new.

Known Tilvar bug worked around here (see chat -- flag for a real fix): the domain-glossary hint the server
injects into its own prompt sometimes leaks into the model's output as a leading line containing "=" pairs
(translated into the target language, so it can't be matched by an English string); `clean()` below strips
any leading lines that look like that before using the result.
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from bs4 import CData, Comment, Doctype, ProcessingInstruction

for _stream in (sys.stdout, sys.stderr):
    # Windows console codepages (e.g. cp1254 on a Turkish locale) can't encode the non-Latin script
    # language labels (Русский, 中文) printed as progress headers below.
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "index.html")
CACHE_PATH = os.path.join(HERE, ".translate_cache.json")
API = "https://tilvar.athena.org.tr/api/translate"
API_KEY = os.environ.get("TILVAR_API_KEY", "")

LANGS = [
    ("tur", "tr", "Türkçe"),
    ("deu", "de", "Deutsch"),
    ("fra", "fr", "Français"),
    ("spa", "es", "Español"),
    ("rus", "ru", "Русский"),
    ("zho", "zh", "中文"),
    ("jpn", "ja", "日本語"),
    ("kor", "ko", "한국어"),
]
EN_LABEL = "English"

SKIP_EXACT = {"WOLLEMI"}  # wordmark: never translated


def clean(s):
    """Strip a leaked glossary-hint preamble line (see module docstring): such a line always contains at
    least one '=' pair and is followed by the real translation on its own line(s)."""
    lines = s.split("\n")
    while len(lines) > 1 and "=" in lines[0]:
        lines = lines[1:]
    return "\n".join(lines).strip()


def load_cache():
    if os.path.exists(CACHE_PATH):
        return json.load(open(CACHE_PATH, encoding="utf-8"))
    return {}


def save_cache(cache):
    json.dump(cache, open(CACHE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def translate(text, tgt, cache):
    key = f"{tgt}:{text}"
    if key in cache:
        return cache[key]
    body = json.dumps({"text": text, "tgt": tgt, "src": "eng"}).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json",
        # Cloudflare's bot check (error 1010) blocks urllib's default "Python-urllib/x.y" User-Agent outright.
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                out = json.loads(r.read().decode("utf-8"))
            t = clean(out.get("translation", text))
            cache[key] = t
            return t
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("Retry-After", "5"))
                print(f"  [429] waiting {wait}s...", file=sys.stderr, flush=True)
                time.sleep(wait + 1)
                continue
            body_txt = e.read().decode("utf-8", errors="replace")
            print(f"  [{e.code}] {body_txt[:200]}", file=sys.stderr, flush=True)
            time.sleep(3)
        except Exception as e:
            print(f"  [error] {e}", file=sys.stderr, flush=True)
            time.sleep(3)
    print(f"  [giving up after 6 attempts, keeping English] {text[:60]!r}", file=sys.stderr, flush=True)
    return text  # give up gracefully: keep the English source rather than crash the build


def should_translate(node):
    if isinstance(node, (Doctype, Comment, CData, ProcessingInstruction)):
        return False  # these are NavigableString subclasses too; find_all(string=True) matches them,
        # and rewriting the Doctype node's text (e.g. "html") turns it into a stray visible text node.
    if node.parent is None or node.parent.name in ("script", "style"):
        return False
    for anc in node.parents:
        if anc.name is None:
            continue
        classes = anc.get("class") or []
        if "code" in classes:
            return False
    return True


def collect_strings(soup):
    """Returns an ordered list of unique strings to translate: text nodes + alt/content attributes."""
    seen = []
    seen_set = set()

    def add(s):
        s = s.strip()
        if s and s not in SKIP_EXACT and s not in seen_set:
            seen_set.add(s)
            seen.append(s)

    for node in soup.find_all(string=True):
        if should_translate(node):
            add(str(node))
    for img in soup.find_all("img"):
        if img.get("alt"):
            add(img["alt"])
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        add(meta_desc["content"])
    return seen


def apply_translations(soup, table):
    for node in soup.find_all(string=True):
        if should_translate(node):
            s = str(node).strip()
            if s in table:
                new_full = str(node).replace(s, table[s])
                node.replace_with(new_full)
    for img in soup.find_all("img"):
        if img.get("alt") and img["alt"].strip() in table:
            img["alt"] = table[img["alt"].strip()]
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content") and meta_desc["content"].strip() in table:
        meta_desc["content"] = table[meta_desc["content"].strip()]


def build_switcher_html(current_code):
    items = [f'<a href="index.html"{" class=\"cur\"" if current_code == "en" else ""}>EN</a>']
    for iso3, code, label in LANGS:
        fname = f"index.{code}.html"
        cur = ' class="cur"' if current_code == code else ""
        items.append(f'<a href="{fname}"{cur}>{code.upper()}</a>')
    return '<div class="langsw">' + " ".join(items) + "</div>"


def inject_hreflang_and_switcher(soup, current_code):
    head = soup.find("head")
    for link in head.find_all("link", rel="alternate"):
        link.decompose()
    base_entries = [("en", "index.html")] + [(code, f"index.{code}.html") for _, code, _ in LANGS]
    for code, fname in base_entries:
        tag = soup.new_tag("link", rel="alternate", hreflang=code, href=fname)
        head.append(tag)
    tag = soup.new_tag("link", rel="alternate", hreflang="x-default", href="index.html")
    head.append(tag)

    nav = soup.find("nav", class_="links")
    if nav:
        old = soup.find("div", class_="langsw")
        if old:
            old.decompose()
        from bs4 import BeautifulSoup as BS
        switcher = BS(build_switcher_html(current_code), "html.parser")
        nav.insert_after(switcher)


def main():
    if not API_KEY:
        print("Set TILVAR_API_KEY first.", file=sys.stderr)
        return 1
    from bs4 import BeautifulSoup

    en_soup = BeautifulSoup(open(SRC, encoding="utf-8").read(), "html.parser")
    inject_hreflang_and_switcher(en_soup, "en")
    open(SRC, "w", encoding="utf-8").write(str(en_soup))

    en_soup = BeautifulSoup(open(SRC, encoding="utf-8").read(), "html.parser")
    strings = collect_strings(en_soup)
    print(f"{len(strings)} unique translatable strings", flush=True)

    cache = load_cache()
    for iso3, code, label in LANGS:
        print(f"\n== {label} ({code}) ==", flush=True)
        table = {}
        for i, s in enumerate(strings):
            table[s] = translate(s, iso3, cache)
            if (i + 1) % 10 == 0:
                save_cache(cache)
                print(f"  {i + 1}/{len(strings)}", flush=True)
            time.sleep(0.15)
        save_cache(cache)

        soup = BeautifulSoup(open(SRC, encoding="utf-8").read(), "html.parser")
        apply_translations(soup, table)
        soup.html["lang"] = code
        title = soup.find("title")
        if title and title.string:
            pass  # already translated as a text node above
        inject_hreflang_and_switcher(soup, code)
        out_path = os.path.join(HERE, f"index.{code}.html")
        open(out_path, "w", encoding="utf-8").write(str(soup))
        print(f"  wrote {out_path}")

    save_cache(cache)
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
