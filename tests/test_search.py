import pytest

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


def test_multiple_search_terms():
    results_list = Delpher().search(query=TEST_QUERIES)
    results_plus = Delpher().search(query="+".join(TEST_QUERIES))
    results_space = Delpher().search(query=" ".join(TEST_QUERIES))
    assert results_list == results_plus == results_space

    for query in TEST_QUERIES:
        results_single = Delpher().search(query=query)
        n_broad_search = results_single["numberOfRecords"]
        n_specific_search = results_single["numberOfRecords"]
        assert n_broad_search <= n_specific_search, (
            "More specific search retrieved larger number of records than broader search."
        )

    gibberish_results = Delpher().search(query=[GIBBERSH, "groente"])
    assert gibberish_results["numberOfRecords"] == 0


def test_query_preparation():
    assert Delpher()._prepare_request_param("  Groente  ") == "groente"  # noqa: SLF001
    assert Delpher()._prepare_request_param(["  Groente  ", " Fruit "]) == "groente+fruit"  # noqa: SLF001
    assert Delpher()._prepare_request_param("GROENTE") == "groente"  # noqa: SLF001

    results_lower = Delpher().search(query="groente")
    results_caps = Delpher().search(query="GROENTE")
    results_mixed = Delpher().search(query="GrOeNtE")
    results_spaced = Delpher().search(query="  Groente  ")
    assert results_lower == results_caps == results_mixed == results_spaced


def test_illegal_search_terms():
    empty_searches = ["", "   ", ["", "   "]]
    for term in empty_searches:
        with pytest.raises(ValueError):
            Delpher().search(query=term)

    illegal_searches = [42, 3.14, ["valid", 42], {"term": "value"}, True, None]
    for term in illegal_searches:
        with pytest.raises(TypeError):
            Delpher().search(query=term)


def test_search_phrase():
    phrase = "groente en fruit"
    results_phrase = Delpher().search(query=f'"{phrase}"')
    results_words = Delpher().search(query=phrase)
    assert results_phrase["numberOfRecords"] > 0, "Phrase search retrieved no records."
    assert results_phrase != results_words, "Phrase search retrieved same records as word search."
    assert results_phrase["numberOfRecords"] <= results_words["numberOfRecords"], (
        "Phrase search retrieved more records than word search."
    )


def test_search_with_operators():
    pytest.skip("Search operators not yet implemented.")


def test_search_with_special_characters():
    pytest.skip("Special character handling not yet implemented.")
    # What happens with diacritics, punctuation, etc?


def test_search_with_wildcards():
    pytest.skip("Wildcard search not yet implemented.")
    # This test may be fused with above (or operators/special characters/wildcards may all be fused
    # into a single test).


def test_within_collection(): ...


def test_invalid_collection(): ...


# Non-string collection, invalid collection name, empty collection name
# also include list of collections while these are not yet implemented


def test_collection_features():
    """Checks that records and facets contain expected fields, depending on the collection."""


def test_within_multiple_collections():
    pytest.skip("Multiple collection search not yet implemented.")


def test_filter_results():
    pytest.skip("Result filtering not yet implemented.")


def test_save_search_results(): ...
