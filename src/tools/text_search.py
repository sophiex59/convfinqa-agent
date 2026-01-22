"""Text search tool for finding facts in document text."""

import re
from typing import Optional


def search_text(
    text: str,
    query: str,
    context_chars: int = 200,
) -> list[str]:
    """
    Search for a query in text and return matching snippets with context.
    
    Args:
        text: Document text to search
        query: Search term or phrase
        context_chars: Characters of context to include around match
        
    Returns:
        List of text snippets containing the query
    """
    if not text or not query:
        return []
    
    snippets = []
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Find all occurrences
    start = 0
    while True:
        pos = text_lower.find(query_lower, start)
        if pos == -1:
            break
        
        # Extract snippet with context
        snippet_start = max(0, pos - context_chars)
        snippet_end = min(len(text), pos + len(query) + context_chars)
        
        snippet = text[snippet_start:snippet_end]
        if snippet_start > 0:
            snippet = "..." + snippet
        if snippet_end < len(text):
            snippet = snippet + "..."
            
        snippets.append(snippet)
        start = pos + 1
    
    return snippets


def extract_numbers(text: str) -> list[tuple[float, str]]:
    """
    Extract all numbers from text with their context.
    
    Args:
        text: Text to extract numbers from
        
    Returns:
        List of (number, context) tuples
    """
    # Pattern for numbers (including currency, percentages, negatives)
    pattern = r'[\$\-]?\d{1,3}(?:,\d{3})*(?:\.\d+)?%?'
    
    results = []
    for match in re.finditer(pattern, text):
        num_str = match.group()
        
        # Parse the number
        clean = num_str.replace('$', '').replace(',', '').replace('%', '')
        try:
            value = float(clean)
            if '%' in num_str:
                value = value / 100  # Convert percentage to decimal
        except ValueError:
            continue
        
        # Get context (20 chars before and after)
        start = max(0, match.start() - 20)
        end = min(len(text), match.end() + 20)
        context = text[start:end].strip()
        
        results.append((value, context))
    
    return results


def find_year_data(
    text: str,
    year: str,
) -> Optional[str]:
    """
    Find text mentioning a specific year.
    
    Args:
        text: Document text
        year: Year to search for (e.g., "2007")
        
    Returns:
        Relevant sentence or None
    """
    # Split into sentences
    sentences = re.split(r'[.!?]', text)
    
    for sentence in sentences:
        if year in sentence:
            return sentence.strip()
    
    return None
