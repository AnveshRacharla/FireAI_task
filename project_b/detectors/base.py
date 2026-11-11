"""
Base detector interface for the NYC 311 Data Quality Engine.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd

from project_b.schemas import DetectionAlert


class BaseDetector(ABC):
    """
    Abstract base class for all data quality detectors.
    Ensures every detector adheres to a standardized invocation signature
    and returns uniform DetectionAlert instances.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def detect(self, df: pd.DataFrame) -> List[DetectionAlert]:
        """
        Scan the input DataFrame and return a list of standardized DetectionAlert objects.

        Args:
            df: pd.DataFrame of NYC 311 records to inspect.

        Returns:
            List[DetectionAlert]: Standardized alerts.
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Return diagnostic or operational statistics for the detector."""
        return {"detector_name": self.name}
