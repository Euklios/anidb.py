1.0.0
------------------
**Added**
 - Requests are now rate-limited to 1 request every 2 seconds *(by default, can be adjusted)*
 - Responses are now cached for 24 hours *(by default, can be adjusted)*
 - Support for Python 2.6 and Python 3+

0.1.0
------------------
**Added**
 - More attributes to the `Anime` model
 - Tests for models

**Changed**
 - "main" title is now used by default
 - Updated xml tag definitions

**Fixed**
 - Future warning in :code:`Anime.fill_from_xml()`
