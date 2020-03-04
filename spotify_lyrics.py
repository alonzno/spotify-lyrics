import sys
import re
import os
import json
import time
import urllib.request

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from bs4 import BeautifulSoup

'''
	BEGIN Function Declarations
'''
def get_lyrics(artist,song_title):
    artist = artist.lower()
    song_title = song_title.lower()
    # remove all except alphanumeric characters from artist and song_title
    artist = re.sub('[^A-Za-z0-9]+', "", artist)
    song_title = re.sub('[^A-Za-z0-9]+', "", song_title)
    if artist.startswith("the"):    # remove starting 'the' from artist e.g. the who -> who
        artist = artist[3:]
    url = "http://azlyrics.com/lyrics/"+artist+"/"+song_title+".html"
    
    try:
        content = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(content, 'html.parser')
        lyrics = str(soup)
        # lyrics lies between up_partition and down_partition
        up_partition = '<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. -->'
        down_partition = '<!-- MxM banner -->'
        lyrics = lyrics.split(up_partition)[1]
        lyrics = lyrics.split(down_partition)[0]
        lyrics = lyrics.replace('<br>','').replace('</br>','').replace('<br/>', '').replace('</div>','').strip()
        return lyrics
    except Exception as e:
        return "Woops, can't find that one.\n" +str(e)

def get_token():
	try:
		cred_f = open('credentials.json')
		credentials = json.loads(cred_f.read())
		username = credentials['username']
		client_id = credentials['id']
		client_secret = credentials['secret']
		redirect_uri = credentials['redirect']
		scope = 'user-read-currently-playing'

		try:
			cache_f = open('.cache-alonzoa-us')
			data = json.loads(cache_f.read())
			if (data['expires_at'] > int(time.time())):
				return util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
			else:
				raise IOError
		except IOError:
			#TODO ADD server intercept req
			return util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
		finally:
			cache_f.close()
	except IOError:
		print('It appears you are lacking the credentials.json file.')
		print('No soup for you')
	finally:
		cred_f.close()


'''
	END Fundtion Declarations
'''

'''
	BEGIN Main Method
'''

token = get_token()

spotify = spotipy.Spotify(auth=token)
current_track_dict = spotify.current_user_playing_track()
current_track_name = current_track_dict['item']['name']
current_artist = current_track_dict['item']['artists'][0]['name']

header = current_track_name + ' by ' + current_artist
print('-'*len(header))
print(header)
print('-'*len(header)+'\n')
print(get_lyrics(current_artist, current_track_name))
'''
	END Main Method
'''