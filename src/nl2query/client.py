import argparse
import json
from pathlib import Path

import requests

# TODO: can these be read from delpher rather than hardcoding them?
COLLECTIONS = {
    "boeken_basis": "boeken",
    "boeken_google": "boeken1",
    "tijdschriften": "dts",
    "kranten": "ddd",
    "externe_kranten": "regio",
    "radiobulletins": "anp",
}


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

    # TODO: create helper function to search through multiple collections and combine results
    def search(self, query: str | list[str], collection: str = "radiobulletins") -> dict:
        """Search Delpher for one or more query terms.

        Args:
            query: A single search term as a string, or a list of search terms.
                When a list is provided, the terms are concatenated into a single query string (i.e.
                "term1+term2+term3").
            collection: Delpher collection to search through. This accepts either the label used on
                the Delpher website (e.g., "boeken_basis") or the corresponding code (e.g.,
                "boeken"). Note that it is not possible to search across multiple collections
                in a single query. If no collection is specified, it defaults to "radiobulletins".

        Returns:
            The API response as a dictionary.
        """
        query = self._prepare_request_param(query)
        if isinstance(collection, list):
            msg = (
                "It is not possible to search across multiple collections at once.\n"
                "Please specify a single collection."
            )
            raise TypeError(msg)
        collection = self._prepare_request_param(collection)

        if collection in COLLECTIONS:
            api_collection = COLLECTIONS[collection]
        elif collection in COLLECTIONS.values():
            api_collection = collection
        else:
            msg = (
                f"Collection not found: {collection}.\n"
                f"Please choose from: {', '.join(COLLECTIONS.values())}."
            )
            raise ValueError(msg)

        try:
            response = requests.get(
                self.DELPHER_URL,
                params={"query": query, "coll": api_collection},
                timeout=10,
            )
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

    def run(self, query: str | list[str], collection: str = "radiobulletins") -> None:
        """Run searches for all queries and save results to JSON.

        Args:
            query: Search term or list of search terms to query.
            collection: Delpher collection to search through. Defaults to radiobulletins.
        """
        self.results = self.search(query=query, collection=collection)

        save_name = f"{query}_{collection}.json"
        self.save_to_json(output_file=save_name)

    def _prepare_request_param(self, param: str | list[str]) -> str:
        """Check that param is a string or list of strings and convert to stripped lowercase string.

        Empty or whitespace-only terms are ignored. If no valid terms remain,
        a ValueError is raised to avoid sending an empty query to the API.
        """
        # TODO: make this generic for any query parameter, not just search terms.
        # lists of search terms vs collections need to be treated differently
        # for search terms, concatenate them into a single query string (e.g., "term1+term2")
        # for collections, raise an error for now, run a loop once implemented
        # right now this helper is only geared at the search terms case, but both are fed through
        if isinstance(param, list):
            if not all(isinstance(term, str) for term in param):
                msg = "All items in query list must be strings."
                raise TypeError(msg)
            filtered_terms = [term.lower() for term in param if term.strip()]
            if not filtered_terms:
                msg = "Search parameter cannot be empty."
                raise ValueError(msg)
            return "+".join(filtered_terms)

        if not isinstance(param, str):
            msg = "Query must be a string or a list of strings."
            raise TypeError(msg)

        if not param.strip():
            msg = "Search parameter cannot be empty."
            raise ValueError(msg)

        return param.lower().strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query Delpher API.")
    parser.add_argument(
        "terms",
        nargs="*",
        default=["watersnood", "storm"],
        help="One or more search terms to query (defaults to watersnood storm).",
    )
    parser.add_argument(
        "-c",
        "--coll",
        default="radiobulletins",
        help=(
            "Optional collection label or code. "
            f"Labels: {', '.join(COLLECTIONS.keys())}. "
            f"Codes: {', '.join(COLLECTIONS.values())}."
        ),
    )
    args = parser.parse_args()

    client = DelpherClient(output_file="delpher_results.json")
    client.run(args.terms, collection=args.coll)
