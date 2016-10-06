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

import re
import xbmc
import xbmcplugin

from koditidal2 import plugin, TidalConfig2, TidalSession2, _T
from tidalapi.models import SearchResult

import debug
from .config import settings
from .fuzzymodels import FuzzyArtistItem, FuzzyAlbumItem, FuzzyTrackItem, FuzzyVideoItem

#------------------------------------------------------------------------------
# Fuzzy Functions
#------------------------------------------------------------------------------

class FuzzyConfig(TidalConfig2):

    def __init__(self):
        TidalConfig2.__init__(self)

    def load(self):
        TidalConfig2.load(self)


class FuzzySession(TidalSession2):

    def __init__(self, config=FuzzyConfig()):
        TidalSession2.__init__(self, config=config)

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
        debug.log('Searching in TDAL: artist="%s", title="%s", album="%s", albumartist="%s", ftartist="%s", year="%s" ...' % (s_artist, s_title, s_album, s_albumartist, s_ftartist, year), xbmc.LOGNOTICE)
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
        headline = '[COLOR yellow]-------- %s --------[/COLOR]'
        xbmcplugin.setContent(plugin.handle, 'songs')
        if searchresults.artists.__len__() > 0:
            self.add_directory_item(_T('Artists'), plugin.url_for_path('/do_nothing'), isFolder=False, label=headline % _T('Artists'))
            if sort:
                searchresults.artists.sort(key=lambda line: line.getSortField(sort), reverse=reverse)
            self.add_list_items(searchresults.artists, end=False)
        if searchresults.albums.__len__() > 0:
            self.add_directory_item(_T('Albums'), plugin.url_for_path('/do_nothing'), isFolder=False, label=headline % _T('Albums'))
            if sort:
                searchresults.albums.sort(key=lambda line: line.getSortField(sort), reverse=reverse)
            self.add_list_items(searchresults.albums, end=False)
        if searchresults.playlists.__len__() > 0:
            self.add_directory_item(_T('Playlists'), plugin.url_for_path('/do_nothing'), isFolder=False, label=headline % _T('Playlists'))
            if sort:
                searchresults.playlists.sort(key=lambda line: line.getSortField(sort), reverse=reverse)
            self.add_list_items(searchresults.playlists, end=False)
        if searchresults.tracks.__len__() > 0:
            self.add_directory_item(_T('Tracks'), plugin.url_for_path('/do_nothing'), isFolder=False, label=headline % _T('Tracks'))
            if sort:
                searchresults.tracks.sort(key=lambda line: line.getSortField(sort), reverse=reverse)
            self.add_list_items(searchresults.tracks, end=False)
        if searchresults.videos.__len__() > 0:
            self.add_directory_item(_T('Videos'), plugin.url_for_path('/do_nothing'), isFolder=False, label=headline % _T('Videos'))
            if sort:
                searchresults.videos.sort(key=lambda line: line.getSortField(sort), reverse=reverse)
            self.add_list_items(searchresults.videos, end=False)
        if end:
            self.add_list_items([], end=True)

# End of File