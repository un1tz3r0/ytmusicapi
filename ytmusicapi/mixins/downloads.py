import sys, os
from PIL import Image
from io import BytesIO

#sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ytmusicapi.parsers.utils import *
#import ytmusicapi
import pytube
import re
import requests
from urllib.parse import parse_qs, urljoin
import json

try:
	import blessings
	clear_eol = blessings.Terminal().clear_eol
except ImportError as err:
	clear_eol = "\x1b[K"

def sanitize(s):
	return "".join(re.split("[^a-zA-Z 0-9_\\(\\)\\[\\]\\:\\'\\\"\\@\\!\\#\\$\\%\\&\\=\\+\\,\\.\\<\\>\\;\\|\\{\\}-]",s)).strip()


class DownloadMixin:

		''' Mixin for ytmusicapi.YTMusic class that uses some parts of pytube to download streams
		at highest available quality by bypassing the signatureCipher obfuscation usually decoded
		in the browser by javascript which is generated for each request that scrambles it  and batch 
		artist, album, track and playlist download. YTMusic class. Some examples of usage are given at the
		end of the module after the rest of the class definition. '''

		def get_streaming_data_decrypted(self, videoId: str) -> dict:

				''' This is based on the YTMusic.get_streaming_data() method but it makes use of pytube to
				decode the signatureCipher obfuscation that "protects" the higher quality adaptiveFormat
				stream URLs from being enjoyed by "bots". Robots deserve access to teh same high-fidelity
				listening experience that we humans take for granted every time we leave auto-play going
				on the tv and then pass out sitting up on the couch, phone in hand, shoes still on, sleep-
				shopping on Amazon. '''

				# ok, we have a videoId, which we need to get a url for the best quality stream for.
				# start by fetching /get_video_info? which should have a watch URL in there somewhere...

				endpoint = "https://www.youtube.com/get_video_info"
				params = {"video_id": videoId, "hl": self.language, "el": "detailpage",
									"c": "WEB_REMIX", "cver": "0.1"}
				response = requests.get(endpoint, params, headers=self.headers, proxies=self.proxies)
				text = parse_qs(response.text)
				if 'player_response' not in text:
						# return text # huh?
						raise Exception('This video is not playable (no player_response key in /get_video_info? response)')

				player_response = json.loads(text['player_response'][0])
				if 'streamingData' not in player_response:
						raise Exception('This video is not playable (no streamingData key in player_response key of /get_video_info? response)')

				watch_url = player_response['microformat']['microformatDataRenderer']['urlCanonical'] # this seems like it will probably break easily... maybe fall back to a recursive search for a watch url anywhere in the JSON? or something?

				# get the watch page's HTML, which we need to get the base.js URL that determines how
				# pytube unscrambles the signatureCipher

				watch_response = requests.get(watch_url, #params,
																			headers=self.headers, proxies=self.proxies)
				watch_html = watch_response.text

				# this is where pytube comes in... given the watch page HTML, it extracts for us the URL of
				# the base.js for the video player, which is where the signatureCipher is descrambled by a
				# variable algorithm coded in minified, obfuscated javascript. thankfully, the task of
				# extracting from the javascript the steps needed to properly unscramble the signatureCipher
				# is also handled by pytube.

				player_js_url = pytube.extract.get_ytplayer_js(watch_html)
				player_js_response = requests.get(urljoin(watch_url, player_js_url), params, headers=self.headers, proxies=self.proxies)
				player_js = player_js_response.text

				cipher = pytube.cipher.Cipher(js = player_js)

				# okay, now we collect all the streams available and apply the cipher to any that have signed
				# URLs. this is where we would also handle DASH manifests... i think? TODO, fo' sho'.

				allformats = []

				sdata = player_response['streamingData']
				for formatsKey in ['formats', 'adaptiveFormats']:
					if formatsKey in sdata.keys():
						for fmt in sdata[formatsKey]:
							if 'signatureCipher' in fmt.keys():
								fmtsigcipherq = parse_qs(fmt['signatureCipher'])
								sig = cipher.get_signature(fmtsigcipherq['s'][0])
								url = fmtsigcipherq['url'][0] + '&' + fmtsigcipherq['sp'][0] + '=' + sig
								fmt['url'] = url
							if not 'url' in fmt.keys():
								print(f"[warn] streamingData contains format with itag {fmt['itag']} without a url key in get_streaming_data_decrypted({repr(videoId)}):\n\n{repr(fmt)}\n")
								continue
							allformats.append(fmt)

				return (sdata, allformats)


		def download_song(self, video_id: str, dest_dir: str, chunk_size: int = 1024*1024,
											skip_existing = True, skip_metadata_existing = False, keep_incomplete = False, title_only_filename = False,
											song_info = None, album_info = None, artist_info = None, playlist = None):
				''' download song with given video_id to dest_dir, in chunks of chunk_size, naming and tagging the downloaded
				file with metadata from album_info, artist_info, song_info, playlist, if supplied. the flag keep_incomplete
				will prevent the removal of partially downloaded files when an exception occurs which interrupts a download.
				when the title_only_filename flag is false, the downloaded files will be named using the following template:
				
				  '<Artist> - <Album> - <Song> [<videoId>].mp4'

				this makes sense if you are downloading a playlist or compilation maybe, or your likes or history and the 
				files mostly have unique or varying artist and album values. when the title_only_filename flag is true, 
				however, then the album and artist parts are omitted, so the files will be named like:
				
					'<Song> [<videoId>].mp4'

				which is more appropriate when called from i.e. the download_artist_albums() method, which creates subdirs for
				the artist and each album within that to download the tracks from each album into.'''
				
				song = self.get_song(video_id)
				if song_info == None:
					song_info = song

				artists = None
				if 'artists' in song.keys():
						nonemptyuniqueartists = list(set([artist for artist in song['artists'] if len(artist) > 0]))
						if len(nonemptyuniqueartists) > 0:
								artists = ", ".join(list(set(song['artists'])))

				if 'title' in song.keys():
						title = song['title']
				else:
						title = None

				if title != None and artists != None and not title_only_filename:
						filename = artists + " - " + title + " [" + song['videoId'] + "]"
				elif title != None:
						filename = title + " [" + song['videoId'] + "]"
				else:
						filename = f"[{song['videoId']}]"

				# pick from available streams one that is audio-only with the highest average bitrate, hence highest objective quality
				try:
					sdata, fmts = self.get_streaming_data_decrypted(song['videoId'])
					audioonlyformats = [fmt for fmt in fmts if fmt['mimeType'].startswith('audio')]
					if len(audioonlyformats) > 0:
						bestfmt = list(sorted([(fmt['averageBitrate'], fmt) for fmt in fmts if fmt['mimeType'].startswith('audio')]))[-1][1]
					else:
						bestfmt = list(sorted([(fmt['averageBitrate'], fmt) for fmt in fmts]))[-1][1]
				except Exception as err:
					raise RuntimeError("Error selecting suitable streaming format: {err}")

				fileext = bestfmt['mimeType'].split("/")[1].split(";")[0] # use sub-type from mimetype as file extension
				fullfilename = dest_dir + "/" + sanitize(filename) + "." + fileext

				if os.path.exists(fullfilename) and skip_existing:
					# file exists and we shouldn't overwrite it...
					print(f"Skipping download, file exists: {repr(fullfilename)}")
					if skip_metadata_existing:
						return False
				else:
					# file does not exist... download it
					print(f"Downloading videoId {repr(song['videoId'])} to file {repr(fullfilename)}...")
					response = requests.get(bestfmt['url'], stream=True, headers=self.headers, proxies=self.proxies)
					if 'content-length' in [k.lower() for k in response.headers.keys()]:
						totalbytes = int([val for key,val in response.headers.items() if key.lower() == 'content-length'][0])
					started = False
					wrotebytes = 0
					complete = False
					try:
							with open(fullfilename, "wb") as fout:
									started = True
									for chunk in response.iter_content(chunk_size=chunk_size):
											fout.write(chunk)
											wrotebytes = wrotebytes + len(chunk)
											print(f"Downloaded {wrotebytes//1024} kbytes...{clear_eol}\r", end="")
											sys.stdout.flush()
									complete = True
									print(f"Downloaded {wrotebytes//1024} kbytes total.{clear_eol}\n")
									sys.stdout.flush()
					finally:
							if started and not complete:
									if not keep_incomplete:
											print(f"Cleaning up partially downloaded file {repr(fullfilename)}...")
											os.remove(fullfilename)
									return False
				#print(f"Adding tags to downloaded file {repr(fullfilename)}...")
				self.add_tags(fullfilename, song_info, artist_info, album_info, playlist)


		def download_playlist(self, playlist, dest_dir = "~/Music",
													#limit_duration = 25*60, no_uploaded = True,
													skip_existing = True, skip_metadata_existing = False, title_only_filename = False,
													artist_info = None, album_info = None):
				dest_dir = os.path.expanduser(dest_dir)

				''' playlist may be specified in a few ways:

					1. a string, interpreted as a playlist id, in which case we fetch the playlist using get_playlist
					2. return value of get_playlist() etc. (dict containing 'tracks' key with a list of dicts with 'videoId' keys)
					3. list of dicts with videoId's
					4. list of videoId strings

					if given the result of a call to, e.g. get_playlist() or get_liked_songs(), the songs we
					want are in a list under the 'tracks' key, assume we were passed either a list
					of things that is directly enumerable and the elements of which each have a 'videoId',
					for instance the dict returned by get_playlist() or get_liked_songs() etc.

					skip_existing and skip_metadata_existing are passed to download_song(), along with artist_info and album_info,
					which are needed to write tag metadata once the download is complete.
				'''

				playlist_items = playlist

				if isinstance(playlist_items, (str, bytes)):
					# if playlist is a string, assume it is a playlist id and download the playlist
					playlist_items = self.get_playlist(playlist_items)
				
				if hasattr(playlist_items, 'keys') and 'tracks' in playlist_items.keys():
					# if playlist is not string-like but is dict-like (or at least, has a keys() method ;) and
					# has a key 'tracks', assume it is a playlist data structure as returned by get_playlist()
					playlist_items = playlist_items['tracks']

				def parseDuration(s):
						fields = s.split(":")
						if len(fields) < 2:
								return int(fields[0])
						elif len(fields) < 3:
								return int(fields[0]) + int(fields[1]) * 60
						else:
								return int(fields[-3])*60*60 + int(fields[-2])*60 + int(fields[-1])

				for listindex, listitem in enumerate(list(playlist_items)):
						if (not 'videoId' in listitem.keys()) or (listitem['videoId'] == None):
								print(f"!!! Playlist item at index {listindex}/{len(playlist_items)} does not have a videoId!")
								#raise KeyError("item in playlist_items does not have a videoId!")
								continue
						
						#if not skip_existing or not skip_metadata_existing or (not check_video_id(listitem['videoId'], dest_dir)) and ((not 'duration' in listitem.keys()) or (parseDuration(listitem['duration']) < 25*60)):
						try:
								self.download_song(listitem['videoId'], dest_dir,
									skip_existing=skip_existing, skip_metadata_existing=skip_metadata_existing, title_only_filename=title_only_filename,
									song_info = listitem, album_info = album_info, artist_info = artist_info, playlist = playlist_items)
						except Exception as err:
								print(f"\nException caught while trying to download videoId {listitem['videoId']}:\n\t-> {err}\n")
								import traceback
								traceback.print_exc()
						#else:
						#		print(f"Skipping videoId {listitem['videoId']} at playlist index {listindex}/{len(playlist_items)} because the file already exists!")


		def download_thumbnails(self, thumbnails, destdir=None):
				for thumbindex, thumbnail in enumerate(thumbnails):
						print(f"Downloading thumbnail {thumbindex}/{len(thumbnails)}...{clear_eol}\r", end="")
						sys.stdout.flush()
						thumbresp = requests.get(thumbnail['url'], headers=self.headers)
						thumbtype = thumbresp.headers['Content-Type'].split('/')[1].split(';')[0]
						if len(thumbnails) == 1:
								thumbname = f"thumbnail.{thumbtype}"
						else:
								thumbname = f"thumbnail{thumbindex+1}.{thumbtype}"
						if destdir == None:
							with BytesIO(thumbresp.content) as fin:
								im = Image.open(fin)
								im.load()
								print(f"{clear_eol}\r", end="")
								sys.stdout.flush()
								yield (thumbname, thumbtype, thumbresp.content, im)
						if not (destdir == None):
							with open(os.path.join(destdir, thumbname), "wb") as fout:
								print(f"Writing {len(thumbresp.content)/1024:.1f}kB thumbnail to {repr(thumbname)}...{clear_eol}\r", end="")
								sys.stdout.flush()
								fout.write(thumbresp.content)
								print(f"{clear_eol}\r", end="")
								sys.stdout.flush()

		def add_tags(self, filename, song=None, artist=None, album=None, playlist=None):
				if song != None:
						from mutagen.mp4 import MP4, MP4Cover
						video = MP4(filename)

						print(f"Adding metadata to file {repr(filename)}...{clear_eol}\r", end="")
						sys.stdout.flush()

						# download thumbnails...
						thumbs = []
						if song != None and 'thumbnail' in song.keys():
							thumbs = song['thumbnail']
						elif song != None and 'thumbnails' in song.keys():
							thumbs = song['thumbnails']
						if hasattr(thumbs, 'keys') and 'thumbnails' in thumbs.keys():
							thumbs = thumbs['thumbnails']
						if len(thumbs) > 0:
							coverart = []
							for tname, ttype, traw, timage in self.download_thumbnails(thumbs, None):
									if ttype == "jpeg":
											coverart.append((timage.width * timage.height, traw))
							video["covr"] = [MP4Cover(traw, imageformat=MP4Cover.FORMAT_JPEG) for pixels, traw in sorted(coverart, key=lambda elem: -elem[0])]

						# set track info...
						tagartist = None
						if not (artist == None):
							tagartist = artist
						tagalbum = None
						tagalbumartist = None
						tagalbumtotal = None
						if not (album == None):
							if 'artists' in album.keys():
								tagalbumartist = album['artists']
							tagalbum = album['title']
							if 'tracks' in album['tracks']:
								tagalbumtotal = len(album['tracks'])
						if not (playlist == None) and tagalbumtotal == None:
							tagalbumtotal = len(playlist['tracks']) if hasattr(playlist, 'keys') and 'tracks' in playlist.keys() else len(playlist)
						tagsong = None
						tagindex = None
						if not (song == None):
							tagsong = song['title']
							if tagartist == None and 'artists' in song.keys():
								tagartist = song['artists']
							if tagalbum == None and 'album' in song.keys():
								tagalbum = song['album']
							if 'index' in song.keys():
								tagindex = song['index']

						# fix for uploaded track artist, comes back as a dict with 'privately_owned' key and 'name' key, which is what we want
						if tagartist != None and hasattr(tagartist, 'keys') and 'name' in tagartist.keys():
							tagartist = tagartist['name']

						wrotetags = []

						def maybetag(tag, val):
							if not(val == None):
								video[tag] = [str(val)] if not isseq(val) else val
								wrotetags.append(tag)

						maybetag('artist', tagartist)
						maybetag('album', tagalbum)
						maybetag('albumartist', tagalbumartist)
						maybetag('tracknumber', tagindex)
						maybetag('tracktotal', tagalbumtotal)

						video.save()
						print(f"Wrote metadata to file {repr(filename)}: {'/'.join(wrotetags)} tags and {len(coverart)} thumbnails")


		def download_artist_albums(self, artistName, musicDir, artistId=None, skip_existing=True, skip_metadata_existing=False):
				''' searches for artist by artistName, using the top result, or using the given artistId (browseId in search
				result artist data) if it is given. create directory in musicDir for artist artistName, and subdirectories for 
				each album by that artist, then downloads each track of the albums. skip_existing controls whether existing 
				files are re-downloaded and overwritten or not, and skip_metadata_existing controls whether tags are written to 
				files even if they exist and were skipped for download due to skip_existing. the thumbnail artwork for the 
				artist page and for each album cover are also downloaded to jpeg files named thumbnailN.jpeg under those 
				directories. '''
				
				# search artist and get first result
				if artistId != None:
					artistBrowseId = artistId
				else:
					artistBrowseId = self.search(artistName, 'artists')[0]['browseId']
				artistInfo = self.get_artist(artistBrowseId)
				print(f"Found artist {repr(artistInfo['name'])}!")
				# find and/or create a directory for the artist in our music collection
				artistDir = os.path.join(os.path.expanduser(musicDir), artistInfo['name'])
				if not os.path.exists(artistDir):
						print(f"Creating artist directory {repr(artistDir)}...")
						os.mkdir(artistDir)
				else:
						print(f"Directory {repr(artistDir)} already exists!")
				# grab thumbnail from artist page
				print(f"Saving thumbnail of artist to {repr(artistDir)}...")
				self.download_thumbnails(artistInfo['thumbnails'], artistDir)
				# sometimes get_artist_album_info does not have a params, in which case use the albums list in artistInfo['albums']['results'] directly
				if 'params' in artistInfo['albums'].keys() and artistInfo['albums']['params'] != None:
					albums = self.get_artist_albums(artistInfo['channelId'], params = artistInfo['albums']['params'])
				else:
					albums = artistInfo['albums']['results']
				# loop through albums
				for albumItem in albums:
						# query album details
						albumInfo = self.get_album(albumItem['browseId'])
						albumName = albumInfo['title']
						print(f"Downloading album {repr(albumName)}...")
						# ensure that album directory exists
						albumDir = os.path.join(artistDir, sanitize(albumName))
						if not os.path.exists(albumDir):
								print(f"Creating album directory {repr(albumDir)}...")
								os.mkdir(albumDir)
						else:
								print(f"Directory {repr(albumDir)} already exists!")
						# grab thumbnail from artist page
						print(f"Saving thumbnail of album to {repr(albumDir)}...")
						self.download_thumbnails(albumInfo['thumbnails'], albumDir)
						# download the tracks
						self.download_playlist(albumInfo['tracks'], dest_dir=albumDir,
																		skip_existing=skip_existing, skip_metadata_existing=skip_metadata_existing,
																		album_info = albumInfo, artist_info=artistInfo, title_only_filename=True)


'''
class YTMusic(ytmusicapi.YTMusic, DownloaderMixin):
		pass

if __name__ == "__main__":
	import sys
	if len(sys.argv) != 2:
		print("Must specify artist name as only argument!")
		sys.exit(1)
	ytm = YTMusic("/home/owner/headers_auth.json")
	ytm.download_artist_albums(sys.argv[-1], "~/Music")
	#ytm.download_artist_albums("Max Graef", "~/Music")
	#ytm.download_artist_albums("Glenn Astro", "~/Music")
	#ytm.download_artist_albums("Emune", "~/Music")
	#ytm.download_artist_albums("Tame Impala", "~/Music")
	#ytm.download_artist_albums("Floating Points", "~/Music")

if __name__ == "__main__":
	# see https://ytmusicapi.readthedocs.org/ for explanation of how to use an authenticated watch page
	# request in a signed-in browser and the browser devtools to set up headers_auth.json for
	# ytmusicapi

	# EXAMPLE - download the last 10 songs in your playback history

	history = ytm.download_playlist(ytm.get_history())

	# EXAMPLE - download the most recent 1000 songs you liked

	ytm.download_playlist(ytm.get_liked_songs(limit=1000))
'''
