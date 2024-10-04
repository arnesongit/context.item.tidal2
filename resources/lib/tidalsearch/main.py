# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2021 arneson
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

from __future__ import absolute_import, division, print_function, unicode_literals

import traceback, os
from datetime import datetime

from kodi_six import xbmc, xbmcgui, xbmcvfs, py2_decode
from requests import HTTPError

from tidal2.common import __addon_id__ as _tidal2_addon_id_
from tidal2.textids import _T, _P
from tidal2.config import settings as tidalSettings
from tidal2.items import PlaylistItem, TrackItem, VideoItem
from tidal2.tidalapi import Playlist

from .common import Const, plugin
from .textids import Msg, _S
from .config import settings, log
from .fuzzysession import FuzzySession, NewMusicSearcher
from .fuzzymodels import FuzzyTrackItem, FuzzyVideoItem
from . import item_info

try:
    # Python 3
    from urllib.parse import quote_plus, unquote_plus
except:
    # Python 2.7
    from urllib import quote_plus, unquote_plus


#------------------------------------------------------------------------------
# Initialization
#------------------------------------------------------------------------------

# Init Session Configuration
session = FuzzySession()

add_items = session.add_list_items
add_directory = session.add_directory_item
add_search_results = session.add_search_result

try:
    FOLDER_MASK = tidalSettings.folder_mask
except:
    FOLDER_MASK = '{folder}'

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
        xbmc.executebuiltin('RunPlugin(%s)' % plugin.url_for(search_field, field='all', text=quote_plus(s_text)))


@plugin.route('/search_field/<field>/<text>')
def search_field(field, text):
    # Unquote special Characters
    s_field = unquote_plus(field).strip()
    s_text = unquote_plus(text).strip()
    values = {'field': s_field, 'text': s_text}
    settings.setSetting('search_parameters_field', repr(values))
    # Execute Search in new Container
    xbmc.executebuiltin('ActivateWindow(Music,%s,return)' % plugin.url_for(search_field_exec))


@plugin.route('/search_field_exec')
def search_field_exec():
    try:
        params = eval(settings.getSetting('search_parameters_field'))
        params.update({'search': ''})
    except:
        log.error('Search Parameters not set !')
        return
    s_field = params.get('field')
    s_text = params.get('text')
    searchresults = session.search(s_field, s_text, limit=50 if s_field.upper() == 'ALL' else 100)
    add_directory(_S(Msg.i30400), plugin.url_for(search_field_edit), isFolder=False)
    add_search_results(searchresults)


@plugin.route('/search_field_edit')
def search_field_edit():
    try:
        params = eval(settings.getSetting('search_parameters_field'))
        params.update({'search': ''})
    except:
        log.error('Search Parameters not set !')
        return
    s_text = params.get('text')
    keyboard = xbmc.Keyboard(s_text, _S(Msg.i30401))
    keyboard.doModal()
    if keyboard.isConfirmed():
        value = py2_decode(keyboard.getText())
        params.update({'text': value})
        settings.setSetting('search_parameters_field', repr(params))
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

    xbmc.executebuiltin('RunPlugin(%s)' % plugin.url_for(search_fuzzy_fields, quote_plus(artist),
                                                                              quote_plus(title),
                                                                              quote_plus(album),
                                                                              quote_plus(albumartist),
                                                                              quote_plus(year)))


@plugin.route('/search_fuzzy_fields/<artist>/<title>/<album>/<albumartist>/<year>')
def search_fuzzy_fields(artist, title, album, albumartist, year):
    # This Function should be called with RunPlugin(...) and not with Container.Update(...)
    # Unquote special Characters
    s_artist = unquote_plus(artist).strip()
    s_title = unquote_plus(title).strip()
    s_album = unquote_plus(album).strip()
    s_albumartist = unquote_plus(albumartist).strip()
    s_year = unquote_plus(year).strip()
    # Save Search Parameters
    values = {'artist': s_artist, 'title': s_title, 'album': s_album, 'albumartist': s_albumartist, 'year': s_year}
    settings.setSetting('search_parameters', repr(values))
    # Execute Search in new Container
    xbmc.executebuiltin('ActivateWindow(Music,%s,return)' % plugin.url_for(search_fuzzy_exec))


