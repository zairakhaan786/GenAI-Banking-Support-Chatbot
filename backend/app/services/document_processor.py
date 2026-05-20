"""
Document Processor
------------------
Handles ingestion of PDF, TXT, and DOCX files.
Returns a list of LangChain Document objects after chunking.
"""

import os
from pathlib import Path
from typing import List, Tuple

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.utils.logger import logger


class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            length_function=len,
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def process_file(self, file_path: str) -> Tuple[List[Document], int]:
        """
        Process a file and return (chunks, raw_char_count).
        Raises ValueError for unsupported types.
        """
        path = Path(file_path)
        ext = path.suffix.lower().lstrip(".")

        logger.info(f"Processing file: {path.name} (type={ext})")

        if ext == "pdf":
            raw_text = self._extract_pdf(file_path)
        elif ext == "txt":
            raw_text = self._extract_txt(file_path)
        elif ext == "docx":
            raw_text = self._extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: .{ext}")

        raw_text = self._clean_text(raw_text)
        chunks = self._chunk_text(raw_text, source=path.name)

        logger.info(f"Produced {len(chunks)} chunks from '{path.name}'")
        return chunks, len(raw_text)

    def process_text_directly(self, text: str, source: str = "inline") -> List[Document]:
        """Chunk a raw string directly (used for the pre-loaded knowledge base)."""
        clean = self._clean_text(text)
        return self._chunk_text(clean, source=source)

    # ── Extraction helpers ─────────────────────────────────────────────────────

    def _extract_pdf(self, path: str) -> str:
        try:
            from pypdf import PdfReader  # pypdf is the maintained fork of PyPDF2
            reader = PdfReader(path)
            pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages.append(f"[Page {i + 1}]\n{page_text}")
            return "\n\n".join(pages)
        except ImportError:
            # Fallback to PyPDF2 if pypdf not installed
            import PyPDF2
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = [
                    page.extract_text() or ""
                    for page in reader.pages
                ]
            return "\n\n".join(pages)
        except Exception as exc:
            logger.error(f"PDF extraction failed for {path}: {exc}")
            raise

    def _extract_txt(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as exc:
            logger.error(f"TXT extraction failed for {path}: {exc}")
            raise

    def _extract_docx(self, path: str) -> str:
        try:
            import docx
            doc = docx.Document(path)
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise ImportError("python-docx is required for DOCX support: pip install python-docx")
        except Exception as exc:
            logger.error(f"DOCX extraction failed for {path}: {exc}")
            raise

    # ── Processing helpers ─────────────────────────────────────────────────────

    def _clean_text(self, text: str) -> str:
        """Basic normalisation: strip excess whitespace and blank lines."""
        import re
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _chunk_text(self, text: str, source: str) -> List[Document]:
        chunks = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[{"source": source}],
        )
        return chunks
