"""Documentation about nl2query."""

import logging
from importlib.metadata import version

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = version("nl2query")
