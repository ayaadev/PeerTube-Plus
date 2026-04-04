import os
import sys
import requests
import json
# Could remove later
import traceback
import xbmcvfs
import threading
from urllib.parse import urlencode, parse_qsl

# Cache results
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

cache = StorageServer.StorageServer("PeerTube-Plus", 1)

import xbmcgui
import xbmcplugin
from xbmcaddon import Addon
from xbmcvfs import translatePath
from datetime import datetime
import time

import inputstreamhelper
PROTOCOL = 'hls'
MIME_TYPE = 'application/vnd.apple.mpegurl'

window = xbmcgui.Window(10000)

URL = sys.argv[0]
HANDLE = int(sys.argv[1])
ADDON_PATH = translatePath(Addon().getAddonInfo('path'))
ICONS_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'icons')
FANART_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'fanart')
ADDON_ID = 'plugin.video.peertube-plus'
USERDATA_PATH = xbmcvfs.translatePath(f'special://userdata/addon_data/{ADDON_ID}/')
#CUSTOM_INSTANCE = xbmcplugin.getSetting(HANDLE,"custom_instance")
CUSTOM_INSTANCE = Addon().getSetting('custom_instance')
window.setProperty("API", f"https://{CUSTOM_INSTANCE}/api/v1")
API = f"https://{CUSTOM_INSTANCE}/api/v1"

# Create a custom exception for use in the functions
class StopExecution(Exception):
    def __init__(self, message=None, data=None):
        self.message = message
        self.data = data
        super().__init__(message)

def get_url(**kwargs):
    return '{}?{}'.format(URL, urlencode(kwargs))

