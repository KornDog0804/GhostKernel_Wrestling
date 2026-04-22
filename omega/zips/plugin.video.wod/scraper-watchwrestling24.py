#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Watch Wrestling 24 Web Scraper
Scrapes watchwrestling24.net for wrestling shows and stream links
WWE | AEW | NJPW | NXT | ROH | Impact | TNA
"""

import requests
import re
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

BASE_URL = "https://watchwrestling24.net"

# Promotion categories on the site
PROMOTION_CATEGORIES = {
    'wwe': '/wwe/',
    'aew': '/aew/',
    'njpw': '/njpw/',
    'impact': '/tna/',  # Site calls it TNA but it's Impact
    'roh': '/roh/',
    'nxt': '/wwe/',  # NXT is under WWE
}

class WatchWrestling24Scraper:
    """Scrape watchwrestling24.net for wrestling content"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_streams(self, promotion):
        """Fetch wrestling shows for a promotion"""
        try:
            if promotion not in PROMOTION_CATEGORIES:
                logger.warning(f"Unknown promotion: {promotion}")
                return []
            
            # Get the category URL
            category_path = PROMOTION_CATEGORIES[promotion]
            url = urljoin(BASE_URL, category_path)
            
            logger.info(f"Scraping {promotion} from {url}")
            
            # Fetch the page
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Parse and extract shows
            streams = self._parse_shows_page(response.text, promotion)
            
            return streams
        
        except requests.RequestException as e:
            logger.error(f"Error fetching {promotion}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing {promotion}: {e}")
            return []
    
    def _parse_shows_page(self, html, promotion):
        """Parse promotion page and extract show listings"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            streams = []
            
            # Look for show containers (typical patterns on streaming sites)
            # Pattern 1: Articles with links
            articles = soup.find_all(['article', 'div'], class_=re.compile('post|show|episode', re.I))
            
            for article in articles[:20]:  # Limit to 20 most recent
                try:
                    # Extract title
                    title_elem = article.find(['h1', 'h2', 'h3', 'a'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Extract link
                    link_elem = article.find('a', href=True)
                    if not link_elem:
                        continue
                    
                    show_url = urljoin(BASE_URL, link_elem['href'])
                    
                    # Extract image/thumbnail
                    img_elem = article.find(['img', 'image'])
                    thumbnail = ""
                    if img_elem:
                        thumbnail = img_elem.get('src', '') or img_elem.get('data-src', '')
                        if thumbnail:
                            thumbnail = urljoin(BASE_URL, thumbnail)
                    
                    # Extract date if available
                    date_elem = article.find(['time', 'span'], class_=re.compile('date|time', re.I))
                    date_str = ""
                    if date_elem:
                        date_str = date_elem.get_text(strip=True)
                    
                    # Create stream object
                    stream = {
                        'title': title,
                        'url': show_url,
                        'thumb': thumbnail,
                        'date': date_str or datetime.now().isoformat(),
                        'plot': f"{promotion.upper()} - {title}",
                        'source': 'watchwrestling24'
                    }
                    
                    streams.append(stream)
                
                except Exception as e:
                    logger.debug(f"Error parsing article: {e}")
                    continue
            
            logger.info(f"Found {len(streams)} shows for {promotion}")
            return streams
        
        except Exception as e:
            logger.error(f"Error parsing page: {e}")
            return []
    
    def get_stream_links(self, show_url):
        """
        Fetch actual playable stream links from a show page
        Returns list of stream URLs
        """
        try:
            response = self.session.get(show_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            stream_urls = []
            
            # Pattern 1: Look for iframe sources
            iframes = soup.find_all('iframe', src=True)
            for iframe in iframes:
                src = iframe.get('src', '')
                if src and ('http' in src or '/' in src):
                    stream_urls.append(src)
            
            # Pattern 2: Look for player divs with data attributes
            players = soup.find_all(['div', 'video'], class_=re.compile('player|video|stream', re.I))
            for player in players:
                # Check for data-src, data-url, src attributes
                for attr in ['data-src', 'data-url', 'data-video', 'src']:
                    src = player.get(attr, '')
                    if src and len(src) > 10:
                        stream_urls.append(src)
            
            # Pattern 3: Look for m3u8 links (HLS streams)
            m3u8_pattern = r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*'
            m3u8_links = re.findall(m3u8_pattern, response.text)
            stream_urls.extend(m3u8_links)
            
            # Pattern 4: Look for mp4 links
            mp4_pattern = r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*'
            mp4_links = re.findall(mp4_pattern, response.text)
            stream_urls.extend(mp4_links)
            
            # Deduplicate
            stream_urls = list(set(stream_urls))
            
            logger.info(f"Found {len(stream_urls)} stream URLs on {show_url}")
            return stream_urls
        
        except Exception as e:
            logger.error(f"Error fetching stream links from {show_url}: {e}")
            return []


def get_streams(promotion):
    """
    Main function to fetch wrestling streams from watchwrestling24
    
    Args:
        promotion (str): 'wwe', 'aew', 'njpw', 'impact', 'roh', 'nxt'
    
    Returns:
        list: Stream objects with title, url, thumb, date, plot
    """
    try:
        scraper = WatchWrestling24Scraper()
        streams = scraper.get_streams(promotion)
        
        return streams
    
    except Exception as e:
        logger.error(f"Error in get_streams: {e}")
        return []


def test_scraper():
    """Test the scraper"""
    try:
        scraper = WatchWrestling24Scraper()
        
        # Test WWE
        print("Testing WWE...")
        wwe_shows = scraper.get_streams('wwe')
        print(f"Found {len(wwe_shows)} WWE shows")
        
        if wwe_shows:
            print(f"Sample: {wwe_shows[0]}")
            # Try to get stream links from first show
            streams = scraper.get_stream_links(wwe_shows[0]['url'])
            print(f"Found {len(streams)} stream links")
        
        # Test AEW
        print("\nTesting AEW...")
        aew_shows = scraper.get_streams('aew')
        print(f"Found {len(aew_shows)} AEW shows")
        
        return True
    
    except Exception as e:
        print(f"Test failed: {e}")
        return False
