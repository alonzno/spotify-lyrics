#!/usr/local/bin/python3

import sys
import re
import os
import urllib.request
import json

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from bs4 import BeautifulSoup

# TODO: REMOVE THESE LINES, BIG SECURITY VULNERABILITY
os.environ["SPOTIPY_CLIENT_ID"] = "e43b96ffdef54e2a8f6aab6b0baa5483"
os.environ["SPOTIPY_CLIENT_SECRET"] = "61c58e9e13174cd58a7f27e7d50e4f4c"

'''
birdy_uri = 'spotify:artist:2WX2uTcsvV5OnS0inACecP'
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

results = spotify.artist_albums(birdy_uri, album_type='album')
albums = results['items']
while results['next']:
    results = spotify.next(results)
    albums.extend(results['items'])

for album in albums:
    print(album['name'])
print("\n\n\n\n")
'''


username = "alonzoa-us"
client_id = "e43b96ffdef54e2a8f6aab6b0baa5483"
client_secret = "61c58e9e13174cd58a7f27e7d50e4f4c"
redirect_uri = "http://127.0.0.1/callback"


scope = 'user-read-currently-playing'
# scope = 'user-read-playback-state'
# works as well

token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

spotify = spotipy.Spotify(auth=token)
current_track_dict = spotify.current_user_playing_track()

current_track_name = current_track_dict['item']['name']
current_artist = current_track_dict['item']['artists'][0]['name']


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
        return "Exception occurred \n" +str(e)

print(get_lyrics(current_artist, current_track_name))