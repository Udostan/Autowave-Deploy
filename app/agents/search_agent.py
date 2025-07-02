from .base_agent import BaseAgent
from app.api.search import do_search

class SearchAgent(BaseAgent):
    """Agent specialized for search functionality.

    This agent handles search queries and returns structured research results.
    """

    def perform_search(self, query):
        """Perform a search using the provided query.

        Args:
            query (str): The search query

        Returns:
            dict: A dictionary containing the search results
        """
        if not query or not isinstance(query, str):
            return {"results": "Invalid search query"}

        # Process the query and get results
        return do_search(query)
