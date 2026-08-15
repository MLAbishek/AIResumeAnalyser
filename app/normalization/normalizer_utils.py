import re
import unicodedata


def normalize_text(value: str) -> str:
    """
    Normalize text for deterministic matching.

    Steps:
    1. Unicode normalization
    2. Lowercase
    3. Normalize separators
    4. Collapse whitespace
    5. Strip surrounding whitespace
    """

    if not isinstance(value, str):
        raise TypeError("value must be a string")

    value = unicodedata.normalize("NFKC", value)

    value = value.lower().strip()

    value = re.sub(r"[\u2010-\u2015]", "-", value)

    value = re.sub(r"\s+", " ", value)

    return value