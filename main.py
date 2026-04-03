import os
import sys
import requests
import json
# Could remove later
import traceback
import xbmcvfs
import threading
from urllib.parse import urlencode, parse_qsl

# TODO
# REMOVE AFTER TESTING
import random

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
window.setProperty("API", f'https://{Addon().getSetting('custom_instance')}/api/v1')

URL = sys.argv[0]
HANDLE = int(sys.argv[1])
ADDON_PATH = translatePath(Addon().getAddonInfo('path'))
ICONS_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'icons')
FANART_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'fanart')
ADDON_ID = 'plugin.video.peertube-plus'
USERDATA_PATH = xbmcvfs.translatePath(f'special://userdata/addon_data/{ADDON_ID}/')
#CUSTOM_INSTANCE = xbmcplugin.getSetting(HANDLE,"custom_instance")
CUSTOM_INSTANCE = Addon().getSetting('custom_instance')
API = f"https://{CUSTOM_INSTANCE}/api/v1"

def get_url(**kwargs):
    return '{}?{}'.format(URL, urlencode(kwargs))

#def get_instances():
    #filename = "instances.json"
    #if not os.path.exists(USERDATA_PATH):
        #try:
            #os.makedirs(USERDATA_PATH)
        #except:
            #xbmc.log("Could not write %s" % USERDATA_PATH, xbmc.LOGDEBUG)
    #FILE_PATH = os.path.join(USERDATA_PATH, filename)
    #if not xbmcvfs.exists(FILE_PATH):
        #xbmc.log("No file, requesting new data!", xbmc.LOGDEBUG)
        #request = requests.get('https://instances.joinpeertube.org/api/v1/instances/hosts?count=2000&start=0&sort=createdAt')
        #r = request.json()
        #try:
            #with xbmcvfs.File(FILE_PATH) as instances_file:
                #instances_file.write(json.dumps(r, ensure_ascii=False, indent=4))
        #except:
            #xbmc.log("Could not write %s" % FILE_PATH, xbmc.LOGDEBUG)
    #else:
        #with xbmcvfs.File(FILE_PATH) as instances_file:
            #r = json.load(instances_file)
    #return r["data"]

# Allow the user to login
def login(mode, token):
    # Check if the user is already logged in
    # TO-DO

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

    #try:
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
            error = dialog.ok('Error logging in', "Your account requires two factor authentication which is unsupported at this time. Sorry for the inconvenience.")

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
        
        # Apparently this is possible according to the API docs.
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
    #except Exception as e:
        #error = dialog.ok('Error logging in', f"Error message: {e}")

# Logout
def logout():
    dialog = xbmcgui.Dialog()
    if not xbmcvfs.exists(USERDATA_PATH):
        error = dialog.notification('Error', 'Please login to continue this action.', xbmcgui.NOTIFICATION_ERROR)
        return

    CREDENTIALS_PATH = USERDATA_PATH + "credentials.json"
    print(f"Credentials path: {CREDENTIALS_PATH}")
    DATA_PATH = USERDATA_PATH + "data.json"

    if xbmcvfs.exists(CREDENTIALS_PATH):
        print("Credentials file exists!")
    else:
        print("Credentials file NOT exists!")

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
        error = dialog.notification('Error', f'An unexpected error occured. Error message: {e}', xbmcgui.NOTIFICATION_ERROR)

# The selection menu of the add-on
def menu():
    xbmcplugin.setPluginCategory(HANDLE, 'Menu')
    xbmcplugin.setContent(HANDLE, 'movies')

    # If the path doesn't exist, the user likely wants to login
    if not xbmcvfs.exists(USERDATA_PATH):
        list_item = xbmcgui.ListItem(label="Login")
        url = get_url(action='login', mode='password', token='0')
        is_folder = True
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    # Set default listing here, independent of if user is authenticated
    listing = []

    # All Videos
    allVideos = xbmcgui.ListItem(label="All Videos")
    allVideosURL = get_url(action='listing', mode='all_videos')

    listing.append((allVideosURL, allVideos, True))
    

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
               
                #xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    except:
        # If there's an exception here, it likely means the file doesn't exist so login
        is_folder = True

        # LOGIN

        login = xbmcgui.ListItem(label="Login")
        loginURL = get_url(action='login', mode='password', token='0')
        
        listing.append((loginURL, login, is_folder))

    # Batch add once
    xbmcplugin.addDirectoryItems(HANDLE, listing, len(listing))

        #xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    #xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)
    
    #if not CUSTOM_INSTANCE or CUSTOM_INSTANCE == "":
        #xbmcgui.Dialog().notification('Error', 'Please specify a PeerTube instance in the add-on settings.', xbmcgui.NOTIFICATION_ERROR)
        #return
    #else:
        #print("YAY!")

