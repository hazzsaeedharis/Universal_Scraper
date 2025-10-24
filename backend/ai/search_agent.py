"""
AI agent for generating search strategies and analyzing results.
"""
import json
from typing import List, Dict
from .groq_client import GroqClient
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SearchAgent:
    """AI agent for intelligent search."""
    
    def __init__(self):
        """Initialize the search agent."""
        self.client = GroqClient()
    
    def generate_search_queries(self, user_query: str, num_queries: int = 3) -> List[str]:
        """
        Generate search queries from a user's natural language query.
        
        Args:
            user_query: User's query (e.g., "beach opening hours in Germany")
            num_queries: Number of search queries to generate
            
        Returns:
            List of search query strings
        """
        system_prompt = """You are a search query optimization expert. 
Generate effective search engine queries that will find the most relevant information.
Return ONLY a JSON array of search query strings, nothing else."""
        
        prompt = f"""Generate {num_queries} different search queries to find information about: "{user_query}"

Make the queries:
1. Specific and focused
2. Likely to return authoritative sources
3. Varied in approach (different angles)

Return format: ["query1", "query2", "query3"]"""
        
        try:
            response = self.client.generate_json(prompt, system_prompt)
            
            # Parse JSON response
            queries = json.loads(response)
            
            if isinstance(queries, list):
                logger.info(f"Generated {len(queries)} search queries for: {user_query}")
                return queries[:num_queries]
            else:
                logger.warning("Unexpected response format, using original query")
                return [user_query]
        
        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            return [user_query]
    
    def analyze_search_results(
        self,
        query: str,
        results: List[Dict]
    ) -> Dict:
        """
        Analyze search results to identify most relevant ones.
        
        Args:
            query: Original user query
            results: List of search results with title, url, snippet
            
        Returns:
            Analysis with relevance scores and recommendations
        """
        # Format results for the prompt
        results_text = ""
        for i, result in enumerate(results[:10]):  # Limit to top 10
            title = result.get('title', 'No title')
            url = result.get('url', '')
            snippet = result.get('snippet', '')
            results_text += f"\n{i+1}. Title: {title}\n   URL: {url}\n   Snippet: {snippet}\n"
        
        system_prompt = """You are an expert at evaluating web search results for relevance and quality.
Analyze the results and return a JSON object with relevance scores."""
        
        prompt = f"""Analyze these search results for the query: "{query}"

{results_text}

For each result, assess:
1. Relevance to the query (0-10)
2. Likely authority/trustworthiness (0-10)
3. Whether it should be scraped

Return JSON format:
{{
  "rankings": [
    {{"index": 1, "relevance": 9, "authority": 8, "should_scrape": true, "reason": "..."}}
  ],
  "top_3_urls": ["url1", "url2", "url3"],
  "summary": "Brief analysis of the results"
}}"""
        
        try:
            response = self.client.generate_json(prompt, system_prompt)
            analysis = json.loads(response)
            logger.info(f"Analyzed {len(results)} search results")
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing search results: {e}")
            # Fallback: return top 3 URLs
            return {
                "rankings": [],
                "top_3_urls": [r.get('url') for r in results[:3]],
                "summary": "Error during analysis, using top results"
            }
    
    def extract_key_information(
        self,
        query: str,
        content: str,
        max_length: int = 500
    ) -> Dict:
        """
        Extract key information from scraped content.
        
        Args:
            query: Original user query
            content: Scraped text content
            max_length: Maximum content length to analyze
            
        Returns:
            Extracted information
        """
        # Truncate content if too long
        if len(content) > max_length * 10:
            content = content[:max_length * 10]
        
        system_prompt = """You are an information extraction expert.
Extract and summarize the most relevant information from the content."""
        
        prompt = f"""From the following content, extract information relevant to: "{query}"

Content:
{content}

Return JSON format:
{{
  "key_facts": ["fact1", "fact2", ...],
  "summary": "Brief summary of relevant information",
  "confidence": 0-10 score for how well this answers the query
}}"""
        
        try:
            response = self.client.generate_json(prompt, system_prompt)
            info = json.loads(response)
            return info
        
        except Exception as e:
            logger.error(f"Error extracting information: {e}")
            return {
                "key_facts": [],
                "summary": "Error extracting information",
                "confidence": 0
            }

