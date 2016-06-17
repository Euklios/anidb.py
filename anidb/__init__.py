from __future__ import absolute_import
from appdirs import user_cache_dir
from datetime import datetime, timedelta
import os
import requests
import xml.etree.cElementTree as etree

from anidb.helper import download_file, AnidbHTTPAdapter
from anidb.models import Anime
import anidb.compat as compat

__author__ = "Dean Gardiner"
__version__ = "1.0.0"
__version_code__ = 100

ANIME_LIST_URL = "http://anidb.net/api/anime-titles.xml.gz"

DEFAULT_CACHE_TTL = 86400  # 24 hours (cached responses are refreshed every 24 hours)
DEFAULT_LANGUAGE = 'en'
DEFAULT_RATE_LIMIT = 2     # 2 seconds (requests are rate limited to 1 every 2 seconds)
DEFAULT_USER_AGENT = "anidb.py (%s)" % __version__


class Anidb(object):
    client_name = "anidbpy"
    client_version = __version_code__

    def __init__(self, auto_download=True, language=DEFAULT_LANGUAGE, cache=True,
                 cache_expire_after=DEFAULT_CACHE_TTL, rate_limit=DEFAULT_RATE_LIMIT,
                 user_agent=DEFAULT_USER_AGENT):

        self.auto_download = auto_download
        self.lang = language
        self.rate_limit = rate_limit

        self.session = None
        self._xml = None

        # Initialize cache
        self._cache_path = self._build_session(cache, cache_expire_after, user_agent)
        self._anime_list_path = os.path.join(self._cache_path, "anime-titles.xml.gz")

    def search(self, term):
        if not self._xml:
            try:
                self._xml = self._read_file(self._anime_list_path)
            except IOError:
                if self.auto_download:
                    self.download_anime_list()
                    self._xml = self._read_file(self._anime_list_path)
                else:
                    raise

        term = term.lower()
        anime_ids = []
        for anime in self._xml.findall("anime"):
            for title in anime.findall("title"):
                if term in title.text.lower():
                    anime_ids.append((int(anime.get("aid")), anime))
                    break
        return [Anime(self, aid, False, xml_node) for aid, xml_node in anime_ids]

    def anime(self, aid):
        return Anime(self, aid)

    def download_anime_list(self, force=False):
        if not force and os.path.exists(self._anime_list_path):
            modified_date = datetime.fromtimestamp(
                os.path.getmtime(self._anime_list_path))
            if modified_date + timedelta(1) > datetime.now():
                return False
        return download_file(self._anime_list_path, ANIME_LIST_URL)

    def _build_session(self, cache, cache_expire_after, user_agent):
        # Retrieve cache directory
        if isinstance(cache, compat.string_types):
            cache_dir = cache
        else:
            cache_dir = user_cache_dir('anidbpy')

        # Ensure cache directory exists
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        if cache:
            # Construct cached requests session
            import requests_cache

            self.session = requests_cache.CachedSession(
                expire_after=cache_expire_after,
                backend='sqlite',
                cache_name=os.path.join(cache_dir, 'anidbpy'),
            )
        else:
            # Construct simple requests session
            self.session = requests.Session()

        # Set user agent
        self.session.headers.update({
            'User-Agent': user_agent
        })

        # Setup request rate limit
        self.session.mount('http://', AnidbHTTPAdapter(self))
        self.session.mount('https://', AnidbHTTPAdapter(self))

        return cache_dir

    @staticmethod
    def _read_file(path):
        f = open(path, 'rb')
        return etree.ElementTree(file=f)
