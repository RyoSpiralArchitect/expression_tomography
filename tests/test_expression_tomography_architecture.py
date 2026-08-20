from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CoreImportBoundaryTests(unittest.TestCase):
    def test_core_modules_do_not_import_task_modules(self) -> None:
        core_dir = ROOT / "expression_tomography/core"
        violations = []
        for path in sorted(core_dir.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if module == "expression_tomography.tasks" or module.startswith(
                        "expression_tomography.tasks."
                    ):
                        violations.append(f"{path.name}:{node.lineno}:{module}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "expression_tomography.tasks" or alias.name.startswith(
                            "expression_tomography.tasks."
                        ):
                            violations.append(f"{path.name}:{node.lineno}:{alias.name}")
        self.assertEqual(violations, [])

    def test_importing_core_providers_does_not_load_tasks(self) -> None:
        script = """
import json
import sys

import expression_tomography.core.providers

loaded = sorted(
    name
    for name in sys.modules
    if name == "expression_tomography.tasks"
    or name.startswith("expression_tomography.tasks.")
)
print(json.dumps(loaded))
"""
        result = subprocess.run(
            [sys.executable, "-S", "-c", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(result.stdout), [])


if __name__ == "__main__":
    unittest.main()
