"""
Módulo para cálculo de similaridade entre textos.
Usa sentence-transformers para similaridade semântica.
"""
from typing import List, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from utils.logger import log
from utils.helpers import clean_text


class SimilarityAnalyzer:
    """Analisador de similaridade textual e semântica."""

    def __init__(self, model_name: str = "paraphrase-MiniLM-L3-v2"):
        """
        Inicializa o analisador com um modelo sentence-transformers.
        Usa modelo pequeno e rápido para uso gratuito/local.
        """
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Carrega o modelo sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            log.info(f"Carregando modelo de similaridade: {self.model_name}")
            self.model = SentenceTransformer(self_model_name)
            log.info("Modelo de similaridade carregado com sucesso.")
        except Exception as e:
            log.warning(f"Não foi possível carregar modelo sentence-transformers: {e}")
            log.warning("Usando fallback para similaridade por token (Jaccard).")
            self.model = None

    def compute_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """Computa embeddings para uma lista de textos."""
        if self.model is None:
            return None
        try:
            texts_clean = [clean_text(t) for t in texts]
            embeddings = self.model.encode(texts_clean, show_progress_bar=False)
            return embeddings
        except Exception as e:
            log.error(f"Erro ao computar embeddings: {e}")
            return None

    def semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridade semântica entre dois textos usando cosine similarity.
        Retorna valor entre 0 e 1.
        """
        if self.model is None:
            return self._jaccard_similarity(text1, text2)

        try:
            embeddings = self.compute_embeddings([text1, text2])
            if embeddings is None:
                return self._jaccard_similarity(text1, text2)

            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
        except Exception as e:
            log.error(f"Erro na similaridade semântica: {e}")
            return self._jaccard_similarity(text1, text2)

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade Jaccard entre conjuntos de tokens."""
        tokens1 = set(clean_text(text1).lower().split())
        tokens2 = set(clean_text(text2).lower().split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def find_most_similar(
        self, query: str, candidates: List[str], threshold: float = 0.7
    ) -> List[Tuple[str, float]]:
        """
        Encontra os textos mais similares ao query.
        Retorna lista de (texto, score) ordenada por similaridade.
        """
        if not candidates:
            return []

        if self.model is None:
            # Fallback: Jaccard para cada candidato
            scores = [
                (cand, self._jaccard_similarity(query, cand))
                for cand in candidates
            ]
        else:
            try:
                all_texts = [query] + candidates
                embeddings = self.compute_embeddings(all_texts)
                if embeddings is None:
                    return self.find_most_similar(query, candidates, threshold)

                query_emb = embeddings[0:1]
                cand_embs = embeddings[1:]

                similarities = cosine_similarity(query_emb, cand_embs)[0]
                scores = list(zip(candidates, similarities))
            except Exception as e:
                log.error(f"Erro find_most_similar: {e}")
                return []

        # Filtra por threshold e ordena
        filtered = [(t, s) for t, s in scores if s >= threshold]
        filtered.sort(key=lambda x: x[1], reverse=True)

        return filtered


# Instância global
similarity_analyzer = SimilarityAnalyzer()