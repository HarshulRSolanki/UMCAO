"""Base abstract class for all language analyzers in UMCAO."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from models.schemas import AnalyzeResponse, UnsupportedLanguageInfo


class BaseAnalyzer(ABC):
    """Abstract Base Class for modular language static analyzers."""

    def __init__(self, language_id: str, display_name: str, is_supported: bool = False):
        self.language_id = language_id.lower()
        self.display_name = display_name
        self.is_supported = is_supported

    @abstractmethod
    def analyze(self, code: str, options: Optional[Dict[str, Any]] = None) -> AnalyzeResponse:
        """Perform static analysis on the provided source code.

        Must NOT execute the code on the web server. Pure static AST/lexical analysis.
        """
        pass

    def get_roadmap_info(self) -> Optional[UnsupportedLanguageInfo]:
        """Return roadmap and architectural info for unsupported/in-development languages."""
        return None
