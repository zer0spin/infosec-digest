class Categorizer:
    """Classifies news items based on keywords."""

    def __init__(self, keywords_map: dict):
        """
        Initializes the categorizer with a map of categories to keywords.
        
        Args:
            keywords_map (dict): A dictionary where keys are category names
                                 and values are lists of keywords.
        """
        if not isinstance(keywords_map, dict):
            raise TypeError("keywords_map must be a dictionary")
        self.keywords_map = {
            category: [kw.lower() for kw in keywords]
            for category, keywords in keywords_map.items()
        }

    def categorize(self, title: str, summary: str) -> str:
        """
        Categorizes an item based on its title and summary.
        
        Args:
            title (str): The title of the news item.
            summary (str): The summary/description of the news item.
            
        Returns:
            str: The determined category name or "General" if no match is found.
        """
        content = f"{title.lower()} {summary.lower()}"
        
        for category, keywords in self.keywords_map.items():
            if any(keyword in content for keyword in keywords):
                return category
        
        return "General"