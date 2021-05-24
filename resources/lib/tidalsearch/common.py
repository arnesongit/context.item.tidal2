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

import os

from kodi_six import xbmcaddon
from routing import Plugin

#------------------------------------------------------------------------------
# Global Definitions
#------------------------------------------------------------------------------

__addon_id__ = 'context.item.tidal2'
addon = xbmcaddon.Addon(__addon_id__)

class Const(object):
    addon_id = addon.getAddonInfo('id')
    addon_name = addon.getAddonInfo('name')
    addon_path = addon.getAddonInfo('path')
    addon_base_url = 'plugin://' + __addon_id__
    addon_fanart = os.path.join(addon_path, 'fanart.jpg')
    addon_icon = os.path.join(addon_path, 'icon.png')
    youtube_addon_id = 'plugin.video.youtube'

class KodiPlugin(Plugin):

    def __init__(self):
        try:
            # Creates a Dump is sys.argv[] is empty !
            Plugin.__init__(self, base_url=Const.addon_base_url)
        except:
            pass
        self.base_url = Const.addon_base_url
        self.name = Const.addon_name

plugin = KodiPlugin()

# End of File