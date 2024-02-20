"""
Enabling Prometheus to get data from user sessions.
"""
from prometheus_client import Counter, Histogram
from streamlit_extras.prometheus import streamlit_registry

registry = streamlit_registry()

# Get total number of visits to the site
VISIT_COUNT = Counter(
    name="visit_count",
    documentation="Number of visits made on the platform",
    registry=registry,
)

# Get total number of searches
SEARCH_COUNT = Counter(
    name="search_count",
    documentation="Number of searches made on the platform",
    registry=registry,
)

# Get total link click count
CLICK_COUNT = Counter(
    name="click_count",
    documentation="Number of clicks on a link",
    registry=registry
)