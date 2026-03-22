"""
Document chunking for RAG
"""
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class Chunk:
    """A chunk of text with metadata"""
    id: str
    content: str
    url: str
    title: str
    site: str
    chunk_index: int
    total_chunks: int


class TextChunker:
    """
    Chunk documents into smaller pieces for RAG.

    Uses semantic boundaries (paragraphs, headers) when possible.
    """

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        content: str,
        url: str,
        title: str,
        site: str,
    ) -> list[Chunk]:
        """
        Chunk a document into smaller pieces.

        Args:
            content: Document text content
            url: Source URL
            title: Document title
            site: Site category

        Returns:
            List of Chunk objects
        """
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(content)

        # Merge or split paragraphs to target chunk size
        chunks = self._create_chunks(paragraphs)

        # Create Chunk objects with metadata
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{url}#chunk-{i}"
            result.append(
                Chunk(
                    id=chunk_id,
                    content=chunk_text,
                    url=url,
                    title=title,
                    site=site,
                    chunk_index=i,
                    total_chunks=len(chunks),
                )
            )

        return result

    def _split_into_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs"""
        # Split on double newlines or common header patterns
        paragraphs = re.split(r'\n\n+|\n(?=[A-Z][^a-z]*:)|(?<=\.)\n(?=[A-Z])', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _create_chunks(self, paragraphs: list[str]) -> list[str]:
        """Create chunks from paragraphs with overlap"""
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # If paragraph itself is too large, split it
                if len(para) > self.chunk_size:
                    para_chunks = self._split_large_paragraph(para)
                    chunks.extend(para_chunks[:-1])
                    current_chunk = para_chunks[-1] if para_chunks else ""
                else:
                    # Start new chunk with overlap from previous
                    overlap = current_chunk[-self.chunk_overlap:] if current_chunk else ""
                    current_chunk = overlap + " " + para if overlap else para
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_paragraph(self, paragraph: str) -> list[str]:
        """Split a large paragraph into smaller chunks"""
        chunks = []
        words = paragraph.split()
        current = ""

        for word in words:
            if len(current) + len(word) + 1 > self.chunk_size:
                chunks.append(current.strip())
                # Add overlap
                overlap_words = current.split()[-20:]  # ~100 chars
                current = " ".join(overlap_words) + " " + word
            else:
                current = current + " " + word if current else word

        if current:
            chunks.append(current.strip())

        return chunks
