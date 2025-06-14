# backend/__init__.py
"""
DocChat AI Backend Module
Handles documentation scraping and RAG functionality
"""

from .scraper import DocumentationScraper
from .rag import DocumentationRAG

__all__ = ['DocumentationScraper', 'DocumentationRAG']
__version__ = '1.0.0'