#def list_instances():
    #xbmcplugin.setPluginCategory(HANDLE, 'Peertube Servers')
    #xbmcplugin.setContent(HANDLE, 'movies')
    #instances = get_instances()
    #for index, genre_info in enumerate(instances):
        #list_item = xbmcgui.ListItem(label=genre_info['host'])
        #info_tag = list_item.getVideoInfoTag()
        #info_tag.setMediaType('video')
        #info_tag.setTitle(genre_info['host'])
        #info_tag.setGenres([genre_info['host']])
        #url = get_url(action='listing', host=genre_info['host'])
        #is_folder = True
        #xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    #if not CUSTOM_INSTANCE == "":
        #list_item = xbmcgui.ListItem(label=CUSTOM_INSTANCE)
        #info_tag = list_item.getVideoInfoTag()
        #info_tag.setMediaType('video')
        #info_tag.setTitle(CUSTOM_INSTANCE)
        ##info_tag.setGenres(CUSTOM_INSTANCE)
        #url = get_url(action='listing', host=CUSTOM_INSTANCE)
        #is_folder = True
        #xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    #xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    #xbmcplugin.endOfDirectory(HANDLE)

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
        print(f"API IS {API}")
        print(f"INSTANCE IS {CUSTOM_INSTANCE}")
        # CHANGE LATER
        # CHANGE LATER
        # CHANGE LATER
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
            error = dialog.notification('Error', 'An unexpected error occured while performing an authenticated action.', xbmcgui.NOTIFICATION_ERROR)
            return False
    except Exception as e:
        error = dialog.notification('Error', f'An unexpected error occured while performing an authenticated action. Error message: {e}', xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()
        return False
         
            

def get_videos(mode, page):
    
    # Only try to get the access token if the user is performing an authenticated request
    if mode != "all_videos":
        # Get the access key
        access_token = get_token()

        # If there was an error, also cancel this function
        if not access_token:
            return False

    start = page * 15

    if mode == "subscriptions":
        headers = {"Authorization": f"Bearer {access_token}"}
        request = requests.get(f"{API}/users/me/subscriptions/videos?start={start}", headers=headers)
    else:
        # Default request
        request = requests.get(f"{API}/videos?start={start}")
    
    r = request.json()
    print(r)
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

# Async get next results without throttling the UI
def fetch_more_items(mode, page):

    # Get the access key
    access_token = get_token()

    # If there was an error, also cancel this function
    if not access_token:
        return False
    
    # Get pagination start
    #start = page * 15
    #start = "16"
    print(f"STARTING AT {start}")

    if mode == "subscriptions":
        headers = {"Authorization": f"Bearer {access_token}"}
        print(f"Inside fetch more items API is: {API}")
        print(f"Inside fetch more items CUSTOM_INSTANCE is: {CUSTOM_INSTANCE}")
        request = requests.get(f"{API}/users/me/subscriptions/videos?start={start}", headers=headers)
    else:
        # Default request
        request = requests.get(f"{API}/videos?start={start}")
    r = request.json()["data"]

    print(f"MADE REQUEST: {r}")
    
    #dataFile = "asyncLoadResults.json"
    #DATA_PATH = USERDATA_PATH + dataFile
    
    #file_data = []
    #with xbmcvfs.File(DATA_PATH, 'r') as file:
        #raw = file.read()
        #if raw.strip():
            #try:
                #file_data = json.loads(raw)
            #except json.JSONDecodeError:
                #print("EXCEPT HAPPENED")
                #file_data = []

    for video in r:
        video["videoURL"], video["description"], video["tags"] = get_video(video["id"])
    
    #file_data.extend(r)

    #with xbmcvfs.File(DATA_PATH, 'w') as file:


        #print(f"Data to be appended: {r}")

        # Append new data
        #file_data["data"].append(r)
        #print(f"File data is: {file_data}")
        #file_data.append(r)
        #file_data.extend(r)
        
        print(f"File data after append: {file_data}")
        # Back to the beginning of the file
        #file.seek(0)
        
        # Write to the file
        #json.dumps(file_data, ensure_ascii=False, indent=4)
        
        # This used to be uncommented, not the line above
        #file.write(json.dumps(file_data, ensure_ascii=False, indent=4))


    # Verify write worked
    #with xbmcvfs.File(DATA_PATH, 'r') as file:
        #new_raw = file.read()
        #new_data = json.loads(new_raw)
        #print(f"VERIFY: File now has {len(new_data)} items")


    print(f"Final check API is: {API}")
    print(f"Final check CUSTOM_INSTANCE is: {CUSTOM_INSTANCE}")


    # Return the data
    #return r["data"]


def list_videos(mode, page):
    print(f"ENTER listing_function with page={page} (thread={threading.current_thread().name})")

    # Maybe you don't need this?
    # TODO TEST
    genre_info = {}

    #if mode == "pagination":
        #dataFile = "asyncLoadResults.json"
        #DATA_PATH = USERDATA_PATH + dataFile
        # Read the data
        #with xbmcvfs.File(DATA_PATH, 'r') as file:
            #content = file.read()
            #data = json.loads(content)

            #start = page * 15
            #end = start + 15

            #genre_info = data[start:end]
            #print(f"Data is: {genre_info}")
    #else:
    
    genre_info = get_videos(mode, page)

    # Add to the page for pagination
    #page += 1

    print(f"PAGE NUMBER IS {page}")

    # Handle async pagination
    #if not results:
        #genre_info = get_videos(mode)
    #else:
        #genre_info = results["data"]

    # If there was an error upstream
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

        #info_tag.setMediaType('movie')
        #info_tag.setTitle(video['name'])
        #info_tag.setPlot(video["truncatedDescription"])

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
        
        #if mode == "pagination":
            #videoURL, description, tags = video["videoURL"], video["description"], video["tags"]
        #else:
        #TODO
        # The second assignment is mostly unnecessary but it's just for testing
        videoURL, description, tags = get_video(video["id"])
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
        #xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    # Save the data to the file
    #dataFile = "asyncLoadResults.json"
    #DATA_PATH = USERDATA_PATH + dataFile

    #with xbmcvfs.File(DATA_PATH, 'w') as file:
        # Write to the file
        #file.write(json.dumps(videos, ensure_ascii=False, indent=4))

    # Add a list item to load more
    # Add two to the page number so it looks like the page starts at 1
    # Improves UX
    refresh_item = xbmcgui.ListItem(label=f"Load More. Page: {page+2}.")
    
    # Use actually correct page number behind the scenes (page+1)
    next_url = get_url(action='listing', mode=mode, page=page+1)
    is_folder = True
    listing.append((next_url, refresh_item, is_folder))
    #xbmcplugin.addDirectoryItem(HANDLE, url, refresh_item, is_folder)

    print(f"ENDING directory with {len(listing)} items, next_url page={page+1}")

    # Batch add once
    xbmcplugin.addDirectoryItems(HANDLE, listing, len(listing))

    # If there was an update through pagination, refresh the view
    #if mode == "pagination":
        #print("THERE WAS PAGINATION AND TRIED TO REFRESH")
        #xbmcplugin.endOfDirectory(HANDLE, succeeded=True, updateListing=True, cacheToDisc=False)
    #else:
    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)

    # Start calling the async function to load more data
    #fetch_more_items(mode, page+1)
    

    #thread = threading.Thread(target=fetch_more_items, args=(mode,))
    #thread.daemon = True
    #thread.start()

    print("listing_function COMPLETE")