# Allow the user to login
def login(mode, token):
    # Check if the user is already logged in

    request = requests.get(f"{API}/oauth-clients/local")
    clientDetails = request.json()

    clientId = clientDetails["client_id"]
    clientSecret = clientDetails["client_secret"]

    dialog = xbmcgui.Dialog()

    # If the user is logging in for the first time, i.e. not refreshing with a token
    if mode == "password":
        username = dialog.input('Please enter your username')
        # We can't use the password input because it hashes the value
        password = dialog.input('Please enter your password', option=xbmcgui.ALPHANUM_HIDE_INPUT)

    url = f"{API}/users/token"

    if mode == "password":
        payload = {'client_id': clientId, 'client_secret': clientSecret, 'grant_type': 'password', 'username': username, 'password': password}
    else:
        payload = {'client_id': clientId, 'client_secret': clientSecret, 'grant_type': 'refresh_token', 'refresh_token': token}
    r = requests.post(url, payload)
    status = r.status_code
    credentials = r.json()

        
    # If the user's password is longer than 72 characters
    if status == 400:
        if credentials["code"] == "invalid_client":
            error = dialog.ok('Error logging in', "There was a mismatch between client details. Please try logging in again.")

        if credentials["code"] == "invalid_grant":
            error = dialog.ok('Error logging in', "Invalid credentials.")

        if "72 bytes" in credentials["detail"]:
            error = dialog.ok('Error logging in', "Due to PeerTube's API limitations, only passwords under 72 characters can be accepted. Please consider keeping your password under 72 characters. Sorry for the inconvenience.")

        return
    
    elif status == 401:
        if credentials["code"] == "missing_two_factor":
            twoFactorCode = dialog.input('Please enter your two factor authentication code.')
            headers = {"x-peertube-otp": twoFactorCode}
            r = requests.post(url, data=payload, headers=headers)
            status = r.status_code
            credentials = r.json()
            #error = dialog.ok('Error logging in', "Your account requires two factor authentication which is unsupported at this time. Sorry for the inconvenience.")

        elif credentials["code"] == "invalid_token":
            error = dialog.ok('Session expired', "Your session as expired. Please login again.")

            # The other try block handles a file not found error, so we don't need to check here
            with xbmcvfs.File(DATA_PATH, 'w') as file:
                # Read the data and load it to JSON
                content = file.read()
                data = json.loads(content)

                # Change the authenticated key to false
                data["authenticated"] = False
                
                # Save the file
                file.write(json.dumps(data, ensure_ascii=False, indent=4))

            return
        else:
            error = dialog.ok('Error logging in', "There was an unspecified authentication failure.")
            return
        
    access_token = credentials["access_token"]
    refresh_token = credentials["refresh_token"]

    credentialsFile = "credentials.json"
    dataFile = "data.json"
    if not xbmcvfs.exists(USERDATA_PATH):
        try:
            xbmcvfs.mkdirs(USERDATA_PATH)
        except:
            error = dialog.notification('Error', 'Could not create userdata directory to store credentials.', xbmcgui.NOTIFICATION_ERROR)
        
    CREDENTIALS_PATH = USERDATA_PATH + credentialsFile
    DATA_PATH = USERDATA_PATH + dataFile

    try:
        with xbmcvfs.File(CREDENTIALS_PATH, 'w') as file:
            file.write(json.dumps(credentials, ensure_ascii=False, indent=4))
        with xbmcvfs.File(DATA_PATH, 'w') as file:
            # Read the data and load it to JSON
            content = file.read()
            data = json.loads(content)

            # Change / add the authenticated key to true
            data["authenticated"] = True 
                
            # Save the file
            file.write(json.dumps(data, ensure_ascii=False, indent=4))

        # Return true to signify success
        return True, access_token
    # If the file doesn't exist
    except (json.JSONDecodeError, FileNotFoundError):
        # Open the file
        with xbmcvfs.File(DATA_PATH, 'w') as file:
            # Create the file and add authenticated = True
            data = {"authenticated": True}
            file.write(json.dumps(data, ensure_ascii=False, indent=4))
    # General catch statement
    except Exception:
        error = dialog.notification('Error', 'Could not write the credentials to file', xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()

# Logout
def logout():
    dialog = xbmcgui.Dialog()
    if not xbmcvfs.exists(USERDATA_PATH):
        error = dialog.notification('Error', 'Please login to continue this action.', xbmcgui.NOTIFICATION_ERROR)
        return

    CREDENTIALS_PATH = USERDATA_PATH + "credentials.json"
    DATA_PATH = USERDATA_PATH + "data.json"

    access_token = None
    
    try:

        # We could do a check here to see if the data says the user is authenticated, but that would duplicate code
        # If the user has managed to make it here, they are probably authenticated

        with xbmcvfs.File(CREDENTIALS_PATH) as file:
            content = file.read()
            data = json.loads(content)
            
            access_token = data["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}
        request = requests.post(f"{API}/users/revoke-token", headers=headers)

        if request.status_code == 200:
            notification = dialog.notification('Success', 'You have been logged out.')
            
            # Change the data file to be unauthenticated
            with xbmcvfs.File(DATA_PATH, 'w') as file:
                content = file.read()
                data = json.loads(content)

                data["authenticated"] = False
                
                file.write(json.dumps(data, ensure_ascii=False, indent=4))

            # Only delete the file if the credentials were revoked at the server.
            xbmcvfs.delete(CREDENTIALS_PATH)

        # If there was a server error, return it
        else:
            response = request.json()
            detail = response["detail"]
            code = response["code"]
            error = dialog.notification(f'HTTP Error {request.status_code}', f'Error message: {detail}. Code: {code}')
    
    except json.JSONDecodeError:
        # For some reason this often happens when logging out, but the error doesn't break anything so just pass
        pass

    except Exception as e:
        traceback.print_exc()
        error = dialog.notification('Error', f'An unexpected error occurred. Error message: {e}', xbmcgui.NOTIFICATION_ERROR)

# The selection menu of the addon
def menu():
    # If the user is back at the menu, set SEARCH_AGAIN to true so it prompts the user to search again
    # Must be string
    Addon().setSetting("search_again", "yes")

    # Check if the custom instance was set
    if not CUSTOM_INSTANCE or CUSTOM_INSTANCE == "" or CUSTOM_INSTANCE.startswith("http"):
        xbmcgui.Dialog().ok('Custom instance not specified', 'Please specify a PeerTube instance in the addon settings. It cannot start with "http". For example, write "instance.com" instead of "https://instance.com".')
        return

    xbmcplugin.setPluginCategory(HANDLE, 'Menu')
    xbmcplugin.setContent(HANDLE, 'movies')

    # Set default listing here, independent of if user is authenticated
    listing = []

    # Local Search
    localSearch = xbmcgui.ListItem(label="Search")
    localSearchURL = get_url(action='listing', mode='local_search')
    listing.append((localSearchURL, localSearch, True))
 
    # Global Search
    globalSearch = xbmcgui.ListItem(label="Global Search")
    globalSearchURL = get_url(action='listing', mode='global_search')
    listing.append((globalSearchURL, globalSearch, True))

    # All Videos
    allVideos = xbmcgui.ListItem(label="All Videos")
    allVideosURL = get_url(action='listing', mode='all_videos')
    listing.append((allVideosURL, allVideos, True))
    
    # Trending
    trending = xbmcgui.ListItem(label="Trending")
    trendingURL = get_url(action='listing', mode='trending')
    listing.append((trendingURL, trending, True))

    # Local Videos
    localVideos = xbmcgui.ListItem(label="Local Videos")
    localVideosURL = get_url(action='listing', mode='local_videos')
    listing.append((localVideosURL, localVideos, True))

    DATA_PATH = USERDATA_PATH + "data.json"
    try:
        with xbmcvfs.File(DATA_PATH) as file:
            content = file.read()
            data = json.loads(content)

            if data["authenticated"] == True:
                is_folder = True
                
                subscriptions = xbmcgui.ListItem(label="Subscriptions")
                subscriptionsURL = get_url(action='listing', mode='subscriptions')
                
                # Append subscriptions to listing variable
                listing.append((subscriptionsURL, subscriptions, is_folder))

                logout = xbmcgui.ListItem(label="Logout")
                logoutURL = get_url(action='logout')

                # Append logout to listing variable
                listing.append((logoutURL, logout, is_folder))

                #xbmcplugin.addDirectoryItems(HANDLE, [(subscriptionsURL, subscriptions, is_folder), (logoutURL, logout, is_folder)])
            else:
                is_folder = True
                
                # LOGIN

                login = xbmcgui.ListItem(label="Login")
                loginURL = get_url(action='login', mode='password', token='0')
                
                listing.append((loginURL, login, is_folder))
               
    except:
        # If there's an exception here, it likely means the file doesn't exist so login
        is_folder = True

        # LOGIN

        login = xbmcgui.ListItem(label="Login")
        loginURL = get_url(action='login', mode='password', token='0')
        
        listing.append((loginURL, login, is_folder))

    # Batch add once
    xbmcplugin.addDirectoryItems(HANDLE, listing, len(listing))

    #xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)

def get_token():
    dialog = xbmcgui.Dialog()
    if not xbmcvfs.exists(USERDATA_PATH):
        error = dialog.notification('Error', 'Please login to continue this action.', xbmcgui.NOTIFICATION_ERROR)
        return False
    
    CREDENTIALS_PATH = USERDATA_PATH + "credentials.json"
    DATA_PATH = USERDATA_PATH + "data.json"

    try:
        credentials = {}
        data = {}

        with xbmcvfs.File(DATA_PATH) as file:
            content = file.read()
            data = json.loads(content)
            
            # We need to check if the program has invalidated the credentials, so check the authentication status
            if not data["authenticated"]:
                error = dialog.notification('Error', 'Please login to continue this action.', xbmcgui.NOTIFICATION_ERROR)
                return False
        
        # Since the user should be authenticated, get the credentials
        with xbmcvfs.File(CREDENTIALS_PATH) as file:
            content = file.read()
            credentials = json.loads(content)
        
        access_token = credentials["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}
        request = requests.get(f"{API}/users/me", headers=headers)
    
        if request.status_code == 401:
            
            # Try to get a new access token with the refresh token
            refresh_token = credentials["refresh_token"]
            successful, token = login("token", refresh_token)

            if successful == True:
                return token
            
            # Return False if it wasn't successful
            return False
        elif request.status_code == 200:
            return access_token
        else:
            error = dialog.notification('Error', 'An unexpected error occurred while performing an authenticated action.', xbmcgui.NOTIFICATION_ERROR)
            return False
    except Exception as e:
        error = dialog.notification('Error', f'An unexpected error occurred while performing an authenticated action. Error message: {e}', xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()
        return False
         
            
# Must take instance_url to invalidate cache if the user changes their instance
def get_videos(instance_url, searchQuery, mode, page):
    
    start = page * 15
    queryParams = f"?start={start}&hasHLSFiles=true"

    # Only try to get the access token if the user is performing an authenticated request
    if mode == "subscriptions":
        # Get the access key
        access_token = get_token()

        # If there was an error, also cancel this function
        if not access_token:
            return False

        headers = {"Authorization": f"Bearer {access_token}"}
        request = requests.get(f"{API}/users/me/subscriptions/videos{queryParams}", headers=headers)
    elif mode == "local_videos":
        request = requests.get(f"{API}/videos{queryParams}&isLocal=true")
    elif mode == "trending":
        request = requests.get(f"{API}/videos{queryParams}&sort=-trending")
    elif mode == "local_search":
        print("Activated local search")
        request = requests.get(f"{API}/search/videos{queryParams}&search={searchQuery}")
    elif mode == "global_search":
        print("Activated global search")
        request = requests.get(f"{API}/search/videos{queryParams}&search={searchQuery}&searchTarget=search-index")
    else:
        print("Activated default request")
        # Default request
        request = requests.get(f"{API}/videos{queryParams}")
    
    r = request.json()
    
    # If there were no results
    if "data" not in r or not r["data"]:
        error = xbmcgui.Dialog().notification('Error', 'No results were found. Please try another feed.', xbmcgui.NOTIFICATION_ERROR)
        raise StopExecution("No results were found", data=[])

    # Return the data
    return r["data"]

def generate_item_info(self, name, url, is_folder=True, thumbnail="",
                        aired="", duration=0, plot="",):
    return {
        "name": name,
        "url": url,
        "is_folder": is_folder,
        "art": {
            "thumb": thumbnail,
        },
        "info": {
            "aired": aired,
            "duration": duration,
            "plot": plot,
            "title": name
        }
    }

def list_videos(mode, page):
    dialog = xbmcgui.Dialog()
       
    SEARCH_AGAIN = Addon().getSetting("search_again")

    if mode == "local_search" or mode == "global_search":
        # Must separate this in an indent so it doesn't activate the else block below
        if SEARCH_AGAIN == "yes":
            Addon().setSetting("search_again", "no")
            searchQuery = dialog.input('Search')
            
            # Set last search
            Addon().setSetting("last_search", searchQuery)

            # If the user cancelled the search
            if searchQuery == "":
                # Go back to menu
                menu()
                return
        else:
            # Get last search if we're not searching again
            searchQuery = Addon().getSetting("last_search")

    else:
        searchQuery = ""

    # Cache results for 1 hour
    # Must pass search here so it gets new data if the user searches for anything new
    # Must pass CUSTOM_INSTANCE so it gets new data if the user changed their instance
    try:
        genre_info = cache.cacheFunction(get_videos, CUSTOM_INSTANCE, searchQuery, mode, page)
        #genre_info = get_videos(CUSTOM_INSTANCE, searchQuery, mode, page)
    except StopExecution:
        return

    # If there was an error upstream
    # This should be covered by the except, though
    if not genre_info:
        return False

    xbmcplugin.setPluginCategory(HANDLE, 'Videos')
    xbmcplugin.setContent(HANDLE, 'movies')
    videos = genre_info

    # List of elements to add to the screen
    listing = []

    for video in videos:
        print(f'Title of video being processed: {video["name"]}')
        list_item = xbmcgui.ListItem(label=video['name'])
        info_tag = list_item.getVideoInfoTag()

        channelName = video["channel"]["displayName"]
        actor = xbmc.Actor(name=channelName)

        # If there is no avatar
        try:
            channelAvatar = video["channel"]["avatars"][1]["fileUrl"]
            actor = xbmc.Actor(name=channelName, thumbnail=channelAvatar)
        except IndexError:
            pass

        date = datetime.fromisoformat(video["publishedAt"][:-1])
        publishedDate = date.strftime("%Y-%m-%d")
        publishedYear = date.year

        views = video["views"]
        likes = video["likes"]
        
        try:
            # Must pass CUSTOM_INSTANCE so it gets new data if the user changed their instance
            # Pass mode here so it can know when it needs to check if results are local or not
            # Pass host here, since the program only knows here
            videoURL, description, tags = cache.cacheFunction(get_video, CUSTOM_INSTANCE, mode, video["account"]["host"], video["id"])
            #videoURL, description, tags = get_video(CUSTOM_INSTANCE, mode, video["account"]["host"], video["id"])
        except StopExecution as e:
            # Manually clear the get_videos cache so the error doesn't get cached in the results
            cache.delete("get_videos")
            
            # If the error message has specific details (message = "Error getting video") then return a more detailed response
            if e.message == "Error getting video":
                errorMessage = e.data[0]
                videoTitle = video["name"]
                videoURL = e.data[1]
                error = dialog.ok("Error getting video", f"One or more videos in the feed refused to be displayed. This is an issue with the video or your PeerTube instance, and not an issue with this addon. Please try another feed, change the instance in the addon settings, or contact your PeerTube instance's administrators.\n\nError message: {errorMessage}\nVideo Title: {videoTitle}\nVideo URL: {videoURL}")
            if e.message == "No streamingPlaylists":
                # Skip the bad global search result
                continue
            else:
                error = dialog.ok("An unexpected error occurred", f"Error message: {e.data[0]}")
            return
        
        # NOTE
        # The second assignment is mostly unnecessary - change in the future

        video["videoURL"], video["description"], video["tags"] = videoURL, description, tags
        
        # ListItem.setInfo is partialy deprecated so we are using the InfoTag as well to future-proof things.
        info_tag.setCast([actor])
        info_tag.setDirectors([channelName])
        info_tag.setPlot(description)
        if tags: info_tag.setTags(tags)
        info_tag.setTitle(video["name"])
        if video["category"]["label"]: info_tag.setGenres([video["category"]["label"]])
        info_tag.setDuration(video["duration"])
        info_tag.setPremiered(publishedDate)
        info_tag.setVotes(likes)
        info_tag.setYear(publishedYear)
        info_tag.setTagLine(f"[COLOR green]Views: {views}[/COLOR]\n[COLOR red]Likes: {likes}[/COLOR]")
        
        # This is deprecated
        list_item.setInfo('video', {
                              'director': channelName,
                              'plot': description,
                              'tag': tags if tags else "",
                              'title': video["name"],
                              'genre': video["category"]["label"],
                              'duration': video["duration"],
                              'premiered': publishedDate,
                              'votes': f"{likes} likes"
                        })
        
        list_item.setProperty('IsPlayable', 'true')
        image = f"https://{CUSTOM_INSTANCE}{video['previewPath']}"
        list_item.setArt({ 'icon': image, 'fanart': image, 'thumb': image, 'poster': image})

        url = get_url(action='play', video=videoURL)
        is_folder = False
        listing.append((url, list_item, is_folder))

    
    # Do a preliminary check to see if there's most likely another page
    # This will still show a next page button even if the results end on a number divisible by 15
    # Could do an API check in the future
    if len(videos) == 15:
        # Add a list item to load more
        # Add two to the page number so it looks like the page starts at 1
        # Improves UX
        refresh_item = xbmcgui.ListItem(label=f"Load More (page {page+2})")
    
        # Use actually correct page number behind the scenes (page+1)
        next_url = get_url(action='listing', mode=mode, page=page+1)
        is_folder = True
        listing.append((next_url, refresh_item, is_folder))

    # Batch add once
    xbmcplugin.addDirectoryItems(HANDLE, listing, len(listing))

    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)

# Must take instance_url to prevent results from other instances being used
# Not used in the function itself
def get_video(instance_url, mode, host, id):
    xbmc.log("id is %s" % id, xbmc.LOGDEBUG)
    API = window.getProperty('API')
    
    try:
        # If it's a global search, always change the API to be host
        if mode == "global_search":
            request = requests.get(f"https://{host}/api/v1/videos/{id}")
        else:
            request = requests.get(f"{API}/videos/{id}")
        r = request.json()

        # Apparently there can just be no streamingPlaylists array, so check for that and skip it if necessary
        if not r["streamingPlaylists"]:
            raise StopExecution("No streamingPlaylists", data=[])

        # There can be a "does_not_respect_follow_constraints" error here, so check the status code and handle the error gracefully
        # See: https://framacolibri.org/t/embed-error-cannot-get-this-video-regarding-follow-constraints/24390
        # See: https://docs.joinpeertube.org/api-rest-reference.html#section/Errors

        # If everything was okay, return
        if request.status_code == 200:
            return r["streamingPlaylists"][0]["playlistUrl"], r["description"], r["tags"]
        else:
            detail = r["detail"]
            originUrl = r["originUrl"]

            raise StopExecution("Error getting video", data=[detail, originUrl])

    except requests.RequestException as e:
        traceback.print_exc()
        raise StopExecution("An unexpected error occurred", data=[e])

def play_video(path):
    # BEGIN INPUT STREAM ADAPTIVE
    STREAM_URL = path
    
    is_helper = inputstreamhelper.Helper(PROTOCOL)
    if not is_helper.check_inputstream():
        xbmcgui.Dialog().notification('Error', 'InputStream Adaptive not available', xbmcgui.NOTIFICATION_ERROR)
        return
    
    list_item = xbmcgui.ListItem(path=STREAM_URL, offscreen=True)
    list_item.setContentLookup(False)
    list_item.setMimeType(MIME_TYPE)

    # Set appropriate inputstream addon property based on Kodi version
    kodi_version = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
    if kodi_version >= 19:
        list_item.setProperty('inputstream', is_helper.inputstream_addon)
    else:
        list_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)

    list_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list_item)

    # END INPUTSTREAM ADAPTIVE

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if not params:
        menu()
        return

    elif params['action'] == 'listing':
        # Handle there being no page provided
        try:
            page = int(params.get('page', 0))
        except:
            page = 0

        list_videos(params['mode'], page)
    elif params['action'] == 'play':
        play_video(params['video'])
    elif params['action'] == 'login':
        login(params['mode'], params['token'])
    elif params['action'] == 'logout':
        logout()
    else:
        raise ValueError(f'Invalid paramstring: {paramstring}!')


if __name__ == '__main__':
    router(sys.argv[2][1:])
