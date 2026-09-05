import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from config import settings


class RagService:

    def __init__(self):

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.JAVA,
            chunk_size=1200,
            chunk_overlap=150
        )

        self.index_path = "rag_index"

        self.vector_store: FAISS | None = None

        self._load_index_if_exists()

    def index_project(self) -> dict:

        project_path = settings.JAVA_PROJECT_PATH

        if not project_path:
            raise RuntimeError(
                "JAVA_PROJECT_PATH is not configured"
            )

        root = Path(project_path)

        if not root.exists():
            raise RuntimeError(
                f"Project path does not exist: {project_path}"
            )

        documents: list[Document] = []

        java_files = list(root.rglob("*.java"))

        for java_file in java_files:

            content = java_file.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            class_name = self._extract_class_name(content)
            package_name = self._extract_package(content)

            methods = self._extract_methods(content)

            if methods:

                for method_name, method_content in methods:

                    document = Document(
                        page_content=method_content,
                        metadata={
                            "file_name": java_file.name,
                            "file_path": str(java_file),
                            "package_name": package_name,
                            "class_name": class_name,
                            "method_name": method_name,
                            "chunk_type": "method",
                            "language": "java"
                        }
                    )

                    documents.append(document)

            else:

                document = Document(
                    page_content=content,
                    metadata={
                        "file_name": java_file.name,
                        "file_path": str(java_file),
                        "package_name": package_name,
                        "class_name": class_name,
                        "method_name": None,
                        "chunk_type": "class",
                        "language": "java"
                    }
                )

                documents.append(document)

        chunks = self.splitter.split_documents(
            documents
        )

        self.vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings
        )

        self.vector_store.save_local(
            self.index_path
        )

        return {
            "java_files": len(java_files),
            "documents": len(documents),
            "chunks": len(chunks),
            "index_path": self.index_path,
            "status": "indexed"
        }

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> list[dict]:

        if self.vector_store is None:
            raise RuntimeError(
                "RAG index does not exist. Call /api/rag/index first."
            )

        matches = self.vector_store.similarity_search_with_score(
            query=query,
            k=top_k
        )

        results = []

        for document, score in matches:

            results.append(
                {
                    "file_name": document.metadata.get(
                        "file_name"
                    ),
                    "class_name": document.metadata.get(
                        "class_name"
                    ),
                    "method_name": document.metadata.get(
                        "method_name"
                    ),
                    "chunk_type": document.metadata.get(
                        "chunk_type"
                    ),
                    "file_path": document.metadata.get(
                        "file_path"
                    ),
                    "similarity_score": float(score),
                    "content": document.page_content
                }
            )

        return results

    def _load_index_if_exists(self):

        index_folder = Path(
            self.index_path
        )

        if not index_folder.exists():
            return

        self.vector_store = FAISS.load_local(
            self.index_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )

    def _extract_package(
        self,
        content: str
    ) -> str | None:

        match = re.search(
            r"package\s+([\w.]+)\s*;",
            content
        )

        if match:
            return match.group(1)

        return None

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

    def _extract_methods(
        self,
        content: str
    ) -> list[tuple[str, str]]:

        method_pattern = re.compile(
            r"""
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
            (?P<method_name>\w+)
            \s*
            \(
                [^)]*
            \)
            \s*
            (?:throws\s+[^{]+)?
            \{
            """,
            re.VERBOSE | re.MULTILINE
        )

        methods = []

        for match in method_pattern.finditer(content):

            method_name = match.group(
                "method_name"
            )

            opening_brace = content.find(
                "{",
                match.start()
            )

            closing_brace = self._find_matching_brace(
                content,
                opening_brace
            )

            if closing_brace == -1:
                continue

            method_content = content[
                match.start():closing_brace + 1
            ]

            methods.append(
                (
                    method_name,
                    method_content.strip()
                )
            )

        return methods

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