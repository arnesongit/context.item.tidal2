# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Arne Svenson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os, re, traceback
from types import DictionaryType

from threading import Thread, currentThread
from Queue import Queue
from datetime import datetime
import requests

import xbmc, xbmcplugin, xbmcgui, xbmcvfs

from requests import HTTPError

from koditidal import plugin as tidalPlugin, addon as tidalAddon, _T, _P, VARIOUS_ARTIST_ID
from koditidal import TidalConfig, TidalSession, TidalUser, TidalFavorites, VideoItem, AlbumItem
from tidalapi import SubscriptionType, AlbumType
from tidalapi.models import SearchResult, PlayableMedia

from debug import DebugHelper
import config
from .config import settings, _S
from .fuzzymodels import FuzzyArtistItem, FuzzyAlbumItem, FuzzyTrackItem, FuzzyVideoItem

debug = DebugHelper(pluginName=settings.addon_name,
                    detailLevel=2 if settings.debug else 1,
                    enableTidalApiLog= True if tidalAddon.getSetting('debug_log') == 'true' else False)

#------------------------------------------------------------------------------
# Fuzzy Functions
#------------------------------------------------------------------------------

class FuzzyConfig(TidalConfig):

    def __init__(self):
        TidalConfig.__init__(self)

    def load(self):
        TidalConfig.load(self)


