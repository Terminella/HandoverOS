from abc import ABC, abstractmethod
from typing import Any

from data_engineering.schemas.source_schema import SourceRecord


class BaseConnector(ABC):
    """
    Abstract base class for all HandoverOS data connectors.

    Every connector must implement the load method and
    return structured SourceRecord objects.
    """

    @abstractmethod
    def load(self, source_data: Any) -> list[SourceRecord]:
        """
        Extract and convert source data into SourceRecord objects.

        Args:
            source_data: Raw data from an authorised source.

        Returns:
            A list of structured SourceRecord objects.
        """
        pass