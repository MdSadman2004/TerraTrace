import math
from typing import List, Dict, Any

class DeedRetriever:
    """
    Simulates a local vector storage and semantic retriever (e.g. ChromaDB / MiniLM).
    Performs cosine similarity checks against a mock corpus of county deeds.
    """
    def __init__(self):
        # Mock database corpus: (Document text, Mock embedding vector)
        # Embedding dimensions: 3 (representing semantic features: [residential, commercial, utility])
        self.corpus = [
            {
                "id": "ref-001",
                "text": "Deed of Trust 1978: Lot 4, Heights zoning, commercial activities forbidden. Building height capped at 25 feet.",
                "vector": [0.8, -0.9, -0.2]
            },
            {
                "id": "ref-002",
                "text": "Water Works easement grant: Standard underground pipeline corridor, utilities access right-of-way 15 feet width.",
                "vector": [-0.1, 0.2, 0.9]
            },
            {
                "id": "ref-003",
                "text": "Zoning Board variance 1995: Commercial subdivision, retail permitted, height limits waived.",
                "vector": [-0.5, 0.9, 0.1]
            }
        ]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude_1 = math.sqrt(sum(a * a for a in vec1))
        magnitude_2 = math.sqrt(sum(b * b for b in vec2))
        if magnitude_1 == 0 or magnitude_2 == 0:
            return 0.0
        return dot_product / (magnitude_1 * magnitude_2)

    def retrieve_precedents(self, query_text: str, k: int = 1) -> List[Dict[str, Any]]:
        # Map simple queries to mock embedding vectors
        query_text = query_text.lower()
        if "height" in query_text or "restriction" in query_text or "covenant" in query_text:
            query_vector = [0.9, -0.8, -0.1]
        elif "easement" in query_text or "utility" in query_text or "pipe" in query_text:
            query_vector = [0.0, 0.1, 0.9]
        elif "commercial" in query_text or "shop" in query_text:
            query_vector = [-0.6, 0.9, 0.1]
        else:
            query_vector = [0.5, 0.5, 0.5] # Neutral
            
        results = []
        for doc in self.corpus:
            similarity = self._cosine_similarity(query_vector, doc["vector"])
            results.append((doc, similarity))
            
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return [res[0] for res in results[:k]]