class FuzzySession(TidalSession):

    def __init__(self, config=FuzzyConfig()):
        TidalSession.__init__(self, config=config)

    def _http_error(self, e):
        try:
            if isinstance(e, HTTPError):
                r = e.response
                if r.status_code in [401, 403]:
                    msg = _T(30210)
                else:
                    msg = r.reason
                try:
                    msg = r.json().get('userMessage')
                except:
                    pass
                if r.status_code == 429:
                    # Too Many Requests. Disable Album Cache
                    self.abortAlbumThreads = True
                xbmcgui.Dialog().notification('%s Error %s' % (tidalPlugin.name, r.status_code), msg, xbmcgui.NOTIFICATION_ERROR)
        except:
            pass
        traceback.print_exc()

    def init_user(self, user_id, subscription_type):
        return FuzzyUser(self, user_id, subscription_type)

    def get_playlist(self, playlist_id):
        playlist = None
        try:
            playlist = TidalSession.get_playlist(self, playlist_id)
        except Exception as e:
            self._http_error(e)
        return playlist

    def get_playlist_items(self, playlist, offset=0, limit=9999, ret='playlistitems'):
        items = []
        try:
            items = TidalSession.get_playlist_items(self, playlist, offset=offset, limit=limit, ret=ret)
        except Exception as e:
            self._http_error(e)
        return items

    def get_playlist_tracks(self, playlist_id, offset=0, limit=9999):
        items = []
        try:
            items = TidalSession.get_playlist_tracks(self, playlist_id, offset=offset, limit=limit)
        except Exception as e:
            self._http_error(e)
        return items

    def get_album(self, album_id, withCache=True):
        album = None
        try:
            album = TidalSession.get_album(self, album_id, withCache=withCache)
        except Exception as e:
            self._http_error(e)
        return album

    def get_album_items(self, album_id, ret='playlistitems'):
        items = []
        try:
            items = TidalSession.get_album_items(self, album_id, ret=ret)
        except Exception as e:
            self._http_error(e)
        return items

    def get_album_tracks(self, album_id, withAlbum=True):
        items = []
        try:
            items = TidalSession.get_album_tracks(self, album_id, withAlbum=withAlbum)
        except Exception as e:
            self._http_error(e)
        return items

    def matchFeaturedArtist(self, text):
        # Extract Featured Artist from text
        try:
            p = re.compile('.*f(ea)?t\.?\s*(\S+[\s\S&]+).*', re.IGNORECASE)
            m = p.match(text)
            return m.group(2).strip().lower()
        except:
            pass
        return ''

    def cleanup_search_text(self, text):
        txt = text.lower()
        # Remove Featured from text
        #txt = txt.split(' ft.')[0].split(' ft ')[0].split('(ft.')[0].split('(ft ')[0].split(' feat')[0].split('(feat')[0]
        # p = re.compile('\(?f(ea)?t\.?\s*\w+[\s\w&]+\)?', re.IGNORECASE)
        p = re.compile('\(?f(ea)?t\.?\s*\S+[\s\S&]+\)?', re.IGNORECASE)
        txt = p.sub('', txt)
        # Remove text with brackets
        txt = re.sub('\(Explicit\)', '', txt)
        #txt = re.sub('\[.*\]', '', txt)
        #txt = re.sub('\(.*\)', '', txt)
        txt = txt.replace("whos", "who's")
        return txt

    def search_fuzzy(self, artist, title, album='', albumartist='', year='', limit=50):
        s_artist = self.cleanup_search_text(artist)
        s_ftartist = self.matchFeaturedArtist(artist)
        if not s_ftartist:
            s_ftartist = self.matchFeaturedArtist(title)
        s_title = self.cleanup_search_text(title)
        s_album = self.cleanup_search_text(album)
        s_albumartist = self.cleanup_search_text(albumartist)
        s_year = '%s' % year
        debug.log('Searching in TDAL: artist="%s", title="%s", album="%s", albumartist="%s", ftartist="%s", year="%s" ...' % (s_artist, s_title, s_album, s_albumartist, s_ftartist, year))
        result = SearchResult()
        artist_ids = []
        album_ids = []
        if s_artist:
            result.artists = self.search('ARTISTS', s_artist, limit=limit).artists
            # Create FuzzyArtists
            result.artists = [FuzzyArtistItem(item) for item in result.artists]
            # Calculate Fuzzy-MatchLevel of found Artists
            for item in result.artists:
                item.setFuzzyLevel(s_artist)
                pass
            # Only Artists which have the minimum MatchLevel and not blacklisted
            result.artists = [item for item in result.artists if item._isFavorite or (item._matchLevel >= settings.artist_min_level and not item.isBlacklisted())]
            # Collect the Artist-IDs
            artist_ids += [item.id for item in result.artists]
        if s_album:
            if s_albumartist and result.artists:
                searchtext = '%s - %s' % (s_albumartist, s_album)
            elif s_artist and result.artists:
                searchtext = '%s - %s' % (s_artist, s_album)
            else:
                searchtext = s_album
            items = self.search('ALBUMS', searchtext, limit=limit).albums
            if len(artist_ids) > 0:
                # Only albums of found artists
                result.albums = [item for item in items if item.artist.id in artist_ids]
            else:
                result.albums = items
            # Create FuzzyAlbums
            result.albums = [FuzzyAlbumItem(item) for item in result.albums]
            # Calculate Fuzzy-MatchLevel of found Albums
            for item in result.albums:
                item.setFuzzyLevel(s_artist, s_album, s_albumartist, s_year)
            # Remove blacklisted results
            result.albums = [item for item in result.albums if item._isFavorite or not item.isBlacklisted()]
            album_ids += [item.id for item in result.albums]
        if s_title:
            if artist and result.artists:
                searchtext = '%s - %s' % (s_artist, s_title)
            else:
                searchtext = s_title
            items = self.search('TRACKS,VIDEOS', searchtext, limit=limit)
            # Create FuzzyTracks
            result.tracks = [FuzzyTrackItem(item) for item in items.tracks]
            result.videos = [FuzzyVideoItem(item) for item in items.videos]
            # Analyze found Tracks
            for item in result.tracks:
                item.setFuzzyLevel(s_artist, s_title, s_album if s_album else s_title, s_albumartist if s_album else s_artist, s_ftartist, s_year)
            # Remove Blacklisted Tracks
            result.tracks = [item for item in result.tracks if item._isFavorite or not item.isBlacklisted()]
            # Analyze found Videos
            for item in result.videos:
                item.setFuzzyLevel(s_artist, s_title, s_year)
            # Remove Blacklisted Videos
            result.videos = [item for item in result.videos if item._isFavorite or not item.isBlacklisted()]
        return result

    def add_search_result(self, searchresults, sort=None, reverse=False, end=True):
        headline = '[COLOR yellow]-------- %s --------[/COLOR]' if tidalAddon.getSetting('color_mode') == 'true' else '-------- %s --------'
        xbmcplugin.setContent(tidalPlugin.handle, 'songs')
        if searchresults.artists.__len__() > 0:
            self.add_directory_item(_T('Artists'), tidalPlugin.url_for_path('/do_nothing'), isFolder=False, label=headline % _T('Artists'))
            if sort:
                searchresults.artists.sort(key=lambda line: line.getSortField(sort), reverse=reverse)
            self.add_list_items(searchresults.artists, end=False)
        if searchresults.albums.__len__() > 0:
            self.add_directory_item(_T('Albums'), tidalPlugin.url_for_path('/do_nothing'), isFolder=False, label=headline % _T('Albums'))
            if sort:
                searchresults.albums.sort(key=lambda line: line.getSortField(sort), reverse=reverse)
            self.add_list_items(searchresults.albums, end=False)
        if searchresults.playlists.__len__() > 0:
            self.add_directory_item(_T('Playlists'), tidalPlugin.url_for_path('/do_nothing'), isFolder=False, label=headline % _T('Playlists'))
            if sort:
                searchresults.playlists.sort(key=lambda line: line.getSortField(sort), reverse=reverse)
            self.add_list_items(searchresults.playlists, end=False)
        if searchresults.tracks.__len__() > 0:
            self.add_directory_item(_T('Tracks'), tidalPlugin.url_for_path('/do_nothing'), isFolder=False, label=headline % _T('Tracks'))
            if sort:
                searchresults.tracks.sort(key=lambda line: line.getSortField(sort), reverse=reverse)
            self.add_list_items(searchresults.tracks, end=False)
        if searchresults.videos.__len__() > 0:
            self.add_directory_item(_T('Videos'), tidalPlugin.url_for_path('/do_nothing'), isFolder=False, label=headline % _T('Videos'))
            if sort:
                searchresults.videos.sort(key=lambda line: line.getSortField(sort), reverse=reverse)
            self.add_list_items(searchresults.videos, end=False)
        if end:
            self.add_list_items([], end=True)


