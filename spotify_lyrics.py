import sys
import re
import os
import json
import time
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from bs4 import BeautifulSoup

'''
    BEGIN Class Declarations
'''
class OAuthRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        request_path = self.path
        self.server.url = request_path

class OAuthHTTPServer:
    def __init__(self, addr):
        self.server = HTTPServer(addr, OAuthRequestHandler)
        self.server.url = None

'''
    END Class Declarations
'''

'''
    BEGIN Function Declarations
'''
def prompt_for_user_token_mod(
    username,
    scope=None,
    client_id=None,
    client_secret=None,
    redirect_uri=None,
    cache_path=None,
    oauth_manager=None,
    show_dialog=False
):
    if not oauth_manager:
        if not client_id:
            client_id = os.getenv("SPOTIPY_CLIENT_ID")

        if not client_secret:
            client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

        if not redirect_uri:
            redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

        if not client_id:
            print(
                """
                You need to set your Spotify API credentials.
                You can do this by setting environment variables like so:
                export SPOTIPY_CLIENT_ID='your-spotify-client-id'
                export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
                export SPOTIPY_REDIRECT_URI='your-app-redirect-url'
                Get your credentials at
                    https://developer.spotify.com/my-applications
            """
            )
            raise spotipy.SpotifyException(550, -1, "no credentials set")

        cache_path = cache_path or ".cache-" + username

    sp_oauth = oauth_manager or spotipy.SpotifyOAuth(
        client_id,
        client_secret,
        redirect_uri,
        scope=scope,
        cache_path=cache_path,
        show_dialog=show_dialog
        )

    # try to get a valid token for this user, from the cache,
    # if not in the cache, the create a new (this will send
    # the user to a web page where they can authorize this app)

    token_info = sp_oauth.get_cached_token()

    if not token_info:

        server_address = ('', 8420)
        httpd = OAuthHTTPServer(server_address)

        import webbrowser

        webbrowser.open(sp_oauth.get_authorize_url())
        httpd.server.handle_request()


        if httpd.server.url:
            url = httpd.server.url

            code = sp_oauth.parse_response_code(url)
            token = sp_oauth.get_access_token(code, as_dict=False)
    else:
        return token_info["access_token"]

    # Auth'ed API request
    if token:
        return token
    else:
        return None

def get_az_lyrics(artist,song_title):
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
        lyrics = lyrics.replace('<br>','') \
            .replace('</br>','') \
            .replace('<br/>', '') \
            .replace('<i>', '') \
            .replace('</i>', '') \
            .replace('</div>','').strip()
        return lyrics
    except Exception as e:
        print("AZ Lyrics failed.\n" +str(e) + "\n")
        raise

def get_musixmatch_lyrics(artist, song_title):
    # Possibly transform inputs in other ways TODO
    artist = "-".join(artist.split())
    song_title = "-".join(song_title.split())

    url = "https://www.musixmatch.com/lyrics/%s/%s" % (artist, song_title)
    headers = {'User-Agent': 'Safari/537.3'}
    req = urllib.request.Request(url=url, headers=headers)

    #print(url)
    try:
        content = urllib.request.urlopen(req).read()
        soup = BeautifulSoup(content, 'html.parser')

        tags = soup.find_all('p', class_='mxm-lyrics__content')

        lyrics = ""
        for tag in tags:
            lyrics += tag.text

        """lyrics = str(soup)
        # # lyrics lies between up_partition and down_partition
        up_partition = '<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. -->'
        down_partition = '<!-- MxM banner -->'
        lyrics = lyrics.split(up_partition)[1]
        lyrics = lyrics.split(down_partition)[0]
        lyrics = lyrics.replace('<br>','') \
            .replace('</br>','') \
            .replace('<br/>', '') \
            .replace('<i>', '') \
            .replace('</i>', '') \
            .replace('</div>','').strip()"""
        return lyrics
    except Exception as e:
        print("Musixmatch failed.\n" +str(e) + "\n")
        raise

def get_token():
    cred_f = None
    cache_f = None

    try:
        cred_f = open(os.path.dirname(os.path.abspath(__file__)) + '/credentials.json')
        credentials = json.loads(cred_f.read())
        username = credentials['username']
        client_id = credentials['id']
        client_secret = credentials['secret']
        redirect_uri = credentials['redirect']
        scope = 'user-read-currently-playing'
        cache_path = os.path.dirname(os.path.abspath(__file__)) + '/.cache-alonzoa-us'


        try:
            cache_f = open(cache_path)
            data = json.loads(cache_f.read())
            if (data['expires_at'] > int(time.time())):
                return util.prompt_for_user_token(username,
                                                  scope,
                                                  client_id=client_id,
                                                  client_secret=client_secret,
                                                  redirect_uri=redirect_uri,
                                                  cache_path=cache_path)
            else:
                raise IOError
        except IOError:
            #TODO ADD server intercept req
            return prompt_for_user_token_mod(username,
                                             scope,
                                             client_id=client_id,
                                             client_secret=client_secret,
                                             redirect_uri=redirect_uri,
                                             cache_path=cache_path)
        finally:
            if cache_f:
                cache_f.close()
    except IOError:
        print('It appears you are lacking the credentials.json file.')
        print('No soup for you')
        quit()
    finally:
        if cred_f:
            cred_f.close()


'''
    END Fundtion Declarations
'''

'''
    BEGIN Main Method
'''

#TODO add args
try:
    token = get_token()

    spotify = spotipy.Spotify(auth=token)
    current_track_dict = spotify.current_user_playing_track()
    current_track_name = current_track_dict['item']['name']
    current_artist = current_track_dict['item']['artists'][0]['name']

    header = current_track_name + ' by ' + current_artist
    print('-'*len(header))
    print(header)
    print('-'*len(header)+'\n')

    try:
        try:
            print(get_az_lyrics(current_artist, current_track_name))
            exit()
        except Exception as e0:
            pass
        try:
            print(get_musixmatch_lyrics(current_artist, current_track_name))
            exit()
        except Exception as e1:
            raise
    except Exception as final:
        print("All fall backs failed")
except TypeError as e:
    print(e)
    print("You might not be listening to music right now, bluh")

'''
    END Main Method
'''
