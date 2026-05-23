import ftfy
from bs4 import BeautifulSoup


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    fixed = ftfy.fix_text(text)
    return fixed


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    cleaned = clean_text(text)
    soup = BeautifulSoup(cleaned, "html.parser")
    stripped = soup.get_text(separator=" ")

    return " ".join(stripped.split())
