import unicodedata
from typing import Any

from data_engineering.schemas.source_schema import SourceRecord


class EvidenceProvenanceResolver:
    """
    Locates evidence quotations inside their original source records.

    Supports:
    - PDF page-level provenance.
    - DOCX paragraph and table-row provenance.
    - Full-text fallback.
    - Unicode-aware normalized matching.
    - Original character offset mapping.
    - Document fingerprint references.

    Offsets are zero-based and end-exclusive.
    """

    @staticmethod
    def _normalize_with_offsets(
        text: str,
    ) -> tuple[str, list[int], list[int]]:
        """Normalize text while preserving original character offsets."""
        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        normalized_chars = []
        start_offsets = []
        end_offsets = []

        pending_whitespace_start = None
        pending_whitespace_end = None

        index = 0

        while index < len(text):

            if text[index].isspace():
                if pending_whitespace_start is None:
                    pending_whitespace_start = index

                pending_whitespace_end = index + 1
                index += 1
                continue

            cluster_start = index
            cluster_end = index + 1

            # Handle modern Hangul Jamo composition:
            # Leading consonant + vowel + optional trailing consonant.
            first = ord(text[index])

            if (
                0x1100 <= first <= 0x1112
                and cluster_end < len(text)
                and 0x1161 <= ord(text[cluster_end]) <= 0x1175
            ):
                cluster_end += 1

                if (
                    cluster_end < len(text)
                    and 0x11A8 <= ord(text[cluster_end]) <= 0x11C2
                ):
                    cluster_end += 1

            # Include following Unicode combining marks.
            while (
                cluster_end < len(text)
                and unicodedata.combining(text[cluster_end]) != 0
            ):
                cluster_end += 1

            normalized_cluster = unicodedata.normalize(
                "NFKC",
                text[cluster_start:cluster_end],
            )

            if not normalized_cluster:
                index = cluster_end
                continue

            if (
                pending_whitespace_start is not None
                and normalized_chars
            ):
                normalized_chars.append(" ")
                start_offsets.append(pending_whitespace_start)
                end_offsets.append(pending_whitespace_end)

            pending_whitespace_start = None
            pending_whitespace_end = None

            for character in normalized_cluster:
                normalized_chars.append(character)
                start_offsets.append(cluster_start)
                end_offsets.append(cluster_end)

            index = cluster_end

        return (
            "".join(normalized_chars),
            start_offsets,
            end_offsets,
        )





    @classmethod
    def _find_matches(
        cls,
        content: str,
        quote: str,
    ) -> list[dict[str, int]]:
        """
        Find every occurrence of a quotation in a text segment.

        Returned offsets refer to the original, unnormalized text.
        """
        normalized_content, starts, ends = (
            cls._normalize_with_offsets(content)
        )

        normalized_quote, _, _ = (
            cls._normalize_with_offsets(quote)
        )

        if not normalized_quote:
            return []

        matches = []
        search_position = 0

        while True:

            position = normalized_content.find(
                normalized_quote,
                search_position,
            )

            if position == -1:
                break

            final_position = (
                position + len(normalized_quote) - 1
            )

            matches.append({
                "start_offset": starts[position],
                "end_offset": ends[final_position],
            })

            # Advance by one to detect overlapping matches too.
            search_position = position + 1

        return matches

    @staticmethod
    def _document_fingerprint(
        source: SourceRecord,
    ) -> str | None:
        """Retrieve the original document fingerprint."""
        fingerprint = source.metadata.get("file_sha256")

        return (
            fingerprint
            if isinstance(fingerprint, str)
            else None
        )

    @staticmethod
    def _valid_pages(
        metadata: dict[str, Any],
    ) -> list[dict] | None:
        """
        Return structurally valid PDF page entries.

        Returns None when metadata is malformed so that the resolver
        can fall back to searching the complete source content.
        """
        if "pages" not in metadata:
            return []

        pages = metadata["pages"]

        if not isinstance(pages, list):
            return None

        for page in pages:

            if not isinstance(page, dict):
                return None

            if not isinstance(page.get("content"), str):
                return None

            page_number = page.get("page_number")

            if (
                not isinstance(page_number, int)
                or isinstance(page_number, bool)
            ):
                return None

        return pages

    @staticmethod
    def _valid_sections(
        metadata: dict[str, Any],
    ) -> list[tuple[int, dict]] | None:
        """
        Return structurally valid DOCX sections with original indexes.

        Returns None when any section is malformed.
        """
        if "sections" not in metadata:
            return []

        sections = metadata["sections"]

        if not isinstance(sections, list):
            return None

        validated_sections = []

        for index, section in enumerate(sections):

            if not isinstance(section, dict):
                return None

            section_type = section.get("type")

            if section_type == "paragraph":

                if not isinstance(section.get("content"), str):
                    return None

            elif section_type == "table":

                rows = section.get("rows")

                if not isinstance(rows, list):
                    return None

                for row in rows:

                    if not isinstance(row, list):
                        return None

                    if not all(
                        isinstance(cell, str)
                        for cell in row
                    ):
                        return None

            else:
                return None

            validated_sections.append((index, section))

        return validated_sections

    def resolve(
        self,
        source: SourceRecord,
        quote: str,
    ) -> dict[str, Any]:
        """
        Locate a quotation within a SourceRecord.

        Offset conventions:
        - PDF: relative to the individual page.
        - DOCX paragraph: relative to the paragraph.
        - DOCX table row: relative to the joined row representation.
        - Full text: relative to source.content.

        End offsets are exclusive.
        """

        if not isinstance(source, SourceRecord):
            raise TypeError(
                "source must be a SourceRecord."
            )

        if not isinstance(quote, str) or not quote.strip():
            raise ValueError(
                "quote must be a non-empty string."
            )

        metadata = source.metadata or {}

        matches = []

        pages = self._valid_pages(metadata)
        sections = self._valid_sections(metadata)

        # PDF page-level provenance.
        if pages is not None and pages:

            for page in pages:

                for location in self._find_matches(
                    page["content"],
                    quote,
                ):
                    matches.append({
                        "location_type": "pdf_page",
                        "page_number": page["page_number"],
                        **location,
                    })

        # DOCX paragraph and table-row provenance.
        elif (
            pages is not None
            and sections is not None
            and sections
        ):

            for section_index, section in sections:

                if section["type"] == "paragraph":

                    content = section["content"]

                    for location in self._find_matches(
                        content,
                        quote,
                    ):
                        matches.append({
                            "location_type": "docx_paragraph",
                            "section_index": section_index,
                            **location,
                        })

                elif section["type"] == "table":

                    for row_index, row in enumerate(section["rows"]):

                        content = " | ".join(row)

                        for location in self._find_matches(
                            content,
                            quote,
                        ):
                            matches.append({
                                "location_type": "docx_table_row",
                                "section_index": section_index,
                                "row_index": row_index,
                                **location,
                            })

        # TXT, CSV, legacy records, or malformed structural metadata.
        else:

            for location in self._find_matches(
                source.content,
                quote,
            ):
                matches.append({
                    "location_type": "full_text",
                    **location,
                })

        if not matches:
            status = "not_found"

        elif len(matches) == 1:
            status = "found"

        else:
            status = "ambiguous"

        return {
            "status": status,
            "source_id": source.source_id,
            "source_name": source.source_name,
            "document_hash": self._document_fingerprint(
                source
            ),
            "content_hash": source.content_hash,
            "quote": quote,
            "match_count": len(matches),
            "matches": matches,
        }