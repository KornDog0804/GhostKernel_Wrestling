#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ghostkernel Wrestling Hub - Main Plugin
Dual-Source Wrestling Streaming
M3U8 IPTV Playlists + watchwrestling24.net Web Scraping
WWE | AEW | Impact | NJPW | NXT | ROH
"""

import xbmcgui
import xbmcplugin
import xbmcaddon
import routing
import logging
from resources import scraper_merged

# Setup
addon = xbmcaddon.Addon()
addon_handle = int(routing.router.plugin_name.split('?')[0].split('=')[1])
logger = logging.getLogger(addon.getAddonInfo('id'))

# Enable debug logging if enabled in settings
if addon.getSetting('debug_logging') == 'true':
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


@routing.route('/')
def index():
    """Main menu - Wrestling Promotions"""
    items = [
        {
            'label': '🎪 WWE',
            'path': routing.url_for(show_promotion, promotion='wwe'),
            'icon': 'DefaultFolder.png',
        },
        {
            'label': '⚡ AEW - All Elite Wrestling',
            'path': routing.url_for(show_promotion, promotion='aew'),
            'icon': 'DefaultFolder.png',
        },
        {
            'label': '🔥 Impact Wrestling (TNA)',
            'path': routing.url_for(show_promotion, promotion='impact'),
            'icon': 'DefaultFolder.png',
        },
        {
            'label': '🇯🇵 NJPW - New Japan Pro Wrestling',
            'path': routing.url_for(show_promotion, promotion='njpw'),
            'icon': 'DefaultFolder.png',
        },
        {
            'label': '🎯 NXT',
            'path': routing.url_for(show_promotion, promotion='nxt'),
            'icon': 'DefaultFolder.png',
        },
        {
            'label': '🏆 ROH - Ring of Honor',
            'path': routing.url_for(show_promotion, promotion='roh'),
            'icon': 'DefaultFolder.png',
        },
        {
            'label': '⚙️ Settings',
            'path': routing.url_for(settings_action),
            'icon': 'DefaultAddonSettings.png'
        }
    ]
    
    for item in items:
        list_item = xbmcgui.ListItem(item['label'])
        list_item.setArt({
            'icon': item['icon'],
            'fanart': addon.getAddonInfo('fanart')
        })
        xbmcplugin.addDirectoryItem(
            addon_handle,
            item['path'],
            list_item,
            isFolder=True
        )
    
    xbmcplugin.endOfDirectory(addon_handle)


@routing.route('/promotion/<promotion>')
def show_promotion(promotion):
    """Show all streams for a wrestling promotion from ALL sources"""
    try:
        logger.info(f"Fetching streams for {promotion}...")
        
        # Fetch streams from merged sources (M3U8 + watchwrestling24)
        streams = scraper_merged.get_streams(promotion)
        
        if not streams:
            xbmcgui.Dialog().notification(
                'Ghostkernel Wrestling',
                f'No {promotion.upper()} streams found',
                xbmcgui.NOTIFICATION_WARNING,
                3000
            )
            logger.warning(f"No streams found for {promotion}")
            return
        
        logger.info(f"Found {len(streams)} total streams for {promotion}")
        
        # Display each stream as a playable item
        for idx, stream in enumerate(streams):
            # Create list item
            list_item = xbmcgui.ListItem(stream['title'])
            
            # Set video info
            list_item.setInfo('video', {
                'title': stream['title'],
                'plot': stream.get('plot', ''),
                'aired': stream.get('date', '')
            })
            
            # Set artwork
            list_item.setArt({
                'thumb': stream.get('thumb', ''),
                'fanart': addon.getAddonInfo('fanart')
            })
            
            # Mark as playable video
            list_item.setProperty('IsPlayable', 'true')
            
            # Add source label if available
            source = stream.get('source', 'unknown')
            list_item.setLabel2(f"[{source.upper()}]")
            
            # Add to list
            xbmcplugin.addDirectoryItem(
                addon_handle,
                routing.url_for(play_stream, url=stream['url']),
                list_item,
                isFolder=False
            )
        
        xbmcplugin.endOfDirectory(addon_handle)
        logger.info(f"Displayed {len(streams)} streams for {promotion}")
    
    except Exception as e:
        logger.error(f"Error showing promotion {promotion}: {e}", exc_info=True)
        xbmcgui.Dialog().notification(
            'Ghostkernel Wrestling',
            f'Error loading streams: {str(e)}',
            xbmcgui.NOTIFICATION_ERROR,
            3000
        )


@routing.route('/play/<url>')
def play_stream(url):
    """Play a stream"""
    try:
        logger.info(f"Playing stream: {url}")
        
        list_item = xbmcgui.ListItem(path=url)
        list_item.setProperty('IsPlayable', 'true')
        
        # Try to use resolveurl if available
        try:
            from resolveurl import resolve
            resolved_url = resolve(url)
            if resolved_url:
                list_item.setPath(resolved_url)
                logger.info(f"Resolved URL via resolveurl")
            else:
                logger.warning("resolveurl returned empty, using direct URL")
        except ImportError:
            logger.debug("resolveurl not available, using direct URL")
        except Exception as e:
            logger.warning(f"resolveurl failed: {e}, using direct URL")
        
        # Set the resolved stream as playable
        xbmcplugin.setResolvedUrl(addon_handle, True, list_item)
        logger.info("Stream playback initiated")
    
    except Exception as e:
        logger.error(f"Playback error: {e}", exc_info=True)
        xbmcgui.Dialog().notification(
            'Ghostkernel Wrestling',
            f'Playback Error: {str(e)}',
            xbmcgui.NOTIFICATION_ERROR,
            3000
        )
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())


@routing.route('/settings')
def settings_action():
    """Open addon settings"""
    addon.openSettings()


if __name__ == '__main__':
    try:
        routing.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        xbmcgui.Dialog().notification(
            'Ghostkernel Wrestling',
            f'Fatal Error: {str(e)}',
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )
