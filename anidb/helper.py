from datetime import date
from requests.adapters import HTTPAdapter, DEFAULT_POOLSIZE, DEFAULT_POOLBLOCK, DEFAULT_RETRIES
import logging
import requests
import time

log = logging.getLogger(__name__)


def download_file(local_filename, url):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return local_filename


def parse_date(value):
    if not value:
        return None

    return date(
        *map(int, value.split("-"))
    )


class AnidbHTTPAdapter(HTTPAdapter):
    def __init__(self, anidb, pool_connections=DEFAULT_POOLSIZE, pool_maxsize=DEFAULT_POOLSIZE,
                 max_retries=DEFAULT_RETRIES, pool_block=DEFAULT_POOLBLOCK):

        super(AnidbHTTPAdapter, self).__init__(pool_connections, pool_maxsize, max_retries, pool_block)

        self.anidb = anidb

        self._last_request_at = None

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        if self._last_request_at:
            since = time.time() - self._last_request_at
            remaining = self.anidb.rate_limit - since

            if remaining > 0:
                log.debug('Waiting %d seconds...', remaining)
                time.sleep(remaining)

        # Send request
        self._last_request_at = time.time()
        return super(AnidbHTTPAdapter, self).send(request, stream, timeout, verify, cert, proxies)
