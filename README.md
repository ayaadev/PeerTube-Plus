<div align="left">
    <img align="left" width=48 src="resources/images/icon.png">
    <h1>PeerTube Plus</h1>
    <b>Finally watch PeerTube on Kodi!</b>
</div>

## Features
- Ability to set a custom instance
- Locally search videos on the custom instance, or search across the entire PeerTube fediverse with SepiaSearch!
- Different feeds (all videos, subscriptions, trending, local videos)
- Account authentication
- 2FA Support
- Metadata on videos for easy searching
- Pagination on video feeds which increases responsiveness

## Planned features
- Filters for global search (SepiaSearch)
- Add a "Playlists" feed which shows the user's playlists (https://github.com/ayaadev/PeerTube-Plus/issues/13)
- Add a "Watch Later" feed (https://github.com/ayaadev/PeerTube-Plus/issues/13)
- Allow for multiple users with their own custom instance (https://github.com/ayaadev/PeerTube-Plus/issues/14)
- Show subscribed channels (and their videos) in a feed (https://github.com/ayaadev/PeerTube-Plus/issues/15)
- Torrent PeerTube videos

**Is a feature you want not listed here? Please [create a new issue](https://github.com/ayaadev/PeerTube-Plus/issues/new?template=%E2%9C%A8-feature-request.md) with your feature request.**

## Requirements
- If you would like to use the **upgraded video player** (spoiler alert: you do!), you need version `22.3.6` or higher of the InputStream Adaptive addon. This is already available for Windows and MacOS Kodi installs. However, they're still working on making it available on Linux. If you would like, you may manually build and install the latest version of InputStream Adaptive [here](https://github.com/xbmc/inputstream.adaptive/wiki/How-to-build). Once you have the necessary version, you will automatically start using the upgraded video player.
- Any PeerTube instance URL, even if you don't have an account. Please see the [configuration section below](https://github.com/ayaadev/PeerTube-Plus/tree/main#configuration).

## Installation
1. In the top left of Kodi, click on the settings wheel
<img width="323" height="313" alt="image" src="https://github.com/user-attachments/assets/bff3ae4c-3f2f-49f9-b76b-a3670c0aeb06" />

2. Navigate to "File manager"
<img width="378" height="375" alt="image" src="https://github.com/user-attachments/assets/e3f5c304-1625-4ae9-a984-492923e8bd15" />

3. Click on "Add source" and click on "<None>" in the window that appears
<img width="514" height="999" alt="image" src="https://github.com/user-attachments/assets/234568dd-0df0-4e3d-8b31-664920c80ed5" />

4. Input `https://ayaadev.github.io` and click "OK"
<img width="551" height="319" alt="image" src="https://github.com/user-attachments/assets/1672844d-27bf-4229-bb80-ccb21758b752" />

5. Enter a name for this source. You can name it anything, but I've named it "AyaaDev Repo" here. Click "OK"
<img width="607" height="998" alt="image" src="https://github.com/user-attachments/assets/305b9856-09d8-4409-bc8b-8f8b8c97f5cf" />

6. Navigate back and click on "Add-ons"
<img width="567" height="359" alt="image" src="https://github.com/user-attachments/assets/b6589e6b-6fe9-4bc1-ad70-57375dc14475" />

7. Click on "Install from zip file"

8. Navigate to the name of the repository you created. In my case, it is "AyaaDev Repo"
<img width="501" height="187" alt="image" src="https://github.com/user-attachments/assets/9591f491-9bdb-4d00-8221-e0a2e4689b8b" />

9. Select the only result on the page
<img width="696" height="210" alt="image" src="https://github.com/user-attachments/assets/cb27c08d-2d0a-4534-8d23-628b4a1ac161" />

10. Click on "Install from repository"
<img width="605" height="107" alt="image" src="https://github.com/user-attachments/assets/6c7c1b1a-0b6c-4f02-af82-6318850ba7f4" />

11. Select "AyaaDev Kodi Repository"
<img width="609" height="275" alt="image" src="https://github.com/user-attachments/assets/1ddc3002-7646-40c1-8642-5b1e6cd24c04" />

12. Select "Video add-ons"
<img width="596" height="312" alt="image" src="https://github.com/user-attachments/assets/6b83864d-9a10-4bdb-b3c4-9849c8e0b404" />

13. Select "PeerTube Plus" and click install!

## Installing from source
1. Run `git clone https://github.com/ayaadev/PeerTube-Plus.git`
2. Run `zip -r plugin.video.peertube-plus.zip plugin.video.peertube-plus/`
3. Open Kodi
4. Click on the settings wheel in the top left
5. Click "Add-ons"
6. Click "Install from zip file"
7. Navigate to the ZIP file you created in step 2.

## Configuration
Before opening the addon, make sure to set the custom instance. Click on the "Configure" button after navigating to the addon:
<img width="2420" height="1281" alt="image" src="https://github.com/user-attachments/assets/94cdb516-46c6-47e3-b721-da84e86d6e1c" />

Set your PeerTube instance in the "Custom instances" setting. It should **not** begin with "http". For example, input "peertube.tech" instead of "https://peertube.tech".
<img width="1451" height="131" alt="image" src="https://github.com/user-attachments/assets/0c666254-fef6-4aaf-a9ed-30bf7b86a590" />
The instance "peertube.tech" is **just an example** for the purpose of this guide. Please set it to any instance you would like.

## Usage
When you first open the addon, you will see the following menu:
<img width="1843" height="497" alt="image" src="https://github.com/user-attachments/assets/de650b47-ad92-4c25-adfe-a0f191eb04b6" />

You are able to access any feed that is shown while you are not logged in (e.g. "All Videos") without a PeerTube account.

If you would like to access your subscriptions feed, click "Login". Input your username, password and two-factor authentication code (if you have 2FA enabled).

<img width="538" height="493" alt="image" src="https://github.com/user-attachments/assets/6956db07-b2ed-4ee2-9085-00b52e7db30e" />

You should now see the "Subscriptions" feed appear.

<img width="539" height="609" alt="image" src="https://github.com/user-attachments/assets/a60eed9a-31ba-4119-8fbe-23cf8255a072" />

To watch any video, simply click on your desired feed and locate the video you would like to play.


## Privacy and Security
- Your username, password and two-factor authentication code are never stored.
- However, your access token and refresh token (which gives the API access to your account) are stored in plaintext in the addon directory.
- These tokens will only last for at most 2 weeks, but treat them like your password and never share it nor your Kodi directory online.
- The plugin only stores data inside its respective directory inside the Kodi folder, except for cached results which are stored in a shared database in `temp/commoncache.db`.

## Known limitations
- For certain videos, video playback has no audio. This is not an issue with this addon but instead an issue with [InputStream Adaptive](https://github.com/xbmc/inputstream.adaptive). They only [recently added support](https://github.com/xbmc/inputstream.adaptive/pull/1915) for PeerTube's separate audio streams, so there may be some bugs.
- Despite that issue, [InputStream Adaptive](https://github.com/xbmc/inputstream.adaptive) is still used because it is the only player (to the best of my knowledge) that can reliably play HLS videos with timeshift support.
- This addon does not torrent the PeerTube video being played. This is a high priority, but is also the reason why the [previous PeerTube addon](https://framagit.org/StCyr/plugin.video.peertube) has [not been updated to the latest version of Kodi](https://framagit.org/StCyr/plugin.video.peertube/-/work_items/21#note_2002965).

## Acknowledgements
This project was inspired by and modified from Haui1112's [plugin.video.pt](https://github.com/Haui1112/plugin.video.pt) Kodi addon. Modifications include:
1. Reworked instance selection. Users can arbitrarily set their instance in the addon settings. This avoids users' frustration when their instance is not listed (see [here](https://github.com/Haui1112/plugin.video.pt/issues/12)).
2. Implemented both local and global search (SepiaSearch)!
3. Fixed video playback and made it more reliable.
4. Added more metadata to videos which makes them easier to identify in the list.
5. Added view and like count to videos.
6. Added separate feeds (all videos, subscriptions, trending, local videos).
7. Setup pagination which makes load times faster and lets users keep browsing all videos in the feed.
8. Cached results for faster load times.
9. Implemented much more error checking, leading to a less buggy experience.
10. Added authentication, so users can perform authenticated actions (e.g. subscriptions feed).
11. Implemented two-factor support for authentication.
12. Implemented automatic renewal of short-lived PeerTube API token.
13. Localized all dialog that the user sees.
14. Et cetera.
