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

from .config import addon

#------------------------------------------------------------------------------
# Global Definitions
#------------------------------------------------------------------------------

class Msg(object):
    # Global Settings
    i30001 = 30001 # TIDAL2 Search ...
    i30003 = 30003 # Export/Import Path
    i30004 = 30004 # Max. Number of simultaneous search requests
    i30011 = 30011 # Globals
    i30070 = 30070 # Enable Debug-Logging

    # Search  SearcSettings
    i30080 = 30080 # Blacklists
    i30081 = 30081 # Fuzzy-Level
    i30082 = 30082 # Blacklist #1
    i30083 = 30083 # Blacklist #2
    i30084 = 30084 # Blacklist #3
    i30085 = 30085 # Reduce Match-Level for Blacklist Match
    i30086 = 30086 # Minimum Match-Level "Artist"/"Album Artist"
    i30087 = 30087 # Factors for Fuzzy Search:
    i30088 = 30088 # Increase Match-Level for Favorite Artists
    i30089 = 30089 # Match only in brackets ( ) or [ ]

    i30101 = 30101 # Artist
    i30102 = 30102 # Album
    i30103 = 30103 # Playlist
    i30104 = 30104 # Track
    i30105 = 30105 # Video
    i30106 = 30106 # Artists
    i30107 = 30107 # Albums
    i30108 = 30108 # Playlists
    i30109 = 30109 # Tracks
    i30110 = 30110 # Videos

    # Program Progr Text
    i30400 = 30400 # Search Again
    i30401 = 30401 # Search
    i30402 = 30402 # Album Artist
    i30403 = 30403 # Album Year
    i30404 = 30404 # Please login first !
    i30405 = 30405 # Start
    i30406 = 30406 # From Position
    i30407 = 30407 # To Position
    i30408 = 30408 # Generate Playlist
    i30409 = 30409 # Playlist for {what}
    i30410 = 30410 # Searching in TIDAL ...
    i30411 = 30411 # Searching ...
    i30412 = 30412 # Not Found
    i30413 = 30413 # {n} of {m} Items found
    i30414 = 30414 # Search canceled
    i30415 = 30415 # Search aborted by user.
    i30416 = 30416 # Insert found Items to the Playlist ?
    i30417 = 30417 # Finished
    i30418 = 30418 # Inserting Tracks into the Playlist ...
    i30419 = 30419 # Search in TIDAL
    i30420 = 30420 # Fuzzy Search
    i30421 = 30421 # Generate Track Playlist
    i30422 = 30422 # Generate Video Playlist
    i30423 = 30423 # Addon Settings
    i30424 = 30424 # ListItem Info
    i30425 = 30425 # Authorization problem
    i30426 = 30426 # Export Favorite {what} ...
    i30427 = 30427 # Import Favorite {what} ...
    i30428 = 30428 # {n} exported
    i30429 = 30429 # {n} imported
    i30430 = 30430 # Delete Favorite {what}
    i30431 = 30431 # Remove all {what} from Favorites ?
    i30432 = 30432 # Import {what}
    i30433 = 30433 # Export User-Playlists
    i30434 = 30434 # Import User-Playlists ...
    i30435 = 30435 # Export User-Playlist
    i30436 = 30436 # Delete all Favorite {what}
    i30437 = 30437 # Search for New Music ...
    i30438 = 30438 # Limit for Search Results
    i30439 = 30439 # Max. age in days
    i30440 = 30440 # Found new music:
    i30441 = 30441 # Adding found Items to Playlists ...
    i30442 = 30442 # Error while Searching for new Music
    i30443 = 30443 # No new music found !
    i30444 = 30444 # Search aborted.
    i30445 = 30445 # Search Threads are still running.
    i30446 = 30446 # Should all Threads be aborted ?
    i30447 = 30447 # Move Atmos tracks ...
    i30448 = 30448 # Move RA360 tracks ...
    i30449 = 30449 # Move MQA tracks ...
    i30450 = 30450 # Move duplicate tracks ...
    i30451 = 30451 # Move Track to other playlist
    i30452 = 30452 # Export to virtual Library
    i30453 = 30453 # Move from here ...
    i30454 = 30454 # How many items ?
    i30455 = 30455 # Move items ...


def _S(txtid):
    try:
        txt = addon.getLocalizedString(txtid)
        return txt
    except:
        return '%s' % txtid

# End of File