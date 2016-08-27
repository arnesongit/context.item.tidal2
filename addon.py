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

import traceback, urllib
import xbmc, xbmcgui
from routing import Plugin
from requests import HTTPError

from tidalapi.config import settings as myTidalSettings
from tidalapi.guistuff import add_directory, add_search_result, colorizeText
from tidalapi.all_strings import _T

from lib.tidalsearch.config import settings
from lib.tidalsearch.tidalsession import TidalSession
from lib.tidalsearch import item_info, config, debug
from lib.tidalsearch.all_strings import _S

#------------------------------------------------------------------------------
# Initialization
#------------------------------------------------------------------------------

plugin = Plugin(settings.addon_base_url)
plugin.name = settings.addon_name

# Init Session Configuration
session = TidalSession()
session.load_session()

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
    album = item.get('Album') if item.get('Compilation') <> 'Yes' else ' ' # item.get('Title')
    albumartist = item.get('AlbumArtist') if item.get('Compilation') <> 'Yes' else ' ' # item.get('Artist')
    year = '%s' % item.get('YearInt')
    
    if not artist: artist = ' '
    if not title: title = ' '
    if not album: album = ' '
    if not albumartist: albumartist = ' '
    if not year: year = ' '

    xbmc.executebuiltin('RunPlugin(%s)' % plugin.url_for(search, urllib.quote_plus(artist.encode('utf-8')),
                                                                 urllib.quote_plus(title.encode('utf-8')),
                                                                 urllib.quote_plus(album.encode('utf-8')),
                                                                 urllib.quote_plus(albumartist.encode('utf-8')),
                                                                 urllib.quote_plus(year.encode('utf-8'))))
    
@plugin.route('/search/<artist>/<title>/<album>/<albumartist>/<year>')
def search(artist, title, album, albumartist, year):
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
    xbmc.executebuiltin('Container.Update(%s, True)' % plugin.url_for(search_exec))

@plugin.route('/search_exec')
def search_exec():
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
    results = session.search_extra(s_artist, s_title, s_album, s_albumartist, s_year, limit=20)
    # Display the Search Results
    add_directory(_T('Search again'), plugin.url_for(search_again, field='ALL'), isFolder=False)
    add_search_result(results, sort='match', reverse=True, end=True)

