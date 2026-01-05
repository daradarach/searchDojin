import requests
from bs4 import BeautifulSoup
import re
import sys
import urllib.parse
from urllib.parse import urlparse, parse_qs, urlunparse

def clean_url(url):
    """
    URLからsrsltidパラメータを除去する。
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    if 'srsltid' in query_params:
        del query_params['srsltid']
        # 再構築
        new_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
        parsed = parsed._replace(query=new_query)
        return urlunparse(parsed)
    return url
    
def extract_product_info(product_url):

    # URLにパラメータを追加
    modified_url = product_url + '&adult_view=1&nrdp=1'
    
    # ページを取得
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(modified_url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # --- 1. 作品名(meta descriptionから) ---
    title = None
    circle = None
    meta_desc = soup.find('meta', attrs={'property': 'og:title'})
    if meta_desc and meta_desc.get('content'):
        content_text = meta_desc['content']
        match = re.search(r'^(.*?)（(.*?)）の通販・購入はメロンブックス', content_text)
        if match:
            title = match.group(1).strip()
            circle = match.group(2).strip()

    author = None
    # 作家名
    author_th = soup.find('th', string=re.compile(r'作家名'))
    if author_th:
        author_a = author_th.find_next_sibling('td').find('a')
        if author_a:
            author = author_a.get_text(strip=True)

    release_date = None
    # --- 2. 発売日 ---
    release_td = soup.find('th', string=re.compile(r'発行日'))
    if release_td:
        release_date_text = release_td.find_next_sibling('td').get_text(strip=True)
        if release_date_text:
            release_date = release_date_text

    # --- 4. イベント名 [追加] ---
    event_name = None
    # まず、指示通り「イベント」<th> を探す
    event_th = soup.find('th', string=re.compile(r'イベント'))
    if event_th:
        event_td = event_th.find_next_sibling('td')
        if event_td:
            event_name = event_td.get_text(strip=True)
            if 'コミックマーケット' in event_name:
                event_name = str.replace(event_name, 'コミックマーケット', 'C')

    return {
        '作品名': title,
        'サークル名': circle,
        '作家名': author,
        '発売日': release_date,
        'イベント名': event_name
    }

