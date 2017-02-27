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

import traceback, urllib, os
from datetime import datetime

import xbmc, xbmcgui, xbmcvfs
from routing import Plugin
from requests import HTTPError

from tidalapi import SearchResult, AlbumType, Playlist
from koditidal import _T, _P, addon as tidalAddon, _addon_id as _tidal_addon_id, VARIOUS_ARTIST_ID
from koditidal2 import AlbumItem2, VideoItem2, PlaylistItem2

from resources.lib.tidalsearch.config import CONST, settings, _S
from resources.lib.tidalsearch.fuzzysession import FuzzySession
from resources.lib.tidalsearch import item_info, config, debug

#------------------------------------------------------------------------------
# Initialization
#------------------------------------------------------------------------------

plugin = Plugin(settings.addon_base_url)
plugin.name = settings.addon_name

# Init Session Configuration
session = FuzzySession()
session.load_session()

add_items = session.add_list_items
add_directory = session.add_directory_item
add_search_results = session.add_search_result

FOLDER_MASK = '[COLOR blue]%s[/COLOR]' if tidalAddon.getSetting('color_mode') == 'true' else '%s'

#------------------------------------------------------------------------------
# Plugin Functions
#------------------------------------------------------------------------------


@plugin.route('/iteminfo')
def iteminfo():
    item_info.itemInfoDialog()


@plugin.route('/search_selected')
def search_selected():
    item = item_info.getSelectedListItem()
    artist = item.get('Artist')
    title = item.get('Title')
    if artist and title:
        s_text = '%s - %s' % (artist, title)
    else:
        s_text = item.get('Label').strip()
    if s_text:
        xbmc.executebuiltin('RunPlugin(%s)' % plugin.url_for(search_field, field='all', text=urllib.quote_plus(s_text.encode('utf-8'))))


@plugin.route('/search_field/<field>/<text>')
def search_field(field, text):
    # Unquote special Characters
    s_field = urllib.unquote_plus(field).decode('utf-8').strip()
    s_text = urllib.unquote_plus(text).decode('utf-8').strip()
    values = {'field': s_field, 'text': s_text}
    config.setSetting('search_parameters_field', repr(values))
    # Execute Search in new Container
    xbmc.executebuiltin('Container.Update(%s, True)' % plugin.url_for(search_field_exec))


@plugin.route('/search_field_exec')
def search_field_exec():
    try:
        params = eval(config.getSetting('search_parameters_field'))
        params.update({'search': ''})
    except:
        debug.log('Search Parameters not set !', xbmc.LOGERROR)
        return
    s_field = params.get('field')
    s_text = params.get('text')
    searchresults = session.search(s_field, s_text, limit=50 if s_field.upper() == 'ALL' else 100)
    add_directory(_S(30400), plugin.url_for(search_field_edit), isFolder=False)
    add_search_results(searchresults)


@plugin.route('/search_field_edit')
def search_field_edit():
    try:
        params = eval(config.getSetting('search_parameters_field'))
        params.update({'search': ''})
    except:
        debug.log('Search Parameters not set !', xbmc.LOGERROR)
        return
    s_text = params.get('text')
    keyboard = xbmc.Keyboard(s_text, _S(30401))
    keyboard.doModal()
    if keyboard.isConfirmed():
        value = keyboard.getText().decode('utf-8')
        params.update({'text': value})
        config.setSetting('search_parameters_field', repr(params))
        xbmc.executebuiltin('Container.Refresh()')


@plugin.route('/search_fuzzy')
def search_fuzzy():
    item = item_info.getSelectedListItem()
    artist = item.get('Artist')
    title = item.get('Title')
    album = item.get('Album') if not item.get('Compilation') else ' ' # item.get('Title')
    albumartist = item.get('AlbumArtist') if not item.get('Compilation') else ' ' # item.get('Artist')
    year = '%s' % item.get('YearInt')

    if not artist: artist = ' '
    if not title: title = ' '
    if not album: album = ' '
    if not albumartist: albumartist = ' '
    if not year: year = ' '

    xbmc.executebuiltin('RunPlugin(%s)' % plugin.url_for(search_fuzzy_fields, urllib.quote_plus(artist.encode('utf-8')),
                                                                              urllib.quote_plus(title.encode('utf-8')),
                                                                              urllib.quote_plus(album.encode('utf-8')),
                                                                              urllib.quote_plus(albumartist.encode('utf-8')),
                                                                              urllib.quote_plus(year.encode('utf-8'))))


