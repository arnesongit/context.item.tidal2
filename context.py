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

import xbmc, xbmcgui

from lib.tidalsearch.config import settings, CONST 
from lib.tidalsearch import item_info, debug
from lib.tidalsearch.all_strings import _S

#------------------------------------------------------------------------------
# Public Functions
#------------------------------------------------------------------------------

def context_menu():
    commands = []
    if settings.debug:
        commands.append( (_S('ListItem Info'), item_info.itemInfoDialog) )
    item = item_info.getSelectedListItem()
    if item.get('Artist') and item.get('Title'):        
        commands.append( (_S('Search in TIDAL'), 'RunPlugin(plugin://%s/search_selected)' % CONST.addon_id) )
        commands.append( (_S('Convert List to Track Playlist'), 'RunPlugin(plugin://%s/convert_to_playlist/tracks)' % CONST.addon_id) )
        commands.append( (_S('Convert List to Video Playlist'), 'RunPlugin(plugin://%s/convert_to_playlist/videos)' % CONST.addon_id) )
    commands.append( (_S('Addon Settings'), 'Addon.OpenSettings("%s")' % CONST.addon_id) )
    menu = [ txt for txt, func in commands]
    selected = xbmcgui.Dialog().select(CONST.addon_name, menu)
    if selected >= 0:
        txt, func = commands[selected]
        if callable(func):
            func()
        else:
            xbmc.executebuiltin(func)

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------

if __name__ == '__main__':

    context_menu()
    debug.killDebugThreads()