@plugin.route('/search_fuzzy_exec')
def search_fuzzy_exec():
    try:
        params = eval(settings.getSetting('search_parameters'))
        params.update({'search': ''})
    except:
        log.error('Search Parameters not set !')
        return
    s_artist = params.get('artist')
    s_title = params.get('title')
    s_album = params.get('album')
    s_albumartist = params.get('albumartist')
    s_year = params.get('year')
    # Search now
    searchresults = session.search_fuzzy(s_artist, s_title, s_album, s_albumartist, s_year, limit=20)
    # Display the Search Results
    add_directory(_S(Msg.i30400), plugin.url_for(search_fuzzy_edit), isFolder=False)
    add_search_results(searchresults, sort='match', reverse=True)


@plugin.route('/search_fuzzy_edit')
def search_fuzzy_edit():
    try:
        params = eval(settings.getSetting('search_parameters'))
        params.update({'search': ''})
    except:
        log.error('Search Parameters not set !')
        return
    cmds = [('search', _S(Msg.i30400) ),
            ('artist', _T('artist') + ': '),
            ('title', _T('track') + ': '),
            ('album', _T('album') + ': '),
            ('albumartist', _S(Msg.i30402) + ': '),
            ('year', _S(Msg.i30403) + ': '),
            ]
    answer = 1
    while answer > 0:
        menue = ['%s%s' % (FOLDER_MASK.format(label=s_head), params.get(s_key)) for s_key, s_head in cmds]
        answer = xbmcgui.Dialog().select(_S(Msg.i30400), menue)
        if answer > 0:
            keyboard = xbmc.Keyboard(params.get(cmds[answer][0]), cmds[answer][1])
            keyboard.doModal()
            if keyboard.isConfirmed():
                value = keyboard.getText()
                params.update({cmds[answer][0]: value})
    if answer == 0:
        settings.setSetting('search_parameters', repr(params))
        xbmc.executebuiltin('Container.Refresh()')
    pass


@plugin.route('/convert_to_playlist/<item_type>')
def convert_to_playlist(item_type):
    if not session.is_logged_in:
        xbmcgui.Dialog().notification(plugin.name, _S(Msg.i30404), xbmcgui.NOTIFICATION_ERROR)
        return
    # Submenu: Parameters for Playlist-Generation
    cmds = [('action', _S(Msg.i30405)),
            ('playlist', _T('playlist') + ': '),
            ('Position', _S(Msg.i30406) + ': '),
            ('NumItems', _S(Msg.i30407) + ': '),
            ]
    item = item_info.getSelectedListItem()
    item['action'] = ''
    item['playlist_id'] = ''
    item['playlist'] = ''
    playlist_id = tidalSettings.default_videoplaylist_id if item_type.startswith('video') else tidalSettings.default_trackplaylist_id
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
        menue = ['%s%s' % (FOLDER_MASK.format(label=s_head), item.get(s_key)) for s_key, s_head in cmds]
        answer = xbmcgui.Dialog().select(_S(Msg.i30408), menue)
        if answer == 0 and not item['playlist_id']:
            answer = 1 # Playlist not set
        if answer > 0:
            if answer == 1:
                playlist = session.user.selectPlaylistDialog(_S(Msg.i30409).format(what=_P('tracks' if item_type.startswith('track') else 'videos')), allowNew=True)
                if playlist:
                    item['playlist_id'] = playlist.id
                    item['playlist'] = playlist.title
            elif answer >= 2 and answer <= 3:
                value = int('0%s' % xbmcgui.Dialog().input(cmds[answer][1], str(item.get(cmds[answer][0])), type=xbmcgui.INPUT_NUMERIC))
                if ( answer == 2 and value <= numItems and value <= item['NumItems'] ) or \
                   ( answer == 3 and value <= numItems and value >= item['Position'] ):
                    item.update({cmds[answer][0]: value})
            else:
                keyboard = xbmc.Keyboard(item.get(cmds[answer][0]), cmds[answer][1])
                keyboard.doModal()
                if keyboard.isConfirmed():
                    value = keyboard.getText()
                    item.update({cmds[answer][0]: value})
    if answer == 0:
        convert_to_playlist_run(item_type, '0%s' % item['Position'], '0%s' % item['NumItems'], item['playlist_id'])


