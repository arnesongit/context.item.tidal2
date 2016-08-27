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

import debug
from .config import addon, settings

#------------------------------------------------------------------------------
# Texts
#------------------------------------------------------------------------------

__STRINGS__ = {
           
    # Login
    'Addon Settings':                   30500,
    'Search in TIDAL':                  30501,
    'Convert List to Track Playlist':   30502,
    'Convert List to Video Playlist':   30503,
    'ListItem Info':                    30504,
}

#------------------------------------------------------------------------------
# Redefinition of '_' for localized Strings
#------------------------------------------------------------------------------
def _S(string_id):
    try:
        if string_id in __STRINGS__:
            text = addon.getLocalizedString(__STRINGS__[string_id])
            if not text:
                text = '%s: %s' % (__STRINGS__[string_id], string_id)
            return text
        else:
            if settings.debug:
                debug.log('String is missing: %s' % string_id)
                return '?: %s' % string_id
            return string_id
    except:
        return '?: %s' % string_id

# End of File