@plugin.route('/search_fuzzy_fields/<artist>/<title>/<album>/<albumartist>/<year>')
def search_fuzzy_fields(artist, title, album, albumartist, year):
    # This Function should be called with RunPlugin(...) and not with Container.Update(...)
    # Unquote special Characters
    s_artist = urllib.unquote_plus(artist).decode('utf-8').strip()
    s_title = urllib.unquote_plus(title).decode('utf-8').strip()
    s_album = urllib.unquote_plus(album).decode('utf-8').strip()
    s_albumartist = urllib.unquote_plus(albumartist).decode('utf-8').strip()
    s_year = urllib.unquote_plus(year).decode('utf-8').strip()
    # Save Search Parameters
    values = {'artist': s_artist, 'title': s_title, 'album': s_album, 'albumartist': s_albumartist, 'year': s_year}
    config.setSetting('search_parameters', repr(values))
    # Execute Search in new Container
    xbmc.executebuiltin('Container.Update(%s, True)' % plugin.url_for(search_fuzzy_exec))


@plugin.route('/search_fuzzy_exec')
def search_fuzzy_exec():
    try:
        params = eval(config.getSetting('search_parameters'))
        params.update({'search': ''})
    except:
        debug.log('Search Parameters not set !', xbmc.LOGERROR)
        return
    s_artist = params.get('artist')
    s_title = params.get('title')
    s_album = params.get('album')
    s_albumartist = params.get('albumartist')
    s_year = params.get('year')
    # Search now
    searchresults = session.search_fuzzy(s_artist, s_title, s_album, s_albumartist, s_year, limit=20)
    # Display the Search Results
    add_directory(_S(30400), plugin.url_for(search_fuzzy_edit), isFolder=False)
    add_search_results(searchresults, sort='match', reverse=True)


@plugin.route('/search_fuzzy_edit')
def search_fuzzy_edit():
    try:
        params = eval(config.getSetting('search_parameters'))
        params.update({'search': ''})
    except:
        debug.log('Search Parameters not set !', xbmc.LOGERROR)
        return
    cmds = [('search', _S(30400) ),
            ('artist', _T('artist') + ': '),
            ('title', _T('track') + ': '),
            ('album', _T('album') + ': '),
            ('albumartist', _S(30402) + ': '),
            ('year', _S(30403) + ': '),
            ]
    answer = 1
    while answer > 0:
        menue = ['%s%s' % (FOLDER_MASK % s_head, params.get(s_key)) for s_key, s_head in cmds]
        answer = xbmcgui.Dialog().select(_S(30400), menue)
        if answer > 0:
            keyboard = xbmc.Keyboard(params.get(cmds[answer][0]).encode('utf-8'), cmds[answer][1])
            keyboard.doModal()
            if keyboard.isConfirmed():
                value = keyboard.getText().decode('utf-8')
                params.update({cmds[answer][0]: value})
    if answer == 0:
        config.setSetting('search_parameters', repr(params))
        xbmc.executebuiltin('Container.Refresh()')
    pass