class FuzzyFavorites(TidalFavorites):

    def __init__(self, session, user_id):
        TidalFavorites.__init__(self, session, user_id)

    def export_ids(self, what, filename, action):
        try:
            ok = False
            path = settings.import_export_path
            if len(path) == 0:
                return
            items = action()
            items = [item for item in items if not isinstance(item, PlayableMedia) or item.available]
            if items and len(items) > 0:
                lines = ['%s' % item.id + '\t' + item.getLabel(extended=False) + '\n' for item in items]
                full_path = os.path.join(path, filename)
                f = xbmcvfs.File(full_path, 'w')
                for line in lines:
                    f.write(line.encode('utf-8'))
                f.close()
                xbmcgui.Dialog().notification(_P(what), _S(30428).format(n=len(lines)), xbmcgui.NOTIFICATION_INFO)
                ok = True
        except Exception as e:
            debug.logException(e)
        return ok

    def import_ids(self, what, filename, action):
        try:
            ok = False
            f = xbmcvfs.File(filename, 'r')
            ids = f.read().decode('utf-8').split('\n')
            f.close()
            ids = [item.split('\t')[0] for item in ids]
            ids = [item for item in ids if len(item) > 0]
            if len(ids) > 0:
                ok = action(ids)
                if ok:
                    xbmcgui.Dialog().notification(_P(what), _S(30429).format(n=len(ids)), xbmcgui.NOTIFICATION_INFO)
        except Exception as e:
            debug.logException(e)
        return ok

    def delete_all(self, what, action, remove):
        try:
            ok = False
            progress = xbmcgui.DialogProgress()
            progress.create(_S(30430).format(what=_P(what)))
            idx = 0
            items = action()
            for item in items:
                if progress.iscanceled():
                    break
                idx = idx + 1
                percent = (idx * 100) / len(items) 
                progress.update(percent, item.getLabel(extended=False))
                remove(item.id)
            ok = not progress.iscanceled()
        except Exception as e:
            debug.logException(e)
        finally:
            progress.close()
        return ok


