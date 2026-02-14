from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import faiss
import numpy as np

from app.config import settings
from app.services.document_service import DocumentService


@dataclass
class ChunkRecord:
    source: str       # filename
    chunk: str        # text chunk


class RAGService:
    """
    Local-docs RAG:
    - data/documents altındaki dokümanları chunk'lar
    - FAISS index oluşturur / yükler
    - search(query) -> en alakalı chunk'ları döndürür
    """
    def __init__(self, embedding_model, top_k: Optional[int] = None):
        self.embedding_model = embedding_model
        self.top_k = top_k or settings.TOP_K_RESULTS

        self.doc_service = DocumentService(
            documents_path=settings.DOCUMENTS_PATH,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

        self.index: Optional[faiss.IndexFlatL2] = None
        self.records: List[ChunkRecord] = []   # index -> chunk mapping

        self.vdb_path = Path(settings.VECTOR_DB_PATH).resolve()
        self.vdb_path.mkdir(parents=True, exist_ok=True)

        self.index_file = self.vdb_path / "faiss.index"
        self.meta_file = self.vdb_path / "chunks.npy"  # basit persist


    def _embed(self, texts: List[str]) -> np.ndarray:
        emb = self.embedding_model.encode(texts, show_progress_bar=False)
        return np.array(emb).astype("float32")


    def ensure_index(self) -> None:
        """Index yoksa yükle; yoksa build et."""
        if self.index is not None and self.records:
            return

        if self.index_file.exists() and self.meta_file.exists():
            self._load()
            return

        self._build_from_documents()
        self._save()


    def _build_from_documents(self) -> None:
        files = self.doc_service.list_documents()
        if not files:
            # boş kalabilir; Agent 2 bunu handle eder
            self.index = None
            self.records = []
            return

        all_chunks: List[str] = []
        all_records: List[ChunkRecord] = []

        for fp in files:
            text = self.doc_service.read_document(fp)
            chunks = self.doc_service.split_text(text)
            filename = Path(fp).name

            for ch in chunks:
                all_chunks.append(ch)
                all_records.append(ChunkRecord(source=filename, chunk=ch))

        if not all_chunks:
            self.index = None
            self.records = []
            return

        embeddings = self._embed(all_chunks)
        dim = embeddings.shape[1]

        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        self.index = index
        self.records = all_records


    def _save(self) -> None:
        if self.index is None:
            return
        faiss.write_index(self.index, str(self.index_file))

        # records'u basitçe (source, chunk) array olarak sakla
        arr = np.array([(r.source, r.chunk) for r in self.records], dtype=object)
        np.save(self.meta_file, arr, allow_pickle=True)


    def _load(self) -> None:
        self.index = faiss.read_index(str(self.index_file))
        arr = np.load(self.meta_file, allow_pickle=True)
        self.records = [ChunkRecord(source=s, chunk=c) for (s, c) in arr.tolist()]


    def search(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        self.ensure_index()

        if self.index is None or not self.records:
            return []

        k = k or self.top_k
        query_emb = self._embed([query])
        distances, indices = self.index.search(query_emb, k)

        out: List[Dict[str, Any]] = []
        for rank, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.records):
                continue
            dist = float(distances[0][rank])
            rec = self.records[idx]
            out.append({
                "file": rec.source,
                "chunk": rec.chunk,
                "distance": dist,
                "relevance": 1.0 / (1.0 + dist),
                "rank": rank + 1,
            })
        return out
