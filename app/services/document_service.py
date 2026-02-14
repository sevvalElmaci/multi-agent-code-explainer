from pathlib import Path
from typing import List
import re


class SimpleTextSplitter:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        chunks = []
        start = 0
        text_len = len(text)

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap, chunk_size'dan küçük olmalı")

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            next_start = end - self.chunk_overlap
            if next_start <= start:
                break

            start = next_start

        return chunks


class DocumentService:
    def __init__(self, documents_path="data/documents", chunk_size=500, chunk_overlap=50):
        self.documents_path = Path(documents_path).resolve()
        self.text_splitter = SimpleTextSplitter(chunk_size, chunk_overlap)

    def split_text(self, text: str):
        return self.text_splitter.split_text(text)

    def _clean_markdown(self, text: str) -> str:
        """
        Markdown syntax'ını temizler — RAG'a gürültüsüz metin girer.

        Temizlenenler:
        - FastAPI özel: {!> ... !} include syntax → tamamen sil
        - FastAPI özel: /// tip, /// warning admonition marker'ları → sil
        - FastAPI özel: //// tab | ... tab marker'ları → sil
        - FastAPI özel: hl_lines="..." highlight attribute → sil
        - Fenced code blocks (``` ... ```) → fence marker sil, kodu koru
        - Inline code (`code`) → backtick'leri sil, kodu koru
        - Headers (## Title) → # işaretlerini sil, başlığı koru
        - Bold/italic (**text**, *text*) → işaretleri sil, metni koru
        - Links ([text](url)) → sadece text'i koru, URL'i at
        - Images (![alt](url)) → tamamen sil
        - HTML tags (<tag>) → sil
        - Yatay çizgiler (---) → sil
        - Fazla boş satırlar → tek boş satıra indir
        """
        # --- FastAPI DOCS ÖZEL SYNTAX ---

        # {!> ../path/to/file.py !} — include direktiflerini tamamen sil
        text = re.sub(r"\{!>.*?!\}", "", text, flags=re.DOTALL)

        # ```Python hl_lines="1 2 3" → ```python (hl_lines attribute'unu sil)
        text = re.sub(r"```[Pp]ython\s+hl_lines=[\"'][^\"']*[\"']", "```python", text)

        # //// tab | Python 3.10+ → tamamen sil
        text = re.sub(r"^////.*$", "", text, flags=re.MULTILINE)

        # /// tip, /// note, /// warning, /// → tamamen sil
        text = re.sub(r"^///.*$", "", text, flags=re.MULTILINE)

        # --- STANDART MARKDOWN ---

        # Fenced code blocks — fence marker'ları sil, kodu koru
        text = re.sub(r"```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```", "", text)

        # Inline code — backtick'leri sil
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Images — tamamen sil (önce links'ten işle)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

        # Links — sadece text'i bırak
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Headers — # işaretlerini sil
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # Bold + italic — işaretleri sil (kelime sınırında _ yakala, identifier içinde değil)
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        text = re.sub(r"(?<!\w)_{1,3}([^_]+)_{1,3}(?!\w)", r"\1", text)

        # HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Yatay çizgiler
        text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

        # Fazla boş satırları temizle
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def read_text_file(self, file_path: str) -> str:
        encodings = ["utf-8", "utf-8-sig", "cp1254", "cp1252", "latin-1"]

        last_err = None
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except Exception as e:
                last_err = e

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Dosya okunamadı ({file_path}). Son hata: {last_err} / {e}")

    def read_markdown_file(self, file_path: str) -> str:
        """
        .md dosyasını okur ve Markdown syntax'ını temizleyerek
        RAG için saf metin döndürür.
        """
        raw = self.read_text_file(file_path)
        return self._clean_markdown(raw)

    def read_document(self, file_path) -> str:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".txt":
            return self.read_text_file(str(file_path))

        if suffix == ".md":
            return self.read_markdown_file(str(file_path))

        raise ValueError(f"Desteklenmeyen dosya türü: {suffix} — sadece .txt ve .md destekleniyor.")

    def process_document(self, file_path):
        text = self.read_document(file_path)
        return self.text_splitter.split_text(text)

    def list_documents(self) -> List[str]:
        """
        data/documents/ altındaki .txt ve .md dosyalarını listeler.
        """
        if not self.documents_path.exists():
            return []

        docs = []
        for suffix in ("*.txt", "*.md"):
            docs.extend(str(p) for p in self.documents_path.glob(suffix))

        return sorted(docs)  # tutarlı sıralama için