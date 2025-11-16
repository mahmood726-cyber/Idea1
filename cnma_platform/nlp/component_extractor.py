"""
Automated component extraction from intervention descriptions.

Uses NLP and machine learning techniques to identify intervention components
from free-text descriptions.
"""

from typing import List, Dict, Set, Optional, Tuple
import numpy as np
import pandas as pd
from collections import Counter
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

from cnma_platform.nlp.text_preprocessor import TextPreprocessor


class ComponentExtractor:
    """
    Automated extraction and standardization of intervention components.

    Uses multiple strategies:
    1. Keyword-based extraction using domain knowledge
    2. TF-IDF for identifying important terms
    3. Clustering for grouping similar components
    4. Similarity matching for standardization
    """

    def __init__(
        self,
        domain: str = "general",
        min_component_freq: int = 1,
        similarity_threshold: float = 0.8,
        use_pretrained: bool = False
    ):
        """
        Initialize component extractor.

        Parameters
        ----------
        domain : str
            Domain of interventions: 'general', 'behavioral', 'pharmaceutical', 'surgical'
        min_component_freq : int
            Minimum frequency for a component to be included
        similarity_threshold : float
            Threshold for considering components as similar (0-1)
        use_pretrained : bool
            Use pre-trained language models (requires sentence-transformers)
        """
        self.domain = domain
        self.min_component_freq = min_component_freq
        self.similarity_threshold = similarity_threshold
        self.use_pretrained = use_pretrained

        self.preprocessor = TextPreprocessor(lowercase=True)

        # Domain-specific component libraries
        self.component_libraries = self._load_component_libraries()

        # Fitted components
        self.components: List[str] = []
        self.component_vectors: Optional[np.ndarray] = None
        self.vectorizer: Optional[TfidfVectorizer] = None

    def _load_component_libraries(self) -> Dict[str, Set[str]]:
        """
        Load domain-specific component libraries.

        Returns
        -------
        libraries : dict
            Dictionary of component sets by domain
        """
        libraries = {
            'behavioral': {
                'cognitive behavioral therapy', 'cbt', 'motivational interviewing',
                'counseling', 'counselling', 'psychotherapy', 'psychoeducation',
                'behavioral activation', 'exposure therapy', 'mindfulness',
                'relaxation', 'stress management', 'goal setting', 'self-monitoring',
                'feedback', 'social support', 'group therapy', 'individual therapy',
                'family therapy', 'problem solving', 'skills training',
            },
            'pharmaceutical': {
                'nicotine replacement therapy', 'nrt', 'varenicline', 'bupropion',
                'medication', 'pharmacotherapy', 'drug therapy', 'antidepressant',
                'anxiolytic', 'stimulant', 'placebo', 'dose', 'dosage',
            },
            'lifestyle': {
                'exercise', 'physical activity', 'diet', 'nutrition', 'weight loss',
                'sleep hygiene', 'smoking cessation', 'alcohol reduction',
            },
            'delivery': {
                'face-to-face', 'telephone', 'online', 'web-based', 'mobile app',
                'text message', 'sms', 'email', 'video', 'telehealth',
                'self-help', 'guided', 'unguided', 'peer support',
            },
            'general': set()  # Will be populated from data
        }

        # Combine all for general domain
        for domain_components in libraries.values():
            libraries['general'].update(domain_components)

        return libraries

    def extract_components(
        self,
        descriptions: List[str],
        method: str = "hybrid"
    ) -> Tuple[List[Set[str]], List[str]]:
        """
        Extract components from intervention descriptions.

        Parameters
        ----------
        descriptions : list
            List of intervention descriptions
        method : str
            Extraction method: 'keyword', 'tfidf', 'hybrid'

        Returns
        -------
        intervention_components : list
            List of component sets for each intervention
        all_components : list
            List of all unique components found
        """
        if method == "keyword":
            return self._keyword_extraction(descriptions)
        elif method == "tfidf":
            return self._tfidf_extraction(descriptions)
        elif method == "hybrid":
            return self._hybrid_extraction(descriptions)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _keyword_extraction(
        self,
        descriptions: List[str]
    ) -> Tuple[List[Set[str]], List[str]]:
        """
        Extract components using keyword matching.

        Parameters
        ----------
        descriptions : list
            List of intervention descriptions

        Returns
        -------
        intervention_components : list
            Component sets for each intervention
        all_components : list
            All unique components
        """
        library = self.component_libraries[self.domain]

        intervention_components = []
        all_components_counter = Counter()

        for desc in descriptions:
            desc_clean = self.preprocessor.clean_text(desc)
            components = set()

            # Match against library
            for component in library:
                # Check for exact match or word boundary match
                pattern = r'\b' + re.escape(component) + r'\b'
                if re.search(pattern, desc_clean):
                    normalized = self.preprocessor.normalize_component_name(component)
                    components.add(normalized)
                    all_components_counter[normalized] += 1

            # Also extract common phrases not in library
            phrases = self.preprocessor.extract_phrases(desc, max_words=3)
            for phrase in phrases:
                if len(phrase.split()) >= 2:  # Only multi-word phrases
                    # Check if it's a potential component (heuristic)
                    if any(keyword in phrase for keyword in ['therapy', 'training', 'support', 'intervention', 'counseling']):
                        normalized = self.preprocessor.normalize_component_name(phrase)
                        if normalized and len(normalized) > 3:
                            components.add(normalized)
                            all_components_counter[normalized] += 1

            intervention_components.append(components)

        # Filter by minimum frequency
        all_components = [
            comp for comp, freq in all_components_counter.items()
            if freq >= self.min_component_freq
        ]

        # Re-filter intervention components
        intervention_components = [
            {comp for comp in comps if comp in all_components}
            for comps in intervention_components
        ]

        self.components = sorted(all_components)

        return intervention_components, self.components

    def _tfidf_extraction(
        self,
        descriptions: List[str],
        top_n: int = 5
    ) -> Tuple[List[Set[str]], List[str]]:
        """
        Extract components using TF-IDF.

        Parameters
        ----------
        descriptions : list
            List of intervention descriptions
        top_n : int
            Number of top terms to extract per intervention

        Returns
        -------
        intervention_components : list
            Component sets for each intervention
        all_components : list
            All unique components
        """
        # Clean descriptions
        cleaned = [self.preprocessor.clean_text(desc) for desc in descriptions]

        # TF-IDF vectorization
        self.vectorizer = TfidfVectorizer(
            max_features=200,
            ngram_range=(1, 3),
            min_df=self.min_component_freq,
            max_df=0.8,
            stop_words='english'
        )

        tfidf_matrix = self.vectorizer.fit_transform(cleaned)
        feature_names = self.vectorizer.get_feature_names_out()

        intervention_components = []
        all_components_set = set()

        for i, desc in enumerate(descriptions):
            # Get top terms for this intervention
            scores = tfidf_matrix[i].toarray().flatten()
            top_indices = scores.argsort()[-top_n:][::-1]
            top_indices = [idx for idx in top_indices if scores[idx] > 0]

            components = {
                self.preprocessor.normalize_component_name(feature_names[idx])
                for idx in top_indices
            }

            # Filter out very short components
            components = {c for c in components if len(c) > 2}

            intervention_components.append(components)
            all_components_set.update(components)

        self.components = sorted(all_components_set)

        return intervention_components, self.components

    def _hybrid_extraction(
        self,
        descriptions: List[str]
    ) -> Tuple[List[Set[str]], List[str]]:
        """
        Hybrid approach combining keyword and TF-IDF extraction.

        Parameters
        ----------
        descriptions : list
            List of intervention descriptions

        Returns
        -------
        intervention_components : list
            Component sets for each intervention
        all_components : list
            All unique components
        """
        # Get components from both methods
        keyword_comps, keyword_all = self._keyword_extraction(descriptions)
        tfidf_comps, tfidf_all = self._tfidf_extraction(descriptions)

        # Combine
        intervention_components = []
        for kw, tf in zip(keyword_comps, tfidf_comps):
            combined = kw.union(tf)
            intervention_components.append(combined)

        all_components = sorted(set(keyword_all).union(set(tfidf_all)))
        self.components = all_components

        # Standardize similar components
        intervention_components, all_components = self._standardize_components(
            intervention_components, all_components
        )

        self.components = all_components

        return intervention_components, all_components

    def _standardize_components(
        self,
        intervention_components: List[Set[str]],
        all_components: List[str]
    ) -> Tuple[List[Set[str]], List[str]]:
        """
        Standardize similar components by merging them.

        Parameters
        ----------
        intervention_components : list
            Component sets for each intervention
        all_components : list
            All unique components

        Returns
        -------
        standardized_components : list
            Standardized component sets
        standardized_all : list
            Standardized unique components
        """
        if len(all_components) == 0:
            return intervention_components, all_components

        # Compute similarity matrix
        if self.use_pretrained:
            similarity_matrix = self._compute_semantic_similarity(all_components)
        else:
            similarity_matrix = self._compute_string_similarity(all_components)

        # Find similar components
        mapping = {}  # Maps component to its standardized form

        for i, comp_i in enumerate(all_components):
            if comp_i in mapping:
                continue

            # Find similar components
            similar = [comp_i]
            for j, comp_j in enumerate(all_components):
                if i != j and similarity_matrix[i, j] > self.similarity_threshold:
                    similar.append(comp_j)

            # Choose representative (shortest or most frequent)
            representative = min(similar, key=len)

            # Map all similar components to representative
            for comp in similar:
                mapping[comp] = representative

        # Apply mapping
        standardized_intervention = []
        for comps in intervention_components:
            standardized = {mapping.get(c, c) for c in comps}
            standardized_intervention.append(standardized)

        standardized_all = sorted(set(mapping.values()))

        return standardized_intervention, standardized_all

    def _compute_string_similarity(self, components: List[str]) -> np.ndarray:
        """
        Compute string similarity using character n-grams.

        Parameters
        ----------
        components : list
            List of component strings

        Returns
        -------
        similarity : np.ndarray
            Similarity matrix
        """
        vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(2, 4),
            lowercase=True
        )

        try:
            vectors = vectorizer.fit_transform(components)
            similarity = cosine_similarity(vectors)
        except:
            # If vectorization fails, return identity matrix
            similarity = np.eye(len(components))

        return similarity

    def _compute_semantic_similarity(self, components: List[str]) -> np.ndarray:
        """
        Compute semantic similarity using pre-trained embeddings.

        Parameters
        ----------
        components : list
            List of component strings

        Returns
        -------
        similarity : np.ndarray
            Similarity matrix
        """
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(components)
            similarity = cosine_similarity(embeddings)
        except ImportError:
            # Fall back to string similarity if sentence-transformers not available
            similarity = self._compute_string_similarity(components)

        return similarity

    def create_component_matrix(
        self,
        intervention_components: List[Set[str]],
        all_components: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Create binary component matrix.

        Parameters
        ----------
        intervention_components : list
            List of component sets for each intervention
        all_components : list, optional
            List of all components (uses self.components if not provided)

        Returns
        -------
        matrix : pd.DataFrame
            Binary matrix indicating component presence
        """
        if all_components is None:
            all_components = self.components

        n_interventions = len(intervention_components)
        n_components = len(all_components)

        matrix = np.zeros((n_interventions, n_components), dtype=int)

        for i, comps in enumerate(intervention_components):
            for j, comp in enumerate(all_components):
                if comp in comps:
                    matrix[i, j] = 1

        df = pd.DataFrame(
            matrix,
            columns=all_components,
            index=[f"intervention_{i+1}" for i in range(n_interventions)]
        )

        return df

    def extract_and_create_matrix(
        self,
        descriptions: List[str],
        method: str = "hybrid"
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Extract components and create matrix in one step.

        Parameters
        ----------
        descriptions : list
            List of intervention descriptions
        method : str
            Extraction method

        Returns
        -------
        matrix : pd.DataFrame
            Binary component matrix
        components : list
            List of all components
        """
        intervention_components, all_components = self.extract_components(
            descriptions, method=method
        )

        matrix = self.create_component_matrix(intervention_components, all_components)

        return matrix, all_components
