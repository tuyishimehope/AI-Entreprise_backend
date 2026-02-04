import hashlib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class ChunkService:
    @staticmethod
    def generate_file_hash(content: bytes) -> str:
        """Generate a unique hash for the file to prevent re-embedding."""
        return hashlib.md5(content).hexdigest()

    @staticmethod
    def simple_chunker(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        if not text:
            return []
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i: i + chunk_size]
            chunks.append(chunk)
        return chunks

    @staticmethod
    def get_most_relevant_chunks(question_vector, chunk_vectors, chunks, top_k=3):

        if not chunks or not isinstance(chunks, list):
            return []

        if chunk_vectors is None or len(chunk_vectors) == 0:
            # Filter out None/Empty strings
            return [c for c in chunks[:top_k] if c]

        try:
            # Ensure numeric conversion
            q_vector = np.array(
                question_vector, dtype=np.float32).reshape(1, -1)
            c_vectors = np.array(chunk_vectors, dtype=np.float32)

            # Handle 1D vs 2D
            if c_vectors.ndim == 1:
                c_vectors = c_vectors.reshape(1, -1)

            # Calculate similarity
            similarities = cosine_similarity(q_vector, c_vectors)[0]

            # Guard: Ensure we don't try to sort more than we have
            actual_k = min(top_k, len(similarities), len(chunks))

            # Get top indices
            top_indices = np.argsort(similarities)[-actual_k:][::-1]

            # Extract relevant text, ensuring we don't return None or empty strings
            results = []
            for i in top_indices:
                if i < len(chunks) and chunks[i]:
                    results.append(chunks[i])

            return results

        except Exception as e:

            # Final safety fallback: Return first chunks
            return [c for c in chunks[:top_k] if c]