@plugin.route('/search_again/<field>')
def search_again(field):
    try:
        params = eval(config.getSetting('search_parameters'))
        params.update({'search': ''})
    except:
        debug.log('Search Parameters not set !', xbmc.LOGERROR)
        return
    again = colorizeText(myTidalSettings.folderColor, _T('Search again'))
    cmds = [('search', again ),
            ('artist', colorizeText(myTidalSettings.favoriteColor, _T('Artist') + ': ')),
            ('title', colorizeText(myTidalSettings.favoriteColor, _T('Track') + ': ')),
            ('album', colorizeText(myTidalSettings.favoriteColor, _T('Album') + ': ')),
            ('albumartist', colorizeText(myTidalSettings.favoriteColor, _T('Album Artist') + ': ')),
            ('year', colorizeText(myTidalSettings.favoriteColor, _T('Album Year') + ': ')),
            ]
    answer = 1
    while answer > 0:
        menue = ['%s%s' % (s_head, params.get(s_key)) for s_key, s_head in cmds]
        answer = xbmcgui.Dialog().select(_T('Search again'), menue)
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
        xbmcgui.Dialog().notification(plugin.name, _S('Please login first'), xbmcgui.NOTIFICATION_ERROR)
        return
    # Submenu: Parameters for Playlist-Generation
    cmds = [('action', colorizeText(myTidalSettings.folderColor, _S('Start')) ),
            ('playlist', colorizeText(myTidalSettings.favoriteColor, _T('Playlist') + ': ')),
            ('Position', colorizeText(myTidalSettings.favoriteColor, _S('From Position') + ': ')),
            ('NumItems', colorizeText(myTidalSettings.favoriteColor, _S('To Position') + ': ')),
            ]
    item = item_info.getSelectedListItem()
    item['action'] = ''
    item['playlist'] = myTidalSettings.default_videoplaylist if item_type.startswith('video') else myTidalSettings.default_trackplaylist
    item['playlist_id'] = myTidalSettings.default_videoplaylist_id if item_type.startswith('video') else myTidalSettings.default_trackplaylist_id
    numItems = item['NumItems']
    answer = 1
    while answer > 0:
        menue = ['%s%s' % (s_head, item.get(s_key)) for s_key, s_head in cmds]
        answer = xbmcgui.Dialog().select(_S('Generate Playlist'), menue)
        if answer == 0 and not item['playlist_id']:
            answer = 1 # Playlist not set
        if answer > 0:
            if answer == 1:
                playlist = session.user.selectPlaylistDialog(_S('Destination Playlist for %s') % _T('Tracks' if item_type.startswith('track') else 'Videos'), allowNew=True)
                if playlist:
                    item['playlist'] = playlist.title
                    item['playlist_id'] = playlist.id
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
        debug.log('Playlist "%s" found.' % playlist_id, xbmc.LOGERROR)
        return
    items = item_info.getAllListItems()
    numItems = len(items)
    if numItems == 0:
        debug.log('No ListItems found.', xbmc.LOGERROR)
        return            
    pos = min(int(from_pos), numItems)
    lastPos = min(int(to_pos), numItems)
    numItems = lastPos - pos + 1
    progress = xbmcgui.DialogProgress()
    progress.create(_S('Searching in TIDAL ...'))
    line3 = _S('Searching ...')
    tracks = []
    while pos <= lastPos and not progress.iscanceled():
        item = items[pos]
        artist = item.get('Artist')
        title = item.get('Title')
        album = item.get('Album') if not item.get('Compilation') else ' ' # item.get('Title')
        albumartist = item.get('AlbumArtist') if not item.get('Compilation') else ' ' # item.get('Artist')
        year = '%s' % item.get('YearInt')
        percent = (pos * 100) / numItems 
        line1 = '%s: %s' % (_T('Artist'), artist)
        line2 = '%s: %s' % (_T('Title'), title)
        progress.update(percent, line1, line2, line3)
        debug.log('Searching Title: %s - %s' % (artist, title), xbmc.LOGNOTICE)
        track_id = item.get('track_id')
        if track_id:
            track = session.get_track(track_id, withAlbum=True)
            if track:
                line3 = 'TIDAL-ID %s: %s - %s (%s)' % (track.id, track.artist.name, track.title, track._year)
                debug.log('Found TIDAL Track-Id %s: %s - %s' % (track.id, track.artist.name, track.title), xbmc.LOGNOTICE)
                tracks.append(track)
                pos = pos + 1
                continue
        result = session.search_extra(artist, title, album, albumartist, year, limit=20)
        if len(result.tracks) > 0:
            # Sort over matchLevel
            result.tracks.sort(key=lambda line: line.getSortField('match'), reverse=True)
            # Take the first result (best matchLevel) 
            track = result.tracks[0]
            line3 = 'ID %s: %s - %s (%s)' % (track.id, track.artist.name, track.title, track._year)
            debug.log('Found Title Id %s: %s - %s' % (track.id, track.artist.name, track.title), xbmc.LOGNOTICE)
            tracks.append(track)
        else:
            debug.log('Title not found.', xbmc.LOGNOTICE)
            line3 = '%s: %s - %s' % (_S('Not Found'), item.get('Artist'), item.get('Title'))
        pos = pos + 1
        
    numTracks = len(tracks)
    line2 = '%s of %s Items found.' % (numTracks, numItems)
    if progress.iscanceled():
        yes = xbmcgui.Dialog().yesno('Search canceled', 'Search aborted by user !', line2, 'Add these Items to the Playlist ?')
        if not yes:
            progress.close()
            debug.log('Search aborted by user.', xbmc.LOGNOTICE)
            return False
    if playlist and numTracks > 0:
        progress.update(99, 'Ready !', line2, 'Inserting Tracks into the Playlist ...')
        session.user.add_playlist_entries(playlist=playlist, items=tracks)
        progress.update(100, 'Ready !', ' ', ' ')
    xbmc.sleep(1000)
    progress.close()

    debug.log('Search terminated successfully.', xbmc.LOGNOTICE)
    return True

#------------------------------------------------------------------------------
# MAIN Program of the Plugin
#------------------------------------------------------------------------------

if __name__ == '__main__':
    try:
        plugin.run()
        session.close()
        debug.killDebugThreads()
    except HTTPError as e:
        if e.response.status_code in [401, 403]:
            dialog = xbmcgui.Dialog()
            dialog.notification(plugin.name, _T('Authorization problem'), xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()

# End of File