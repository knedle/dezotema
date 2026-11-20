import re
import unicodedata

from pymdownx.slugs import slugify as _slugify


def slugify(text: str) -> str:
    """Stejný slug jako MkDocs toc (pymdownx.slugs.slugify, lower)."""
    return _slugify(case="lower")(text, "-")


def ascii_slug(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")
