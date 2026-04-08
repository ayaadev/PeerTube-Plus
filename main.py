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

__localize__ = Addon().getLocalizedString

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
    credentialsFile = "credentials.json"
    dataFile = "data.json"
    if not xbmcvfs.exists(USERDATA_PATH):
        try:
            xbmcvfs.mkdirs(USERDATA_PATH)
        except:
            error = dialog.notification(__localize__(30011), __localize__(30012), xbmcgui.NOTIFICATION_ERROR)
        
    CREDENTIALS_PATH = USERDATA_PATH + credentialsFile
    DATA_PATH = USERDATA_PATH + dataFile

    # Check if the user is already logged in

    request = requests.get(f"{API}/oauth-clients/local")
    clientDetails = request.json()

    clientId = clientDetails["client_id"]
    clientSecret = clientDetails["client_secret"]

    dialog = xbmcgui.Dialog()

    # If the user is logging in for the first time, i.e. not refreshing with a token
    if mode == "password":
        username = dialog.input(__localize__(30001))
        # We can't use the password input because it hashes the value
        password = dialog.input(__localize__(30002), option=xbmcgui.ALPHANUM_HIDE_INPUT)

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
            error = dialog.ok(__localize__(30003), __localize__(30004))

            # The other try block handles a file not found error, so we don't need to check here
            with xbmcvfs.File(DATA_PATH, 'r') as file:
                # Read the data and load it to JSON
                content = file.read()
                data = json.loads(content)

                # Change the authenticated key to false
                data["authenticated"] = False
                
            with xbmcvfs.File(DATA_PATH, 'w') as file:
                # Save the file
                file.write(json.dumps(data, ensure_ascii=False, indent=4))

        if credentials["code"] == "invalid_grant":
            error = dialog.ok(__localize__(30003), __localize__(30005))
            
            # The other try block handles a file not found error, so we don't need to check here
            with xbmcvfs.File(DATA_PATH, 'r') as file:
                # Read the data and load it to JSON
                content = file.read()
                data = json.loads(content)

                # Change the authenticated key to false
                data["authenticated"] = False
                
            with xbmcvfs.File(DATA_PATH, 'w') as file:
                # Save the file
                file.write(json.dumps(data, ensure_ascii=False, indent=4))

        if "72 bytes" in credentials["detail"]:
            error = dialog.ok(__localize__(30003), __localize__(30006))

        return
    
    elif status == 401:
        if credentials["code"] == "missing_two_factor":
            twoFactorCode = dialog.input(__localize__(30007))
            headers = {"x-peertube-otp": twoFactorCode}
            r = requests.post(url, data=payload, headers=headers)
            status = r.status_code
            credentials = r.json()
            #error = dialog.ok('Error logging in', "Your account requires two factor authentication which is unsupported at this time. Sorry for the inconvenience.")

        elif credentials["code"] == "invalid_token":
            data = {}

            # The other try block handles a file not found error, so we don't need to check here
            with xbmcvfs.File(DATA_PATH, 'r') as file:
                # Read the data and load it to JSON
                content = file.read()
                data = json.loads(content)

                # Change the authenticated key to false
                data["authenticated"] = False
                
            with xbmcvfs.File(DATA_PATH, 'w') as file:
                # Save the file
                file.write(json.dumps(data, ensure_ascii=False, indent=4))

            error = dialog.ok(__localize__(30008), __localize__(30009))
            
            return
        else:
            error = dialog.ok(__localize__(30003), __localize__(30010))
            return
        
    access_token = credentials["access_token"]
    refresh_token = credentials["refresh_token"]

    data = {}

    try:
        with xbmcvfs.File(CREDENTIALS_PATH, 'w') as file:
            file.write(json.dumps(credentials, ensure_ascii=False, indent=4))
        with xbmcvfs.File(DATA_PATH, 'r') as file:
            # Read the data and load it to JSON
            content = file.read()
            data = json.loads(content)

            # Change / add the authenticated key to true
            data["authenticated"] = True 
        
        with xbmcvfs.File(DATA_PATH, 'w') as file:
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
        error = dialog.notification(__localize__(30011), __localize__(30013), xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()

# Logout
def logout():
    dialog = xbmcgui.Dialog()
    if not xbmcvfs.exists(USERDATA_PATH):
        error = dialog.notification(__localize__(30011), __localize__(30014), xbmcgui.NOTIFICATION_ERROR)
        return

    CREDENTIALS_PATH = USERDATA_PATH + "credentials.json"
    DATA_PATH = USERDATA_PATH + "data.json"

    data = {}

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
            notification = dialog.notification(__localize__(30015), __localize__(30016))
            
            # Change the data file to be unauthenticated
            with xbmcvfs.File(DATA_PATH, 'r') as file:
                content = file.read()
                data = json.loads(content)

                data["authenticated"] = False
            
            # Write to file
            with xbmcvfs.File(DATA_PATH, 'w') as file:
                file.write(json.dumps(data, ensure_ascii=False, indent=4))

            # Only delete the file if the credentials were revoked at the server.
            xbmcvfs.delete(CREDENTIALS_PATH)

        # If there was a server error, return it
        else:
            response = request.json()
            detail = response["detail"]
            code = response["code"]
            error = dialog.notification(__localize__(30017).format(request.status_code), __localize__(30018).format(detail, code), xbmcgui.NOTIFICATION_ERROR)
   
            # Change the data file to be unauthenticated
            with xbmcvfs.File(DATA_PATH, 'r') as file:
                content = file.read()
                data = json.loads(content)

                data["authenticated"] = False
            
            # Write to file
            with xbmcvfs.File(DATA_PATH, 'w') as file:
                file.write(json.dumps(data, ensure_ascii=False, indent=4))

    except json.JSONDecodeError:
        # For some reason this often happens when logging out, but the error doesn't break anything so just pass
        pass

    except Exception as e:
        traceback.print_exc()
        error = dialog.notification(__localize__(30011), __localize__(30019).format(e), xbmcgui.NOTIFICATION_ERROR)

# Delete a search
def delete_search(mode, search):
    dataFile = "data.json"
    if not xbmcvfs.exists(USERDATA_PATH):
        try:
            xbmcvfs.mkdirs(USERDATA_PATH)
        except:
            error = dialog.notification(__localize__(30011), __localize__(30012), xbmcgui.NOTIFICATION_ERROR)
        
    DATA_PATH = USERDATA_PATH + dataFile

    data = {}

    try:
        with xbmcvfs.File(DATA_PATH, 'r') as file:
            # Read the data and load it to JSON
            content = file.read()
            data = json.loads(content)

            # Remove search
            data[mode].remove(search)

        with xbmcvfs.File(DATA_PATH, 'w') as file:
            # Save the file
            file.write(json.dumps(data, ensure_ascii=False, indent=4))

        # Return to menu
        xbmc.executebuiltin("Container.Refresh")
        return
    # If the file doesn't exist
    except json.JSONDecodeError:
        # This shouldn't be possible so pass
        pass
    # General catch statement
    except Exception:
        error = dialog.notification(__localize__(30011), __localize__(30013), xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()


# Create a new search
def new_search(mode):
    # Get search
    dialog = xbmcgui.Dialog()
    searchQuery = dialog.input(__localize__(30022))

    dataFile = "data.json"
    if not xbmcvfs.exists(USERDATA_PATH):
        try:
            xbmcvfs.mkdirs(USERDATA_PATH)
        except:
            error = dialog.notification(__localize__(30011), __localize__(30012), xbmcgui.NOTIFICATION_ERROR)
        
    DATA_PATH = USERDATA_PATH + dataFile

    data = {}

    try:
        with xbmcvfs.File(DATA_PATH, 'r') as file:
            # Read the data and load it to JSON
            content = file.read()
            data = json.loads(content)

            if not mode in data:
                data[mode] = [searchQuery]
            else:
                # Prepend to search
                data[mode].insert(0, searchQuery)
                data[mode] = data[mode][:15]

        with xbmcvfs.File(DATA_PATH, 'w') as file:
            # Save the file
            file.write(json.dumps(data, ensure_ascii=False, indent=4))

        # Return to menu
        xbmc.executebuiltin("Container.Refresh")
        return
    # If the file doesn't exist
    except json.JSONDecodeError:  
        traceback.print_exc()
        xbmc.log("In JSON Except")
        # Open the file
        with xbmcvfs.File(DATA_PATH, 'w') as file:
            # Create the file and add history key
            data[mode] = [searchQuery]
            file.write(json.dumps(data, ensure_ascii=False, indent=4))
    # General catch statement
    except Exception:
        error = dialog.notification(__localize__(30011), __localize__(30013), xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()


# Show search menu
def search_menu(mode):
    dialog = xbmcgui.Dialog()
    
    listing = []

    newSearch = xbmcgui.ListItem(label=__localize__(30039))
    newSearchURL = get_url(action='new_search', mode=mode)
    listing.append((newSearchURL, newSearch, True))

    dataFile = "data.json"
    if not xbmcvfs.exists(USERDATA_PATH):
        try:
            xbmcvfs.mkdirs(USERDATA_PATH)
        except:
            error = dialog.notification(__localize__(30011), __localize__(30012), xbmcgui.NOTIFICATION_ERROR)
        
    DATA_PATH = USERDATA_PATH + dataFile

    try:
        with xbmcvfs.File(DATA_PATH, 'r') as file:
            # Read the data and load it to JSON
            content = file.read()
            data = json.loads(content)

            for item in data[mode]:
                # Item = search query
                searchItem = xbmcgui.ListItem(label=item)
                searchItemURL = get_url(action='listing', mode=mode, search=item)
                
                # Context menu
                query = get_url(action='delete_search', mode=mode, search=item)
                command = f"RunPlugin({query})"
                searchItem.addContextMenuItems([(__localize__(30041), command)])

                listing.append((searchItemURL, searchItem, True))
    
    # If there is no history yet, ignore
    except KeyError:
        pass
    # If the file doesn't exist
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    # General catch statement
    except Exception:
        error = dialog.notification(__localize__(30011), __localize__(30040), xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()

    # Batch add once
    xbmcplugin.addDirectoryItems(HANDLE, listing, len(listing))

    xbmcplugin.endOfDirectory(HANDLE)

# The selection menu of the addon
def menu():

    # Check if the custom instance was set
    if not CUSTOM_INSTANCE or CUSTOM_INSTANCE == "" or CUSTOM_INSTANCE.startswith("http"):
        xbmcgui.Dialog().ok(__localize__(30020), __localize__(30021))
        return

    xbmcplugin.setPluginCategory(HANDLE, 'Menu')
    xbmcplugin.setContent(HANDLE, 'movies')

    # Set default listing here, independent of if user is authenticated
    listing = []

    # Local Search
    localSearch = xbmcgui.ListItem(label=__localize__(30022))
    localSearchURL = get_url(action='search', mode='local_search')
    listing.append((localSearchURL, localSearch, True))
 
    # Global Search
    globalSearch = xbmcgui.ListItem(label=__localize__(30023))
    globalSearchURL = get_url(action='search', mode='global_search')
    listing.append((globalSearchURL, globalSearch, True))

    # All Videos
    allVideos = xbmcgui.ListItem(label=__localize__(30024))
    allVideosURL = get_url(action='listing', mode='all_videos')
    listing.append((allVideosURL, allVideos, True))
    
    # Trending
    trending = xbmcgui.ListItem(label=__localize__(30025))
    trendingURL = get_url(action='listing', mode='trending')
    listing.append((trendingURL, trending, True))

    # Local Videos
    localVideos = xbmcgui.ListItem(label=__localize__(30026))
    localVideosURL = get_url(action='listing', mode='local_videos')
    listing.append((localVideosURL, localVideos, True))

    DATA_PATH = USERDATA_PATH + "data.json"
    try:
        with xbmcvfs.File(DATA_PATH) as file:
            content = file.read()
            data = json.loads(content)

            if data["authenticated"] == True:
                is_folder = True
                
                subscriptions = xbmcgui.ListItem(label=__localize__(30027))
                subscriptionsURL = get_url(action='listing', mode='subscriptions')
                
                # Append subscriptions to listing variable
                listing.append((subscriptionsURL, subscriptions, is_folder))

                logout = xbmcgui.ListItem(label=__localize__(30028))
                logoutURL = get_url(action='logout')

                # Append logout to listing variable
                listing.append((logoutURL, logout, is_folder))

                #xbmcplugin.addDirectoryItems(HANDLE, [(subscriptionsURL, subscriptions, is_folder), (logoutURL, logout, is_folder)])
            else:
                is_folder = True
                
                # LOGIN

                login = xbmcgui.ListItem(label=__localize__(30029))
                loginURL = get_url(action='login', mode='password', token='0')
                
                listing.append((loginURL, login, is_folder))
               
    except:
        # If there's an exception here, it likely means the file doesn't exist so login
        is_folder = True

        # LOGIN

        login = xbmcgui.ListItem(label=__localize__(30029))
        loginURL = get_url(action='login', mode='password', token='0')
        
        listing.append((loginURL, login, is_folder))

    # Batch add once
    xbmcplugin.addDirectoryItems(HANDLE, listing, len(listing))

    #xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)

def get_token():
    dialog = xbmcgui.Dialog()
    if not xbmcvfs.exists(USERDATA_PATH):
        error = dialog.notification(__localize__(30011), __localize__(30014), xbmcgui.NOTIFICATION_ERROR)
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
                error = dialog.notification(__localize__(30011), __localize__(30014), xbmcgui.NOTIFICATION_ERROR)
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
            
            # If the login function returned an error, it will cause a TypeError
            try:
                successful, token = login("token", refresh_token)
            except TypeError:
                successful = False

            if successful == True:
                return token
            
            # Return False if it wasn't successful
            return False
        elif request.status_code == 200:
            return access_token
        else:
            error = dialog.notification(__localize__(30011), __localize__(30030), xbmcgui.NOTIFICATION_ERROR)
            return False
    except Exception as e:
        error = dialog.notification(__localize__(30011), __localize__(30031).format(e), xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()
        return False
         
            
# Must take instance_url to invalidate cache if the user changes their instance
def get_videos(instance_url, searchQuery, mode, page):
    
    start = page * 15
    queryParams = f"?start={start}&count=15&hasHLSFiles=true"

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
        request = requests.get(f"{API}/search/videos{queryParams}&search={searchQuery}")
    elif mode == "global_search":
        request = requests.get(f"https://sepiasearch.org/api/v1/search/videos{queryParams}&search={searchQuery}")
    else:
        # Default request
        request = requests.get(f"{API}/videos{queryParams}")
    
    r = request.json()
    
    # If there were no results
    if "data" not in r or not r["data"]:
        error = xbmcgui.Dialog().notification(__localize__(30011), __localize__(30032), xbmcgui.NOTIFICATION_ERROR)
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

def list_videos(mode, search, page):
    dialog = xbmcgui.Dialog()
       
    # Cache results for 1 hour
    # Must pass search here so it gets new data if the user searches for anything new
    # Must pass CUSTOM_INSTANCE so it gets new data if the user changed their instance
    try:
        # TODO
        #genre_info = cache.cacheFunction(get_videos, CUSTOM_INSTANCE, search, mode, page)
        genre_info = get_videos(CUSTOM_INSTANCE, search, mode, page)
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
        xbmc.log(f'Title of video being processed: {video["name"]}')
        list_item = xbmcgui.ListItem(label=video['name'])
        info_tag = list_item.getVideoInfoTag()

        channelName = video["channel"]["displayName"]
        actor = xbmc.Actor(name=channelName)

        # If there is no avatar
        try:
            channelAvatar = video["channel"]["avatars"][1]["fileUrl"]
            actor = xbmc.Actor(name=channelName, thumbnail=channelAvatar)
        except KeyError:
            # If there was a keyerror, it likely means the API responded with "url" instead of "fileUrl" for the avatar image
            channelAvatar = video["channel"]["avatars"][1]["url"]
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
            # TODO
            #videoURL, description, tags = cache.cacheFunction(get_video, CUSTOM_INSTANCE, mode, video["account"]["host"], video["id"])
            videoURL, description, tags = get_video(CUSTOM_INSTANCE, mode, video["account"]["host"], video["id"])
        except StopExecution as e:
            # Manually clear the get_videos cache so the error doesn't get cached in the results
            cache.delete("get_videos")
            
            # If the error message has specific details (message = "Error getting video") then return a more detailed response
            if e.message == "Error getting video":
                errorMessage = e.data[0]
                videoTitle = video["name"]
                videoURL = e.data[1]
                error = dialog.ok(__localize__(30033), __localize__(30034).format(errorMessage, videoTitle, videoURL))
            if e.message == "No streamingPlaylists":
                # Skip the bad global search result
                continue
            else:
                error = dialog.ok(__localize__(30011), __localize__(30019).format(e.data[0]))
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
        viewText = __localize__(30035).format(views)
        likeText = __localize__(30036).format(likes)
        info_tag.setTagLine(f"[COLOR green]{viewText}[/COLOR]\n[COLOR red]{likeText}[/COLOR]")
        
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
        refresh_item = xbmcgui.ListItem(label=__localize__(30037).format(page+2))
    
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

        # There can be no streamingPlaylists array, so check for that and try returning the fileUrl instead
        if not r["streamingPlaylists"]:
            # If there are no files, skip it
            if not r["files"]:
                raise StopExecution("No streamingPlaylists", data=[])
            
            # If there were files, return
            return r["files"][0]["fileUrl"], r["description"], r["tags"]

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

# Create a custom function to compare version numbers
def compare_versions(v1, v2):
    version1 = [int(x) for x in v1.split('.')]
    version2 = [int(x) for x in v2.split('.')]
    return version1 > version2

def play_video(path):
    # Get helper 
    is_helper = inputstreamhelper.Helper(PROTOCOL)

    # Default version if InputStream adaptive isn't found
    version = "0.0.0"
   
    showInputStreamAdaptive = Addon().getSetting("show_inputstream_adaptive")

    # Check InputStream Adaptive version
    # We're only prompting to install InputStream Adaptive once, because they can still use the fallback video player
    if showInputStreamAdaptive == "True":
        if is_helper.check_inputstream():
            addon = Addon('inputstream.adaptive')
            version = addon.getAddonInfo('version')
        else:
            # Don't show the popup again
            Addon().setSetting("show_inputstream_adaptive", "False")

    # If the user has a high enough InputStream adaptive version which supports separate audio, use it
    # Must also be a m3u8 file. If path ends in .mp4 it must go to the else block.
    if compare_versions(version, "22.3.6") and path.endswith(".m3u8"):
    
        # BEGIN INPUT STREAM ADAPTIVE
        STREAM_URL = path
    
        if not is_helper.check_inputstream():
            xbmcgui.Dialog().notification(__localize__(30011), __localize__(30038), xbmcgui.NOTIFICATION_ERROR)
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
       
    else:
        play_item = xbmcgui.ListItem(offscreen=True)
        play_item.setPath(path)
        xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)

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

        # Handle no search being provided
        try:
            searchQuery = params.get('search', 1)
        except:
            searchQuery = ""

        list_videos(params['mode'], searchQuery, page)
    elif params['action'] == 'play':
        play_video(params['video'])
    elif params['action'] == 'login':
        login(params['mode'], params['token'])
    elif params['action'] == 'logout':
        logout()
    elif params['action'] == 'search':
        search_menu(params['mode'])
    elif params['action'] == 'new_search':
        new_search(params['mode'])
    elif params['action'] == 'delete_search':
        delete_search(params['mode'], params['search'])
    else:
        raise ValueError(f'Invalid paramstring: {paramstring}!')


if __name__ == '__main__':
    router(sys.argv[2][1:])
