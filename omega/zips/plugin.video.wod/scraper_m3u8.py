#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
M3U8 Scraper Module - Ghostkernel Wrestling Hub
Parses IPTV m3u8 playlists to extract wrestling streams
WWE | AEW | NJPW | NXT | ROH | Impact Wrestling
"""

import requests
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Wrestling channel keywords to match in m3u8 playlists
WRESTLING_KEYWORDS = {
    'wwe': ['WWE', 'World Wrestling Entertainment', 'RAW', 'SmackDown', 'NXT'],
    'aew': ['AEW', 'Dynamite', 'Rampage', 'Collision', 'All Elite Wrestling'],
    'njpw': ['NJPW', 'New Japan Pro Wrestling', 'Wrestling Kingdom'],
    'impact': ['Impact', 'TNA', 'Impact Wrestling', 'IMPACT TV'],
    'roh': ['ROH', 'Ring of Honor'],
    'nxt': ['NXT'],
}


class M3U8Parser:
    """Parse m3u8 IPTV playlists and extract wrestling streams"""
    
    def __init__(self, m3u8_url):
        self.m3u8_url = m3u8_url
        self.channels = []
        self.wrestling_channels = {}
    
    def fetch_playlist(self):
        """Download and parse m3u8 playlist"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.m3u8_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            self.parse_m3u8(response.text)
            self._categorize_wrestling_channels()
            
            return True
        
        except requests.RequestException as e:
            logger.error(f"Error fetching m3u8 playlist: {e}")
            return False
        except Exception as e:
            logger.error(f"Error parsing m3u8: {e}")
            return False
    
    def parse_m3u8(self, content):
        """Parse m3u8 content and extract channel info"""
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for EXTINF lines (channel metadata)
            if line.startswith('#EXTINF:'):
                channel_info = self._parse_extinf(line)
                
                # Next non-comment line is the stream URL
                i += 1
                while i < len(lines):
                    url_line = lines[i].strip()
                    if url_line and not url_line.startswith('#'):
                        channel_info['url'] = url_line
                        self.channels.append(channel_info)
                        break
                    i += 1
            
            i += 1
    
    def _parse_extinf(self, extinf_line):
        """Parse EXTINF metadata line"""
        channel = {
            'name': '',
            'logo': '',
            'url': '',
            'tvg_id': '',
            'tvg_name': ''
        }
        
        # Extract tvg-name
        tvg_name_match = re.search(r'tvg-name="([^"]*)"', extinf_line)
        if tvg_name_match:
            channel['tvg_name'] = tvg_name_match.group(1)
        
        # Extract tvg-logo
        logo_match = re.search(r'tvg-logo="([^"]*)"', extinf_line)
        if logo_match:
            channel['logo'] = logo_match.group(1)
        
        # Extract display name (after comma at end)
        name_match = re.search(r',(.+)$', extinf_line)
        if name_match:
            channel['name'] = name_match.group(1).strip()
        elif channel['tvg_name']:
            channel['name'] = channel['tvg_name']
        
        return channel
    
    def _categorize_wrestling_channels(self):
        """Categorize channels by wrestling promotion"""
        for promotion, keywords in WRESTLING_KEYWORDS.items():
            self.wrestling_channels[promotion] = []
            
            for channel in self.channels:
                channel_text = f"{channel['name']} {channel['tvg_name']}".upper()
                
                # Check if any keyword matches
                for keyword in keywords:
                    if keyword.upper() in channel_text:
                        self.wrestling_channels[promotion].append(channel)
                        break
    
    def get_wrestling_streams(self, promotion):
        """Get all streams for a specific wrestling promotion"""
        return self.wrestling_channels.get(promotion, [])
    
    def get_all_wrestling(self):
        """Get all wrestling channels grouped by promotion"""
        return self.wrestling_channels


def get_streams(promotion, show=None):
    """
    Main function to fetch wrestling streams
    
    Args:
        promotion (str): 'wwe', 'aew', 'njpw', 'impact', 'roh', 'nxt'
        show (str): Optional show name filter
    
    Returns:
        list: Stream objects with title, url, thumb, date, plot
    """
    try:
        # Get m3u8 URL from addon settings or use default
        m3u8_url = get_m3u8_url()
        
        if not m3u8_url:
            logger.warning("No m3u8 URL configured")
            return []
        
        # Parse the playlist
        parser = M3U8Parser(m3u8_url)
        if not parser.fetch_playlist():
            return []
        
        # Get channels for promotion
        channels = parser.get_wrestling_streams(promotion)
        
        if not channels:
            logger.warning(f"No channels found for {promotion}")
            return []
        
        # Convert channels to stream format
        streams = []
        for channel in channels:
            stream = {
                'title': channel['name'] or channel['tvg_name'],
                'url': channel['url'],
                'thumb': channel['logo'],
                'date': datetime.now().isoformat(),
                'plot': f"{promotion.upper()} - {channel['name']}"
            }
            streams.append(stream)
        
        return streams
    
    except Exception as e:
        logger.error(f"Error in get_streams: {e}")
        return []


def get_m3u8_url():
    """
    Get m3u8 URL from addon settings or return default
    """
    try:
        import xbmcaddon
        addon = xbmcaddon.Addon()
        
        # Try to get from settings first
        m3u8_url = addon.getSetting('m3u8_url')
        
        if m3u8_url:
            return m3u8_url
    
    except Exception as e:
        logger.debug(f"Could not read from settings: {e}")
    
    # Return hardcoded default (you can update this)
    # This is the m3u8 URL you found
    return "http://ubusercontent.com/m3u8/NETWORK.m3u8"


def test_m3u8(url):
    """Test if an m3u8 URL is valid and has wrestling content"""
    try:
        parser = M3U8Parser(url)
        if parser.fetch_playlist():
            wrestling_count = sum(len(channels) for channels in parser.wrestling_channels.values())
            return {
                'valid': True,
                'total_channels': len(parser.channels),
                'wrestling_channels': wrestling_count,
                'promotions': {k: len(v) for k, v in parser.wrestling_channels.items() if v}
            }
        return {'valid': False, 'error': 'Failed to parse playlist'}
    
    except Exception as e:
        return {'valid': False, 'error': str(e)}
