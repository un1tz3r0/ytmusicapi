ytmusicapi: Unofficial API for YouTube Music
############################################

.. image:: https://img.shields.io/pypi/dm/ytmusicapi?style=flat-square
    :alt: PyPI Downloads
    :target: https://pypi.org/project/ytmusicapi/

.. image:: https://img.shields.io/codecov/c/github/sigma67/ytmusicapi?style=flat-square
    :alt: Code coverage
    :target: https://codecov.io/gh/sigma67/ytmusicapi

.. image:: https://img.shields.io/github/v/release/sigma67/ytmusicapi?style=flat-square
    :alt: Latest release
    :target: https://github.com/sigma67/ytmusicapi/releases/latest

.. image:: https://img.shields.io/github/commits-since/sigma67/ytmusicapi/latest?style=flat-square
    :alt: Commits since latest release
    :target: https://github.com/sigma67/ytmusicapi/commits


A fork of sigma67's work-in-progress API that emulates web requests from the YouTube Music web client, that adds downloading of streams to disk for offline listening.

Downloaded files are named and placed in subdirectories according to artist and album and title metadata, and the saved files are tagged appropriately using mutagen. Thumbnail images are
downloaded as well and either saved to files (in the case of artist and album thumbnails) or added as image metadata tags (in the case of songs). Partially downloaded files are deleted
if the download is interrupted. Existing files are skipped and not re-downloaded by default. 

Currently you need to extract your authentication data from your web browser and provide it through a file for it to work.

.. features

Features
--------
| **Downloading**:

* download songs by videoId
* batch-download playlists, albums and artists
* uses highest-quality stream available, prefers audio-only formats but will fall back to video/* mimetypes if there are no audio/* streams available
* uses pytube to decode signatureCipher-protected stream urls by analyzing decoding steps in the generated base.js referenced by the watch page (tricky!)
* names and places downloaded files into subdirectories based on artist/album/title metadata
* downloads and saves thumbnail images for artists, albums and songs
* uses mutagen to tag downloaded files with artist/album/title/thumbnail metadata

| **Browsing**:

* search (including all filters)
* get artist information and releases (songs, videos, albums, singles)
* get user information (videos, playlists)
* get albums
* get song metadata
* get watch playlists (playlist that appears when you press play in YouTube Music)

| **Library management**:

* get library contents: playlists, songs, artists, albums and subscriptions
* add/remove library content: rate songs, albums and playlists, subscribe/unsubscribe artists

| **Playlists**:

* create and delete playlists
* modify playlists: edit metadata, add/move/remove tracks
* get playlist contents

| **Uploads**:

* Upload songs and remove them again
* List uploaded songs, artists and albums


Usage
------
.. code-block:: python

    from ytmusicapi import YTMusic

    ytmusic = YTMusic('headers_auth.json')
    playlistId = ytmusic.create_playlist("test", "test description")
    search_results = ytmusic.search("Oasis Wonderwall")
    ytmusic.add_playlist_items(playlistId, [search_results[0]['videoId']])

The `tests <https://github.com/sigma67/ytmusicapi/blob/master/tests/test.py>`_ are also a great source of usage examples.

.. end-features

Requirements
==============

- Python 3.5 or higher - https://www.python.org

Setup and Usage
===============

See the `Documentation <https://ytmusicapi.readthedocs.io/en/latest/usage.html>`_ for detailed instructions

Contributing
==============

Pull requests are welcome. There are still some features that are not yet implemented.
Please, refer to `CONTRIBUTING.rst <https://github.com/sigma67/ytmusicapi/blob/master/CONTRIBUTING.rst>`_ for guidance.