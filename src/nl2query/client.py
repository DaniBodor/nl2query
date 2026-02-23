import argparse
import json
from pathlib import Path
from typing import Any

import requests

from nl2query.collections import COLLECTIONS
from nl2query.collections import COLLECTIONS_BY_CODE
from nl2query.collections import CollectionConfig


class DelpherClient:
    """HTTP client for querying Delpher API and saving results to JSON."""

    DELPHER_URL = "https://www.delpher.nl/nl/api/results"
    DEFAULT_COLLECTION = "radiobulletins"

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

    def search(
        self,
        query: str | list[str],
        collection: str = DEFAULT_COLLECTION,
        facets: dict[str, str | list[str]] | None = None,
    ) -> dict:
        """Search Delpher for one or more query terms.

        Args:
            query: A single search term as a string, or a list of search terms.
                When a list is provided, the terms are combined into a single
                query string using the "+" operator.
            collection: Optional collection name to limit the search. Both labels
                (e.g., "Boeken_Basis") and codes (e.g., "boeken") are accepted.
                Defaults to radiobulletins (anp) if not specified.
            facets: Optional facet filters to include in the request.
                Example: {"type": "advertentie"} translates to
                facets[type][]=advertentie.

        Returns:
            The API response as a dictionary.
        """
        query = self._query_list_to_string(query)
        collection_config = self._resolve_collection(collection)
        try:
            request_params: dict[str, Any] = {"query": query, "coll": collection_config.code}
            request_params.update(
                self._build_facet_params(facets, allowed_facets=collection_config.allowed_facets),
            )
            response = requests.get(
                self.DELPHER_URL,
                params=request_params,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return] #TODO: fix return type
        except requests.exceptions.RequestException as e:
            msg = f"Error querying '{query}': {e}"
            raise type(e)(msg) from e

    def _build_facet_params(
        self,
        facets: dict[str, str | list[str]] | None,
        allowed_facets: frozenset[str] | None = None,
    ) -> dict[str, str | list[str]]:
        """Convert facet filters into Delpher API request params.

        Delpher expects facet filters as keys with the format
        ``facets[<facet_name>][]``.

        Example:
            {"type": "advertentie"} -> {"facets[type][]": "advertentie"}
        """
        if not facets:
            return {}

        facet_params: dict[str, str | list[str]] = {}
        for facet_name, facet_value in facets.items():
            normalized_name = facet_name.strip()
            if not normalized_name:
                msg = "Facet names must be non-empty strings."
                raise ValueError(msg)
            if allowed_facets is not None and normalized_name not in allowed_facets:
                msg = (
                    f"Facet '{normalized_name}' is not allowed for this collection. "
                    f"Allowed facets: {', '.join(sorted(allowed_facets))}."
                )
                raise ValueError(msg)

            if isinstance(facet_value, str):
                if not facet_value.strip():
                    msg = f"Facet '{normalized_name}' must be non-empty."
                    raise ValueError(msg)
                facet_params[f"facets[{normalized_name}][]"] = facet_value
                continue

            if isinstance(facet_value, list):
                filtered_values = [
                    value for value in facet_value if isinstance(value, str) and value.strip()
                ]
                if not filtered_values:
                    msg = f"Facet '{normalized_name}' must contain at least one non-empty value."
                    raise ValueError(msg)
                facet_params[f"facets[{normalized_name}][]"] = filtered_values
                continue

            msg = f"Facet '{normalized_name}' must be a string or a list of strings."
            raise TypeError(msg)

        return facet_params

    def _resolve_collection(self, collection: str | None) -> CollectionConfig:
        """Resolve a collection label or code to a collection configuration."""
        normalized_collection = (collection or self.DEFAULT_COLLECTION).strip().lower()
        if not normalized_collection:
            msg = "Collection must be non-empty when provided."
            raise ValueError(msg)

        if normalized_collection in COLLECTIONS:
            return COLLECTIONS[normalized_collection]

        if normalized_collection in COLLECTIONS_BY_CODE:
            return COLLECTIONS_BY_CODE[normalized_collection]

        msg = f"Invalid collection: {collection}"
        raise ValueError(msg)

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

    def run(self, query: str | list[str], collection: str = DEFAULT_COLLECTION) -> None:
        """Run searches for all queries and save results to JSON.

        Args:
            query: Search term or list of search terms to query.
            collection: Optional collection name to limit the search.
                Defaults to radiobulletins.
        """
        query = self._query_list_to_string(query)
        collection_config = self._resolve_collection(collection)
        self.results = self.search(query=query, collection=collection_config.code)

        save_name = f"{query}_{collection_config.code}.json"
        self.save_to_json(output_file=save_name)

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
    parser.add_argument(
        "-c",
        "--coll",
        default=DelpherClient.DEFAULT_COLLECTION,
        help=(
            "Optional collection label or code. "
            f"Labels: {', '.join(COLLECTIONS.keys())}. "
            f"Codes: {', '.join(COLLECTIONS_BY_CODE.keys())}."
        ),
    )
    args = parser.parse_args()

    client = DelpherClient(output_file="delpher_results.json")
    client.run(args.terms, collection=args.coll)
