import requests
from bs4 import BeautifulSoup
import re
import sys
from urllib.parse import urlparse, parse_qs, urlunparse

def extract_product_info(product_url):

    # ページを取得
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(product_url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # --- 1. 作品名(meta descriptionから) ---
    title = None
    circle = None
    author = None

    pagetitle = soup.find('title').get_text(strip=True)
    if pagetitle:
        match = re.search(r'^(.*?)\s\[(.*?)\((.*?)\)\].*', pagetitle)
        if match:
            title = match.group(1).strip()
            circle = match.group(2).strip()
            author = match.group(3).strip()

    release_date = None
    # --- 2. 発売日 ---
    release_td = soup.find('td', string=re.compile(r'発行日'))
    if release_td:
        release_date_text = release_td.find_next_sibling('td').get_text(strip=True)
        if release_date_text:
            release_date = release_date_text

    # --- 3. イベント名 ---
    event_name = None
    event_td = soup.find('td', string=re.compile(r'初出イベント'))  
    if event_td:
        event_text = event_td.find_next_sibling('td').get_text(strip=True)
        if event_text:
            match = re.search(r'^\d{4}/\d{2}/\d{2}\s+(.*?)$', event_text)
            if match:
                event_name = match.group(1).strip()

    return {
        '作品名': title,
        'サークル名': circle,
        '作家名': author,
        '発売日': release_date,
        'イベント名': event_name
    }
