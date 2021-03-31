# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Arne Svenson
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

from tidal2.debug import DebugHelper
from .common import addon

#------------------------------------------------------------------------------
# Configuration Class
#------------------------------------------------------------------------------

class Config(object):

    def __init__(self):
        self.load()

    def getSetting(self, setting):
        return addon.getSetting(setting)

    def setSetting(self, setting, value):
        addon.setSetting(setting, value)

    def getAddonInfo(self, val):
        return addon.getAddonInfo(val)

    def load(self):

        self.import_export_path = self.getSetting('import_export_path')

        self.max_thread_count = max(1, int('0%s' % self.getSetting('max_thread_count')))
        self.debug = True if self.getSetting('debug_log') == 'true' else False

        # Blacklist Settings
        self.blacklist1 = self.getSetting('blacklist1').split()
        self.blacklist2 = self.getSetting('blacklist2').split()
        self.blacklist3 = self.getSetting('blacklist3').split()
        self.blacklist1_brackets = True if self.getSetting('blacklist1_brackets') == 'true' else False
        self.blacklist2_brackets = True if self.getSetting('blacklist2_brackets') == 'true' else False
        self.blacklist3_brackets = True if self.getSetting('blacklist3_brackets') == 'true' else False
        self.blacklist1_percent = float('0%s' % self.getSetting('blacklist1_percent'))
        self.blacklist2_percent = float('0%s' % self.getSetting('blacklist2_percent'))
        self.blacklist3_percent = float('0%s' % self.getSetting('blacklist3_percent'))

        # Fuzzy-Settings
        self.artist_favorite_addition = float('0%s' % self.getSetting('artist_favorite_addition'))
        self.artist_min_level = float('0%s' % self.getSetting('artist_min_level'))
        self.fuzzy_artist_level = float('0%s' % self.getSetting('fuzzy_artist_level'))
        self.fuzzy_title_level = float('0%s' % self.getSetting('fuzzy_title_level'))
        self.fuzzy_album_level = float('0%s' % self.getSetting('fuzzy_album_level'))
        self.fuzzy_album_artist_level = float('0%s' % self.getSetting('fuzzy_album_artist_level'))
        self.fuzzy_album_year_level = float('0%s' % self.getSetting('fuzzy_album_year_level'))

#------------------------------------------------------------------------------
# Configuration
#------------------------------------------------------------------------------

settings = Config()

log = DebugHelper(enableDebugLog=settings.debug, enableInfoLog=settings.debug)


# End of File
