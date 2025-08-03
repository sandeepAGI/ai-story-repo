#!/usr/bin/env python3
"""
Language detection utilities for customer stories.
Detects language from URL patterns and content analysis.
"""

import re
import logging
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Detect language of customer stories from URL and content"""
    
    def __init__(self):
        # URL-based language patterns (most reliable)
        self.url_language_patterns = {
            'Chinese (Simplified)': ['/zh-cn/', '/zh-hans/'],
            'Chinese (Traditional)': ['/zh-tw/', '/zh-hant/'],
            'Japanese': ['/ja-jp/', '/ja/'],
            'Korean': ['/ko-kr/', '/ko/'],
            'German': ['/de-de/', '/de/'],
            'French': ['/fr-fr/', '/fr/'],
            'Spanish': ['/es-es/', '/es/'],
            'Portuguese': ['/pt-br/', '/pt/'],
            'Italian': ['/it-it/', '/it/'],
            'Dutch': ['/nl-nl/', '/nl/'],
            'Russian': ['/ru-ru/', '/ru/'],
            'Arabic': ['/ar-sa/', '/ar/'],
            'Hindi': ['/hi-in/', '/hi/'],
            'Swedish': ['/sv-se/', '/sv/'],
            'Norwegian': ['/no-no/', '/no/'],
            'Danish': ['/da-dk/', '/da/'],
            'Finnish': ['/fi-fi/', '/fi/']
        }
        
        # Character-based detection for content analysis
        self.character_ranges = {
            'Chinese': (0x4E00, 0x9FFF),  # CJK Unified Ideographs
            'Japanese': [(0x3040, 0x309F), (0x30A0, 0x30FF)],  # Hiragana + Katakana
            'Korean': (0xAC00, 0xD7AF),  # Hangul
            'Arabic': (0x0600, 0x06FF),  # Arabic
            'Russian': (0x0400, 0x04FF),  # Cyrillic
            'Hindi': (0x0900, 0x097F),   # Devanagari
        }
    
    def detect_language_from_url(self, url: str) -> Optional[str]:
        """Detect language from URL patterns (most reliable method)"""
        if not url:
            return None
        
        url_lower = url.lower()
        
        for language, patterns in self.url_language_patterns.items():
            if any(pattern in url_lower for pattern in patterns):
                logger.debug(f"Detected {language} from URL pattern: {url}")
                return language
        
        return None
    
    def detect_language_from_content(self, text: str, threshold: int = 10) -> Optional[str]:
        """Detect language from character analysis (fallback method)"""
        if not text or len(text.strip()) < threshold:
            return None
        
        char_counts = {}
        total_chars = 0
        
        for char in text:
            char_code = ord(char)
            total_chars += 1
            
            # Check each language's character ranges
            for lang, ranges in self.character_ranges.items():
                if isinstance(ranges, tuple):
                    ranges = [ranges]
                
                for start, end in ranges:
                    if start <= char_code <= end:
                        char_counts[lang] = char_counts.get(lang, 0) + 1
                        break
        
        if not char_counts or total_chars == 0:
            return None
        
        # Find language with highest character percentage
        max_lang = max(char_counts.items(), key=lambda x: x[1])
        lang_name, count = max_lang
        
        # Require at least 10% of characters to be from the detected language
        percentage = count / total_chars
        if percentage >= 0.1:
            logger.debug(f"Detected {lang_name} from content analysis: {percentage:.2%} match")
            return lang_name
        
        return None
    
    def detect_language(self, url: str, title: str = "", content: str = "") -> Tuple[str, str, float]:
        """
        Comprehensive language detection with confidence scoring
        
        Returns:
            tuple: (language, detection_method, confidence_score)
        """
        
        # Method 1: URL-based detection (highest confidence)
        url_language = self.detect_language_from_url(url)
        if url_language:
            return url_language, "url_pattern", 0.95
        
        # Method 2: Content-based detection (medium confidence)  
        # Check title first (more reliable than full content)
        if title:
            title_language = self.detect_language_from_content(title, threshold=5)
            if title_language:
                return title_language, "title_analysis", 0.80
        
        # Check full content (lower confidence due to mixed content)
        if content:
            content_language = self.detect_language_from_content(content, threshold=50)
            if content_language:
                return content_language, "content_analysis", 0.60
        
        # Default to English (lowest confidence)
        return "English", "default", 0.30
    
    def normalize_language_name(self, language: str) -> str:
        """Normalize language names for consistency"""
        language_mapping = {
            'Chinese (Simplified)': 'Chinese',
            'Chinese (Traditional)': 'Chinese',
            'zh-cn': 'Chinese',
            'zh-tw': 'Chinese',
            'ja-jp': 'Japanese', 
            'ja': 'Japanese',
            'ko-kr': 'Korean',
            'ko': 'Korean',
            'de-de': 'German',
            'de': 'German',
            'fr-fr': 'French', 
            'fr': 'French',
            'es-es': 'Spanish',
            'es': 'Spanish',
            'pt-br': 'Portuguese',
            'pt': 'Portuguese',
            'it-it': 'Italian',
            'it': 'Italian',
            'nl-nl': 'Dutch',
            'nl': 'Dutch'
        }
        
        return language_mapping.get(language, language)

def detect_story_language(url: str, title: str = "", content: str = "") -> Dict[str, any]:
    """
    Convenience function for detecting story language
    
    Returns:
        dict: {
            'language': str,
            'method': str, 
            'confidence': float,
            'normalized': str
        }
    """
    detector = LanguageDetector()
    language, method, confidence = detector.detect_language(url, title, content)
    normalized = detector.normalize_language_name(language)
    
    return {
        'language': language,
        'method': method,
        'confidence': confidence,
        'normalized': normalized
    }