@plugin.route('/convert_to_playlist_run/<item_type>/<from_pos>/<to_pos>/<playlist_id>')
def convert_to_playlist_run(item_type, from_pos, to_pos, playlist_id):
    playlist = session.get_playlist(playlist_id)
    if not playlist:
        log.error('Playlist "%s" not found.' % playlist_id)
        return
    listitems = item_info.getAllListItems()
    numItems = len(listitems)
    if numItems == 0:
        log.error('No ListItems found.')
        return
    pos = min(int(from_pos), numItems) - 1
    lastPos = min(int(to_pos), numItems) - 1
    numItems = lastPos - pos + 1
    progress = xbmcgui.DialogProgress()
    progress.create(_S(Msg.i30410))
    percent = 0
    line1 = ''
    line2 = ''
    line3 = _S(Msg.i30411)
    items = []
    while pos <= lastPos and not progress.iscanceled():
        li = listitems[pos]
        artist = li.get('Artist')
        title = li.get('Title')
        album = li.get('Album') if not li.get('Compilation') else '' # item.get('Title')
        albumartist = li.get('AlbumArtist') if not li.get('Compilation') else '' # item.get('Artist')
        year = '%s' % li.get('YearInt')
        percent = int((pos * 100) / numItems)
        line1 = '%s: %s' % (_T('artist'), artist)
        line2 = '%s: %s' % (_T('track'), title)
        progress.update(percent, "\n".join([line1, line2, line3]))
        log.info('Searching Title: %s - %s' % (artist, title))
        item_id = li.get('video_id', None) if item_type.startswith('video') else li.get('track_id', None)
        if item_id:
            track = session.get_track(item_id, withAlbum=True)
            if track:
                line3 = 'TIDAL-ID %s: %s - %s (%s)' % (track.id, track.artist.name, track.title, track.year)
                log.info('Found TIDAL Track-Id %s: %s - %s' % (track.id, track.artist.name, track.title))
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
            log.info('Found Title Id %s: %s - %s' % (track.id, track.artist.name, track.title))
            items.append(track)
        elif item_type.startswith('video') and len(result.videos) > 0:
            # Sort over matchLevel
            result.videos.sort(key=lambda line: line.getSortField('match'), reverse=True)
            # Take the first result (best matchLevel) 
            video = result.videos[0]
            line3 = 'ID %s: %s - %s (%s)' % (video.id, video.artist.name, video.title, video.year)
            log.info('Found Video Id %s: %s - %s' % (video.id, video.artist.name, video.title))
            items.append(video)
        else:
            log.info('Title not found.')
            line3 = '%s: %s - %s' % (_S(Msg.i30412), li.get('Artist'), li.get('Title'))
        pos = pos + 1

    progress.update(percent, "\n".join([line1, line2, line3]))
    xbmc.sleep(2000)
    foundItems = len(items)
    line2 = _S(Msg.i30413).format(n=foundItems, m=numItems)
    if progress.iscanceled():
        yes = xbmcgui.Dialog().yesno(_S(Msg.i30414), _S(Msg.i30415), line2, _S(Msg.i30416))
        if not yes:
            progress.close()
            log.info('Search aborted by user.')
            return False
    if playlist and foundItems > 0:
        progress.update(99, "\n".join([_S(Msg.i30417), line2, _S(Msg.i30418)]))
        session.user.add_playlist_entries(playlist=playlist, item_ids=['%s' % item.id for item in items])
        progress.update(100, _S(Msg.i30417))
    xbmc.sleep(1000)
    progress.close()

    log.info('Search terminated successfully.')
    return True


@plugin.route('/user_playlist/add_id/<playlist_id>/<item_id>')
def user_playlist_add_id(playlist_id, item_id):
    try:
        playlist = session.get_playlist(playlist_id)
        if playlist:
            session.user.add_playlist_entries(playlist=playlist, item_ids=['%s' % item_id])
            numItems = playlist.numberOfItems + 1
            log.info('Added ID %s to Playlist %s at position %s' % (item_id, playlist.title, numItems))
    except Exception as e:
        log.logException(e, 'Failed to add ID %s to playlist %s' % (item_id, playlist_id))
        traceback.print_exc()


