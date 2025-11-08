# backend/recommender.py
# TF-IDF + cosine similarity recommender for NGOs based on summary + details
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import numpy as np

class TFIDFRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        self.tfidf_matrix = None
        self.ngo_ids = []

    def fit(self, ngos):
        # ngos: list of dicts with 'id' and 'text'
        self.ngo_ids = [g['id'] for g in ngos]
        corpus = [g['text'] for g in ngos]
        if len(corpus) == 0:
            self.tfidf_matrix = None
            return
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def recommend(self, ngo_id=None, top_k=5, prefer_verified_ids=None):
        # if ngo_id provided, recommend similar NGOs
        if self.tfidf_matrix is None:
            return []
        if ngo_id and ngo_id in self.ngo_ids:
            idx = self.ngo_ids.index(ngo_id)
            cosine_similarities = linear_kernel(self.tfidf_matrix[idx:idx+1], self.tfidf_matrix).flatten()
            # remove self
            cosine_similarities[idx] = -1
            top_indices = cosine_similarities.argsort()[::-1][:top_k]
            rec_ids = [self.ngo_ids[i] for i in top_indices]
        else:
            # generic recommendation: highest average TF-IDF score -> fallback
            sums = self.tfidf_matrix.sum(axis=1).A1
            top_indices = np.argsort(sums)[::-1][:top_k]
            rec_ids = [self.ngo_ids[i] for i in top_indices]
        # optionally boost verified
        if prefer_verified_ids:
            # place verified ones first preserving order
            verified = [rid for rid in rec_ids if rid in prefer_verified_ids]
            others = [rid for rid in rec_ids if rid not in prefer_verified_ids]
            rec_ids = verified + others
        return rec_ids
