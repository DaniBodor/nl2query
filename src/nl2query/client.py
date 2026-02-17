import argparse
import json
from pathlib import Path
import requests


class DelpherClient:
    """HTTP client for querying Delpher API and saving results to JSON."""

    DELPHER_URL = "https://www.delpher.nl/nl/api/results"

    def __init__(
        self,
        output_file: str = "delpher_results.json",
        output_dir: str | Path | None = None,
    ):
        """Initialize the Delpher client.

        Args:
            output_file: Path to the output JSON file for storing results.
            output_dir: Directory to store output files; defaults to repo outputs/.
        """
        self.output_file = output_file
        self.output_dir = output_dir or Path(__file__).resolve().parents[2] / "outputs"
        self.results: dict = {}

    def search(self, query: str | list[str]) -> dict:
        """Search Delpher for one or more query terms.

        Args:
            query: A single search term as a string, or a list of search terms.
                When a list is provided, the terms are combined into a single
                query string using the "+" operator.

        Returns:
            The API response as a dictionary.
        """
        query = self._query_list_to_string(query)

        try:
            response = requests.get(self.DELPHER_URL, params={"query": query}, timeout=10)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return] #TODO: fix return type
        except requests.exceptions.RequestException as e:
            msg = f"Error querying '{query}': {e}"
            raise type(e)(msg) from e

    def save_to_json(
        self,
        output_file: str | None = None,
        output_dir: str | Path | None = None,
    ) -> None:
        """Save collected results to a JSON file.

        Args:
            output_file: Optional path to override the default output file.
            output_dir: Optional directory to override the default output directory.
        """
        filename = Path(output_file or self.output_file)
        if not filename.suffix:
            filename = filename.with_suffix(".json")
        base_dir = Path(output_dir or self.output_dir)
        destination = filename if filename.is_absolute() else base_dir / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {destination}")  # noqa: T201

    def run(self, query: str | list[str]) -> None:
        """Run searches for all queries and save results to JSON.

        Args:
            query: Search term or list of search terms to query.
        """
        query = self._query_list_to_string(query)
        self.results = self.search(query)
        self.save_to_json(output_file=query)

    def _query_list_to_string(self, query: str | list[str]) -> str:
        """Convert a query (string or list of terms) to a single string for API requests.

        Empty or whitespace-only terms are ignored. If no valid terms remain,
        a ValueError is raised to avoid sending an empty query to the API.
        """
        if isinstance(query, list):
            # Filter out empty or whitespace-only terms
            filtered_terms = [term for term in query if isinstance(term, str) and term.strip()]
            if not filtered_terms:
                msg = "Query list must contain at least one non-empty term."
                raise ValueError(msg)
            return "+".join(filtered_terms)

        # Query is a single string
        if not isinstance(query, str):
            msg = "Query must be a string or a list of strings."
            raise TypeError(msg)
        if not query.strip():
            msg = "Query string must be non-empty."
            raise ValueError(msg)
        return query


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query Delpher API.")
    parser.add_argument(
        "terms",
        nargs="*",
        default=["watersnood", "storm"],
        help="One or more search terms to query (defaults to watersnood storm).",
    )
    args = parser.parse_args()

    client = DelpherClient(output_file="delpher_results.json")
    client.run(args.terms)
