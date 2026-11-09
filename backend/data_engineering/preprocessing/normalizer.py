import re
import unicodedata


class TextNormalizer:

    @staticmethod
    def normalize_text(text: str) -> str:

        if not isinstance(text, str):
            raise TypeError("Input must be a string")

        # Normalize Unicode characters
        text = unicodedata.normalize("NFKC", text)

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove trailing spaces from each line
        lines = [line.strip() for line in text.split("\n")]

        # Remove excessive blank lines
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove unnecessary spaces
        text = re.sub(r"[ \t]{2,}", " ", text)

        return text.strip()