@plugin.route('/convert_to_playlist/<item_type>')
def convert_to_playlist(item_type):
    if not session.is_logged_in:
        xbmcgui.Dialog().notification(plugin.name, _S(30404), xbmcgui.NOTIFICATION_ERROR)
        return
    # Submenu: Parameters for Playlist-Generation
    cmds = [('action', _S(30405)),
            ('playlist', _T('playlist') + ': '),
            ('Position', _S(30406) + ': '),
            ('NumItems', _S(30407) + ': '),
            ]
    item = item_info.getSelectedListItem()
    item['action'] = ''
    item['playlist_id'] = ''
    item['playlist'] = ''
    playlist_id = tidalAddon.getSetting('default_videoplaylist_id') if item_type.startswith('video') else tidalAddon.getSetting('default_trackplaylist_id')
    if playlist_id:
        try:
            playlist = session.get_playlist(playlist_id)
            if playlist:
                item['playlist_id'] = playlist.id
                item['playlist'] = playlist.title
        except:
            pass
    numItems = item['NumItems']
    answer = 1
    while answer > 0:
        menue = ['%s%s' % (FOLDER_MASK % s_head, item.get(s_key)) for s_key, s_head in cmds]
        answer = xbmcgui.Dialog().select(_S(30408), menue)
        if answer == 0 and not item['playlist_id']:
            answer = 1 # Playlist not set
        if answer > 0:
            if answer == 1:
                playlist = session.user.selectPlaylistDialog(_S(30409) % _P('tracks' if item_type.startswith('track') else 'videos'), allowNew=True)
                if playlist:
                    item['playlist_id'] = playlist.id
                    item['playlist'] = playlist.title
            elif answer >= 2 and answer <= 3:
                value = int('0%s' % xbmcgui.Dialog().input(cmds[answer][1], str(item.get(cmds[answer][0])), type=xbmcgui.INPUT_NUMERIC))
                if ( answer == 2 and value <= numItems and value <= item['NumItems'] ) or \
                   ( answer == 3 and value <= numItems and value >= item['Position'] ):
                    item.update({cmds[answer][0]: value})
            else:
                keyboard = xbmc.Keyboard(item.get(cmds[answer][0]).encode('utf-8'), cmds[answer][1])
                keyboard.doModal()
                if keyboard.isConfirmed():
                    value = keyboard.getText().decode('utf-8')
                    item.update({cmds[answer][0]: value})
    if answer == 0:
        convert_to_playlist_run(item_type, '0%s' % item['Position'], '0%s' % item['NumItems'], item['playlist_id'])


@plugin.route('/convert_to_playlist_run/<item_type>/<from_pos>/<to_pos>/<playlist_id>')
def convert_to_playlist_run(item_type, from_pos, to_pos, playlist_id):
    playlist = session.get_playlist(playlist_id)
    if not playlist:
        debug.log('Playlist "%s" not found.' % playlist_id, xbmc.LOGERROR)
        return
    listitems = item_info.getAllListItems()
    numItems = len(listitems)
    if numItems == 0:
        debug.log('No ListItems found.', xbmc.LOGERROR)
        return
    pos = min(int(from_pos), numItems) - 1
    lastPos = min(int(to_pos), numItems) - 1
    numItems = lastPos - pos + 1
    progress = xbmcgui.DialogProgress()
    progress.create(_S(30410))
    percent = 0
    line1 = ''
    line2 = ''
    line3 = _S(30411)
    items = []
    while pos <= lastPos and not progress.iscanceled():
        li = listitems[pos]
        artist = li.get('Artist')
        title = li.get('Title')
        album = li.get('Album') if not li.get('Compilation') else '' # item.get('Title')
        albumartist = li.get('AlbumArtist') if not li.get('Compilation') else '' # item.get('Artist')
        year = '%s' % li.get('YearInt')
        percent = (pos * 100) / numItems 
        line1 = '%s: %s' % (_T('artist'), artist)
        line2 = '%s: %s' % (_T('track'), title)
        progress.update(percent, line1, line2, line3)
        debug.log('Searching Title: %s - %s' % (artist, title), xbmc.LOGNOTICE)
        item_id = li.get('video_id', None) if item_type.startswith('video') else li.get('track_id', None)
        if item_id:
            track = session.get_track(item_id, withAlbum=True)
            if track:
                line3 = 'TIDAL-ID %s: %s - %s (%s)' % (track.id, track.artist.name, track.title, track.year)
                debug.log('Found TIDAL Track-Id %s: %s - %s' % (track.id, track.artist.name, track.title), xbmc.LOGNOTICE)
                items.append(track)
                pos = pos + 1
                continue
        result = session.search_fuzzy(artist, title, album, albumartist, year, limit=20)
        if item_type.startswith('track') and len(result.tracks) > 0:
            # Sort over matchLevel
            result.tracks.sort(key=lambda line: line.getSortField('match'), reverse=True)
            # Take the first result (best matchLevel) 
            track = result.tracks[0]
            line3 = 'ID %s: %s - %s (%s)' % (track.id, track.artist.name, track.title, track.year)
            debug.log('Found Title Id %s: %s - %s' % (track.id, track.artist.name, track.title), xbmc.LOGNOTICE)
            items.append(track)
        elif item_type.startswith('video') and len(result.videos) > 0:
            # Sort over matchLevel
            result.videos.sort(key=lambda line: line.getSortField('match'), reverse=True)
            # Take the first result (best matchLevel) 
            video = result.videos[0]
            line3 = 'ID %s: %s - %s (%s)' % (video.id, video.artist.name, video.title, video.year)
            debug.log('Found Video Id %s: %s - %s' % (video.id, video.artist.name, video.title), xbmc.LOGNOTICE)
            items.append(video)
        else:
            debug.log('Title not found.', xbmc.LOGNOTICE)
            line3 = '%s: %s - %s' % (_S(30412), li.get('Artist'), li.get('Title'))
        pos = pos + 1

    progress.update(percent, line1, line2, line3)
    xbmc.sleep(2000)
    foundItems = len(items)
    line2 = _S(30413) % (foundItems, numItems)
    if progress.iscanceled():
        yes = xbmcgui.Dialog().yesno(_S(30414), _S(30415), line2, _S(30416))
        if not yes:
            progress.close()
            debug.log('Search aborted by user.', xbmc.LOGNOTICE)
            return False
    if playlist and foundItems > 0:
        progress.update(99, _S(30417), line2, _S(30418))
        session.user.add_playlist_entries(playlist=playlist, item_ids=['%s' % item.id for item in items])
        progress.update(100, _S(30417), ' ', ' ')
    xbmc.sleep(1000)
    progress.close()

    debug.log('Search terminated successfully.', xbmc.LOGNOTICE)
    return True


