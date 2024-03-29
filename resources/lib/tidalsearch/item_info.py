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

import os, re
from datetime import date

from kodi_six import xbmc, xbmcgui

from .common import Const, PY2
from .config import log


#------------------------------------------------------------------------------
# Display multiple Lines as a dialog
#------------------------------------------------------------------------------

def showDialog(lines, timeout=0):
    win = xbmcgui.WindowDialog()
    background_img  = os.path.join(Const.addon_path, 'resources','media','info_background.png')
    starty = 0
    h = 75 + 25 * len(lines)
    win.addControl(xbmcgui.ControlImage(x=0, y=starty, width=1920, height=h, filename=background_img, colorDiffuse='0xEEEEEEEE'))
    y = starty
    for line in lines:
        y += 25
        win.addControl(xbmcgui.ControlLabel(x=50, y=y, width=1820, height=25, label=line))
    if timeout > 0:
        win.show()
        xbmc.sleep(5000)
        win.close()
    else:
        win.doModal()
    del win

#------------------------------------------------------------------------------
# itemInfoDialog
#------------------------------------------------------------------------------

def itemInfoDialog():
    item = getSelectedListItem()
    tidalIds = []
    if item.get('track_id'):
        tidalIds.append('track_id=\"%s\"' % item.get('track_id'))
    if item.get('video_id'):
        tidalIds.append('video_id=\"%s\"' % item.get('video_id'))
    lines = ('FolderPath= \"%s\"' % item.get('FolderPath'),
             'Content= \"%s\"' % item.get('Content'),
             'URL= \"%s\"' % item.get('FileNameAndPath'),
             'Label= \"%s\"' % item.get('Label'),
             'Artist= \"%s\"' % item.get('Artist'),
             'Title= \"%s\"' % item.get('Title'),
             'Album= \"%s\"' % item.get('Album'),
             'AlbumArtist= \"%s\"' % item.get('AlbumArtist'),
             'Track= \"%s\" %s' % (item.get('TrackNumber'), 'Compilation' if item.get('Compilation') else ''),
             'Genre= \"%s\"' % item.get('Genre'),
             'Comment= \"%s\"' % item.get('Comment'),
             'Rating= \"%s\", UserRating= \"%s\"' % (item.get('Rating'), item.get('UserRating')),
             'PlotOutline= \"%s\"' % item.get('PlotOutline'),
             'Studio= \"%s\"' % item.get('Studio'),
             'Year= \"%s\", Date=\"%s\", ReleaseDate=\"%s\"' % (item.get('Year'), item.get('Date'), item.get('ReleaseDate')),
             'Duration= \"%s\"' % item.get('Duration'),
             'Fanart= \"%s\"' % item.get('Fanart'),
             'Thumb= \"%s\"' % item.get('Thumbnail'),
             'Type= \"%s\" %s' % (item.get('Type'), ','.join(tidalIds)),
             )
    for line in lines:
        log.info(line)
    showDialog(lines)

#------------------------------------------------------------------------------
# Get Informations of ListItems
#------------------------------------------------------------------------------

def getSelectedListItem():
    focusId = xbmcgui.Window().getFocusId()
    pos = xbmc.getInfoLabel('Container(%s).Position' % focusId)
    return getGuiListItem(focusId, pos)

def getAllListItems():
    focusId = xbmcgui.Window().getFocusId()
    numItems = int('0%s' % xbmc.getInfoLabel('Container(%s).NumItems' % focusId))
    items = []
    for pos in range(1,numItems):
        item = getGuiListItem(focusId, pos)
        if item.get('Artist') and item.get('Title'):
            items.append(item)
    return items

