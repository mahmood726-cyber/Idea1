"""
Text preprocessing utilities for intervention descriptions.
"""

import re
from typing import List, Dict, Set
import pandas as pd


class TextPreprocessor:
    """
    Preprocessor for intervention text descriptions.

    Handles cleaning, normalization, and standardization of intervention
    descriptions before component extraction.
    """

    def __init__(self, lowercase: bool = True, remove_punctuation: bool = False):
        """
        Initialize text preprocessor.

        Parameters
        ----------
        lowercase : bool
            Convert text to lowercase
        remove_punctuation : bool
            Remove punctuation from text
        """
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation

        # Common intervention-related stopwords to remove
        self.stopwords = {
            'intervention', 'treatment', 'therapy', 'program', 'approach',
            'method', 'technique', 'strategy', 'protocol', 'procedure'
        }

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        Parameters
        ----------
        text : str
            Raw text

        Returns
        -------
        cleaned : str
            Cleaned text
        """
        if pd.isna(text):
            return ""

        # Convert to string
        text = str(text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Lowercase
        if self.lowercase:
            text = text.lower()

        # Remove punctuation if requested
        if self.remove_punctuation:
            text = re.sub(r'[^\w\s]', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

        return text

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.

        Parameters
        ----------
        text : str
            Input text

        Returns
        -------
        tokens : list
            List of tokens
        """
        text = self.clean_text(text)

        # Simple whitespace tokenization
        tokens = text.split()

        # Remove stopwords
        tokens = [t for t in tokens if t not in self.stopwords]

        return tokens

    def extract_phrases(self, text: str, max_words: int = 3) -> List[str]:
        """
        Extract n-gram phrases from text.

        Parameters
        ----------
        text : str
            Input text
        max_words : int
            Maximum phrase length

        Returns
        -------
        phrases : list
            List of extracted phrases
        """
        tokens = self.tokenize(text)
        phrases = []

        for n in range(1, max_words + 1):
            for i in range(len(tokens) - n + 1):
                phrase = ' '.join(tokens[i:i+n])
                phrases.append(phrase)

        return phrases

    def normalize_component_name(self, component: str) -> str:
        """
        Normalize component name for standardization.

        Parameters
        ----------
        component : str
            Component name

        Returns
        -------
        normalized : str
            Normalized component name
        """
        # Clean
        component = self.clean_text(component)

        # Remove common prefixes/suffixes
        component = re.sub(r'^(with|without|plus|minus)\s+', '', component)
        component = re.sub(r'\s+(component|element|part)$', '', component)

        # Standardize common synonyms
        synonyms = {
            'behavioral': 'behavioural',
            'counseling': 'counselling',
            'cbt': 'cognitive behavioral therapy',
            'nrt': 'nicotine replacement therapy',
        }

        for old, new in synonyms.items():
            if old in component:
                component = component.replace(old, new)

        return component.strip()

    def identify_modifiers(self, text: str) -> Dict[str, List[str]]:
        """
        Identify intensity, frequency, and duration modifiers.

        Parameters
        ----------
        text : str
            Intervention description

        Returns
        -------
        modifiers : dict
            Dictionary of modifier types and values
        """
        modifiers = {
            'intensity': [],
            'frequency': [],
            'duration': [],
        }

        text = self.clean_text(text)

        # Intensity patterns
        intensity_patterns = [
            r'(low|medium|high|intensive|intensive)\s+intensity',
            r'(minimal|moderate|vigorous|intensive)',
        ]
        for pattern in intensity_patterns:
            matches = re.findall(pattern, text)
            modifiers['intensity'].extend(matches)

        # Frequency patterns
        frequency_patterns = [
            r'(\d+)\s+(times?|sessions?)\s+(per|a)\s+(day|week|month)',
            r'(daily|weekly|monthly|twice weekly)',
        ]
        for pattern in frequency_patterns:
            matches = re.findall(pattern, text)
            if matches:
                modifiers['frequency'].extend([' '.join(m) if isinstance(m, tuple) else m for m in matches])

        # Duration patterns
        duration_patterns = [
            r'(\d+)\s+(weeks?|months?|days?)',
            r'for\s+(\d+)\s+(weeks?|months?)',
        ]
        for pattern in duration_patterns:
            matches = re.findall(pattern, text)
            if matches:
                modifiers['duration'].extend([' '.join(m) if isinstance(m, tuple) else m for m in matches])

        return modifiers