@plugin.route('/user_playlist/add_id/<playlist_id>/<item_id>')
def user_playlist_add_id(playlist_id, item_id):
    try:
        playlist = session.get_playlist(playlist_id)
        if playlist:
            session.user.add_playlist_entries(playlist=playlist, item_ids=['%s' % item_id])
            numItems = playlist.numberOfItems + 1
            debug.log('Added ID %s to Playlist %s at position %s' % (item_id, playlist.title, numItems))
    except Exception, e:
        debug.log(e, 'Failed to add ID %s to playlist %s' % (item_id, playlist_id), level=xbmc.LOGERROR)
        traceback.print_exc()


@plugin.route('/favorites/export/<what>')
def favorites_export(what):
    name = 'favo_%s_%s.cfg' % (what, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
    if not session.is_logged_in:
        return
    if what == 'playlists':
        session.user.favorites.export_ids(what=_P('Playlists'), filename=name, action=session.user.favorites.playlists)
    elif what == 'artists':
        session.user.favorites.export_ids(what=_P('Artists'), filename=name, action=session.user.favorites.artists)
    elif what == 'albums':
        session.user.favorites.export_ids(what=_P('Albums'), filename=name, action=session.user.favorites.albums)
    elif what == 'tracks':
        session.user.favorites.export_ids(what=_P('Tracks'), filename=name, action=session.user.favorites.tracks)
    elif what == 'videos':
        session.user.favorites.export_ids(what=_P('Videos'), filename=name, action=session.user.favorites.videos)


@plugin.route('/favorites/import/<what>')
def favorites_import(what):
    path = settings.import_export_path
    if len(path) == 0 or not session.is_logged_in:
        return
    files = xbmcvfs.listdir(path)[1]
    files = [name for name in files if name.startswith('favo_%s' % what)]
    selected = xbmcgui.Dialog().select(path, files)
    if selected < 0:
        return
    name = os.path.join(path, files[selected])
    ok = False
    if what == 'playlists':
        ok = session.user.favorites.import_ids(what=_T('Playlists'), filename=name, action=session.user.favorites.add_playlist)
    elif what == 'artists':
        ok = session.user.favorites.import_ids(what=_T('Artists'), filename=name, action=session.user.favorites.add_artist)
    elif what == 'albums':
        ok = session.user.favorites.import_ids(what=_T('Albums'), filename=name, action=session.user.favorites.add_album)
    elif what == 'tracks':
        ok = session.user.favorites.import_ids(what=_T('Tracks'), filename=name, action=session.user.favorites.add_track)
    elif what == 'videos':
        ok = session.user.favorites.import_ids(what=_T('Videos'), filename=name, action=session.user.favorites.add_video)
    return ok


@plugin.route('/favorites/delete_all/<what>')
def favorites_delete_all(what):
    ok = xbmcgui.Dialog().yesno(heading=_S(30430) % _P(what), line1=_S(30431).format(what=_P(what)))
    if ok:
        if what == 'playlists':
            session.user.favorites.delete_all(what=_T('Playlists'), action=session.user.favorites.playlists, remove=session.user.favorites.remove_playlist)
        elif what == 'artists':
            session.user.favorites.delete_all(what=_T('Artists'), action=session.user.favorites.artists, remove=session.user.favorites.remove_artist)
        elif what == 'albums':
            session.user.favorites.delete_all(what=_T('Albums'), action=session.user.favorites.albums, remove=session.user.favorites.remove_album)
        elif what == 'tracks':
            session.user.favorites.delete_all(what=_T('Tracks'), action=session.user.favorites.tracks, remove=session.user.favorites.remove_track)
        elif what == 'videos':
            session.user.favorites.delete_all(what=_T('Videos'), action=session.user.favorites.videos, remove=session.user.favorites.remove_video)
    return ok


@plugin.route('/user_playlist_export/<playlist_id>')
def user_playlist_export(playlist_id):
    if not session.is_logged_in:
        return
    try:
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        playlist = session.get_playlist(playlist_id)
        if playlist and playlist.numberOfItems > 0:
            filename = 'playlist_%s_%s.cfg' % (playlist.title, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
            filename = filename.replace(' ', '_')
            session.user.export_playlists([playlist], filename)
    except Exception, e:
        debug.logException(e)
    finally:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )


@plugin.route('/user_playlist_export_all')
def user_playlist_export_all():
    if not session.is_logged_in:
        return
    try:
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        items = session.user.playlists()
        filename = 'playlist_all_%s.cfg' % datetime.now().strftime('%Y-%m-%d-%H%M%S')
        session.user.export_playlists(items, filename)
    except Exception, e:
        debug.logException(e)
    finally:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )


