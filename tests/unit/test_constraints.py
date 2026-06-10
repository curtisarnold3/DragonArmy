"""Hard constraint guards (C-1, C-6) - enforce architectural boundaries."""

import ast
from pathlib import Path


def test_pipeline_has_no_llm_imports():
    """C-1: Pipeline must not import any LLM/ML libraries.

    Guards against: anthropic, openai, langchain, transformers, torch, tensorflow
    """
    pipeline_dir = Path(__file__).parent.parent.parent / "pipeline"
    forbidden = ["anthropic", "openai", "langchain", "transformers", "torch", "tensorflow"]

    for py_file in pipeline_dir.rglob("*.py"):
        with open(py_file, "r") as f:
            content = f.read()

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name.split('.')[0] not in forbidden, \
                            f"{py_file}: imports forbidden module {alias.name}"
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert node.module.split('.')[0] not in forbidden, \
                            f"{py_file}: imports from forbidden module {node.module}"
        except SyntaxError:
            pass  # Skip files with syntax errors


def test_pipeline_has_no_web_imports():
    """C-6: Pipeline must not import from api/ or web/ packages.

    Pipeline must be testable in isolation without web dependencies.
    """
    pipeline_dir = Path(__file__).parent.parent.parent / "pipeline"
    forbidden_prefixes = ["api", "web"]

    for py_file in pipeline_dir.rglob("*.py"):
        with open(py_file, "r") as f:
            content = f.read()

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split('.')[0]
                        assert module not in forbidden_prefixes, \
                            f"{py_file}: imports forbidden web module {alias.name}"
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module = node.module.split('.')[0]
                        assert module not in forbidden_prefixes, \
                            f"{py_file}: imports from forbidden web module {node.module}"
        except SyntaxError:
            pass  # Skip files with syntax errors
