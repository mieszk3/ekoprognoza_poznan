"""Constants for the Ekoprognoza Poznań integration."""

from datetime import timedelta
import logging

DOMAIN = "ekoprognoza_poznan"
LOGGER = logging.getLogger(__package__)

FORECAST_URL = "https://www.poznan.pl/epowietrze/?co=ekoprognoza"
PAGE_URL = "https://www.poznan.pl/mim/wos/atmosfera.html"

REFRESH_TIMES = ((6, 30), (18, 0))
RETRY_INTERVAL = timedelta(minutes=30)
REQUEST_TIMEOUT = 30