def get_video(id):
    xbmc.log("id is %s" % id, xbmc.LOGDEBUG)
    API = window.getProperty('API')
    request = requests.get(f"{API}/videos/{id}")
    r = request.json()
    #xbmc.log("request is %s" % r, xbmc.LOGDEBUG)
    return r["streamingPlaylists"][0]["playlistUrl"], r["description"], r["tags"]


def play_video(path):

    #url = path
    #li = xbmcgui.ListItem(path=url)

    # Tell Kodi to use InputStream FFmpeg Direct
    #li.setProperty('inputstream', 'inputstream.ffmpegdirect')

    # Mark as HLS (manifest)
    #li.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')

    # Set mimetype so Kodi and the addon recognize it as HLS
    #li.setProperty('mimetype', 'application/x-mpegURL')

    # Optional: force FFmpeg open mode (instead of curl)
    #li.setProperty('inputstream.ffmpegdirect.open_mode', 'ffmpeg')

    # Optional: if it is a live stream
    #li.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
    #li.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')

    #xbmcplugin.setResolvedUrl(HANDLE, True, li)
    
    #print(path)


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



    #print("step 1")
    #is_helper = inputstreamhelper.Helper(PROTOCOL)
    #print(is_helper.check_inputstream)
    #if is_helper.check_inputstream():
        #print("step 2")
        #play_item = xbmcgui.ListItem(path)
        #play_item.setContentLookup(False)
        #play_item.setMimeType(MIME_TYPE)
#
        #play_item.setProperty('inputstream', is_helper.inputstream_addon)
        
        #print("step 3")

        #play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
        #print("step 4")
        ##play_item.setProperty('inputstream.adaptive.license_type', DRM)
        #play_item.setProperty('inputstream.adaptive.license_key', LICENSE_URL + '||R{SSM}|')
        #xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, play_item)
        #print("step 5")

    #addon_handle = int(sys.argv[1])

    #play_item = xbmcgui.ListItem(label="HLS Stream")
    #play_item.setProperty("IsPlayable", "true")

    #play_item.setProperty("inputstream", "inputstream.adaptive")
    #play_item.setProperty("inputstream.adaptive.manifest_type", "hls")
    #play_item.setMimeType("application/x-mpegURL")

    #play_item.setPath(path)
    #xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if not params:
        menu()

    elif params['action'] == 'listing':
        # Handle there being no page provided
        try:
            page = int(params.get('page', 0))
        except:
            page = 0

        print(f"Page number being passed in router: {page} (full params: {params})")

        #print(f"Page number being passed in router: {page}")
        
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
