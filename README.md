# context.item.tidal2

This is a Kodi Context Menu Addon to search for TIDAL content.

This Addon requires my Kodi TIDAL2 Addon [plugin.audio.tidal2](https://github.com/arnesongit/plugin.audio.tidal2)

See [changelog.txt](https://github.com/arnesongit/context.item.tidal2/blob/master/changelog.txt) for informations.

## Manual Installation

1. Download the zip file from the repository folder [for Kodi 19](https://github.com/arnesongit/repository.tidal2/tree/main/context.item.tidal2)
   or [for Kodi 17 and 18](https://github.com/arnesongit/repository.tidal2/tree/until-leia/context.item.tidal2).
2. Use "Install from Zip" Method to install the addon. You have to allow third party addon installation in the Kodi settings !

## Installation with TIDAL2 Repository

With this method you will get updates automatically.

1. Download the Repository zip file [for Kodi 19](https://github.com/arnesongit/repository.tidal2/blob/main/repository.tidal2/repository.tidal2-0.2.0.zip?raw=true)
   or [for Kodi 17 and 18](https://github.com/arnesongit/repository.tidal2/blob/until-leia/repository.tidal2/repository.tidal2-0.1.0.zip?raw=true).
2. Use "Install from Zip" Method to install the repository. You have to allow third party addon installation in the Kodi settings !

## Update from Kodi 18 to Kodi 19

If you use my TIDAL2 repository, please uninstall this repository before upgrading to Kodi 19.

After the Kodi 19 update you can install the new TIDAL2 addon from zip file as described above
or you can install my [new TIDAL2 Repository for Kodi 19](https://github.com/arnesongit/repository.tidal2/blob/main/repository.tidal2/repository.tidal2-0.2.0.zip?raw=true)
and upgrade the TIDAL2 addon from this repository.

## Using the "TIDAL2 Search" context item menu

This addon appears as "TIDAL2 Search..." in the context menu of a selected item.

If you select this menu entry, a new submenu pops up and you can call following functions:
- Fuzzy Search
- Search in TIDAL
- Generate Track Playlist
- Generate Video Playlist
- ListItem Info  (if you enable debug logging in the addon settings)

With "Fuzzy Search" and "Search in TIDAL" the addon reads the information of the selected list item, calls the search function
in the TIDAL2 addon with this informations and shows the search result page of the TIDAL2 addon.
This works with all kinds of media items you can select, also with other addons and directory folder items (files).

With "Generate Track Playlist" and "Generate Video Playlist" multiple items of the actutal item list can be searched
with the Fuzzy search method. The best matching results will be inserted into a TIDAL playlist.

## TIDAL2 Search as Keyboard Hotkey

You can also call the TIDAL2 Search context menu with a hotkey, if you add the conext menu call into the keyboard.xml
file (within the keymaps folder of the Kodi user data folder).

Callable functions:

RunPlugin(plugin://context.item.tidal2/context_menu)        Opens the TIDAL2 Search context menu
RunPlugin(plugin://context.item.tidal2/search_fuzzy)        Start "Fuzzy Search" directly with the selected item
RunPlugin(plugin://context.item.tidal2/search_selected)     Start "Search in TIDAL" directly with the selected item

Here is an example to start the context menu with F1 function key on the keyboard (which is the red button on my remote control).
Example: keyboard.xml
```
<keymap>
  <global>
    <keyboard>
      <f1>RunPlugin(plugin://context.item.tidal2/context_menu)</f1>         <!-- Red Button -->
    </keyboard>
  </global>
</keymap>
```