@plugin.route('/user_playlist_import')
def user_playlist_import():
    path = settings.import_export_path
    if len(path) == 0 or not session.is_logged_in:
        return
    files = xbmcvfs.listdir(path)[1]
    files = [name for name in files if name.startswith('playlist_')]
    selected = xbmcgui.Dialog().select(path, files)
    if selected < 0:
        return
    name = os.path.join(path, files[selected])
    try:
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        session.user.import_playlists(name)
    except Exception, e:
        debug.logException(e)
    finally:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )    


def search_artist_news_run(progress, pos, numItems, artist, items, diff_days, result, total, album_playlist, track_playlist, video_playlist):
    found_items = []
    for item in items:
        diff = datetime.today() - item.releaseDate
        if not item._userplaylists and diff.days < diff_days:
            if isinstance(item, VideoItem2):
                found_items.append(item)
                result.videos.append(item)
                total.videos.append(item)
            elif isinstance(item, AlbumItem2):
                if item.type == 'ALBUM':
                    found_items.append(item)
                    result.albums.append(item)
                    total.albums.append(item)
                else:
                    # EPs and Singles
                    found_items.append(item)
                    result.tracks.append(item)
                    total.tracks.append(item)
    line1 = '%s: %s' % (_T('artist'), artist.name)
    line2 = '%s %s / %s %s / %s %s' % (len(result.albums), _P('albums'), len(result.tracks), 'Singles', len(result.videos), _P('videos'))
    line3 = _S(30411) if len(found_items) == 0 else _S(30440)
    percent = (pos * 100) / numItems
    progress.update(percent, line1, line2, line3)
    # Add to Playlist here ...
    album_ids = []
    track_ids = []
    video_ids = []
    for item in found_items:
        if progress.iscanceled():
            return
        if item._userplaylists:
            continue
        if isinstance(item, VideoItem2):
            video_ids.append('%s' % item.id)
        elif isinstance(item, AlbumItem2):
            tracks = session.get_album_items(item.id)
            for track in tracks:
                if track.available:
                    if not track._userplaylists:
                        if item.type == AlbumType.album or item.type == AlbumType.ep:
                            album_ids.append('%s' % track.id)
                        else:
                            track_ids.append('%s' % track.id)
                    break
    if len(album_ids) > 0 or len(track_ids) > 0 or len(video_ids) > 0:
        line3 = _S(30441)
        progress.update(percent, line1, line2, line3)
        if len(album_ids) > 0 and album_playlist.id:
            album_playlist._etag = None
            session.user.add_playlist_entries(album_playlist, album_ids)
        if len(track_ids) > 0 and track_playlist.id:
            track_playlist._etag = None
            session.user.add_playlist_entries(track_playlist, track_ids)
        if len(video_ids) > 0 and video_playlist.id:
            video_playlist._etag = None
            session.user.add_playlist_entries(video_playlist, video_ids)
    return


