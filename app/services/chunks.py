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
        """
        Standard cosine similarity search. 
        Note: If using pgvector in the future, this moves to the SQL layer.
        """
        # Ensure vectors are 2D for sklearn
        q_vector = np.array(question_vector).reshape(1, -1)
        c_vectors = np.array(chunk_vectors)

        similarities = cosine_similarity(q_vector, c_vectors)[0]
        
        # Get indices of the highest scores
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [chunks[i] for i in top_indices]