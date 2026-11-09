from data_engineering.preprocessing.normalizer import TextNormalizer


def test_remove_extra_spaces():

    text = "   Hello     HandoverOS   "

    result = TextNormalizer.normalize_text(text)

    assert result == "Hello HandoverOS"


def test_remove_excessive_blank_lines():

    text = "First line\n\n\n\nSecond line"

    result = TextNormalizer.normalize_text(text)

    assert result == "First line\n\nSecond line"


def test_normalize_line_endings():

    text = "First line\r\nSecond line"

    result = TextNormalizer.normalize_text(text)

    assert result == "First line\nSecond line"


def test_empty_input():

    result = TextNormalizer.normalize_text("")

    assert result == ""


def test_reject_non_string():

    import pytest

    with pytest.raises(TypeError):
        TextNormalizer.normalize_text(123)