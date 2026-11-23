import unicodedata


# Retire les accents et espaces extérieurs, puis passe le texte en minuscules.
def normalize_label(text: str) -> str:
    """Normalize string for robust comparison: lowercase, strip, remove accents."""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text.lower().strip())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")
