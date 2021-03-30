ytmusicapi: Unofficial API for YouTube Music
############################################

.. image:: https://img.shields.io/pypi/dm/ytmusicapi?style=flat-square
    :alt: PyPI Downloads
    :target: https://pypi.org/project/ytmusicapi/

.. image:: https://badges.gitter.im/sigma67/ytmusicapi.svg
   :alt: Ask questions at https://gitter.im/sigma67/ytmusicapi
   :target: https://gitter.im/sigma67/ytmusicapi

.. image:: https://img.shields.io/codecov/c/github/sigma67/ytmusicapi?style=flat-square
    :alt: Code coverage
    :target: https://codecov.io/gh/sigma67/ytmusicapi

.. image:: https://img.shields.io/github/v/release/sigma67/ytmusicapi?style=flat-square
    :alt: Latest release
    :target: https://github.com/sigma67/ytmusicapi/releases/latest

.. image:: https://img.shields.io/github/commits-since/sigma67/ytmusicapi/latest?style=flat-square
    :alt: Commits since latest release
    :target: https://github.com/sigma67/ytmusicapi/commits


YTMusicAPI
=======
ytmusicapi is a Python 3 library to send requests to the YouTube Music API.
It emulates YouTube Music web client requests using the user's cookie data for authentication.

This is a fork of sigma67's work-in-progress API that emulates web requests from the YouTube Music web client, that adds downloading of streams to disk for offline listening.

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
* get artist information and releases (songs, videos, albums, singles, related artists)
* get user information (videos, playlists)
* get albums
* get song metadata
* get watch playlists (playlist that appears when you press play in YouTube Music)
* get song lyrics

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

Basic usage and search querying:

.. code-block:: python

    from ytmusicapi import YTMusic

    ytmusic = YTMusic('headers_auth.json')
    playlistId = ytmusic.create_playlist('test', 'test description')
    search_results = ytmusic.search('Oasis Wonderwall')
    ytmusic.add_playlist_items(playlistId, [search_results[0]['videoId']])

Downloading for offline listening:

.. code-block:: python

    import os
    import ytmusicapi

    ytm = ytmusicapi.YTMusic(os.path.expanduser("~/.headers_auth.json"))

    # download an artists discography
    ytm.download_artist_albums("Floating Points", "~/Music")

    # download the last 10 songs in your playback history
    ytm.download_playlist(ytm.get_history())

    # download the most recent 100 songs you liked
    ytm.download_playlist(ytm.get_liked_songs(limit=100))


The `tests <https://github.com/sigma67/ytmusicapi/blob/master/tests/test.py>`_ are also a great source of usage examples.

.. end-features

Requirements
==============

- Python 3.5 or higher - https://www.python.org
- Python modules:
	- mutagen
	- requests
	- pytube

Setup and Usage
===============

See the `Documentation <https://ytmusicapi.readthedocs.io/en/latest/usage.html>`_ for detailed instructions

Contributing
==============

Pull requests are welcome. There are still some features that are not yet implemented.
Please, refer to `CONTRIBUTING.rst <https://github.com/sigma67/ytmusicapi/blob/master/CONTRIBUTING.rst>`_ for guidance.