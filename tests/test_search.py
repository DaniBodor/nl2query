from nl2query.client import DelpherClient as Delpher

TEST_QUERIES = ["groente", "fruit", "watersnood"]
GIBBERSH = "bfhdgbkjdngsdf"


def test_single_search_term():
    for query in TEST_QUERIES:
        results = Delpher().search(query=query)

        assert isinstance(results, dict)
        assert "numberOfRecords" in results
        assert isinstance(results["numberOfRecords"], int)
        assert results["numberOfRecords"] > 0

        assert "records" in results
        assert isinstance(results["records"], list)
        assert len(results["records"]) == 10  # results["numberOfRecords"] # noqa: PLR2004
        # this is capped at 10 by default, needs to be implemented in the API call

        assert "facets" in results
        assert isinstance(results["facets"], list)

    gibberish_results = Delpher().search(query=GIBBERSH)
    assert gibberish_results["numberOfRecords"] == 0
