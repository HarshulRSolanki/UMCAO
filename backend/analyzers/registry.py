"""Registry for modular multi-language analyzers in UMCAO."""

from typing import Dict, List, Optional, Any
from .base import BaseAnalyzer
from .python_analyzer import PythonAnalyzer
from .c_analyzer import CAnalyzer
from .cpp_analyzer import CppAnalyzer
from .java_analyzer import JavaAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer


class AnalyzerRegistry:
    """Registry maintaining active and planned language analyzers."""

    def __init__(self):
        self._analyzers: Dict[str, BaseAnalyzer] = {}
        self._aliases: Dict[str, str] = {
            "py": "python",
            "python": "python",
            "c": "c",
            "cpp": "cpp",
            "c++": "cpp",
            "cplusplus": "cpp",
            "java": "java",
            "js": "javascript",
            "javascript": "javascript",
        }
        self._register_default_analyzers()

    def _register_default_analyzers(self):
        self.register(PythonAnalyzer())
        self.register(CAnalyzer())
        self.register(CppAnalyzer())
        self.register(JavaAnalyzer())
        self.register(JavaScriptAnalyzer())

    def register(self, analyzer: BaseAnalyzer):
        self._analyzers[analyzer.language_id] = analyzer

    def get_analyzer(self, language: str) -> Optional[BaseAnalyzer]:
        norm = language.strip().lower()
        lang_key = self._aliases.get(norm, norm)
        return self._analyzers.get(lang_key)

    def list_languages(self) -> List[Dict[str, Any]]:
        result = []
        for key, analyzer in self._analyzers.items():
            result.append({
                "id": analyzer.language_id,
                "name": analyzer.display_name,
                "supported": analyzer.is_supported,
                "engine": "Python AST" if analyzer.is_supported else (analyzer.get_roadmap_info().planned_engine if analyzer.get_roadmap_info() else "Planned"),
            })
        return result


analyzer_registry = AnalyzerRegistry()
