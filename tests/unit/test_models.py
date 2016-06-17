from anidb import Anidb
from anidb.models import BaseAttribute
from anidb.models import Category
from anidb.models import Episode
from anidb.models import Picture
from anidb.models import Tag
from anidb.models import Title

from datetime import date
from xml.etree import ElementTree as ET
import pytest


@pytest.mark.parametrize('attribute, value', (
    ('text_attr', 'bla bla bla'),
    ('number_attr', 123),
    ('empty_attr', '')
))
def test_base_attributes(attribute, value):
    """Test whether basic attributes get set correctly."""
    element = ET.fromstring('<bla %s="%s"></bla>' % (attribute, str(value)))
    base = BaseAttribute(None, element)

    base._attributes(attribute)
    assert getattr(base, attribute) == str(value)


@pytest.mark.parametrize('value', ('bla bla bla', 123, False, 'false', 'FaLsE', None))
def test_base_false_flags(value):
    """Check whether boolean falses are handled correctly."""
    element = ET.fromstring('<bla flag="%s"></bla>' % value)
    base = BaseAttribute(None, element)

    base._booleans('flag', 'missing_flag')
    assert base.flag is False
    assert base.missing_flag is False


@pytest.mark.parametrize('value', (True, 'True', 'tRuE', 'true', 'TruE'))
def test_base_true_flags(value):
    """Check whether boolean trues are handled correctly."""
    element = ET.fromstring('<bla flag="%s"></bla>' % value)
    base = BaseAttribute(None, element)

    base._booleans('flag')
    assert base.flag is True


@pytest.mark.parametrize('text', ('bla', '1123', 'bla<span>ble</span>'))
def test_base_texts(text):
    """Check whether base texts are gotten correctly."""
    element = ET.fromstring('<bla><child>%s</child></bla>' % text)
    base = BaseAttribute(None, element)

    base._texts('child')
    assert base.child == element.getchildren()[0].text


@pytest.mark.parametrize('child', (
    '', '<child></child>', '<child><span>1123</span></child>'))
def test_base_empty_texts(child):
    """Check whether empty texts are returned as None."""
    element = ET.fromstring('<bla>%s</bla>' % child)
    base = BaseAttribute(None, element)

    base._texts('child')
    assert base.child is None


def test_title():
    element = ET.fromstring(
        '<title xml:lang="x-jat" type="main">Gintama (2015)</title>'
    )
    title = Title(None, element)
    assert title.lang == 'x-jat'
    assert title.type == 'main'
    assert str(title) == 'Gintama (2015)'


def test_category():
    element = ET.fromstring(
        '''<category id="12" weight="123" hentai="true">
            <name>category1</name>
            <description>description</description>
        </category>'''
    )
    cat = Category(None, element)
    assert cat.id == '12'
    assert cat.weight == '123'
    assert cat.hentai is True
    assert cat.name == 'category1'
    assert cat.description == 'description'


def test_tag():
    element = ET.fromstring(
        '''<tag id="30" weight="20" localspoiler="false" globalspoiler="false"
                verified="true" update="2014-09-10">
            <name>meta tags</name>
            <description>These tags are used for maintenance.</description>
        </tag>
        '''
    )
    tag = Tag(None, element)
    assert tag.id == '30'
    assert tag.weight == '20'
    assert tag.localspoiler is False
    assert tag.globalspoiler is False
    assert tag.verified is True
    assert tag.update == date(2014, 9, 10)
    assert tag.count == 20
    assert tag.name == 'meta tags'
    assert tag.description == 'These tags are used for maintenance.'


def test_picture():
    element = ET.fromstring('<picture>166237.jpg</picture>')
    pic = Picture(None, element)
    assert pic.url == 'http://img7.anidb.net/pics/anime/166237.jpg'


def test_episode():
    title_xmls = [
        '<title xml:lang="en">The Two Apes</title>',
        '<title xml:lang="fr">Les deux singes</title>',
        '<title xml:lang="x-jat">Futari no Etekou</title>',
    ]
    element = ET.fromstring(
        '''<episode id="172424" update="2015-10-08">
                <epno type="1">28</epno>
                <length>25</length>
                <airdate>2015-10-14</airdate>
                <rating votes="1">7.63</rating>
                %s
        </episode>''' % '\n'.join(title_xmls)
    )
    ep = Episode(None, element)
    assert ep.id == '172424'
    assert ep.airdate == date(2015, 10, 14)
    assert ep.length == '25'
    assert ep.epno == '28'
    assert ep.type == 1
    assert ep.number == 28


def test_episode_titles():
    """Check if the titles are correctly added."""
    title_xmls = [
        '<title xml:lang="en">The Two Apes</title>',
        '<title xml:lang="fr">Les deux singes</title>',
        '<title xml:lang="x-jat">Futari no Etekou</title>',
    ]
    element = ET.fromstring(
        '''<episode id="172424" update="2015-10-08">
                <epno type="1">28</epno>
                <length>25</length>
                <airdate>2015-10-14</airdate>
                <rating votes="1">7.63</rating>
                %s
        </episode>''' % '\n'.join(title_xmls)
    )
    gintama = Anidb().search('gintama (2015)')[0]
    ep = Episode(gintama, element)

    assert str(ep.title) == 'The Two Apes'

    titles = [Title(gintama, ET.fromstring(title)) for title in title_xmls]
    lang_titles = {title.lang: title for title in titles}

    for title in ep.titles:
        assert str(lang_titles[title.lang]) == str(title)
        assert ep.get_title(title.lang) == title

    # check if changing the anidb language changes the default title
    gintama.anidb.lang = 'fr'
    assert str(ep.title) == str(lang_titles['fr'])

    # check if specifying a language for which there is no title works
    gintama.anidb.lang = 'pl'
    assert not ep.title