class FuzzyUser(TidalUser):

    def __init__(self, session, user_id, subscription_type=SubscriptionType.hifi):
        TidalUser.__init__(self, session, user_id, subscription_type)
        self.favorites = FuzzyFavorites(session, user_id)

    def export_playlists(self, playlists, filename):
        path = settings.import_export_path
        if len(path) == 0:
            return
        full_path = os.path.join(path, filename)
        fd = xbmcvfs.File(full_path, 'w')
        numItems = 0
        progress = xbmcgui.DialogProgress()
        progress.create(_S(30433))
        idx = 0
        for playlist in playlists:
            idx = idx + 1
            percent = (idx * 100) / len(playlists) 
            progress.update(percent, playlist.getLabel(extended=False))
            items = self._session.get_playlist_items(playlist=playlist)
            items = [item for item in items if item.available]
            if len(items) > 0:
                numItems += playlist.numberOfItems
                fd.write(repr({ 'uuid': playlist.id,
                                'title': playlist.title,
                                'description': playlist.description,
                                'ids': [item.id for item in items]  }) + b'\n')
        fd.close()
        progress.close()
        xbmcgui.Dialog().notification(_P('Playlists'), _S(30428).format(n=numItems), xbmcgui.NOTIFICATION_INFO)

    def import_playlists(self, filename):
        try:
            ok = False
            f = xbmcvfs.File(filename, 'r')
            lines = f.read().decode('utf-8').split('\n')
            f.close()
            playlists = []
            names = []
            for line in lines:
                try:
                    if len(line) > 0:
                        item = eval(line)
                        if isinstance(item, DictionaryType):
                            playlists.append(item)
                            names.append(item.get('title'))
                except:
                    pass
            if len(names) < 1:
                return False
            selected = xbmcgui.Dialog().select(_S(30432).format(what=_T('Playlist')), names)
            if selected < 0:
                return False
            item = playlists[selected]
            item_ids = []
            for bItem in item.get('ids'):
                bItem = '%s' % bItem
                if bItem not in item_ids:
                    item_ids.append(bItem)
            dialog = xbmcgui.Dialog()
            title = dialog.input(_T(30233), item.get('title'), type=xbmcgui.INPUT_ALPHANUM)
            if not title:
                return False
            description = dialog.input(_T(30234), item.get('description'), type=xbmcgui.INPUT_ALPHANUM)
            playlist = self.create_playlist(title, description)
            if playlist:
                ok = self.add_playlist_entries(playlist=playlist, item_ids=item_ids)
                if ok:
                    xbmcgui.Dialog().notification(_T('Playlist'), _S(30429).format(n=playlist.title), xbmcgui.NOTIFICATION_INFO)
        except Exception as e:
            debug.logException(e)
        return ok

    def add_playlist_entries(self, playlist=None, item_ids=[]):
        ok = False
        try:
            ok = TidalUser.add_playlist_entries(self, playlist=playlist, item_ids=item_ids)
        except:
            try:
                progress = xbmcgui.DialogProgress()
                progress.create(_S(30434))
                valid_ids = []
                idx = 0
                notFound = 0
                for item_id in item_ids:
                    if progress.iscanceled():
                        break
                    validItem = None
                    try:
                        validItem = self._session.get_track(item_id)
                    except:
                        pass
                    if not validItem:
                        try:
                            validItem = self._session.get_video(item_id)
                        except:
                            pass
                    idx = idx + 1
                    percent = (idx * 100) / len(item_ids)
                    if validItem:
                        line1 = validItem.getLabel(extended=False)
                        valid_ids.append(item_id)
                    else:
                        line1 = '%s: %s' % (item_id, _S(30412))
                        notFound = notFound + 1
                    line3 = '%s: %s' % (_S(30412), notFound)
                    progress.update(percent, line1=line1, line2=_S(30413).format(n=len(valid_ids), m=len(item_ids)), line3=line3)
                if len(valid_ids) > 0 and not progress.iscanceled():
                    ok = TidalUser.add_playlist_entries(self, playlist=playlist, item_ids=valid_ids)
            except:
                pass
            finally:
                progress.close()
        return ok


