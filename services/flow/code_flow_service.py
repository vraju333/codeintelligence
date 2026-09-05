import re
from pathlib import Path

from config import settings


class CodeFlowService:

    def __init__(self):
        self.project_path = settings.JAVA_PROJECT_PATH

        if not self.project_path:
            raise RuntimeError(
                "JAVA_PROJECT_PATH is not configured"
            )

        self.root = Path(self.project_path)

        self.class_files: dict[str, Path] = {}
        self.class_contents: dict[str, str] = {}
        self.class_fields: dict[str, dict[str, str]] = {}
        self.repository_classes: set[str] = set()

        self._load_project()

    def _load_project(self):

        java_files = list(
            self.root.rglob("*.java")
        )

        for java_file in java_files:

            content = java_file.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            class_name = self._extract_class_name(
                content
            )

            if not class_name:
                continue

            self.class_files[class_name] = java_file
            self.class_contents[class_name] = content

            self.class_fields[class_name] = (
                self._extract_fields(content)
            )

            if self._is_repository(content):
                self.repository_classes.add(
                    class_name
                )

    def analyze(
        self,
        class_name: str,
        method_name: str
    ) -> dict:

        if class_name not in self.class_contents:
            raise RuntimeError(
                f"Class not found: {class_name}"
            )

        visited = set()

        flow = self._trace_method(
            class_name=class_name,
            method_name=method_name,
            visited=visited,
            depth=0
        )

        simplified_flow = (
            self._build_simplified_flow(flow)
        )

        return {
            "start_class": class_name,
            "start_method": method_name,
            "flow": flow,
            "simplified_flow": simplified_flow
        }

    def _trace_method(
        self,
        class_name: str,
        method_name: str,
        visited: set,
        depth: int
    ) -> dict:

        key = f"{class_name}.{method_name}"

        if key in visited:
            return {
                "class_name": class_name,
                "method_name": method_name,
                "recursive": True,
                "calls": []
            }

        if depth > 10:
            return {
                "class_name": class_name,
                "method_name": method_name,
                "max_depth_reached": True,
                "calls": []
            }

        if (
            class_name in self.repository_classes
            and self._is_repository_operation(
                method_name
            )
        ):
            return {
                "class_name": class_name,
                "method_name": method_name,
                "found": True,
                "type": "REPOSITORY",
                "framework": "SPRING_DATA_JPA",
                "operation": self._repository_operation_type(
                    method_name
                ),
                "calls": []
            }

        visited.add(key)

        content = self.class_contents.get(
            class_name
        )

        if not content:
            return {
                "class_name": class_name,
                "method_name": method_name,
                "found": False,
                "calls": []
            }

        method_body = self._extract_method_body(
            content,
            method_name
        )

        if not method_body:
            return {
                "class_name": class_name,
                "method_name": method_name,
                "found": False,
                "calls": []
            }

        detected_calls = self._extract_calls(
            class_name,
            method_body
        )

        child_calls = []

        for target_class, target_method in detected_calls:

            if (
                target_class in self.repository_classes
                and self._is_repository_operation(
                    target_method
                )
            ):
                child_calls.append(
                    {
                        "class_name": target_class,
                        "method_name": target_method,
                        "found": True,
                        "type": "REPOSITORY",
                        "framework": "SPRING_DATA_JPA",
                        "operation": (
                            self._repository_operation_type(
                                target_method
                            )
                        ),
                        "calls": []
                    }
                )

                continue

            if target_class not in self.class_contents:
                child_calls.append(
                    {
                        "class_name": target_class,
                        "method_name": target_method,
                        "external": True,
                        "calls": []
                    }
                )

                continue

            child = self._trace_method(
                class_name=target_class,
                method_name=target_method,
                visited=visited,
                depth=depth + 1
            )

            child_calls.append(child)

        return {
            "class_name": class_name,
            "method_name": method_name,
            "found": True,
            "calls": child_calls
        }

    def _extract_class_name(
        self,
        content: str
    ) -> str | None:

        match = re.search(
            r"\b(class|interface|enum|record)\s+(\w+)",
            content
        )

        if match:
            return match.group(2)

        return None

    def _extract_fields(
        self,
        content: str
    ) -> dict[str, str]:

        fields = {}

        pattern = re.compile(
            r"""
            private
            \s+
            (?:final\s+)?
            (?P<type>[\w<>?,\s]+)
            \s+
            (?P<name>\w+)
            \s*;
            """,
            re.VERBOSE
        )

        for match in pattern.finditer(content):

            field_type = match.group(
                "type"
            ).strip()

            field_name = match.group(
                "name"
            ).strip()

            fields[field_name] = field_type

        return fields

    def _extract_method_body(
        self,
        content: str,
        method_name: str
    ) -> str | None:

        pattern = re.compile(
            rf"""
            (?:
                public|
                protected|
                private
            )
            \s+
            (?:static\s+)?
            (?:final\s+)?
            (?:synchronized\s+)?
            (?:<[^>]+>\s+)?
            [\w<>\[\],.?]+\s+
            {re.escape(method_name)}
            \s*
            \(
                [^)]*
            \)
            \s*
            (?:throws\s+[^{{]+)?
            \{{
            """,
            re.VERBOSE | re.MULTILINE
        )

        match = pattern.search(content)

        if not match:
            return None

        opening_brace = content.find(
            "{",
            match.start()
        )

        closing_brace = (
            self._find_matching_brace(
                content,
                opening_brace
            )
        )

        if closing_brace == -1:
            return None

        return content[
            opening_brace + 1:closing_brace
        ]

    def _extract_calls(
            self,
            current_class: str,
            method_body: str
    ) -> list[tuple[str, str]]:

        fields = self.class_fields.get(
            current_class,
            {}
        )

        cleaned_body = (
            self._remove_constructor_expressions(
                method_body
            )
        )

        candidates = []

        object_call_pattern = re.compile(
            r"""
            (?P<object>\w+)
            \.
            (?P<method>\w+)
            \s*
            \(
            """,
            re.VERBOSE
        )

        for match in object_call_pattern.finditer(
                cleaned_body
        ):

            object_name = match.group(
                "object"
            )

            method_name = match.group(
                "method"
            )

            target_class = None

            if object_name in fields:

                target_class = self._clean_type(
                    fields[object_name]
                )

            elif object_name == "this":

                target_class = current_class

            if not target_class:
                continue

            position = match.start()

            candidates.append(
                {
                    "class_name": target_class,
                    "method_name": method_name,
                    "position": position,
                    "statement_start":
                        self._find_statement_start(
                            cleaned_body,
                            position
                        ),
                    "depth":
                        self._parenthesis_depth(
                            cleaned_body,
                            position
                        )
                }
            )

        direct_pattern = re.compile(
            r"""
            (?<!\.)
            \b
            (?P<method>[a-zA-Z_]\w*)
            \s*
            \(
            """,
            re.VERBOSE
        )

        ignored = {
            "if",
            "for",
            "while",
            "switch",
            "catch",
            "return",
            "throw",
            "new",
            "super",
            "this",
            "synchronized",
            "try",
            "CONSTRUCTOR"
        }

        for match in direct_pattern.finditer(
                cleaned_body
        ):

            method_name = match.group(
                "method"
            )

            if method_name in ignored:
                continue

            if self._looks_like_constructor(
                    method_name
            ):
                continue

            if not self._method_exists(
                    current_class,
                    method_name
            ):
                continue

            position = match.start()

            candidates.append(
                {
                    "class_name": current_class,
                    "method_name": method_name,
                    "position": position,
                    "statement_start":
                        self._find_statement_start(
                            cleaned_body,
                            position
                        ),
                    "depth":
                        self._parenthesis_depth(
                            cleaned_body,
                            position
                        )
                }
            )

        candidates.sort(
            key=lambda item: (
                item["statement_start"],
                -item["depth"],
                item["position"]
            )
        )

        result = []
        seen = set()

        for candidate in candidates:

            call = (
                candidate["class_name"],
                candidate["method_name"]
            )

            if call in seen:
                continue

            seen.add(call)
            result.append(call)

        return result

    def _find_statement_start(
            self,
            content: str,
            position: int
    ) -> int:

        semicolon = content.rfind(
            ";",
            0,
            position
        )

        opening_brace = content.rfind(
            "{",
            0,
            position
        )

        closing_brace = content.rfind(
            "}",
            0,
            position
        )

        return max(
            semicolon,
            opening_brace,
            closing_brace
        )

    def _parenthesis_depth(
            self,
            content: str,
            position: int
    ) -> int:

        depth = 0
        in_string = False
        escape = False

        for character in content[:position]:

            if character == "\\" and not escape:
                escape = True
                continue

            if character == '"' and not escape:
                in_string = not in_string

            escape = False

            if in_string:
                continue

            if character == "(":
                depth += 1

            elif character == ")":
                depth = max(
                    0,
                    depth - 1
                )

        return depth

    def _remove_constructor_expressions(
        self,
        content: str
    ) -> str:

        return re.sub(
            r"\bnew\s+[A-Z]\w*(?:<[^>]+>)?\s*\(",
            "CONSTRUCTOR(",
            content
        )

    def _looks_like_constructor(
        self,
        method_name: str
    ) -> bool:

        if not method_name:
            return False

        return method_name[0].isupper()

    def _is_repository(
        self,
        content: str
    ) -> bool:

        patterns = [
            r"extends\s+JpaRepository",
            r"extends\s+CrudRepository",
            r"extends\s+PagingAndSortingRepository",
            r"@Repository"
        ]

        return any(
            re.search(pattern, content)
            for pattern in patterns
        )

    def _is_repository_operation(
        self,
        method_name: str
    ) -> bool:

        prefixes = (
            "save",
            "find",
            "exists",
            "delete",
            "count",
            "get",
            "read",
            "query"
        )

        return method_name.startswith(
            prefixes
        )

    def _repository_operation_type(
        self,
        method_name: str
    ) -> str:

        if method_name.startswith("save"):
            return "WRITE"

        if method_name.startswith("delete"):
            return "DELETE"

        if method_name.startswith("exists"):
            return "EXISTS"

        if method_name.startswith("count"):
            return "COUNT"

        return "READ"

    def _method_exists(
        self,
        class_name: str,
        method_name: str
    ) -> bool:

        content = self.class_contents.get(
            class_name
        )

        if not content:
            return False

        pattern = re.compile(
            rf"\b{re.escape(method_name)}\s*\("
        )

        return bool(
            pattern.search(content)
        )

    def _clean_type(
        self,
        type_name: str
    ) -> str:

        type_name = type_name.strip()

        if "<" in type_name:
            type_name = type_name.split(
                "<",
                1
            )[0]

        return type_name.strip()

    def _remove_duplicates(
        self,
        calls: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:

        result = []
        seen = set()

        for call in calls:

            if call in seen:
                continue

            seen.add(call)
            result.append(call)

        return result

    def _find_matching_brace(
        self,
        content: str,
        opening_brace: int
    ) -> int:

        depth = 0
        in_string = False
        escape = False

        for index in range(
            opening_brace,
            len(content)
        ):

            character = content[index]

            if character == "\\" and not escape:
                escape = True
                continue

            if character == '"' and not escape:
                in_string = not in_string

            escape = False

            if in_string:
                continue

            if character == "{":
                depth += 1

            elif character == "}":
                depth -= 1

                if depth == 0:
                    return index

        return -1

    def _build_simplified_flow(
        self,
        flow: dict
    ) -> list[str]:

        result = []

        self._collect_simplified_nodes(
            flow,
            result
        )

        return result

    def _collect_simplified_nodes(
        self,
        node: dict,
        result: list[str]
    ):

        class_name = node.get(
            "class_name"
        )

        method_name = node.get(
            "method_name"
        )

        if not class_name or not method_name:
            return

        current = (
            f"{class_name}.{method_name}"
        )

        if current not in result:
            result.append(current)

        calls = node.get(
            "calls",
            []
        )

        for child in calls:

            if self._include_in_simplified_flow(
                child
            ):
                self._collect_simplified_nodes(
                    child,
                    result
                )

    def _include_in_simplified_flow(
        self,
        node: dict
    ) -> bool:

        class_name = node.get(
            "class_name",
            ""
        )

        method_name = node.get(
            "method_name",
            ""
        )

        if node.get("type") == "REPOSITORY":
            return True

        if class_name.endswith(
            "Controller"
        ):
            return True

        if class_name.endswith(
            "Service"
        ):
            return True

        if class_name.endswith(
            "Mapper"
        ):
            if method_name in {
                "toEntity",
                "toResponse"
            }:
                return True

        return False