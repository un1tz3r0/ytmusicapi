from ytmusicapi.helpers import *
from ytmusicapi.parsers.browsing import *
from ytmusicapi.parsers.albums import *
from ytmusicapi.parsers.playlists import *
from ytmusicapi.parsers.utils import treefind
from ytmusicapi.parsers.library import parse_albums

class BrowsingMixin:
    def search(self,
                query: str,
                filter: str = None,
                limit: int = 20,
                ignore_spelling: bool = False) -> List[Dict]:
        """
        Search YouTube music
        Returns results within the provided category.

        :param query: Query string, i.e. 'Oasis Wonderwall'
        :param filter: Filter for item types. Allowed values:
          'songs', 'videos', 'albums', 'artists', 'playlists', 'uploads'.
          Default: Default search, including all types of items.
        :param limit: Number of search results to return
          Default: 20
        :param ignore_spelling: Whether to ignore YTM spelling suggestions.
          If True, the exact search term will be searched for, and will not be corrected.
          This does not have any effect when the filter is set to 'uploads'.
          Default: False, will use YTM's default behavior of autocorrecting the search.
        :return: List of results depending on filter.
          resultType specifies the type of item (important for default search).
          albums, artists and playlists additionally contain a browseId, corresponding to
          albumId, channelId and playlistId (browseId='VL'+playlistId)

          Example list::

            [
              {
                "videoId": "ZrOKjDZOtkA",
                "title": "Wonderwall (Remastered)",
                "artists": [
                  {
                    "name": "Oasis",
                    "id": "UCmMUZbaYdNH0bEd1PAlAqsA"
                  }
                ],
                "album": {
                  "name": "(What's The Story) Morning Glory? (Remastered)",
                  "id": "MPREb_9nqEki4ZDpp"
                },
                "duration": "4:19",
                "thumbnails": [...],
                "resultType": "song"
              }
            ]
        """
        body = {'query': query}
        endpoint = 'search'
        search_results = []
        filters = ['albums', 'artists', 'playlists', 'songs', 'videos', 'uploads']
        if filter and filter not in filters:
            raise Exception(
                "Invalid filter provided. Please use one of the following filters or leave out the parameter: "
                + ', '.join(filters))

        if filter:
            param1 = 'Eg-KAQwIA'

            if not ignore_spelling:
                param3 = 'MABqChAEEAMQCRAFEAo%3D'
            else:
                param3 = 'MABCAggBagoQBBADEAkQBRAK'

            if filter == 'uploads':
                params = 'agIYAw%3D%3D'
            else:
                if filter == 'videos':
                    param2 = 'BABGAAgACgA'
                elif filter == 'albums':
                    param2 = 'BAAGAEgACgA'
                elif filter == 'artists':
                    param2 = 'BAAGAAgASgA'
                elif filter == 'playlists':
                    param2 = 'BAAGAAgACgB'
                elif filter == 'uploads':
                    self.__check_auth()
                    param2 = 'RABGAEgASgB'
                else:
                    param2 = 'RAAGAAgACgA'
                params = param1 + param2 + param3

            body['params'] = params
        elif ignore_spelling:
            body['params'] = "QgIIAQ%3D%3D"

        response = self._send_request(endpoint, body)

        # no results
        if 'contents' not in response:
            return search_results

        if 'tabbedSearchResultsRenderer' in response['contents']:
            results = response['contents']['tabbedSearchResultsRenderer']['tabs'][int(
                filter == "uploads")]['tabRenderer']['content']
        else:
            results = response['contents']

        results = nav(results, SECTION_LIST)

        # no results
        if len(results) == 1 and 'itemSectionRenderer' in results:
            return search_results

        for res in results:
            if 'musicShelfRenderer' in res:
                results = res['musicShelfRenderer']['contents']

                type = filter[:-1] if filter else None
                search_results.extend(self.parser.parse_search_results(results, type))

                if 'continuations' in res['musicShelfRenderer']:
                    request_func = lambda additionalParams: self._send_request(
                        endpoint, body, additionalParams)

                    parse_func = lambda contents: self.parser.parse_search_results(contents, type)

                    search_results.extend(
                        get_continuations(res['musicShelfRenderer'], 'musicShelfContinuation',
                                          limit - len(search_results), request_func, parse_func))

        return search_results

    def get_artist(self, channelId: str) -> Dict:
        """
        Get information about an artist and their top releases (songs,
        albums, singles and videos). The top lists contain pointers
        for getting the full list of releases. For songs/videos, pass
        the browseId to :py:func:`get_playlist`. For albums/singles,
        pass browseId and params to :py:func:`get_artist_albums`.

        :param channelId: channel id of the artist
        :return: Dictionary with requested information.

        Example::

            {
                "description": "Oasis were ...",
                "views": "1838795605",
                "name": "Oasis",
                "channelId": "UCUDVBtnOQi4c7E8jebpjc9Q",
                "subscribers": "2.3M",
                "subscribed": false,
                "thumbnails": [...],
                "songs": {
                    "browseId": "VLPLMpM3Z0118S42R1npOhcjoakLIv1aqnS1",
                    "results": [
                        {
                            "videoId": "ZrOKjDZOtkA",
                            "title": "Wonderwall (Remastered)",
                            "thumbnails": [...],
                            "artist": "Oasis",
                            "album": "(What's The Story) Morning Glory? (Remastered)"
                        }
                    ]
                },
                "albums": {
                    "results": [
                        {
                            "title": "Familiar To Millions",
                            "thumbnails": [...],
                            "year": "2018",
                            "browseId": "MPREb_AYetWMZunqA"
                        }
                    ],
                    "browseId": "UCmMUZbaYdNH0bEd1PAlAqsA",
                    "params": "6gPTAUNwc0JDbndLYlFBQV..."
                },
                "singles": {
                    "results": [
                        {
                            "title": "Stand By Me (Mustique Demo)",
                            "thumbnails": [...],
                            "year": "2016",
                            "browseId": "MPREb_7MPKLhibN5G"
                        }
                    ],
                    "browseId": "UCmMUZbaYdNH0bEd1PAlAqsA",
                    "params": "6gPTAUNwc0JDbndLYlFBQV..."
                },
                "videos": {
                    "results": [
                        {
                            "title": "Wonderwall",
                            "thumbnails": [...],
                            "views": "358M",
                            "videoId": "bx1Bh8ZvH84",
                            "playlistId": "PLMpM3Z0118S5xuNckw1HUcj1D021AnMEB"
                        }
                    ],
                    "browseId": "VLPLMpM3Z0118S5xuNckw1HUcj1D021AnMEB"
                }
            }
        """
        if channelId.startswith("MPLA"):
            channelId = channelId[4:]
        body = prepare_browse_endpoint("ARTIST", channelId)
        endpoint = 'browse'
        response = self._send_request(endpoint, body)
        results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST)

        artist = {'description': None, 'views': None}
        header = response['header']['musicImmersiveHeaderRenderer']
        artist['name'] = nav(header, TITLE_TEXT)
        descriptionShelf = find_object_by_key(results,
                                              'musicDescriptionShelfRenderer',
                                              is_key=True)
        if descriptionShelf:
            artist['description'] = descriptionShelf['description']['runs'][0]['text']
            artist['views'] = None if 'subheader' not in descriptionShelf else descriptionShelf[
                'subheader']['runs'][0]['text']
        subscription_button = header['subscriptionButton']['subscribeButtonRenderer']
        artist['channelId'] = subscription_button['channelId']
        artist['subscribers'] = nav(subscription_button,
                                    ['subscriberCountText', 'runs', 0, 'text'], True)
        artist['subscribed'] = subscription_button['subscribed']
        artist['thumbnails'] = nav(header, THUMBNAILS, True)
        artist['songs'] = {'browseId': None}
        if 'musicShelfRenderer' in results[0]:  # API sometimes does not return songs
            musicShelf = nav(results, MUSIC_SHELF)
            if 'navigationEndpoint' in nav(musicShelf, TITLE):
                artist['songs']['browseId'] = nav(musicShelf, TITLE + NAVIGATION_BROWSE_ID)
            artist['songs']['results'] = parse_playlist_items(musicShelf['contents'])

        artist.update(self.parser.parse_artist_contents(results))
        return artist

    def get_artist_albums(self, channelId: str, params: str) -> List[Dict]:
        """
        Get the full list of an artist's albums or singles

        :param channelId: channel Id of the artist
        :param params: params obtained by :py:func:`get_artist`
        :return: List of albums or singles

        Example::

            {
                "browseId": "MPREb_0rtvKhqeCY0",
                "artist": "Armin van Buuren",
                "title": "This I Vow (feat. Mila Josef)",
                "thumbnails": [...],
                "type": "EP",
                "year": "2020"
            }
        """
        body = {"browseId": channelId, "params": params}
        endpoint = 'browse'
        response = self._send_request(endpoint, body)
        artist = nav(response['header']['musicHeaderRenderer'], TITLE_TEXT)
        try:
          results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST + MUSIC_SHELF)
        except:
          results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST + [0, 'gridRenderer'])
        albums = []
        try:
          release_type = nav(results, TITLE_TEXT).lower()
        except:
          release_type = nav(results, ['header', 'gridHeaderRenderer'] + TITLE_TEXT).lower()
        for result in results['contents'] if 'contents' in results.keys() else results['items']:
            try:
              data = result['musicResponsiveListItemRenderer']
            except:
              data = result['musicTwoRowItemRenderer']

            browseId = nav(data, NAVIGATION_BROWSE_ID)

            try:
              title = get_item_text(data['title'], 0)
            except:
              title = [v for k,v in list(treefind(data, lambda p,v: 'title' in p and 'text' in p))][0]

            try:
              thumbnails = nav(data, THUMBNAILS)
            except:
              thumbnails = [v for k,v in list(treefind(data, lambda p,v: len(p) > 0 and str(p[-1]) == 'thumbnails'))][0]

            try:
              album_type = get_item_text(data['subtitle'], 0*1) if release_type == "albums" else "Single"
              year = get_item_text(data, 1, 2 if release_type == "albums" else 0, True)
            except:
              subtitle = [v for k,v in list(treefind(data, lambda p,v: 'subtitle' in p and 'text' in p))]
              album_type = subtitle[0]
              year = subtitle[2]

            albums.append({
                "browseId": browseId,
                "artist": artist,
                "title": title,
                "thumbnails": thumbnails,
                "type": album_type,
                "year": year
            })

        return albums

    def get_user(self, channelId: str) -> Dict:
        """
        Retrieve a user's page. A user may own videos or playlists.

        :param channelId: channelId of the user
        :return: Dictionary with information about a user.

        Example::

            {
              "name": "4Tune – No Copyright Music",
              "videos": {
                "browseId": "UC44hbeRoCZVVMVg5z0FfIww",
                "results": [
                  {
                    "title": "Epic Music Soundtracks 2019",
                    "videoId": "bJonJjgS2mM",
                    "playlistId": "RDAMVMbJonJjgS2mM",
                    "thumbnails": [
                      {
                        "url": "https://i.ytimg.com/vi/bJon...",
                        "width": 800,
                        "height": 450
                      }
                    ],
                    "views": "19K"
                  }
                ]
              },
              "playlists": {
                "browseId": "UC44hbeRoCZVVMVg5z0FfIww",
                "results": [
                  {
                    "title": "♚ Machinimasound | Playlist",
                    "playlistId": "PLRm766YvPiO9ZqkBuEzSTt6Bk4eWIr3gB",
                    "thumbnails": [
                      {
                        "url": "https://i.ytimg.com/vi/...",
                        "width": 400,
                        "height": 225
                      }
                    ]
                  }
                ],
                "params": "6gO3AUNvWU..."
              }
            }
        """
        endpoint = 'browse'
        body = {"browseId": channelId}
        response = self._send_request(endpoint, body)
        user = {'name': nav(response, ['header', 'musicVisualHeaderRenderer'] + TITLE_TEXT)}
        results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST)
        user.update(self.parser.parse_artist_contents(results))
        return user

    def get_user_playlists(self, channelId: str, params: str) -> List[Dict]:
        """
        Retrieve a list of playlists for a given user.
        Call this function again with the returned ``params`` to get the full list.

        :param channelId: channelId of the user.
        :param params: params obtained by :py:func:`get_artist`
        :return: List of user playlists.

        Example::

            [
                {
                  "browseId": "VLPLkqz3S84Tw-T4WwdS5EAMHegVhWH9vZIx",
                  "title": "Top 10 vídeos del momento... hasta el momento! | Vevo Playlist",
                  "thumbnails": [
                    {
                      "url": "https://i.ytimg.com/vi/...",
                      "width": 400,
                      "height": 225
                    }
                  ]
                }
            ]
        """
        endpoint = 'browse'
        body = {"browseId": channelId, 'params': params}
        response = self._send_request(endpoint, body)
        data = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST + MUSIC_SHELF)
        user_playlists = []
        for result in data['contents']:
            data = result['musicResponsiveListItemRenderer']
            user_playlists.append({
                "browseId": nav(data, NAVIGATION_BROWSE_ID),
                "title": get_item_text(data, 0),
                "thumbnails": nav(data, THUMBNAILS),
            })
        return user_playlists

    def get_album(self, browseId: str) -> Dict:
        """
        Get information and tracks of an album

        :param browseId: browseId of the album, for example
            returned by :py:func:`search`
        :return: Dictionary with title, description, artist and tracks.

        Each track is in the following format::

            {
              "title": "Seven",
              "trackCount": "7",
              "durationMs": "1439579",
              "playlistId": "OLAK5uy_kGnhwT08mQMGw8fArBowdtlew3DpgUt9c",
              "releaseDate": {
                "year": 2016,
                "month": 10,
                "day": 28
              },
              "description": "Seven is ...",
              "thumbnails": [...],
              "artist": [
                {
                  "name": "Martin Garrix",
                  "id": "UCqJnSdHjKtfsrHi9aI-9d3g"
                }
              ],
              "tracks": [
                {
                  "index": "1",
                  "title": "WIEE (feat. Mesto)",
                  "artists": "Martin Garrix",
                  "videoId": "8xMNeXI9wxI",
                  "lengthMs": "203406",
                  "likeStatus": "INDIFFERENT"
                }
              ]
            }
        """
        body = prepare_browse_endpoint("ALBUM", browseId)
        endpoint = 'browse'
        response = self._send_request(endpoint, body)
        data = nav(response, FRAMEWORK_MUTATIONS)
        album = {}
        album_data = find_object_by_key(data, 'musicAlbumRelease', 'payload', True)
        album['title'] = album_data['title']
        album['trackCount'] = album_data['trackCount']
        album['durationMs'] = album_data['durationMs']
        album['playlistId'] = album_data['audioPlaylistId']
        album['releaseDate'] = album_data['releaseDate']
        album['description'] = find_object_by_key(data, 'musicAlbumReleaseDetail', 'payload',
                                                  True)['description']
        album['thumbnails'] = album_data['thumbnailDetails']['thumbnails']
        album['artist'] = []
        artists_data = find_objects_by_key(data, 'musicArtist', 'payload')
        for artist in artists_data:
            album['artist'].append({
                'name': artist['musicArtist']['name'],
                'id': artist['musicArtist']['externalChannelId']
            })
        album['tracks'] = []

        track_library_details = {}
        for item in data:
            if 'musicTrackUserDetail' in item['payload']:
                like_state = item['payload']['musicTrackUserDetail']['likeState'].split('_')[-1]
                parent_track = item['payload']['musicTrackUserDetail']['parentTrack']
                like_state = 'INDIFFERENT' if like_state in ['NEUTRAL', 'UNKNOWN'] else like_state[:-1]
                track_library_details[parent_track] = like_state

            if 'musicLibraryEdit' in item['payload']:
                entity_key = item['entityKey']
                track_library_details[entity_key] = {
                    'add': item['payload']['musicLibraryEdit']['addToLibraryFeedbackToken'],
                    'remove': item['payload']['musicLibraryEdit']['removeFromLibraryFeedbackToken']
                }

        for item in data[3:]:
            if 'musicTrack' in item['payload']:
                track = {}
                track['index'] = item['payload']['musicTrack']['albumTrackIndex']
                track['title'] = item['payload']['musicTrack']['title']
                track['thumbnails'] = item['payload']['musicTrack']['thumbnailDetails'][
                    'thumbnails']
                track['artists'] = item['payload']['musicTrack']['artistNames']
                # in case the song is unavailable, there is no videoId
                track['videoId'] = item['payload']['musicTrack']['videoId'] if 'videoId' in item[
                    'payload']['musicTrack'] else None
                # very occasionally lengthMs is not returned
                track['lengthMs'] = item['payload']['musicTrack'][
                    'lengthMs'] if 'lengthMs' in item['payload']['musicTrack'] else None
                track['likeStatus'] = track_library_details[item['entityKey']]
                if 'libraryEdit' in item['payload']['musicTrack']:
                    track['feedbackTokens'] = track_library_details[item['payload']['musicTrack']['libraryEdit']]
                album['tracks'].append(track)

        return album

    def get_song(self, videoId: str) -> Dict:
        """
        Returns metadata about a song or video.

        :param videoId: Video id
        :return: Dictionary with song metadata.

        Example::

            {
              "videoId": "ZrOKjDZOtkA",
              "title": "Wonderwall (Remastered)",
              "lengthSeconds": "259",
              "keywords": [
                "Oasis",
                "(What's",
                "..."
              ],
              "channelId": "UCmMUZbaYdNH0bEd1PAlAqsA",
              "isOwnerViewing": false,
              "shortDescription": "Provided to YouTube by Ignition...",
              "isCrawlable": true,
              "thumbnail": {
                "thumbnails": [
                  {
                    "url": "https://i.ytimg.com/vi/ZrOKjDZOtkA/maxresdefault.jpg",
                    "width": 1920,
                    "height": 1080
                  }
                ]
              },
              "averageRating": 4.5673099,
              "allowRatings": true,
              "viewCount": "18136380",
              "author": "Oasis - Topic",
              "isPrivate": false,
              "isUnpluggedCorpus": false,
              "isLiveContent": false,
              "provider": "Ignition",
              "artists": [
                "Oasis"
              ],
              "copyright": "℗ 2014 Big Brother Recordings ...",
              "production": [
                "Composer: Noel Gallagher",
                "Lyricist: Noel Gallagher",
                "Producer: Owen Morris & Noel Gallagher"
              ],
              "release": "2014-09-29"
              "category": "Music"
            }

        """
        endpoint = "https://www.youtube.com/get_video_info"
        params = {"video_id": videoId, "hl": self.language, "el": "detailpage"}
        response = requests.get(endpoint, params, headers=self.headers, proxies=self.proxies)
        text = parse_qs(response.text)
        if 'player_response' not in text:
            return text
        player_response = json.loads(text['player_response'][0])
        song_meta = player_response['videoDetails']
        song_meta['category'] = player_response['microformat']['playerMicroformatRenderer'][
            'category']
        if song_meta['shortDescription'].endswith("Auto-generated by YouTube."):
            try:
                description = song_meta['shortDescription'].split('\n\n')
                for i, detail in enumerate(description):
                    description[i] = codecs.escape_decode(detail)[0].decode('utf-8')
                song_meta['provider'] = description[0].replace('Provided to YouTube by ', '')
                song_meta['artists'] = [artist for artist in description[1].split(' · ')[1:]]
                song_meta['copyright'] = description[3]
                song_meta['release'] = None if len(description) < 5 else description[4].replace(
                    'Released on: ', '')
                song_meta['production'] = None if len(description) < 6 else [
                    pub for pub in description[5].split('\n')
                ]
            except (KeyError, IndexError):
                pass
        return song_meta

    def get_streaming_data(self, videoId: str) -> Dict:
        """
        Returns the streaming data for a song or video.

        :param videoId: Video id
        :return: Dictionary with song streaming data.

        Example::

            {
                "expiresInSeconds": "21540",
                "formats": [
                    {
                        "itag": 18,
                        "mimeType": "video/mp4; codecs=\"avc1.42001E, mp4a.40.2\"",
                        "bitrate": 306477,
                        "width": 360,
                        "height": 360,
                        "lastModified": "1574970034520502",
                        "contentLength": "9913027",
                        "quality": "medium",
                        "fps": 25,
                        "qualityLabel": "360p",
                        "projectionType": "RECTANGULAR",
                        "averageBitrate": 306419,
                        "audioQuality": "AUDIO_QUALITY_LOW",
                        "approxDurationMs": "258809",
                        "audioSampleRate": "44100",
                        "audioChannels": 2,
                        "signatureCipher": "s=..."
                    }
                ],
                "adaptiveFormats": [
                    {
                        "itag": 137,
                        "mimeType": "video/mp4; codecs=\"avc1.640020\"",
                        "bitrate": 312234,
                        "width": 1078,
                        "height": 1080,
                        "initRange": {
                            "start": "0",
                            "end": "738"
                        },
                        "indexRange": {
                            "start": "739",
                            "end": "1382"
                        },
                        "lastModified": "1574970033536914",
                        "contentLength": "5674377",
                        "quality": "hd1080",
                        "fps": 25,
                        "qualityLabel": "1080p",
                        "projectionType": "RECTANGULAR",
                        "averageBitrate": 175432,
                        "approxDurationMs": "258760",
                        "signatureCipher": "s=..."
                    },
                    {...},
                    {
                        "itag": 140,
                        "mimeType": "audio/mp4; codecs=\"mp4a.40.2\"",
                        "bitrate": 131205,
                        "initRange": {
                            "start": "0",
                            "end": "667"
                        },
                        "indexRange": {
                            "start": "668",
                            "end": "1011"
                        },
                        "lastModified": "1574969975805792",
                        "contentLength": "4189579",
                        "quality": "tiny",
                        "projectionType": "RECTANGULAR",
                        "averageBitrate": 129521,
                        "highReplication": true,
                        "audioQuality": "AUDIO_QUALITY_MEDIUM",
                        "approxDurationMs": "258773",
                        "audioSampleRate": "44100",
                        "audioChannels": 2,
                        "loudnessDb": 1.1422243,
                        "signatureCipher": "s=..."
                    },
                    {...}
                ]
            }

        """
        endpoint = "https://www.youtube.com/get_video_info"
        params = {
            "video_id": videoId,
            "hl": self.language,
            "el": "detailpage",
            "c": "WEB_REMIX",
            "cver": "0.1"
        }
        response = requests.get(endpoint, params, headers=self.headers, proxies=self.proxies)
        text = parse_qs(response.text)
        if 'player_response' not in text:
            return text

        player_response = json.loads(text['player_response'][0])
        if 'streamingData' not in player_response:
            raise Exception('This video is not playable.')

        return player_response['streamingData']

    def get_lyrics(self, browseId: str) -> Dict:
        """
        Returns lyrics of a song or video.

        :param browseId: Lyrics browse id obtained from `get_watch_playlist`
        :return: Dictionary with song lyrics.

        Example::

            {
                "lyricsFound": True,
                "lyrics": "Today is gonna be the day\\nThat they're gonna throw it back to you\\n",
                "source": "Source: LyricFind"
            }

        """
        lyrics = {}
        response = self._send_request('browse', {'browseId': browseId})
        if 'sectionListRenderer' in response['contents'].keys():
            lyrics['lyricsFound'] = True
            lyrics['lyrics'] = response['contents']['sectionListRenderer']['contents'][0][
                'musicDescriptionShelfRenderer']['description']['runs'][0]['text']
            lyrics['source'] = response['contents']['sectionListRenderer']['contents'][0][
                'musicDescriptionShelfRenderer']['footer']['runs'][0]['text']
        else:
            lyrics['lyricsFound'] = False
            lyrics['lyrics'] = response['contents']['messageRenderer']['subtext'][
                'messageSubtextRenderer']['text']['runs'][0]['text']
            lyrics['source'] = response['contents']['messageRenderer']['text']['runs'][0]['text']
        return lyrics

    def search(self,
               query: str,
               filter: str = None,
               limit: int = 20,
               ignore_spelling: bool = False) -> List[Dict]:
        """
        Search YouTube music
        Returns results within the provided category.

        :param query: Query string, i.e. 'Oasis Wonderwall'
        :param filter: Filter for item types. Allowed values: ``songs``, ``videos``, ``albums``, ``artists``, ``playlists``, ``community_playlists``, ``featured_playlists``, ``uploads``.
          Default: Default search, including all types of items.
        :param limit: Number of search results to return
          Default: 20
        :param ignore_spelling: Whether to ignore YTM spelling suggestions.
          If True, the exact search term will be searched for, and will not be corrected.
          This does not have any effect when the filter is set to ``uploads``.
          Default: False, will use YTM's default behavior of autocorrecting the search.
        :return: List of results depending on filter.
          resultType specifies the type of item (important for default search).
          albums, artists and playlists additionally contain a browseId, corresponding to
          albumId, channelId and playlistId (browseId=``VL``+playlistId)

          Example list for default search with one result per resultType for brevity. Normally
          there are 3 results per resultType and an additional ``thumbnails`` key::

            [
              {
                "resultType": "video",
                "videoId": "vU05Eksc_iM",
                "title": "Wonderwall",
                "artists": [
                  {
                    "name": "Oasis",
                    "id": "UCmMUZbaYdNH0bEd1PAlAqsA"
                  }
                ],
                "views": "1.4M",
                "duration": "4:38"
              },
              {
                "resultType": "song",
                "videoId": "ZrOKjDZOtkA",
                "title": "Wonderwall",
                "artists": [
                  {
                    "name": "Oasis",
                    "id": "UCmMUZbaYdNH0bEd1PAlAqsA"
                  }
                ],
                "album": {
                  "name": "(What's The Story) Morning Glory? (Remastered)",
                  "id": "MPREb_9nqEki4ZDpp"
                },
                "duration": "4:19",
                "isExplicit": false,
                "feedbackTokens": {
                  "add": null,
                  "remove": null
                }
              },
              {
                "resultType": "album",
                "browseId": "MPREb_9nqEki4ZDpp",
                "title": "(What's The Story) Morning Glory? (Remastered)",
                "type": "Album",
                "artist": "Oasis",
                "year": "1995",
                "isExplicit": false
              },
              {
                "resultType": "playlist",
                "browseId": "VLPLK1PkWQlWtnNfovRdGWpKffO1Wdi2kvDx",
                "title": "Wonderwall - Oasis",
                "author": "Tate Henderson",
                "itemCount": "174"
              },
              {
                "resultType": "video",
                "videoId": "bx1Bh8ZvH84",
                "title": "Wonderwall",
                "artists": [
                  {
                    "name": "Oasis",
                    "id": "UCmMUZbaYdNH0bEd1PAlAqsA"
                  }
                ],
                "views": "386M",
                "duration": "4:38"
              },
              {
                "resultType": "artist",
                "browseId": "UCmMUZbaYdNH0bEd1PAlAqsA",
                "artist": "Oasis",
                "shuffleId": "RDAOkjHYJjL1a3xspEyVkhHAsg",
                "radioId": "RDEMkjHYJjL1a3xspEyVkhHAsg"
              }
            ]


        """
        body = {'query': query}
        endpoint = 'search'
        search_results = []
        filters = [
            'albums', 'artists', 'playlists', 'community_playlists', 'featured_playlists', 'songs',
            'videos', 'uploads'
        ]
        if filter and filter not in filters:
            raise Exception(
                "Invalid filter provided. Please use one of the following filters or leave out the parameter: "
                + ', '.join(filters))

        params = None
        if filter:
            if filter == 'uploads':
                params = 'agIYAw%3D%3D'

            elif filter == 'playlists':
                params = 'Eg-KAQwIABAAGAAgACgB'
                if not ignore_spelling:
                    params += 'MABqChAEEAMQCRAFEAo%3D'
                else:
                    params += 'MABCAggBagoQBBADEAkQBRAK'

            elif 'playlists' in filter:
                param1 = 'EgeKAQQoA'
                if filter == 'featured_playlists':
                    param2 = 'Dg'
                else:  # community_playlists
                    param2 = 'EA'

                if not ignore_spelling:
                    param3 = 'BagwQDhAKEAMQBBAJEAU%3D'
                else:
                    param3 = 'BQgIIAWoMEA4QChADEAQQCRAF'

                filter = 'playlists'  # reset to playlists for parser

            else:
                param1 = 'EgWKAQI'
                filter_params = {'songs': 'I', 'videos': 'Q', 'albums': 'Y', 'artists': 'g'}
                param2 = filter_params[filter]
                if not ignore_spelling:
                    param3 = 'AWoMEA4QChADEAQQCRAF'
                else:
                    param3 = 'AUICCAFqDBAOEAoQAxAEEAkQBQ%3D%3D'

            params = params if params else param1 + param2 + param3

        elif ignore_spelling:
            params = 'EhGKAQ4IARABGAEgASgAOAFAAUICCAE%3D'

        if params:
            body['params'] = params
        response = self._send_request(endpoint, body)

        # no results
        if 'contents' not in response:
            return search_results

        if 'tabbedSearchResultsRenderer' in response['contents']:
            results = response['contents']['tabbedSearchResultsRenderer']['tabs'][int(
                filter == "uploads")]['tabRenderer']['content']
        else:
            results = response['contents']

        results = nav(results, SECTION_LIST)

        # no results
        if len(results) == 1 and 'itemSectionRenderer' in results:
            return search_results

        for res in results:
            if 'musicShelfRenderer' in res:
                results = res['musicShelfRenderer']['contents']

                type = filter[:-1] if filter else None
                search_results.extend(self.parser.parse_search_results(results, type))

                if 'continuations' in res['musicShelfRenderer']:
                    request_func = lambda additionalParams: self._send_request(
                        endpoint, body, additionalParams)

                    parse_func = lambda contents: self.parser.parse_search_results(contents, type)

                    search_results.extend(
                        get_continuations(res['musicShelfRenderer'], 'musicShelfContinuation',
                                          limit - len(search_results), request_func, parse_func))

        return search_results

    def get_artist(self, channelId: str) -> Dict:
        """
        Get information about an artist and their top releases (songs,
        albums, singles, videos, and related artists). The top lists
        contain pointers for getting the full list of releases. For
        songs/videos, pass the browseId to :py:func:`get_playlist`.
        For albums/singles, pass browseId and params to :py:func:
        `get_artist_albums`.

        :param channelId: channel id of the artist
        :return: Dictionary with requested information.

        Example::

            {
                "description": "Oasis were ...",
                "views": "1838795605",
                "name": "Oasis",
                "channelId": "UCUDVBtnOQi4c7E8jebpjc9Q",
                "subscribers": "2.3M",
                "subscribed": false,
                "thumbnails": [...],
                "songs": {
                    "browseId": "VLPLMpM3Z0118S42R1npOhcjoakLIv1aqnS1",
                    "results": [
                        {
                            "videoId": "ZrOKjDZOtkA",
                            "title": "Wonderwall (Remastered)",
                            "thumbnails": [...],
                            "artist": "Oasis",
                            "album": "(What's The Story) Morning Glory? (Remastered)"
                        }
                    ]
                },
                "albums": {
                    "results": [
                        {
                            "title": "Familiar To Millions",
                            "thumbnails": [...],
                            "year": "2018",
                            "browseId": "MPREb_AYetWMZunqA"
                        }
                    ],
                    "browseId": "UCmMUZbaYdNH0bEd1PAlAqsA",
                    "params": "6gPTAUNwc0JDbndLYlFBQV..."
                },
                "singles": {
                    "results": [
                        {
                            "title": "Stand By Me (Mustique Demo)",
                            "thumbnails": [...],
                            "year": "2016",
                            "browseId": "MPREb_7MPKLhibN5G"
                        }
                    ],
                    "browseId": "UCmMUZbaYdNH0bEd1PAlAqsA",
                    "params": "6gPTAUNwc0JDbndLYlFBQV..."
                },
                "videos": {
                    "results": [
                        {
                            "title": "Wonderwall",
                            "thumbnails": [...],
                            "views": "358M",
                            "videoId": "bx1Bh8ZvH84",
                            "playlistId": "PLMpM3Z0118S5xuNckw1HUcj1D021AnMEB"
                        }
                    ],
                    "browseId": "VLPLMpM3Z0118S5xuNckw1HUcj1D021AnMEB"
                },
                "related": {
                    "results": [
                        {
                            "browseId": "UCt2KxZpY5D__kapeQ8cauQw",
                            "subscribers": "450K",
                            "title": "The Verve"
                        },
                        {
                            "browseId": "UCwK2Grm574W1u-sBzLikldQ",
                            "subscribers": "341K",
                            "title": "Liam Gallagher"
                        },
                        ...
                    ]
                }
            }
        """
        if channelId.startswith("MPLA"):
            channelId = channelId[4:]
        body = prepare_browse_endpoint("ARTIST", channelId)
        endpoint = 'browse'
        response = self._send_request(endpoint, body)
        results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST)

        if len(results) == 1:
            # not a YouTube Music Channel, a standard YouTube Channel ID with no music content was given
            raise ValueError(f"The YouTube Channel {channelId} has no music content.")

        artist = {'description': None, 'views': None}
        header = response['header']['musicImmersiveHeaderRenderer']
        artist['name'] = nav(header, TITLE_TEXT)
        descriptionShelf = find_object_by_key(results,
                                              'musicDescriptionShelfRenderer',
                                              is_key=True)
        if descriptionShelf:
            artist['description'] = nav(descriptionShelf, DESCRIPTION)
            artist['views'] = None if 'subheader' not in descriptionShelf else descriptionShelf[
                'subheader']['runs'][0]['text']
        subscription_button = header['subscriptionButton']['subscribeButtonRenderer']
        artist['channelId'] = subscription_button['channelId']
        artist['shuffleId'] = nav(header,
                                  ['playButton', 'buttonRenderer'] + NAVIGATION_WATCH_PLAYLIST_ID,
                                  True)
        artist['radioId'] = nav(header, ['startRadioButton', 'buttonRenderer']
                                + NAVIGATION_WATCH_PLAYLIST_ID, True)
        artist['subscribers'] = nav(subscription_button,
                                    ['subscriberCountText', 'runs', 0, 'text'], True)
        artist['subscribed'] = subscription_button['subscribed']
        artist['thumbnails'] = nav(header, THUMBNAILS, True)
        artist['songs'] = {'browseId': None}
        if 'musicShelfRenderer' in results[0]:  # API sometimes does not return songs
            musicShelf = nav(results[0], MUSIC_SHELF)
            if 'navigationEndpoint' in nav(musicShelf, TITLE):
                artist['songs']['browseId'] = nav(musicShelf, TITLE + NAVIGATION_BROWSE_ID)
            artist['songs']['results'] = parse_playlist_items(musicShelf['contents'])

        artist.update(self.parser.parse_artist_contents(results))
        return artist

    def get_artist_albums(self, channelId: str, params: str) -> List[Dict]:
        """
        Get the full list of an artist's albums or singles

        :param channelId: channel Id of the artist
        :param params: params obtained by :py:func:`get_artist`
        :return: List of albums in the format of :py:func:`get_library_albums`,
          except artists key is missing.

        """
        body = {"browseId": channelId, "params": params}
        endpoint = 'browse'
        response = self._send_request(endpoint, body)
        results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST_ITEM + GRID_ITEMS)
        albums = parse_albums(results)

        return albums

    def get_user(self, channelId: str) -> Dict:
        """
        Retrieve a user's page. A user may own videos or playlists.

        :param channelId: channelId of the user
        :return: Dictionary with information about a user.

        Example::

            {
              "name": "4Tune – No Copyright Music",
              "videos": {
                "browseId": "UC44hbeRoCZVVMVg5z0FfIww",
                "results": [
                  {
                    "title": "Epic Music Soundtracks 2019",
                    "videoId": "bJonJjgS2mM",
                    "playlistId": "RDAMVMbJonJjgS2mM",
                    "thumbnails": [
                      {
                        "url": "https://i.ytimg.com/vi/bJon...",
                        "width": 800,
                        "height": 450
                      }
                    ],
                    "views": "19K"
                  }
                ]
              },
              "playlists": {
                "browseId": "UC44hbeRoCZVVMVg5z0FfIww",
                "results": [
                  {
                    "title": "♚ Machinimasound | Playlist",
                    "playlistId": "PLRm766YvPiO9ZqkBuEzSTt6Bk4eWIr3gB",
                    "thumbnails": [
                      {
                        "url": "https://i.ytimg.com/vi/...",
                        "width": 400,
                        "height": 225
                      }
                    ]
                  }
                ],
                "params": "6gO3AUNvWU..."
              }
            }
        """
        endpoint = 'browse'
        body = {"browseId": channelId}
        response = self._send_request(endpoint, body)
        user = {'name': nav(response, ['header', 'musicVisualHeaderRenderer'] + TITLE_TEXT)}
        results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST)
        user.update(self.parser.parse_artist_contents(results))
        return user

    def get_user_playlists(self, channelId: str, params: str) -> List[Dict]:
        """
        Retrieve a list of playlists for a given user.
        Call this function again with the returned ``params`` to get the full list.

        :param channelId: channelId of the user.
        :param params: params obtained by :py:func:`get_artist`
        :return: List of user playlists in the format of :py:func:`get_library_playlists`

        """
        endpoint = 'browse'
        body = {"browseId": channelId, 'params': params}
        response = self._send_request(endpoint, body)
        results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST_ITEM + GRID_ITEMS)
        user_playlists = parse_content_list(results, parse_playlist)

        return user_playlists

    def get_album_browse_id(self, audioPlaylistId: str):
        """
        Get an album's browseId based on its audioPlaylistId
        :param audioPlaylistId: id of the audio playlist  (starting with `OLAK5uy_`)
        :return: browseId (starting with `MPREb_`)
        """
        params = {"list": audioPlaylistId}
        response = self._send_get_request(YTM_DOMAIN + "/playlist", params)
        matches = re.findall(r"\"MPRE.+?\"", response)
        browse_id = None
        if len(matches) > 0:
            browse_id = matches[0].encode('utf8').decode('unicode-escape').strip('"')
        return browse_id

    def get_album(self, browseId: str) -> Dict:
        """
        Get information and tracks of an album

        :param browseId: browseId of the album, for example
            returned by :py:func:`search`
        :return: Dictionary with title, description, artist and tracks.

        Each track is in the following format::

            {
              "title": "Seven",
              "trackCount": "7",
              "durationMs": "1439579",
              "playlistId": "OLAK5uy_kGnhwT08mQMGw8fArBowdtlew3DpgUt9c",
              "releaseDate": {
                "year": 2016,
                "month": 10,
                "day": 28
              },
              "description": "Seven is ...",
              "thumbnails": [...],
              "artist": [
                {
                  "name": "Martin Garrix",
                  "id": "UCqJnSdHjKtfsrHi9aI-9d3g"
                }
              ],
              "tracks": [
                {
                  "index": "1",
                  "title": "WIEE (feat. Mesto)",
                  "artists": "Martin Garrix",
                  "videoId": "8xMNeXI9wxI",
                  "lengthMs": "203406",
                  "likeStatus": "INDIFFERENT"
                }
              ]
            }
        """
        body = prepare_browse_endpoint("ALBUM", browseId)
        endpoint = 'browse'
        response = self._send_request(endpoint, body)
        album = {}
        data = nav(response, FRAMEWORK_MUTATIONS, True)
        if not data:
            album = parse_album_header(response)
            results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST_ITEM + MUSIC_SHELF)
            album['tracks'] = parse_playlist_items(results['contents'])
        else:
            album_data = find_object_by_key(data, 'musicAlbumRelease', 'payload', True)
            album['title'] = album_data['title']
            album['trackCount'] = album_data['trackCount']
            album['durationMs'] = album_data['durationMs']
            album['playlistId'] = album_data['audioPlaylistId']
            album['releaseDate'] = album_data['releaseDate']
            album['description'] = find_object_by_key(data, 'musicAlbumReleaseDetail', 'payload',
                                                      True)['description']
            album['thumbnails'] = album_data['thumbnailDetails']['thumbnails']
            album['artist'] = []
            artists_data = find_objects_by_key(data, 'musicArtist', 'payload')
            for artist in artists_data:
                album['artist'].append({
                    'name': artist['musicArtist']['name'],
                    'id': artist['musicArtist']['externalChannelId']
                })
            album['tracks'] = []

            track_library_details = {}
            for item in data:
                if 'musicTrackUserDetail' in item['payload']:
                    like_state = item['payload']['musicTrackUserDetail']['likeState'].split(
                        '_')[-1]
                    parent_track = item['payload']['musicTrackUserDetail']['parentTrack']
                    like_state = 'INDIFFERENT' if like_state in ['NEUTRAL', 'UNKNOWN'
                                                                 ] else like_state[:-1]
                    track_library_details[parent_track] = like_state

                if 'musicLibraryEdit' in item['payload']:
                    entity_key = item['entityKey']
                    track_library_details[entity_key] = {
                        'add': item['payload']['musicLibraryEdit']['addToLibraryFeedbackToken'],
                        'remove':
                        item['payload']['musicLibraryEdit']['removeFromLibraryFeedbackToken']
                    }

            for item in data[3:]:
                if 'musicTrack' in item['payload']:
                    music_track = item['payload']['musicTrack']
                    track = {}
                    track['index'] = music_track['albumTrackIndex']
                    track['title'] = music_track['title']
                    track['thumbnails'] = music_track['thumbnailDetails']['thumbnails']
                    track['artists'] = music_track['artistNames']
                    # in case the song is unavailable, there is no videoId
                    track['videoId'] = music_track['videoId'] if 'videoId' in item['payload'][
                        'musicTrack'] else None
                    # very occasionally lengthMs is not returned
                    track['lengthMs'] = music_track[
                        'lengthMs'] if 'lengthMs' in music_track else None
                    track['likeStatus'] = track_library_details[item['entityKey']]
                    track['isExplicit'] = music_track['contentRating'][
                        'explicitType'] == 'MUSIC_ENTITY_EXPLICIT_TYPE_EXPLICIT'
                    if 'libraryEdit' in music_track:
                        track['feedbackTokens'] = track_library_details[music_track['libraryEdit']]
                    album['tracks'].append(track)

        return album

    def get_song(self, videoId: str, signatureTimestamp: int = None) -> Dict:
        """
        Returns metadata and streaming information about a song or video.

        :param videoId: Video id
        :param signatureTimestamp: Provide the current YouTube signatureTimestamp.
            If not provided a default value will be used, which might result in invalid streaming URLs
        :return: Dictionary with song metadata.

        Example::

            {
              "videoDetails": {
                "allowRatings": true,
                "author": "Oasis - Topic",
                "averageRating": 4.5783687,
                "channelId": "UCmMUZbaYdNH0bEd1PAlAqsA",
                "isCrawlable": true,
                "isLiveContent": false,
                "isOwnerViewing": false,
                "isPrivate": false,
                "isUnpluggedCorpus": false,
                "lengthSeconds": "259",
                "musicVideoType": "MUSIC_VIDEO_TYPE_ATV",
                "thumbnail": {
                  "thumbnails": [...]
                },
                "title": "Wonderwall",
                "videoId": "ZrOKjDZOtkA",
                "viewCount": "27429003"
              },
              "microformat": {
                "microformatDataRenderer": {
                  "androidPackage": "com.google.android.apps.youtube.music",
                  "appName": "YouTube Music",
                  "availableCountries": ["AE",...],
                  "category": "Music",
                  "description": "Provided to YouTube by Ignition Wonderwall · Oasis ...",
                  "familySafe": true,
                  "iosAppArguments": "https://music.youtube.com/watch?v=ZrOKjDZOtkA",
                  "iosAppStoreId": "1017492454",
                  "linkAlternates": [
                    {
                      "hrefUrl": "android-app://com.google.android.youtube/http/youtube.com/watch?v=ZrOKjDZOtkA"
                    },
                    {
                      "hrefUrl": "ios-app://544007664/http/youtube.com/watch?v=ZrOKjDZOtkA"
                    },
                    {
                      "alternateType": "application/json+oembed",
                      "hrefUrl": "https://www.youtube.com/oembed?format=json&url=...",
                      "title": "Wonderwall (Remastered)"
                    },
                    {
                      "alternateType": "text/xml+oembed",
                      "hrefUrl": "https://www.youtube.com/oembed?format=xml&url=...",
                      "title": "Wonderwall (Remastered)"
                    }
                  ],
                  "noindex": false,
                  "ogType": "video.other",
                  "pageOwnerDetails": {
                    "externalChannelId": "UCmMUZbaYdNH0bEd1PAlAqsA",
                    "name": "Oasis - Topic",
                    "youtubeProfileUrl": "http://www.youtube.com/channel/UCmMUZbaYdNH0bEd1PAlAqsA"
                  },
                  "paid": false,
                  "publishDate": "2017-01-25",
                  "schemaDotOrgType": "http://schema.org/VideoObject",
                  "siteName": "YouTube Music",
                  "tags": ["Oasis",...],
                  "thumbnail": {
                    "thumbnails": [
                      {
                        "height": 720,
                        "url": "https://i.ytimg.com/vi/ZrOKjDZOtkA/maxresdefault.jpg",
                        "width": 1280
                      }
                    ]
                  },
                  "title": "Wonderwall (Remastered) - YouTube Music",
                  "twitterCardType": "player",
                  "twitterSiteHandle": "@YouTubeMusic",
                  "unlisted": false,
                  "uploadDate": "2017-01-25",
                  "urlApplinksAndroid": "vnd.youtube.music://music.youtube.com/watch?v=ZrOKjDZOtkA&feature=applinks",
                  "urlApplinksIos": "vnd.youtube.music://music.youtube.com/watch?v=ZrOKjDZOtkA&feature=applinks",
                  "urlCanonical": "https://music.youtube.com/watch?v=ZrOKjDZOtkA",
                  "urlTwitterAndroid": "vnd.youtube.music://music.youtube.com/watch?v=ZrOKjDZOtkA&feature=twitter-deep-link",
                  "urlTwitterIos": "vnd.youtube.music://music.youtube.com/watch?v=ZrOKjDZOtkA&feature=twitter-deep-link",
                  "videoDetails": {
                    "durationIso8601": "PT4M19S",
                    "durationSeconds": "259",
                    "externalVideoId": "ZrOKjDZOtkA"
                  },
                  "viewCount": "27429003"
                }
              },
              "playabilityStatus": {
                "contextParams": "Q0FFU0FnZ0I=",
                "miniplayer": {
                  "miniplayerRenderer": {
                    "playbackMode": "PLAYBACK_MODE_ALLOW"
                  }
                },
                "playableInEmbed": true,
                "status": "OK"
              },
              "streamingData": {
                "adaptiveFormats": [
                  {
                    "approxDurationMs": "258760",
                    "averageBitrate": 178439,
                    "bitrate": 232774,
                    "contentLength": "5771637",
                    "fps": 25,
                    "height": 1080,
                    "indexRange": {
                      "end": "1398",
                      "start": "743"
                    },
                    "initRange": {
                      "end": "742",
                      "start": "0"
                    },
                    "itag": 137,
                    "lastModified": "1614620567944400",
                    "mimeType": "video/mp4; codecs=\"avc1.640020\"",
                    "projectionType": "RECTANGULAR",
                    "quality": "hd1080",
                    "qualityLabel": "1080p",
                    "signatureCipher": "s=_xxxOq0QJ8...",
                    "width": 1078
                  }[...]
                ],
                "expiresInSeconds": "21540",
                "formats": [
                  {
                    "approxDurationMs": "258809",
                    "audioChannels": 2,
                    "audioQuality": "AUDIO_QUALITY_LOW",
                    "audioSampleRate": "44100",
                    "averageBitrate": 179462,
                    "bitrate": 179496,
                    "contentLength": "5805816",
                    "fps": 25,
                    "height": 360,
                    "itag": 18,
                    "lastModified": "1614620870611066",
                    "mimeType": "video/mp4; codecs=\"avc1.42001E, mp4a.40.2\"",
                    "projectionType": "RECTANGULAR",
                    "quality": "medium",
                    "qualityLabel": "360p",
                    "signatureCipher": "s=kXXXOq0QJ8...",
                    "width": 360
                  }
                ]
              }
            }

        """
        endpoint = 'player'
        if not signatureTimestamp:
            signatureTimestamp = get_datestamp() - 1

        params = {
            "playbackContext": {
                "contentPlaybackContext": {
                    "signatureTimestamp": signatureTimestamp
                }
            },
            "video_id": videoId
        }
        response = self._send_request(endpoint, params)
        keys = ['videoDetails', 'playabilityStatus', 'streamingData', 'microformat']
        for k in list(response.keys()):
            if k not in keys:
                del response[k]
        return response

    def get_lyrics(self, browseId: str) -> Dict:
        """
        Returns lyrics of a song or video.

        :param browseId: Lyrics browse id obtained from `get_watch_playlist`
        :return: Dictionary with song lyrics.

        Example::

            {
                "lyrics": "Today is gonna be the day\\nThat they're gonna throw it back to you\\n",
                "source": "Source: LyricFind"
            }

        """
        lyrics = {}
        if not browseId:
            raise Exception("Invalid browseId provided. This song might not have lyrics.")

        response = self._send_request('browse', {'browseId': browseId})
        lyrics['lyrics'] = nav(response, ['contents'] + SECTION_LIST_ITEM
                               + ['musicDescriptionShelfRenderer'] + DESCRIPTION, True)
        lyrics['source'] = nav(response, ['contents'] + SECTION_LIST_ITEM
                               + ['musicDescriptionShelfRenderer', 'footer'] + RUN_TEXT, True)

        return lyrics

    def get_mood_categories(self) -> Dict:
        """
        Fetch "Moods & Genres" categories from YouTube Music.

        :return: Dictionary of sections and categories.

        Example::

            {
                'For you': [
                    {
                        'params': 'ggMPOg1uX1ZwN0pHT2NBT1Fk',
                        'title': '1980s'
                    },
                    {
                        'params': 'ggMPOg1uXzZQbDB5eThLRTQ3',
                        'title': 'Feel Good'
                    },
                    ...
                ],
                'Genres': [
                    {
                        'params': 'ggMPOg1uXzVLbmZnaWI4STNs',
                        'title': 'Dance & Electronic'
                    },
                    {
                        'params': 'ggMPOg1uX3NjZllsNGVEMkZo',
                        'title': 'Decades'
                    },
                    ...
                ],
                'Moods & moments': [
                    {
                        'params': 'ggMPOg1uXzVuc0dnZlhpV3Ba',
                        'title': 'Chill'
                    },
                    {
                        'params': 'ggMPOg1uX2ozUHlwbWM3ajNq',
                        'title': 'Commute'
                    },
                    ...
                ],
            }

        """
        sections = {}
        response = self._send_request('browse', {'browseId': 'FEmusic_moods_and_genres'})
        for section in nav(response, SINGLE_COLUMN_TAB + SECTION_LIST):
            title = nav(section, GRID + ['header', 'gridHeaderRenderer'] + TITLE_TEXT)
            sections[title] = []
            for category in nav(section, GRID_ITEMS):
                sections[title].append({
                    "title": nav(category, CATEGORY_TITLE),
                    "params": nav(category, CATEGORY_PARAMS)
                })

        return sections

    def get_mood_playlists(self, params: str) -> List[Dict]:
        """
        Retrieve a list of playlists for a given "Moods & Genres" category.

        :param params: params obtained by :py:func:`get_mood_categories`
        :return: List of playlists in the format of :py:func:`get_library_playlists`

        """
        playlists = []
        response = self._send_request('browse', {
            'browseId': 'FEmusic_moods_and_genres_category',
            'params': params
        })
        for section in nav(response, SINGLE_COLUMN_TAB + SECTION_LIST):
            path = []
            if 'gridRenderer' in section:
                path = GRID_ITEMS
            elif 'musicCarouselShelfRenderer' in section:
                path = ['musicCarouselShelfRenderer', 'contents']
            elif 'musicImmersiveCarouselShelfRenderer' in section:
                path = ['musicImmersiveCarouselShelfRenderer', 'contents']
            if len(path):
                results = nav(section, path)
                playlists += parse_content_list(results, parse_playlist)

        return playlists

    def get_basejs_url(self):
        """
        Extract the URL for the `base.js` script from YouTube Music.

        :return: URL to `base.js`
        """
        response = self._send_get_request(url=YTM_DOMAIN)
        match = re.search(r'jsUrl"\s*:\s*"([^"]+)"', response)
        if match is None:
            raise Exception("Could not identify the URL for base.js player.")

        return YTM_DOMAIN + match.group(1)

    def get_signatureTimestamp(self, url: str = None) -> int:
        """
        Fetch the `base.js` script from YouTube Music and parse out the
        `signatureTimestamp` for use with :py:func:`get_song`.

        :param url: Optional. Provide the URL of the `base.js` script. If this
            isn't specified a call will be made to :py:func:`get_basejs_url`.
        :return: `signatureTimestamp` string
        """
        if url is None:
            url = self.get_basejs_url()
        response = self._send_get_request(url=url)
        match = re.search(r"signatureTimestamp[:=](\d+)", response)
        if match is None:
            raise Exception("Unable to identify the signatureTimestamp.")

        return int(match.group(1))