@plugin.route('/search_artist_news')
def search_artist_news():
    if not session.is_logged_in:
        xbmcgui.Dialog().notification(plugin.name, _S(30404), xbmcgui.NOTIFICATION_ERROR)
        return
    item = item_info.getSelectedListItem()
    artists = []
    if item.get('FileNameAndPath').find('%s/artist/' % _tidal_addon_id) >= 0:
        artist_id = item.get('FileNameAndPath').split('/artist/')[1].split('/')[0]
        artist = session.get_artist(artist_id)
        if artist:
            artists.append(artist)
    else:
        artists = session.user.favorites.get('artists')
    if len(artists) == 0:
        debug.log('No selected Artists found', level=xbmc.LOGERROR)
        return

    if not session.is_logged_in:
        xbmcgui.Dialog().notification(plugin.name, _S(30404), xbmcgui.NOTIFICATION_ERROR)
        return
    # Submenu: Parameters for Playlist-Generation
    cmds = [('action', _S(30405)),
            ('album_playlist', _S(30409) % _P('albums') + ': '),
            ('track_playlist', _S(30409) % _P('tracks') + ': '),
            ('video_playlist', _S(30409) % _P('videos') + ': '),
            ('limit', _S(30438) + ': '),
            ('diff_days', _S(30439) + ': '),
            ]
    if tidalAddon.getSetting('default_albumplaylist_id'):
        album_playlist = session.get_playlist(tidalAddon.getSetting('default_albumplaylist_id'))
        if not album_playlist:
            album_playlist = PlaylistItem2()
            album_playlist.title = ''
    if tidalAddon.getSetting('default_trackplaylist_id'):
        track_playlist = session.get_playlist(tidalAddon.getSetting('default_trackplaylist_id'))
        if not track_playlist:
            track_playlist = PlaylistItem2()
            track_playlist.title = ''
    if tidalAddon.getSetting('default_videoplaylist_id'):
        video_playlist = session.get_playlist(tidalAddon.getSetting('default_videoplaylist_id'))
        if not video_playlist:
            video_playlist = PlaylistItem2()
            video_playlist.title = ''
    item = {'action': '',
            'album_playlist': album_playlist.title,
            'album_playlist_id': album_playlist.id,
            'track_playlist': track_playlist.title,
            'track_playlist_id': track_playlist.id,
            'video_playlist': video_playlist.title,
            'video_playlist_id': video_playlist.title,
            'limit': 40,
            'diff_days': 90
            }
    answer = 1
    while answer > 0:
        menue = ['%s%s' % (FOLDER_MASK % s_head, item.get(s_key)) for s_key, s_head in cmds]
        answer = xbmcgui.Dialog().select(_S(30437), menue)
        if answer > 0:
            if answer >= 1 and answer <= 3:
                playlist = session.user.selectPlaylistDialog(_S(30409) % _P(['', 'albums', 'tracks', 'videos'][answer]), allowNew=True)
                if playlist:
                    item[['', 'album_playlist_id', 'track_playlist_id', 'video_playlist_id'][answer]] = playlist.id
                    item[['', 'album_playlist', 'track_playlist', 'video_playlist'][answer]] = playlist.title
                    if answer == 1:
                        album_playlist = playlist
                    elif answer == 2:
                        track_playlist = playlist
                    elif answer == 3:
                        video_playlist = playlist
                else:
                    item[['', 'album_playlist_id', 'track_playlist_id', 'video_playlist_id'][answer]] = None
                    item[['', 'album_playlist', 'track_playlist', 'video_playlist'][answer]] = ''
                    if answer == 1:
                        album_playlist = PlaylistItem2(Playlist())
                        album_playlist.title = ''
                    elif answer == 2:
                        track_playlist = PlaylistItem2(Playlist())
                        track_playlist.title = ''
                    elif answer == 3:
                        video_playlist = PlaylistItem2(Playlist())
                        video_playlist.title = ''
            elif answer >= 4 and answer <= 5:
                value = int('0%s' % xbmcgui.Dialog().input(cmds[answer][1], str(item.get(cmds[answer][0])), type=xbmcgui.INPUT_NUMERIC))
                item.update({cmds[answer][0]: value})
    if answer < 0:
        return
    # Searching now
    progress = xbmcgui.DialogProgress()
    progress.create(_S(30437))
    progress.update(0, line1=_S(30411))
    numItems = len(artists) * 3  # Albums, Singles, Videos
    pos = 0
    limit = item.get('limit', 20)
    diff_days = item.get('diff_days', 90)
    total = SearchResult()
    for artist in artists:
        if progress.iscanceled():
            break
        if VARIOUS_ARTIST_ID == '%s' % artist.id:
            continue
        debug.log('Searching for artist %s ...' % artist.name, xbmc.LOGNOTICE)
        result = SearchResult()
        pos += 1
        if album_playlist.id:
            items = session.get_artist_albums(artist.id, limit=limit)
            search_artist_news_run(progress, pos, numItems, artist, items, diff_days, result, total, album_playlist, track_playlist, video_playlist)
        pos += 1
        if album_playlist.id or track_playlist.id:
            items = session.get_artist_albums_ep_singles(artist.id, limit=limit)
            search_artist_news_run(progress, pos, numItems, artist, items, diff_days, result, total, album_playlist, track_playlist, video_playlist)
        pos += 1
        if video_playlist.id:
            items = session.get_artist_videos(artist.id, limit=limit)
            search_artist_news_run(progress, pos, numItems, artist, items, diff_days, result, total, album_playlist, track_playlist, video_playlist)
        if len(result.albums) > 0 or len(result.tracks) > 0 or len(result.videos) > 0:
            total.artists.append(artist)
    progress.update(100, line1=_S(30417))
    xbmc.sleep(2000)
    progress.close()
    return

