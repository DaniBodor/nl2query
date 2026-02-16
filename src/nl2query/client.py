import json
from pathlib import Path
import requests


class DelphersClient:
    """HTTP client for querying Delpher API and saving results to JSON."""

    DELPHER_URL = "https://www.delpher.nl/nl/api/results"

    def __init__(self, output_file: str = "delpher_results.json"):
        """Initialize the Delpher client.

        Args:
            output_file: Path to the output JSON file for storing results.
        """
        self.output_file = output_file
        self.results: dict = {}

    def search(self, query: str | list[str]) -> dict:
        """Search for a single query term in Delpher API.

        Args:
            query: The search term to query.

        Returns:
            The API response as a dictionary.
        """
        if isinstance(query, list):
            query = "+".join(query)

        try:
            response = requests.get(self.DELPHER_URL, params={"query": query}, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            msg = f"Error querying '{query}': {e}"
            raise requests.HTTPError(msg) from e

    def save_to_json(self) -> None:
        """Save collected results to a JSON file."""
        with Path(self.output_file).open("w") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {self.output_file}")  # noqa: T201

    def run(self, queries: str | list[str]) -> None:
        """Run searches for all queries and save results to JSON.

        Args:
            queries: List of search terms to query.
        """
        self.results = self.search(queries)
        self.save_to_json()


if __name__ == "__main__":
    # Example usage
    client = DelphersClient(output_file="delpher_results.json")
    search_terms = ["watersnood", "storm"]
    client.run(search_terms)
