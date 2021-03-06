from __future__ import absolute_import
import xml.etree.ElementTree as ET

from anidb.helper import parse_date
import anidb.compat as compat


class Anime(object):

    def __init__(self, anidb, id, auto_load=True, xml=None):
        self.anidb = anidb
        self.id = id
        self.titles = []
        self.synonyms = []
        self.all_episodes = []
        self.episodes = {}
        self.picture = None
        self.rating_permanent = None
        self.rating_temporary = None
        self.rating_review = None
        self.categories = []
        self.tags = []
        self.start_date = None
        self.end_date = None
        self.description = None

        if xml:
            self.fill_from_xml(xml)

        self._loaded = False
        if auto_load:
            self.load()

    def __repr__(self):
        return "<Anime id: %s, loaded:%s>" % (self.id, self.loaded)

    @property
    def loaded(self):
        return self._loaded

    def load(self):
        """Load all extra information for this anime.

        The anidb url should look like this:
        http://api.anidb.net:9001/httpapi?request=anime&client={str}&clientver={int}&protover=1&aid={int}
        """
        params = {
            "client": self.anidb.client_name,
            "clientver": self.anidb.client_version,

            "protover": 1,
            "request": "anime",
            "aid": self.id
        }

        response = self.anidb.session.get("http://api.anidb.net:9001/httpapi", params=params)

        self._xml = ET.fromstring(response.text.encode("UTF-8"))
        self.fill_from_xml(self._xml)
        self._loaded = True

    def fill_from_xml(self, xml):
        if xml.find("titles") is not None:
            self.titles = [Title(self, n) for n in xml.find("titles")]
        else:
            self.titles = [Title(self, n) for n in xml.findall("title")]
            return
        self.synonyms = [t for t in self.titles if t.type == "synonym"]
        if xml.find("episodes") is not None:
            self.all_episodes = sorted([Episode(self, n) for n in xml.find("episodes")])
            self.episodes = dict([
                (e.number, e) for e in self.all_episodes
                if e.type == 1
            ])
        if xml.find("picture") is not None:
            self.picture = Picture(self, xml.find("picture"))
        if xml.find("ratings") is not None:
            if xml.find("ratings").find("permanent") is not None:
                self.rating_permanent = xml.find("ratings").find("permanent").text
            if xml.find("ratings").find("temporary") is not None:
                self.rating_temporary = xml.find("ratings").find("temporary").text
            if xml.find("ratings").find("review") is not None:
                self.rating_review = xml.find("ratings").find("review").text
        if xml.find("categories") is not None:
            self.categories = [Category(self, c) for c in xml.find("categories")]
        if xml.find("tags") is not None:
            self.tags = sorted([Tag(self, t) for t in xml.find("tags")])
        if xml.find("startdate") is not None:
            self.start_date = parse_date(xml.find("startdate").text)
        if xml.find("enddate") is not None:
            self.end_date = parse_date(xml.find("enddate").text)
        if xml.find("description") is not None:
            self.description = xml.find("description").text

    @property
    def title(self):
        return self.get_title("main")

    def get_title(self, type=None, lang=None):
        if not type:
            type = "main"
        for t in self.titles:
            if t.type == type:
                return t
        if not lang:
            lang = self.anidb.lang
        for t in self.titles:
            if t.lang == lang:
                return t


class BaseAttribute(object):

    def __init__(self, anime, xml_node):
        self.anime = anime
        self._xml = xml_node

    def _attributes(self, *attrs):
        """Set the given attributes.

        :param list attrs: the attributes to be set.
        """
        for attr in attrs:
            setattr(self, attr, self._xml.attrib.get(attr))

    def _booleans(self, *attrs):
        """Set the given attributes after casting them to bools.

        :param list attrs: the attributes to be set.
        """
        for attr in attrs:
            value = self._xml.attrib.get(attr)
            setattr(self, attr, value is not None and value.lower() == "true")

    def _texts(self, *attrs):
        """Set the text values of the given attributes.

        :param list attrs: the attributes to be found.
        """
        for attr in attrs:
            value = self._xml.find(attr)
            setattr(self, attr, value.text if value is not None else None)

    def __str__(self):
        return self._xml.text

    def __repr__(self):
        return compat.u("<%s: %s>") % (
            self.__class__.__name__,
            unicode(self)
        )


class Category(BaseAttribute):

    def __init__(self, anime, xml_node):
        super(Category, self).__init__(anime, xml_node)
        self._attributes('id', 'weight')
        self._booleans('hentai')
        self._texts('name', 'description')


class Tag(BaseAttribute):

    def __init__(self, anime, xml_node):
        super(Tag, self).__init__(anime, xml_node)
        self._attributes('id', 'update', 'weight')
        if self.update:
            self.update = parse_date(self.update)

        self._booleans('spoiler', 'localspoiler', 'globalspoiler', 'verified')
        self._texts('name', 'description')
        self.count = int(self.weight) if self.weight else 0
        """The importance of this tag."""

    def __cmp__(self, other):
        return self.count - other.count


class Title(BaseAttribute):

    def __init__(self, anime, xml_node):
        super(Title, self).__init__(anime, xml_node)
        # apperently xml:lang is "{http://www.w3.org/XML/1998/namespace}lang"
        self.lang = self._xml.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        self.type = self._xml.attrib.get("type")


class Picture(BaseAttribute):

    def __str__(self):
        return self.url

    @property
    def url(self):
        return "http://img7.anidb.net/pics/anime/%s" % self._xml.text


class Episode(BaseAttribute):

    def __init__(self, anime, xml_node):
        super(Episode, self).__init__(anime, xml_node)
        self._attributes('id')
        self._texts('airdate', 'length', 'epno')
        self.airdate = parse_date(self.airdate)

        self.titles = [Title(self, n) for n in self._xml.findall("title")]
        self.type = int(self._xml.find("epno").attrib["type"])
        self.number = self.epno or 0
        if self.type == 1:
            self.number = int(self.number)

    @property
    def title(self):
        return self.get_title()

    def get_title(self, lang=None):
        if not lang:
            lang = self.anime.anidb.lang
        for t in self.titles:
            if t.lang == lang:
                return t

    def __str__(self):
        return compat.u("%s: %s") % (self.number, self.title)

    def __cmp__(self, other):
        if self.type > other.type:
            return -1
        elif self.type < other.type:
            return 1

        if self.number < other.number:
            return -1
        return 1
