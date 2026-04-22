#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Merged Scraper - Ghostkernel Wrestling Hub
Combines M3U8 IPTV playlists + watchwrestling24.net web scraping
Provides dual-source redundancy for maximum uptime
"""

import logging
from resources import scraper_m3u8
from resources import scraper_watchwrestling24

logger = logging.getLogger(__name__)


def get_streams(promotion, show=None):
    """
    Get wrestling streams from ALL sources
    Merges results from M3U8 + watchwrestling24
    
    Args:
        promotion (str): 'wwe', 'aew', 'njpw', 'impact', 'roh', 'nxt'
        show (str): Optional show filter
    
    Returns:
        list: Combined stream objects from both sources
    """
    try:
        all_streams = []
        
        # Source 1: M3U8 IPTV playlists
        try:
            m3u8_streams = scraper_m3u8.get_streams(promotion, show)
            if m3u8_streams:
                logger.info(f"M3U8: Found {len(m3u8_streams)} streams for {promotion}")
                all_streams.extend(m3u8_streams)
        except Exception as e:
            logger.warning(f"M3U8 scraper error: {e}")
        
        # Source 2: watchwrestling24.net
        try:
            ww24_streams = scraper_watchwrestling24.get_streams(promotion)
            if ww24_streams:
                logger.info(f"WatchWrestling24: Found {len(ww24_streams)} shows for {promotion}")
                all_streams.extend(ww24_streams)
        except Exception as e:
            logger.warning(f"watchwrestling24 scraper error: {e}")
        
        logger.info(f"Total streams found for {promotion}: {len(all_streams)}")
        
        # Sort by date (most recent first)
        try:
            all_streams.sort(key=lambda x: x.get('date', ''), reverse=True)
        except:
            pass
        
        return all_streams
    
    except Exception as e:
        logger.error(f"Error in merged scraper: {e}")
        return []


def get_m3u8_streams_only(promotion):
    """Get streams from M3U8 source only"""
    try:
        return scraper_m3u8.get_streams(promotion)
    except Exception as e:
        logger.error(f"Error getting M3U8 streams: {e}")
        return []


def get_watchwrestling24_streams_only(promotion):
    """Get streams from watchwrestling24 source only"""
    try:
        return scraper_watchwrestling24.get_streams(promotion)
    except Exception as e:
        logger.error(f"Error getting watchwrestling24 streams: {e}")
        return []


def test_all_sources():
    """Test both scraper sources"""
    try:
        print("Testing merged scraper...\n")
        
        # Test WWE from both sources
        print("=" * 50)
        print("WWE - M3U8 Source")
        print("=" * 50)
        m3u8_wwe = get_m3u8_streams_only('wwe')
        print(f"Found {len(m3u8_wwe)} streams")
        if m3u8_wwe:
            for stream in m3u8_wwe[:3]:
                print(f"  - {stream['title']}")
        
        print("\n" + "=" * 50)
        print("WWE - watchwrestling24.net Source")
        print("=" * 50)
        ww24_wwe = get_watchwrestling24_streams_only('wwe')
        print(f"Found {len(ww24_wwe)} shows")
        if ww24_wwe:
            for show in ww24_wwe[:3]:
                print(f"  - {show['title']}")
        
        print("\n" + "=" * 50)
        print("WWE - Combined Sources")
        print("=" * 50)
        combined = get_streams('wwe')
        print(f"Found {len(combined)} total streams")
        
        return True
    
    except Exception as e:
        print(f"Test failed: {e}")
        return False
