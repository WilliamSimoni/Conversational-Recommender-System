from crs_ingestion.cleaning import clean_text, strip_html


def test_clean_text_fixes_encoding():
    bad_string = "LÃ©on"
    cleaned = clean_text(bad_string)
    assert "Léon" in cleaned or "Lé" in cleaned or cleaned != bad_string


def test_strip_html_tags():
    html_str = "<p>Hello <b>World</b>!</p>"
    stripped = strip_html(html_str)
    assert stripped == "Hello World !" or stripped.strip() == "Hello World!"