@plugin.route('/favorites/export/<what>')
def favorites_export(what):
    name = 'favo_%s_%s.cfg' % (what, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
    if not session.is_logged_in:
        return
    if what == 'playlists':
        session.user.favorites.export_ids(what=_P(what), filename=name, action=session.user.favorites.playlists)
    elif what == 'artists':
        session.user.favorites.export_ids(what=_P('Artists'), filename=name, action=session.user.favorites.artists)
    elif what == 'albums':
        session.user.favorites.export_ids(what=_P('Albums'), filename=name, action=session.user.favorites.albums)
    elif what == 'tracks':
        session.user.favorites.export_ids(what=_P('Tracks'), filename=name, action=session.user.favorites.tracks)
    elif what == 'videos':
        session.user.favorites.export_ids(what=_P('Videos'), filename=name, action=session.user.favorites.videos)
    elif what == 'mixes':
        session.user.favorites.export_ids(what=_P('Mixes'), filename=name, action=session.user.favorites.mixes)


@plugin.route('/favorites/import/<what>')
def favorites_import(what):
    path = settings.import_export_path
    if len(path) == 0 or not session.is_logged_in:
        return
    files = xbmcvfs.listdir(path)[1]
    files = [py2_decode(name) for name in files if py2_decode(name).startswith('favo_%s' % what)]
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
    elif what == 'mixes':
        ok = session.user.favorites.import_ids(what=_T('Mixes'), filename=name, action=session.user.favorites.add_mix)
    return ok


@plugin.route('/favorites/delete_all/<what>')
def favorites_delete_all(what):
    ok = xbmcgui.Dialog().yesno(_S(Msg.i30430).format(what=_P(what)), _S(Msg.i30431).format(what=_P(what)))
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
        elif what == 'mixes':
            session.user.favorites.delete_all(what=_T('Mixes'), action=session.user.favorites.videos, remove=session.user.favorites.remove_mix)
    return ok


@plugin.route('/user_playlist_export/<playlist_id>')
def user_playlist_export(playlist_id):
    if not session.is_logged_in:
        return
    try:
        playlist = session.get_playlist(playlist_id)
        if playlist and playlist.numberOfItems > 0:
            filename = 'playlist_%s_%s.cfg' % (playlist.title, datetime.now().strftime('%Y-%m-%d-%H%M%S'))
            filename = filename.replace(' ', '_')
            session.user.export_playlists([playlist], filename)
    except Exception as e:
        log.logException(e)


@plugin.route('/user_playlist_export_all')
def user_playlist_export_all():
    if not session.is_logged_in:
        return
    try:
        items = session.user.playlists()
        filename = 'playlist_all_%s.cfg' % datetime.now().strftime('%Y-%m-%d-%H%M%S')
        session.user.export_playlists(items, filename)
    except Exception as e:
        log.logException(e)


@plugin.route('/user_playlist_import')
def user_playlist_import():
    path = settings.import_export_path
    if len(path) == 0 or not session.is_logged_in:
        return
    files = xbmcvfs.listdir(path)[1]
    files = [py2_decode(name) for name in files if py2_decode(name).startswith('playlist_')]
    selected = xbmcgui.Dialog().select(path, files)
    if selected < 0:
        return
    name = os.path.join(path, files[selected])
    try:
        session.user.import_playlists(name)
    except Exception as e:
        log.logException(e)


@plugin.route('/search_artist_music')
def search_artist_music():
    if not session.is_logged_in:
        xbmcgui.Dialog().notification(plugin.name, _S(Msg.i30404), xbmcgui.NOTIFICATION_ERROR)
        return
    if settings.getSetting('search_artist_music_running') == 'true':
        if xbmcgui.Dialog().yesno(_S(Msg.i30437), _S(Msg.i30445)+'\n'+_S(Msg.i30446)):
            settings.setSetting('search_artist_music_abort', 'true')
        return
    item = item_info.getSelectedListItem()
    artists = []
    if item.get('FileNameAndPath').find('%s/artist/' % _tidal2_addon_id_) >= 0:
        artist_id = item.get('FileNameAndPath').split('/artist/')[1].split('/')[0]
        artist = session.get_artist(artist_id)
        if artist:
            artists.append(artist)
    else:
        artists = session.user.favorites.get('artists')
    if len(artists) == 0:
        log.error('No selected Artists found')
        return

    if not session.is_logged_in:
        xbmcgui.Dialog().notification(plugin.name, _S(Msg.i30404), xbmcgui.NOTIFICATION_ERROR)
        return
    # Submenu: Parameters for Playlist-Generation
    cmds = [('action', _S(Msg.i30405)),
            ('album_playlist', _S(Msg.i30409).format(what=_P('albums')) + ': '),
            ('track_playlist', _S(Msg.i30409).format(what=_P('tracks')) + ': '),
            ('video_playlist', _S(Msg.i30409).format(what=_P('videos')) + ': '),
            ('limit', _S(Msg.i30438) + ': '),
            ('diff_days', _S(Msg.i30439) + ': '),
            ]
    album_playlist = None
    track_playlist = None
    video_playlist = None
    if settings.getSetting('default_albumplaylist_id'):
        album_playlist = session.get_playlist(settings.getSetting('default_albumplaylist_id'))
    if not album_playlist and tidalSettings.default_albumplaylist_id:
        album_playlist = session.get_playlist(tidalSettings.default_albumplaylist_id)
    if not album_playlist:
        album_playlist = PlaylistItem(Playlist())
        album_playlist.title = ''
    if settings.getSetting('default_trackplaylist_id'):
        track_playlist = session.get_playlist(settings.getSetting('default_trackplaylist_id'))
    if not track_playlist and tidalSettings.default_trackplaylist_id:
        track_playlist = session.get_playlist(tidalSettings.default_trackplaylist_id)
    if not track_playlist:
        track_playlist = PlaylistItem(Playlist())
        track_playlist.title = ''
    if settings.getSetting('default_videoplaylist_id'):
        video_playlist = session.get_playlist(settings.getSetting('default_videoplaylist_id'))
    if not video_playlist and tidalSettings.default_videoplaylist_id:
        video_playlist = session.get_playlist(tidalSettings.default_videoplaylist_id)
    if not video_playlist:
        video_playlist = PlaylistItem(Playlist())
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
        menue = ['%s%s' % (FOLDER_MASK.format(label=s_head), item.get(s_key)) for s_key, s_head in cmds]
        answer = xbmcgui.Dialog().select(_S(Msg.i30437), menue)
        if answer > 0:
            if answer >= 1 and answer <= 3:
                playlist = session.user.selectPlaylistDialog(_S(Msg.i30409).format(what=_P(['', 'albums', 'tracks', 'videos'][answer])), allowNew=True)
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
                        album_playlist = PlaylistItem(Playlist())
                        album_playlist.title = ''
                    elif answer == 2:
                        track_playlist = PlaylistItem(Playlist())
                        track_playlist.title = ''
                    elif answer == 3:
                        video_playlist = PlaylistItem(Playlist())
                        video_playlist.title = ''
            elif answer >= 4 and answer <= 5:
                value = int('0%s' % xbmcgui.Dialog().input(cmds[answer][1], str(item.get(cmds[answer][0])), type=xbmcgui.INPUT_NUMERIC))
                item.update({cmds[answer][0]: value})
    if answer < 0:
        return
    # Saving used Playlist-IDs
    settings.setSetting('default_albumplaylist_id', album_playlist.id if album_playlist.id else '')
    settings.setSetting('default_trackplaylist_id', track_playlist.id if track_playlist.id else '')
    settings.setSetting('default_videoplaylist_id', video_playlist.id if video_playlist.id else '')
    # Searching now
    searcher = NewMusicSearcher(session, album_playlist, track_playlist, video_playlist, limit=item.get('limit', 20), diffDays=item.get('diff_days', 90))
    settings.setSetting('search_artist_music_running', 'true')
    settings.setSetting('search_artist_music_abort', 'false')
    searcher.search(artists, thread_count=settings.max_thread_count)
    settings.setSetting('search_artist_music_running', 'false')


@plugin.route('/user_playlist_move/<what>/<playlist_id>')
def user_playlist_move(what, playlist_id):
    if not session.is_logged_in:
        return
    try:
        mqa_tracks = []
        hires_tracks = []
        atmos_tracks = []
        ra360_tracks = []
        dup_tracks = []
        pattern_tracks = []
        good_tracks = {}
        playlist = session.get_playlist(playlist_id)
        isAlbumPlaylist = True if 'ALBUM' in playlist.description else False
        search_pattern = None
        if what == 'pattern':
            search_pattern = xbmcgui.Dialog().input('Suchmuster')
            if not search_pattern:
                return
        items = []
        for item in session.get_playlist_items(playlist):
            if item.available and isinstance(item, TrackItem):
                items.append( FuzzyTrackItem(item) )
            elif item.available and isinstance(item, VideoItem):
                item.isHiRes = False
                item.isMqa = False
                item.isDolbyAtmos = False
                item.isSony360RA = False
                items.append( FuzzyVideoItem(item) )
        for item in items:
            if item.isMqa:
                mqa_tracks.append(item)
            if item.isHiRes:
                hires_tracks.append(item)
            if item.isDolbyAtmos:
                atmos_tracks.append(item)
            if item.isSony360RA:
                ra360_tracks.append(item)
            label = item.album.getSimpleLabel() if isAlbumPlaylist else item.getSimpleLabel()
            if search_pattern and search_pattern.lower() in label.lower():
                pattern_tracks.append(item)
            good = good_tracks.get(label, None)
            if good == None:
                good_tracks[label] = item
            else:
                # Item with same name exists. Keep the one, which is 'better'
                if  ( item.isMqa == good.isMqa and item.explicit and not good.explicit ) or \
                    ( item.explicit == good.explicit and item.isMqa and not good.isMqa ) or \
                    ( item.isHiRes == good.isHiRes and item.explicit and not good.explicit ) or \
                    ( item.explicit == good.explicit and item.isHiRes and not good.isHiRes ) or \
                    ( isAlbumPlaylist and item.explicit == good.explicit and ( item.isMqa == good.isMqa or item.isHiRes == good.isHiRes ) and session.get_album(item.album.id).numberOfItems > session.get_album(good.album.id).numberOfItems ):
                    # The item is better
                    dup_tracks.append(good)
                    good_tracks[label] = item
                else:
                    # The exiting track is 'better'
                    dup_tracks.append(item)
        if what == 'mqa':
            items = mqa_tracks
        elif what == 'hires':
            items = hires_tracks
        elif what == 'atmos':
            items = atmos_tracks
        elif what == '360':
            items = ra360_tracks
        elif what == 'pattern':
            items = pattern_tracks
        else:
            items = dup_tracks
        text = ['%s: %s' % (i._playlist_pos, i.getLabel()) for i in items]
        selected = xbmcgui.Dialog().multiselect(_S(Msg.i30451), text, preselect=list(range(len(items))))
        if selected:
            dest_playlist = session.user.selectPlaylistDialog(allowNew=True)
            if dest_playlist and playlist.id != dest_playlist.id:
                session.user.add_playlist_entries(dest_playlist, ['%s' % items[i].id for i in selected])
                session.user.remove_playlist_entry(playlist, entry_no=','.join(['%s' % items[i]._playlist_pos for i in selected]))
    except Exception as e:
        log.logException(e)
        traceback.print_exc()
    xbmc.executebuiltin('Container.Refresh()')


@plugin.route('/user_playlist_move_from/<playlist_id>/<item_id>')
def user_playlist_move_from(playlist_id, item_id):
    if not session.is_logged_in:
        return
    try:
        playlist = session.get_playlist(playlist_id)
        items = session.get_playlist_items(playlist)
        while len(items) > 0 and '%s' % items[0].id != '%s' % item_id:
            items.pop(0)
        if len(items) > 0:
            count = int('0' + xbmcgui.Dialog().numeric(0, _S(Msg.i30454), defaultt='%s' % len(items)))
            if count < 1:
                return
            if count > len(items):
                count = len(items)
            text = ['%s: %s' % (i._playlist_pos, i.getLabel()) for i in items]
            selected = xbmcgui.Dialog().multiselect(_S(Msg.i30451), text, preselect=list(range(len(items)))[0:count])
            if selected:
                dest_playlist = session.user.selectPlaylistDialog(allowNew=True)
                if dest_playlist and playlist.id != dest_playlist.id:
                    session.user.add_playlist_entries(dest_playlist, ['%s' % items[i].id for i in selected])
                    session.user.remove_playlist_entry(playlist, entry_no=','.join(['%s' % items[i]._playlist_pos for i in selected]))
    except Exception as e:
        log.logException(e)
        traceback.print_exc()
    xbmc.executebuiltin('Container.Refresh()')


@plugin.route('/export_artist_nfo/<artist_id>')
def export_artist_nfo(artist_id):
    session.export_artist_nfo(artist_id)

@plugin.route('/export_album_nfo/<album_id>')
def export_album_nfo(album_id):
    session.export_album_nfo(album_id)


#------------------------------------------------------------------------------
# Context Menu Function
#------------------------------------------------------------------------------

@plugin.route('/context_menu')
def context_menu():
    commands = []
    item = item_info.getSelectedListItem()
    if item.get('Artist') and item.get('Title'):
        commands.append( (_S(Msg.i30420), search_fuzzy) )
        commands.append( (_S(Msg.i30419), search_selected) )
        commands.append( (_S(Msg.i30421), 'RunPlugin(plugin://%s/convert_to_playlist/tracks)' % Const.addon_id) )
        commands.append( (_S(Msg.i30422), 'RunPlugin(plugin://%s/convert_to_playlist/videos)' % Const.addon_id) )
    if item.get('FileNameAndPath').find('%s/favorites/artists' % _tidal2_addon_id_) >= 0:
        commands.append( (_S(Msg.i30437), 'RunPlugin(plugin://%s/search_artist_music)' % Const.addon_id) )
        commands.append( (_S(Msg.i30426).format(what=_P('artists')), 'RunPlugin(plugin://%s/favorites/export/artists)' % Const.addon_id) )
        commands.append( (_S(Msg.i30427).format(what=_P('artists')), 'RunPlugin(plugin://%s/favorites/import/artists)' % Const.addon_id) )
        commands.append( (_S(Msg.i30436).format(what=_P('artists')), 'RunPlugin(plugin://%s/favorites/delete_all/artists)' % Const.addon_id) )
    elif item.get('FileNameAndPath').find('%s/favorites/albums' % _tidal2_addon_id_) >= 0:
        commands.append( (_S(Msg.i30426).format(what=_P('albums')), 'RunPlugin(plugin://%s/favorites/export/albums)' % Const.addon_id) )
        commands.append( (_S(Msg.i30427).format(what=_P('albums')), 'RunPlugin(plugin://%s/favorites/import/albums)' % Const.addon_id) )
        commands.append( (_S(Msg.i30436).format(what=_P('albums')), 'RunPlugin(plugin://%s/favorites/delete_all/albums)' % Const.addon_id) )
    elif item.get('FileNameAndPath').find('%s/favorites/playlists' % _tidal2_addon_id_) >= 0:
        commands.append( (_S(Msg.i30426).format(what=_P('playlists')), 'RunPlugin(plugin://%s/favorites/export/playlists)' % Const.addon_id) )
        commands.append( (_S(Msg.i30427).format(what=_P('playlists')), 'RunPlugin(plugin://%s/favorites/import/playlists)' % Const.addon_id) )
        commands.append( (_S(Msg.i30436).format(what=_P('playlists')), 'RunPlugin(plugin://%s/favorites/delete_all/playlists)' % Const.addon_id) )
    elif item.get('FileNameAndPath').find('%s/favorites/tracks' % _tidal2_addon_id_) >= 0:
        commands.append( (_S(Msg.i30426).format(what=_P('tracks')), 'RunPlugin(plugin://%s/favorites/export/tracks)' % Const.addon_id) )
        commands.append( (_S(Msg.i30427).format(what=_P('tracks')), 'RunPlugin(plugin://%s/favorites/import/tracks)' % Const.addon_id) )
        commands.append( (_S(Msg.i30436).format(what=_P('tracks')), 'RunPlugin(plugin://%s/favorites/delete_all/tracks)' % Const.addon_id) )
    elif item.get('FileNameAndPath').find('%s/favorites/videos' % _tidal2_addon_id_) >= 0:
        commands.append( (_S(Msg.i30426).format(what=_P('videos')), 'RunPlugin(plugin://%s/favorites/export/videos)' % Const.addon_id) )
        commands.append( (_S(Msg.i30427).format(what=_P('videos')), 'RunPlugin(plugin://%s/favorites/import/videos)' % Const.addon_id) )
        commands.append( (_S(Msg.i30436).format(what=_P('videos')), 'RunPlugin(plugin://%s/favorites/delete_all/videos)' % Const.addon_id) )
    elif item.get('FileNameAndPath').find('%s/favorites/mixes' % _tidal2_addon_id_) >= 0:
        commands.append( (_S(Msg.i30426).format(what=_P('mixes')), 'RunPlugin(plugin://%s/favorites/export/mixes)' % Const.addon_id) )
        commands.append( (_S(Msg.i30427).format(what=_P('mixes')), 'RunPlugin(plugin://%s/favorites/import/mixes)' % Const.addon_id) )
        commands.append( (_S(Msg.i30436).format(what=_P('mixes')), 'RunPlugin(plugin://%s/favorites/delete_all/mixes)' % Const.addon_id) )
    elif item.get('FileNameAndPath').find('%s/user_playlists' % _tidal2_addon_id_) >= 0:
        commands.append( (_S(Msg.i30433), 'RunPlugin(plugin://%s/user_playlist_export_all)' % Const.addon_id) )
        commands.append( (_S(Msg.i30434), 'RunPlugin(plugin://%s/user_playlist_import)' % Const.addon_id) )
    if item.get('FileNameAndPath').find('%s/artist/' % _tidal2_addon_id_) >= 0:
        commands.append( (_S(Msg.i30437), 'RunPlugin(plugin://%s/search_artist_music)' % Const.addon_id) )
        if settings.enable_nfo_export:
            artist_id = item.get('FileNameAndPath').split('artist/')[1].split('/')[0]
            commands.append( (_S(Msg.i30452), 'RunPlugin(plugin://%s/export_artist_nfo/%s)' % (Const.addon_id, artist_id)) )
    if item.get('FileNameAndPath').find('%s/album/' % _tidal2_addon_id_) >= 0:
        if settings.enable_nfo_export:
            album_id = item.get('FileNameAndPath').split('album/')[1].split('/')[0]
            commands.append( (_S(Msg.i30452), 'RunPlugin(plugin://%s/export_album_nfo/%s)' % (Const.addon_id, album_id)) )
    if item.get('FolderPath').find('%s/user_playlists' % _tidal2_addon_id_) >= 0 and item.get('FileNameAndPath').find('playlist/') > 0:
        uuid = item.get('FileNameAndPath').split('playlist/')[1].split('/')[0]
        commands.append( (_S(Msg.i30435), 'RunPlugin(plugin://%s/user_playlist_export/%s)' % (Const.addon_id, uuid)) )
    if item.get('FolderPath').find('%s/user_folders' % _tidal2_addon_id_) >= 0 and item.get('FileNameAndPath').find('playlist/') > 0:
        uuid = item.get('FileNameAndPath').split('playlist/')[1].split('/')[0]
        commands.append( (_S(Msg.i30435), 'RunPlugin(plugin://%s/user_playlist_export/%s)' % (Const.addon_id, uuid)) )
        # commands.append( (_S(Msg.i30449), 'RunPlugin(plugin://%s/user_playlist_move/mqa/%s)' % (Const.addon_id, uuid)) )
        commands.append( (_S(Msg.i30447), 'RunPlugin(plugin://%s/user_playlist_move/atmos/%s)' % (Const.addon_id, uuid)) )
        # commands.append( (_S(Msg.i30448), 'RunPlugin(plugin://%s/user_playlist_move/360/%s)' % (Const.addon_id, uuid)) )
        commands.append( (_S(Msg.i30450), 'RunPlugin(plugin://%s/user_playlist_move/duplicates/%s)' % (Const.addon_id, uuid)) )
        commands.append( (_S(Msg.i30455), 'RunPlugin(plugin://%s/user_playlist_move/pattern/%s)' % (Const.addon_id, uuid)) )
    if item.get('FolderPath').find('%s/playlist' % _tidal2_addon_id_) >= 0 and item.get('FolderPath').find('/items') > 0:
        uuid = item.get('FolderPath').split('playlist/')[1].split('/')[0]
        session.user.load_cache()
        plist = session.user.playlists_cache.get(uuid, '')
        if plist:
            item_id = None
            if item.get('FileNameAndPath').find('play_track/') > 0:
                item_id = item.get('FileNameAndPath').split('play_track/')[1].split('/')[0]
            elif item.get('FileNameAndPath').find('play_video/') > 0:
                item_id = item.get('FileNameAndPath').split('play_video/')[1].split('/')[0]
            if item_id and item_id in plist['ids']:
                commands.append( (_S(Msg.i30453), 'RunPlugin(plugin://%s/user_playlist_move_from/%s/%s)' % (Const.addon_id, uuid, item_id)) )
    commands.append( (_S(Msg.i30423), 'Addon.OpenSettings("%s")' % Const.addon_id) )
    commands.append( ('TIDAL2-' + _S(Msg.i30423), 'Addon.OpenSettings("%s")' % _tidal2_addon_id_) )
    if settings.debug:
        commands.append( (_S(Msg.i30424), item_info.itemInfoDialog) )
    menu = [ txt for txt, func in commands]
    try:
        selected = xbmcgui.Dialog().contextmenu(menu)
    except:
        selected = xbmcgui.Dialog().select(Const.addon_name, menu)
    if selected >= 0:
        txt, func = commands[selected]
        if callable(func):
            func()
        else:
            xbmc.executebuiltin(func)

#------------------------------------------------------------------------------
# MAIN Program of the Plugin
#------------------------------------------------------------------------------

def run():
    try:
        plugin.run()
    except HTTPError as e:
        r = e.response
        if r.status_code in [401, 403]:
            msg = _S(Msg.i30425)
        else:
            msg = r.reason
        try:
            msg = r.json().get('userMessage')
        except:
            pass
        xbmcgui.Dialog().notification('%s Error %s' % (plugin.name, r.status_code), msg, xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()
    except:
        traceback.print_exc()
    finally:
        log.killDebugThreads()