def getGuiListItem(focusId, pos):

    labels = [ 'FileNameAndPath', 'Label', 'Artist', 'Title', 'Album', 'AlbumArtist', 'Rating', 'UserRating', 'Date', 'ReleaseDate',
               'Genre', 'TrackNumber', 'PlotOutline', 'Studio', 'Comment', 'Year', 'Duration', 'Fanart', 'Thumbnail' ]
    position = 'Container(%s).ListitemPosition(%s).' % (focusId, pos)
    # Initial Item Label Values
    item = {'FolderPath': xbmc.getInfoLabel('Container.FolderPath'),
            'Content': xbmc.getInfoLabel('Container.Content'),
            'FocusID': focusId,
            'Position': int('0%s' % pos),
            'NumItems': int('0%s' % xbmc.getInfoLabel('Container(%s).NumItems' % focusId)),
            'OriLabel': xbmc.getInfoLabel(position + 'Label'),
            'Compilation': False}
    # Patterns to remove from Colored Labels
    #patterns = [ '\[COLOR \w+\]', '\[\/COLOR\]', '\[\/?B\]', '\[\/?I\]', '\[\/?LIGHT\]',
    #             '\[\/?UPPERCASE\]','\[\/?LOWERCASE\]', '\[\/?CAPITALIZE\]', '\[CR\]',
    patterns = [ '\[[^]]*\]', '\(\d+\)',
                '\(\s*Explicit\s*\)', '\(\s*Album Version\s*\)', '\(Stream locked\)', '\(Stream gesperrt\)' ]
    resubs = [re.compile(pattern) for pattern in patterns]
    coloredLabels = [ 'Label', 'Artist', 'Title', 'Album', 'AlbumArtist' ]
    # Get all Labels
    for label in labels:
        labelText =  xbmc.getInfoLabel(position + label)
        if label in coloredLabels:
            for resub in resubs:
                labelText = resub.sub('', labelText)
        item[label] = labelText

    all_extensions = {'mp3': 'mp3', 'm4a': 'm4a', 'mp4': 'mp4', 'ogg': 'ogg'}
    # Create other properties
    extension = ''
    itemType = 'music'
    if '.' in item.get('FileNameAndPath'):
        extension = all_extensions.get(item.get('FileNameAndPath').split('.')[-1].lower())
        if extension in ('mp4', 'mkv', 'wmv'):
            itemType = 'video'
        else:
            itemType = 'music'

    # Extract TIDAL Track-ID from comment, if set
    try:
        if PY2:
            match = re.match('.*track_id=(\d+).*', item.get('Comment'), re.IGNORECASE)
        else:
            match = re.match('.*track_id=(\d+).*', item.get('Comment'), re.RegexFlag.IGNORECASE)
        item['track_id'] = match.group(1).strip()
        itemType = 'music'
    except:
        pass
    # Extract TIDAL Video-ID from comment, if set
    try:
        if PY2:
            match = re.match('.*video_id=(\d+).*', item.get('PlotOutline'), re.IGNORECASE)
        else:
            match = re.match('.*video_id=(\d+).*', item.get('PlotOutline'), re.RegexFlag.IGNORECASE)
        item['video_id'] = match.group(1).strip()
        itemType = 'video'
    except:
        pass

    # TrackNumber as Integer
    intTrack = 0
    try:
        trackNumber = item.get('TrackNumber')
        intTrack = int('0%s' % trackNumber)
    except:
        pass
    s_albumartist = '%s' % item.get('AlbumArtist')
    if intTrack == 0 or 'divers' in s_albumartist.lower() or 'various' in s_albumartist.lower():
        trackNumber = ''
        item.update({'Compilation': True})
    # Year as Integer
    try:
        year = item.get('Year')
        intYear = int('0%s' % year)
        if intYear >= 197 and intYear <= 201:
            intYear = (intYear * 10) + 5
            year = '%s' & intYear
        if intYear < 1960 or intYear > 2099:
            intYear = date.today().year
            year = '%s' % intYear
    except:
        intYear = date.today().year
        year = '%s' % intYear

    if (Const.youtube_addon_id in item.get('FileNameAndPath') or not item.get('Artist')) and item.get('Title').find(' - ') > 0:
        # Get artist from title from the Youtube-Addon Label
        artist, title = item.get('Title').split(' - ', 1)
        item.update({'Artist': artist, 'Title': title}) 
    elif not item.get('Artist') and not item.get('Title') and item.get('Label').find(' - ') > 0:
        artist, title = item.get('Label').split(' - ', 1)
        if '.' in title:
            extension = title.split('.')[-1].lower()
            if len(extension) == 3:
                title = title.split('.')[0]
        item.update({'Artist': artist, 'Title': title})

    # Set/Update some Properties
    item.update({'Extension': extension, 
                 'Type': itemType,
                 'TrackNumber': trackNumber,
                 'TrackNumberInt': intTrack,
                 'Year': year,
                 'YearInt': intYear,
                 })
    return item

# End of File