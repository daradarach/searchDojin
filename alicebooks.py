import requests
from bs4 import BeautifulSoup
import re
import urllib.parse


def extract_product_info(product_url):
    """Extract basic product metadata from an alice-books.com product page.

    Returns dict with keys: {'作品名','サークル名','作家名','発売日','イベント名'}
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        resp = requests.get(product_url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception:
        raise

    soup = BeautifulSoup(resp.content, 'html.parser')

    title = None
    circle = None
    author = None
    release_date = None
    event_name = None

    # 1) Extract title and circle from the h1/header structure
    # Alice Books typically shows title as "タイトル / サークル名" in the heading
    heading = soup.find('h1')
    if heading:
        h1_text = heading.get_text(strip=True)
        # Split by " / " to separate title and circle
        if ' / ' in h1_text:
            parts = h1_text.split(' / ')
            title = parts[0].strip()
            if len(parts) > 1:
                circle = parts[1].strip()
        else:
            title = h1_text
    
    # 2) Try og:title as fallback
    if not title:
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            content = og_title['content'].strip()
            if ' / ' in content:
                parts = content.split(' / ')
                title = parts[0].strip()
                if len(parts) > 1 and not circle:
                    circle = parts[1].strip()
            else:
                title = content

    # 3) Extract circle from circle link (if not already found)
    if not circle:
        circle_link = soup.find('a', href=re.compile(r'circle_id='))
        if circle_link:
            circle = circle_link.get_text(strip=True)

    # 4) Extract author from the metadata table
    # Look for table rows with labels like "主な作家" (main author)
    try:
        for tr in soup.find_all('tr'):
            th = tr.find('th')
            td = tr.find('td')
            if th and td:
                label = th.get_text(strip=True)
                value = td.get_text(strip=True)
                if '作家' in label or '著者' in label:
                    author = value
                    break
    except Exception:
        pass

    # 5) Extract release date from metadata table
    # Look for rows with labels like "発行日" (release date)
    try:
        for tr in soup.find_all('tr'):
            th = tr.find('th')
            td = tr.find('td')
            if th and td:
                label = th.get_text(strip=True)
                value = td.get_text(strip=True)
                if '発行日' in label or '発売日' in label:
                    release_date = value
                    break
    except Exception:
        pass

    # 6) Alternative: look for metadata in structured divs
    try:
        # Alice Books may use definition list (dl/dt/dd) for metadata
        dts = soup.find_all('dt')
        for dt in dts:
            label = dt.get_text(strip=True)
            dd = dt.find_next('dd')
            if dd:
                value = dd.get_text(strip=True)
                if '発行日' in label or '発売日' in label:
                    if not release_date:
                        release_date = value
                elif ('作家' in label or '著者' in label) and not author:
                    author = value
    except Exception:
        pass

    return {
        '作品名': title or '',
        'サークル名': circle or '',
        '作家名': author or '',
        '発売日': release_date or '',
        'イベント名': event_name or ''
    }


def clean_url(url):
    """Normalize alice-books.com URLs to product detail page format."""
    # Already in the proper format for alice-books
    return url
