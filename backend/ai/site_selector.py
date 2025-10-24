"""
AI-powered site selector for choosing which websites to scrape.
"""
import json
from typing import List, Dict
from .groq_client import GroqClient
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SiteSelector:
    """AI agent for selecting relevant websites."""
    
    def __init__(self):
        """Initialize the site selector."""
        self.client = GroqClient()
    
    def rank_urls(
        self,
        query: str,
        urls_with_context: List[Dict],
        max_select: int = 5
    ) -> List[str]:
        """
        Rank and select the most relevant URLs to scrape.
        
        Args:
            query: User's information need
            urls_with_context: List of dicts with url, title, snippet
            max_select: Maximum URLs to select
            
        Returns:
            List of selected URLs
        """
        if not urls_with_context:
            return []
        
        # Format URLs for the prompt
        urls_text = ""
        for i, item in enumerate(urls_with_context[:15]):  # Limit to 15
            title = item.get('title', 'No title')
            url = item.get('url', '')
            snippet = item.get('snippet', '')
            urls_text += f"\n{i+1}. {title}\n   URL: {url}\n   Context: {snippet}\n"
        
        system_prompt = """You are an expert at evaluating websites for information quality and relevance.
Your goal is to select the most authoritative and relevant websites to scrape for comprehensive information."""
        
        prompt = f"""Task: Select the top {max_select} websites to scrape for this query: "{query}"

Available websites:
{urls_text}

Criteria:
1. Relevance to the query
2. Authority and trustworthiness (prefer .gov, .edu, official organizations)
3. Likely to contain comprehensive information
4. Avoid duplicates and low-quality sources

Return ONLY a JSON array of the selected URLs in priority order:
["url1", "url2", "url3"]"""
        
        try:
            response = self.client.generate_json(prompt, system_prompt)
            selected_urls = json.loads(response)
            
            if isinstance(selected_urls, list):
                logger.info(f"Selected {len(selected_urls)} URLs to scrape")
                return selected_urls[:max_select]
            else:
                logger.warning("Unexpected response format")
                return [item['url'] for item in urls_with_context[:max_select]]
        
        except Exception as e:
            logger.error(f"Error selecting URLs: {e}")
            # Fallback: return first N URLs
            return [item['url'] for item in urls_with_context[:max_select]]
    
    def should_follow_link(
        self,
        query: str,
        link_text: str,
        link_url: str,
        context: str = ""
    ) -> bool:
        """
        Decide if a link should be followed based on relevance.
        
        Args:
            query: Original query
            link_text: Anchor text of the link
            link_url: URL of the link
            context: Surrounding context
            
        Returns:
            True if link should be followed
        """
        # Simple heuristic - can be enhanced with AI
        # For now, use keyword matching
        query_keywords = set(query.lower().split())
        link_keywords = set((link_text + " " + link_url).lower().split())
        
        # Check for overlap
        overlap = query_keywords.intersection(link_keywords)
        
        return len(overlap) > 0

