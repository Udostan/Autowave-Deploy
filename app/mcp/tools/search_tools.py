"""
Web search tools for the MCP server.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SearchTools:
    """
    Tools for web search and information retrieval.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.serper_api_key = os.environ.get("SERPER_API_KEY", "")
        self.google_api_key = os.environ.get("GOOGLE_API_KEY", "")
        self.google_cx = os.environ.get("GOOGLE_CX", "")

        # Check if we have at least one API key
        if not self.serper_api_key and not (self.google_api_key and self.google_cx):
            self.logger.warning("No API keys found for web search. Using fallback methods.")

    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using available APIs, ensuring diverse sources.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of search results from diverse sources
        """
        # Add diversity keywords to the query
        diverse_query = self._enhance_query_for_diversity(query)
        self.logger.info(f"Enhanced query for diversity: {diverse_query}")

        # Try different APIs in order of preference
        results = []
        if self.serper_api_key:
            results = self._search_web_serper(diverse_query, num_results + 5)  # Get extra results for filtering
        elif self.google_api_key and self.google_cx:
            results = self._search_web_google(diverse_query, num_results + 5)  # Get extra results for filtering
        else:
            # Fallback to a basic search method
            results = self._search_web_fallback(diverse_query, num_results + 5)  # Get extra results for filtering

        # Ensure diversity of sources
        return self._ensure_source_diversity(results, num_results)

    def _search_web_serper(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using Serper API.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of search results
        """
        try:
            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": query,
                "num": num_results
            })
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status()

            data = response.json()
            organic = data.get("organic", [])

            results = []
            for item in organic:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "position": item.get("position", 0),
                    "source": "Serper"
                })

            return results
        except Exception as e:
            self.logger.error(f"Error searching web with Serper: {str(e)}")
            return []

    def _search_web_google(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using Google Custom Search API.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of search results
        """
        try:
            url = f"https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_cx,
                "q": query,
                "num": min(num_results, 10)  # Google API max is 10
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            results = []
            for item in items:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Google"
                })

            return results
        except Exception as e:
            self.logger.error(f"Error searching web with Google: {str(e)}")
            return []

    def _search_web_fallback(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fallback method for web search when no API keys are available.
        Uses a basic web scraping approach to get search results.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of search results
        """
        try:
            # Use DuckDuckGo as a fallback search engine
            encoded_query = quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # Extract search results
            for result in soup.select('.result')[:num_results]:
                title_elem = result.select_one('.result__title')
                link_elem = result.select_one('.result__url')
                snippet_elem = result.select_one('.result__snippet')

                title = title_elem.get_text(strip=True) if title_elem else ""
                link = link_elem.get('href') if link_elem else ""
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if title and link:
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                        "source": "DuckDuckGo"
                    })

            # If we couldn't get results from DuckDuckGo, try a different approach
            if not results:
                # Use a basic Google search as a last resort
                url = f"https://www.google.com/search?q={encoded_query}"
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract search results from Google
                for result in soup.select('div.g')[:num_results]:
                    title_elem = result.select_one('h3')
                    link_elem = result.select_one('a')
                    snippet_elem = result.select_one('div.VwiC3b')

                    title = title_elem.get_text(strip=True) if title_elem else ""
                    link = link_elem.get('href') if link_elem else ""
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if title and link and link.startswith('http'):
                        results.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet,
                            "source": "Google"
                        })

            self.logger.info(f"Fallback search found {len(results)} results")
            return results

        except Exception as e:
            self.logger.error(f"Error in fallback search: {str(e)}")
            # Return some hardcoded results as a last resort
            return [{
                "title": "Small Business Administration",
                "link": "https://www.sba.gov/",
                "snippet": "The U.S. Small Business Administration provides resources and guidance for starting and growing a small business.",
                "source": "Fallback"
            }, {
                "title": "SCORE - Free Business Mentoring",
                "link": "https://www.score.org/",
                "snippet": "SCORE offers free business mentoring, workshops, and resources for entrepreneurs and small business owners.",
                "source": "Fallback"
            }, {
                "title": "Business.gov - Official Guide to Government Information and Services",
                "link": "https://www.usa.gov/business",
                "snippet": "Learn about starting and managing a business, taxes, licenses and permits, and more.",
                "source": "Fallback"
            }]

    def _enhance_query_for_diversity(self, query: str) -> str:
        """
        Enhance the query to promote diverse results from different sources.

        Args:
            query: The original search query

        Returns:
            An enhanced query for more diverse results
        """
        # Don't modify queries that are already specific
        if len(query.split()) > 10:
            return query

        # General diversity terms that can be applied to most queries
        general_diversity_terms = [
            'comprehensive guide',
            'multiple perspectives',
            'diverse sources',
            'global perspective',
            'different viewpoints',
            'various approaches',
            'multiple sources',
            'in-depth analysis'
        ]

        # Topic-specific diversity terms
        topic_specific_terms = {}

        # Small business terms
        topic_specific_terms['business'] = [
            'international perspective',
            'global resources',
            'worldwide business',
            'multiple countries',
            'diverse business sources',
            'international examples',
            'global business practices'
        ]

        # Technology terms
        topic_specific_terms['technology'] = [
            'latest developments',
            'multiple platforms',
            'different technologies',
            'tech comparison',
            'various tech solutions',
            'technology alternatives'
        ]

        # Travel terms
        topic_specific_terms['travel'] = [
            'international destinations',
            'global travel',
            'diverse locations',
            'multiple countries',
            'travel alternatives',
            'various travel options'
        ]

        # Health terms
        topic_specific_terms['health'] = [
            'multiple approaches',
            'diverse health perspectives',
            'alternative treatments',
            'global health practices',
            'various health solutions'
        ]

        # Education terms
        topic_specific_terms['education'] = [
            'diverse educational approaches',
            'global education systems',
            'multiple learning methods',
            'educational alternatives',
            'various teaching techniques'
        ]

        # Check if query matches any specific topics
        selected_terms = general_diversity_terms
        for topic, terms in topic_specific_terms.items():
            if topic in query.lower():
                selected_terms = terms
                break

        # Add a random diversity term to the query
        import random
        selected_term = random.choice(selected_terms)
        enhanced_query = f"{query} {selected_term}"

        return enhanced_query

    def _ensure_source_diversity(self, results: List[Dict[str, Any]], num_results: int) -> List[Dict[str, Any]]:
        """
        Filter and reorder search results to ensure diversity of sources.

        Args:
            results: The original search results
            num_results: The number of results to return

        Returns:
            A filtered and reordered list of results with diverse sources
        """
        if not results:
            return []

        # Extract domains from URLs
        for result in results:
            url = result.get('link', '')
            # Extract domain from URL
            import re
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if domain_match:
                result['domain'] = domain_match.group(1)
            else:
                result['domain'] = 'unknown'

        # Group results by domain
        domain_groups = {}
        for result in results:
            domain = result.get('domain', 'unknown')
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(result)

        # Categorize domains by type
        gov_domains = [domain for domain in domain_groups.keys() if '.gov' in domain]
        edu_domains = [domain for domain in domain_groups.keys() if '.edu' in domain]
        org_domains = [domain for domain in domain_groups.keys() if '.org' in domain]
        com_domains = [domain for domain in domain_groups.keys() if '.com' in domain or '.co.' in domain or '.io' in domain]
        other_domains = [domain for domain in domain_groups.keys() if domain not in gov_domains + edu_domains + org_domains + com_domains]

        # Ensure we have a diverse mix of sources
        diverse_results = []

        # Define the order of domain types to prioritize
        # We'll take a balanced approach to ensure diversity
        domain_type_order = [
            com_domains,  # Commercial sites often have the most up-to-date info
            org_domains,  # Non-profit organizations often have good objective info
            edu_domains,  # Educational institutions provide academic perspective
            gov_domains,  # Government sources provide official information
            other_domains # Other domains for additional diversity
        ]

        # First pass: Take one result from each domain type in order
        for domain_type in domain_type_order:
            # Shuffle domains within each type for more randomness
            import random
            random.shuffle(domain_type)

            # Take one result from each domain in this type
            for domain in domain_type:
                if domain_groups[domain] and len(diverse_results) < num_results:
                    diverse_results.append(domain_groups[domain].pop(0))

        # Second pass: Take another result from each domain type
        # This ensures we get more diversity if we need more results
        if len(diverse_results) < num_results:
            for domain_type in domain_type_order:
                for domain in domain_type:
                    if domain_groups[domain] and len(diverse_results) < num_results:
                        diverse_results.append(domain_groups[domain].pop(0))

        # Fill remaining slots with remaining results
        remaining_results = []
        for domain, domain_results in domain_groups.items():
            remaining_results.extend(domain_results)

        # Sort remaining results by position
        remaining_results.sort(key=lambda x: x.get('position', 999))

        # Add remaining results until we reach num_results
        while remaining_results and len(diverse_results) < num_results:
            diverse_results.append(remaining_results.pop(0))

        # Shuffle the results slightly to avoid always having the same order of sources
        # But maintain some order based on relevance
        if diverse_results:
            # Keep the first few results in order (they're likely most relevant)
            top_results = diverse_results[:min(3, len(diverse_results))]
            # Shuffle the rest
            rest_results = diverse_results[min(3, len(diverse_results)):]
            random.shuffle(rest_results)
            diverse_results = top_results + rest_results

        # Return only the requested number of results
        return diverse_results[:num_results]

    def fetch_webpage(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract content from a webpage.

        Args:
            url: The URL of the webpage to fetch

        Returns:
            The extracted content from the webpage
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Get the content type
            content_type = response.headers.get('Content-Type', '')

            # Check if it's HTML
            if 'text/html' in content_type:
                # Simple extraction of text content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()

                # Get text
                text = soup.get_text(separator='\n', strip=True)

                # Get title
                title = soup.title.string if soup.title else ""

                # Get meta description
                meta_desc = ""
                meta_tag = soup.find("meta", attrs={"name": "description"})
                if meta_tag:
                    meta_desc = meta_tag.get("content", "")

                return {
                    "url": url,
                    "title": title,
                    "description": meta_desc,
                    "content": text[:5000],  # Limit content length
                    "content_type": content_type
                }
            else:
                return {
                    "url": url,
                    "error": f"Unsupported content type: {content_type}"
                }
        except Exception as e:
            self.logger.error(f"Error fetching webpage from {url}: {str(e)}")
            return {
                "url": url,
                "error": str(e)
            }