class NewMusicSearcher(object):

    def __init__(self, session, album_playlist, track_playlist, video_playlist, limit, diffDays):
        self.session = session
        self.album_playlist = album_playlist
        self.track_playlist = track_playlist
        self.video_playlist = video_playlist
        self.found_albums = []
        self.found_tracks = []
        self.found_videos = []
        self.artistQueue = Queue(maxsize=99999)
        self.artistCount = 0
        self.searchLimit = limit
        self.diffDays = diffDays
        self.abortThreads = True
        self.runningThreads = {}
        self.progress = xbmcgui.DialogProgressBG()

    def progress_update(self, heading):
        try:
            self.progress.update(percent=((self.artistCount - self.artistQueue.qsize()) * 100) / self.artistCount,
                                 heading=heading,
                                 message='%s:%s, %s:%s, %s:%s (Threads:%s)' % (_P('albums'), len(self.found_albums),
                                                                               _P('tracks'), len(self.found_tracks),
                                                                               _P('videos'), len(self.found_videos),
                                                                               len(self.runningThreads.keys())) )
        except:
            pass

    def search_thread(self):
        try:
            debug.log('Search Thread %s started.' % currentThread().ident)
            while not xbmc.Monitor().waitForAbort(timeout=0.01) and not self.abortThreads:
                try:
                    artist = self.artistQueue.get_nowait()
                except:
                    break
                try:
                    items = []
                    if not self.abortThreads and self.album_playlist.id:
                        items += self.session.get_artist_albums(artist.id, limit=self.searchLimit)
                    if not self.abortThreads and (self.album_playlist.id or self.track_playlist.id):
                        items += self.session.get_artist_albums_ep_singles(artist.id, limit=self.searchLimit)
                    if not self.abortThreads and self.video_playlist.id:
                        items += self.session.get_artist_videos(artist.id, limit=self.searchLimit)
                    for item in items:
                        if self.abortThreads: break
                        diff = datetime.today() - item.releaseDate
                        if not item._userplaylists and diff.days < self.diffDays:
                            if isinstance(item, VideoItem):
                                if not '%s' % item.id in self.found_videos:
                                    debug.log('Found new Video: %s' % item.getLabel(extended=False))
                                    self.found_videos.append('%s' % item.id)
                            elif isinstance(item, AlbumItem):
                                tracks = self.session.get_album_items(item.id)
                                for track in tracks:
                                    if track.available:
                                        # Use first Track in an Album as PlaylistItem
                                        if item.type == AlbumType.album or item.type == AlbumType.ep:
                                            if not '%s' % track.id in self.found_albums:
                                                debug.log('Found new Album: %s' % item.getLabel(extended=False))
                                                self.found_albums.append('%s' % track.id)
                                        elif not track._userplaylists:
                                            if not '%s' % track.id in self.found_tracks:
                                                debug.log('Found new Track: %s' % item.getLabel(extended=False))
                                                self.found_tracks.append('%s' % track.id)
                                        break
                    self.progress_update(heading='%s: %s' % (_T('artist'), artist.name))
                    pass
                except requests.HTTPError as e:
                    r = e.response
                    msg = 'Error'
                    try:
                        msg = r.reason
                        msg = r.json().get('userMessage')
                    except:
                        pass
                    #debug.log('Error getting Album ID %s' % album_id, xbmc.LOGERROR)
                    if r.status_code == 429 and not self.abortThreads:
                        self.abortThreads = True
                        debug.log('Too many requests. Aborting Workers ...', xbmc.LOGERROR)
                        self.albumQueue._init(9999)
                        xbmcgui.Dialog().notification(_S(30437), msg, xbmcgui.NOTIFICATION_ERROR)
        except Exception as e:
            traceback.print_exc()
        self.runningThreads.pop(currentThread().ident, None)
        debug.log('Search Thread %s terminated.' % currentThread().ident)
        return

    def search(self, artists, thread_count=1):
        for artist in artists:
            try:
                if VARIOUS_ARTIST_ID != '%s' % artist.id and not artist._isLocked:
                    self.artistQueue.put(artist)
            except:
                if VARIOUS_ARTIST_ID != '%s' % artist.id:
                    self.artistQueue.put(artist)
        self.artistCount = self.artistQueue.qsize()
        if self.artistCount < 1:
            debug.log('No Artist to search ...')
            return
        debug.log('Start: Searching new Music for %s Artists ...' % self.artistCount)
        self.abortThreads = False
        threadsToStart = thread_count if thread_count < self.artistCount else self.artistCount
        self.runningThreads = {}
        self.progress = xbmcgui.DialogProgressBG()
        self.progress.create(heading=_S(30437))
        try:
            self.progress_update(heading=_S(30437))
            xbmc.sleep(500)
            while len(self.runningThreads.keys()) < threadsToStart:
                try:
                    worker = Thread(target=self.search_thread)
                    worker.start()
                    self.runningThreads.update({worker.ident: worker})
                except Exception as e:
                    debug.log(str(e), xbmc.LOGERROR)
            debug.log('Waiting until all Threads are terminated')
            startTime = datetime.today()
            stopWatch = startTime
            remainingArtists = self.artistCount
            lastCount = self.artistCount
            while len(self.runningThreads.keys()) > 0 and not xbmc.Monitor().waitForAbort(timeout=0.01):
                for worker in self.runningThreads.values():
                    worker.join(5)
                    if config.getSetting('search_artist_music_abort') == 'true':
                        debug.log('Stopping all Workers ...')
                        self.abortThreads = True
                        config.setSetting('search_artist_music_abort', 'false')
                    if worker.isAlive():
                        now = datetime.today()
                        runningTime = now - startTime
                        remainingArtists = self.artistQueue.qsize()
                        debug.log('Workers still running after %s seconds, %s Artists remaining ...' % (runningTime.seconds, remainingArtists))
                        diff = now - stopWatch
                        if lastCount > remainingArtists:
                            # Workers are still removing artists from the queue
                            lastCount = remainingArtists
                            stopWatch = now
                        elif diff.seconds >= 60:
                            # Timeout: Stopping Threads with the Stop-Flag
                            debug.log('Timeout, sending Stop to Workers ...')
                            self.abortThreads = True
                            break
                    else:
                        # Removing terminates Thread
                        self.runningThreads.pop(worker.ident, None)
                if self.abortThreads:
                    xbmcgui.Dialog().notification(_S(30437), _S(30444), icon=xbmcgui.NOTIFICATION_WARNING)
                    for worker in self.runningThreads.values():
                        debug.log('Waiting for Thread %s to terminate ...' % worker.ident)
                        worker.join(5)
                        self.runningThreads.pop(worker.ident, None)
                    xbmc.sleep(2000)
            if len(self.found_albums) > 0 or len(self.found_tracks) > 0 or len(self.found_videos) > 0:
                self.progress_update(heading=_S(30441))
                if len(self.found_albums) > 0 and self.album_playlist.id:
                    self.album_playlist._etag = None
                    try:
                        self.session.user.add_playlist_entries(self.album_playlist, self.found_albums)
                    except:
                        pass
                if len(self.found_tracks) > 0 and self.track_playlist.id:
                    self.track_playlist._etag = None
                    try:
                        self.session.user.add_playlist_entries(self.track_playlist, self.found_tracks)
                    except:
                        pass
                if len(self.found_videos) > 0 and self.video_playlist.id:
                    self.video_playlist._etag = None
                    try:
                        self.session.user.add_playlist_entries(self.video_playlist, self.found_videos)
                    except:
                        pass
                message = '%s:%s, %s:%s, %s:%s' % (_P('albums'), len(self.found_albums),
                                                   _P('tracks'), len(self.found_tracks),
                                                   _P('videos'), len(self.found_videos))
                xbmcgui.Dialog().notification(_S(30440), message, icon=xbmcgui.NOTIFICATION_INFO)
                debug.log('Found: %s' % message)
            else:
                debug.log('No new Music found !')
                xbmcgui.Dialog().notification(_S(30437), _S(30443), icon=xbmcgui.NOTIFICATION_INFO)
        except Exception as e:
            debug.log(str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(_S(30437), _S(30442), icon=xbmcgui.NOTIFICATION_ERROR)
        finally:
            xbmc.sleep(2000)
            self.progress.close()
        debug.log('End: Searching for new Music.')

# End of File