#------------------------------------------------------------------------------
# Context Menu Function
#------------------------------------------------------------------------------

@plugin.route('/context_menu')
def context_menu():
    commands = []
    item = item_info.getSelectedListItem()
    if item.get('Artist') and item.get('Title'):
        commands.append( (_S(30420), search_fuzzy) )
        commands.append( (_S(30419), search_selected) )
        commands.append( (_S(30421), 'RunPlugin(plugin://%s/convert_to_playlist/tracks)' % CONST.addon_id) )
        commands.append( (_S(30422), 'RunPlugin(plugin://%s/convert_to_playlist/videos)' % CONST.addon_id) )
    if item.get('FileNameAndPath').find('%s/favorites/artists' % _tidal_addon_id) >= 0:
        commands.append( (_S(30437), 'RunPlugin(plugin://%s/search_artist_news)' % CONST.addon_id) )
        commands.append( (_S(30426) % _P('artists'), 'RunPlugin(plugin://%s/favorites/export/artists)' % CONST.addon_id) )
        commands.append( (_S(30427) % _P('artists'), 'RunPlugin(plugin://%s/favorites/import/artists)' % CONST.addon_id) )
        commands.append( (_S(30436) % _P('artists'), 'RunPlugin(plugin://%s/favorites/delete_all/artists)' % CONST.addon_id) )
    elif item.get('FileNameAndPath').find('%s/favorites/albums' % _tidal_addon_id) >= 0:
        commands.append( (_S(30426) % _P('albums'), 'RunPlugin(plugin://%s/favorites/export/albums)' % CONST.addon_id) )
        commands.append( (_S(30427) % _P('albums'), 'RunPlugin(plugin://%s/favorites/import/albums)' % CONST.addon_id) )
        commands.append( (_S(30436) % _P('albums'), 'RunPlugin(plugin://%s/favorites/delete_all/albums)' % CONST.addon_id) )
    elif item.get('FileNameAndPath').find('%s/favorites/playlists' % _tidal_addon_id) >= 0:
        commands.append( (_S(30426) % _P('playlists'), 'RunPlugin(plugin://%s/favorites/export/playlists)' % CONST.addon_id) )
        commands.append( (_S(30427) % _P('playlists'), 'RunPlugin(plugin://%s/favorites/import/playlists)' % CONST.addon_id) )
        commands.append( (_S(30436) % _P('playlists'), 'RunPlugin(plugin://%s/favorites/delete_all/playlists)' % CONST.addon_id) )
    elif item.get('FileNameAndPath').find('%s/favorites/tracks' % _tidal_addon_id) >= 0:
        commands.append( (_S(30426) % _P('tracks'), 'RunPlugin(plugin://%s/favorites/export/tracks)' % CONST.addon_id) )
        commands.append( (_S(30427) % _P('tracks'), 'RunPlugin(plugin://%s/favorites/import/tracks)' % CONST.addon_id) )
        commands.append( (_S(30436) % _P('tracks'), 'RunPlugin(plugin://%s/favorites/delete_all/tracks)' % CONST.addon_id) )
    elif item.get('FileNameAndPath').find('%s/favorites/videos' % _tidal_addon_id) >= 0:
        commands.append( (_S(30426) % _P('videos'), 'RunPlugin(plugin://%s/favorites/export/videos)' % CONST.addon_id) )
        commands.append( (_S(30427) % _P('videos'), 'RunPlugin(plugin://%s/favorites/import/videos)' % CONST.addon_id) )
        commands.append( (_S(30436) % _P('videos'), 'RunPlugin(plugin://%s/favorites/delete_all/videos)' % CONST.addon_id) )
    elif item.get('FileNameAndPath').find('%s/user_playlists' % _tidal_addon_id) >= 0:
        commands.append( (_S(30433), 'RunPlugin(plugin://%s/user_playlist_export_all)' % CONST.addon_id) )
        commands.append( (_S(30434), 'RunPlugin(plugin://%s/user_playlist_import)' % CONST.addon_id) )
    if item.get('FileNameAndPath').find('%s/artist/' % _tidal_addon_id) >= 0:
        commands.append( (_S(30437), 'RunPlugin(plugin://%s/search_artist_news)' % CONST.addon_id) )
    if item.get('FolderPath').find('%s/user_playlists' % _tidal_addon_id) >= 0:
        uuid = item.get('FileNameAndPath').split('playlist/')[1]
        commands.append( (_S(30435), 'RunPlugin(plugin://%s/user_playlist_export/%s)' % (CONST.addon_id, uuid)) )
    commands.append( (_S(30423), 'Addon.OpenSettings("%s")' % CONST.addon_id) )
    commands.append( ('TIDAL2-' + _S(30423), 'Addon.OpenSettings("%s")' % _tidal_addon_id) )
    if settings.debug:
        commands.append( (_S(30424), item_info.itemInfoDialog) )
    menu = [ txt for txt, func in commands]
    try:
        selected = xbmcgui.Dialog().contextmenu(menu)
    except:
        selected = xbmcgui.Dialog().select(CONST.addon_name, menu)
    if selected >= 0:
        txt, func = commands[selected]
        if callable(func):
            func()
        else:
            xbmc.executebuiltin(func)

#------------------------------------------------------------------------------
# MAIN Program of the Plugin
#------------------------------------------------------------------------------

if __name__ == '__main__':
    try:
        plugin.run()
    except HTTPError as e:
        r = e.response
        if r.status_code in [401, 403]:
            msg = _S(30425)
        else:
            msg = r.reason
        try:
            msg = r.json().get('userMessage')
        except:
            pass
        xbmcgui.Dialog().notification('%s Error %s' % (plugin.name, r.status_code), msg, xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()
