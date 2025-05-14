"""
Services package for skillmatch app.
"""
from .ai import parse_cv_file, rank_candidate

__all__ = [
    'parse_cv_file',
    'rank_candidate',
]
