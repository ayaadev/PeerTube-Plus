<div align="left">
    <img align="left" width=48 src="resources/images/icon.png">
    <h1>PeerTube Plus</h1>
    <b>Finally watch PeerTube on Kodi!</b>
</div>

## Features
- Ability to set a custom instance
- Locally search the custom instance, or globally search with SepiaSearch!
- Different feeds (all videos, subscriptions, trending, local videos)
- Account authentication
- 2FA Support
- Metadata on videos for easy searching
- Pagination on video feeds which increases responsiveness

## Planned features
- Torrent PeerTube videos

**Is a feature you want not listed here? Please [create a new issue](https://github.com/ayaadev/PeerTube-Plus/issues/new) with your feature request.**

## Requirements
- Any PeerTube instance URL, even if you don't have an account. Please see the [configuration section below](https://github.com/ayaadev/PeerTube-Plus/tree/main#configuration).

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

You are able to access any feed (e.g. "All Videos") without logging in.

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
2. Implemented both local and global search with SepiaSearch!
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
13. Et cetera.
