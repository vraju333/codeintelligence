import re
import subprocess
from pathlib import Path

from config import settings


class GitDiffService:

    def __init__(self):

        if not settings.JAVA_PROJECT_PATH:
            raise RuntimeError(
                "JAVA_PROJECT_PATH is not configured"
            )

        self.project_path = Path(
            settings.JAVA_PROJECT_PATH
        )

    def analyse_changes(self):

        self._validate_git_repository()

        changed_files = self._get_changed_java_files()

        results = []

        for relative_path in changed_files:

            file_path = (
                self.project_path /
                relative_path
            )

            changed_lines = (
                self._get_changed_line_numbers(
                    relative_path
                )
            )

            methods = []

            if file_path.exists():

                methods = (
                    self._find_changed_methods(
                        file_path,
                        changed_lines
                    )
                )

            results.append(
                {
                    "file_path": relative_path,
                    "file_name": Path(
                        relative_path
                    ).name,
                    "class_name": Path(
                        relative_path
                    ).stem,
                    "changed_lines": sorted(
                        changed_lines
                    ),
                    "changed_methods": methods
                }
            )

        return {
            "project_path": str(
                self.project_path
            ),
            "total_changed_java_files": len(
                results
            ),
            "changed_files": results
        }

    def _validate_git_repository(self):

        result = subprocess.run(
            [
                "git",
                "rev-parse",
                "--is-inside-work-tree"
            ],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            raise RuntimeError(
                "JAVA_PROJECT_PATH is not a Git repository"
            )

    def _get_changed_java_files(self):

        files = set()

        commands = [
            [
                "git",
                "diff",
                "--name-only"
            ],
            [
                "git",
                "diff",
                "--cached",
                "--name-only"
            ]
        ]

        for command in commands:

            result = subprocess.run(
                command,
                cwd=self.project_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                continue

            for line in result.stdout.splitlines():

                line = line.strip()

                if line.endswith(".java"):
                    files.add(line)

        return sorted(files)

    def _get_changed_line_numbers(
        self,
        relative_path: str
    ):

        changed_lines = set()

        commands = [
            [
                "git",
                "diff",
                "--unified=0",
                "--",
                relative_path
            ],
            [
                "git",
                "diff",
                "--cached",
                "--unified=0",
                "--",
                relative_path
            ]
        ]

        for command in commands:

            result = subprocess.run(
                command,
                cwd=self.project_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                continue

            for line in result.stdout.splitlines():

                if not line.startswith("@@"):
                    continue

                match = re.search(
                    r"\+(\d+)(?:,(\d+))?",
                    line
                )

                if not match:
                    continue

                start = int(
                    match.group(1)
                )

                count = int(
                    match.group(2) or 1
                )

                if count == 0:
                    continue

                for number in range(
                    start,
                    start + count
                ):
                    changed_lines.add(
                        number
                    )

        return changed_lines

    def _find_changed_methods(
        self,
        file_path: Path,
        changed_lines: set[int]
    ):

        content = file_path.read_text(
            encoding="utf-8"
        )

        lines = content.splitlines()

        method_ranges = (
            self._extract_method_ranges(
                lines
            )
        )

        changed_methods = []

        for method in method_ranges:

            start_line = method[
                "start_line"
            ]

            end_line = method[
                "end_line"
            ]

            affected_lines = [
                line
                for line in changed_lines
                if start_line
                <= line
                <= end_line
            ]

            if not affected_lines:
                continue

            changed_methods.append(
                {
                    "method_name": method[
                        "method_name"
                    ],
                    "start_line": start_line,
                    "end_line": end_line,
                    "changed_lines": sorted(
                        affected_lines
                    )
                }
            )

        return changed_methods

    def _extract_method_ranges(
        self,
        lines: list[str]
    ):

        methods = []

        method_pattern = re.compile(
            r"""
            ^\s*
            (?:
                public|
                protected|
                private
            )
            \s+
            (?:
                static\s+
            )?
            (?:
                final\s+
            )?
            (?:
                synchronized\s+
            )?
            [\w<>\[\],.?]+\s+
            (?P<name>[A-Za-z_]\w*)
            \s*
            \(
            """,
            re.VERBOSE
        )

        index = 0

        while index < len(lines):

            line = lines[index]

            match = method_pattern.search(
                line
            )

            if not match:

                index += 1
                continue

            method_name = match.group(
                "name"
            )

            signature_start = index

            brace_index = index
            found_open_brace = False

            while brace_index < len(lines):

                current = lines[
                    brace_index
                ]

                if "{" in current:
                    found_open_brace = True
                    break

                if ";" in current:
                    break

                brace_index += 1

            if not found_open_brace:

                index += 1
                continue

            brace_count = 0
            method_end = brace_index

            started = False

            for method_end in range(
                brace_index,
                len(lines)
            ):

                current = lines[
                    method_end
                ]

                open_count = current.count(
                    "{"
                )

                close_count = current.count(
                    "}"
                )

                if open_count > 0:
                    started = True

                brace_count += open_count
                brace_count -= close_count

                if started and brace_count == 0:
                    break

            methods.append(
                {
                    "method_name": method_name,
                    "start_line": (
                        signature_start + 1
                    ),
                    "end_line": (
                        method_end + 1
                    )
                }
            )

            index = method_end + 1

        return methods