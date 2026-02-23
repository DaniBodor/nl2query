from dataclasses import dataclass


@dataclass(frozen=True)
class CollectionConfig:
    """Configuration for a Delpher collection."""

    code: str
    allowed_facets: frozenset[str] | None = None


# TODO: load collections and facets from Delpher dynamically.
COLLECTIONS: dict[str, CollectionConfig] = {
    "boeken_basis": CollectionConfig(code="boeken"),
    "boeken_google": CollectionConfig(code="boeken1"),
    "tijdschriften": CollectionConfig(code="dts"),
    "kranten": CollectionConfig(code="ddd"),
    "externe_kranten": CollectionConfig(code="regio"),
    "radiobulletins": CollectionConfig(code="anp"),
}

COLLECTIONS_BY_CODE: dict[str, CollectionConfig] = {
    config.code: config for config in COLLECTIONS.values()
}
