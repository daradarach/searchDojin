import requests
from bs4 import BeautifulSoup
import re


def extract_product_info(product_url):
    """Extract basic product metadata from a DLsite product page.

    Returns a dict with the same keys as other site modules:
    {'作品名','サークル名','作家名','発売日','イベント名'}
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

    # 1) Prefer H1 with itemprop/name for DLsite pages, e.g. <h1 itemprop="name" id="work_name">Title</h1>
    h1 = soup.find('h1', attrs={'itemprop': 'name', 'id': 'work_name'})
    if not h1:
        # try less strict matches
        h1 = soup.find('h1', attrs={'itemprop': 'name'}) or soup.find('h1', id='work_name') or soup.find('h1')
    if h1:
        title = h1.get_text(strip=True)

    # 2) Try og:title as a fallback (may contain circle info)
    meta_title = soup.find('meta', attrs={'property': 'og:title'})
    if meta_title and meta_title.get('content'):
        content = meta_title['content']
        # common patterns: "作品名（サークル名）...", "作品名 / サークル名"
        m = re.search(r'^(.*?)（(.*?)）', content)
        if m:
            # only set title if missing; always prefer h1-derived title
            if not title:
                title = m.group(1).strip()
            if not circle:
                circle = m.group(2).strip()
        else:
            m2 = re.search(r'^(.*?)\s*[/-]\s*(.*?)$', content)
            if m2:
                if not title:
                    title = m2.group(1).strip()
                if not circle:
                    circle = m2.group(2).strip()
            else:
                if not title:
                    title = content.strip()

    # First try the explicit maker span used on DLsite pages: <span itemprop="brand" class="maker_name"> <a>Circle</a> </span>
    circle_span = soup.find('span', attrs={'itemprop': 'brand', 'class': 'maker_name'})
    if circle_span:
        a = circle_span.find('a')
        if a and a.get_text(strip=True):
            circle = a.get_text(strip=True)
        else:
            circle = circle_span.get_text(strip=True)

    # Fallback: try to find a circle/maker link anywhere
    if not circle:
        circle_link = soup.find('a', href=re.compile(r'/maker/'))
        if circle_link and circle_link.get_text(strip=True):
            circle = circle_link.get_text(strip=True)

    # Try to extract author: DLsite pages often have a table row like <th>作者</th><td><a>Author</a></td>
    author_th = soup.find('th', string=re.compile(r'作者|著者'))
    if author_th:
        td = author_th.find_next_sibling('td')
        if td:
            a = td.find('a')
            if a and a.get_text(strip=True):
                author = a.get_text(strip=True)
            else:
                author = td.get_text(strip=True)

    # Fallback: some pages use itemprop="author"
    if not author:
        author_tag = soup.find(attrs={'itemprop': 'author'})
        if author_tag and author_tag.get_text(strip=True):
            author = author_tag.get_text(strip=True)

    # Try to locate release date: look for nodes containing 発売日/販売日/登録日
    date_label = soup.find(text=re.compile(r'発売日|販売日|登録日'))
    if date_label:
        # sometimes label is in a dt/th and value is next sibling
        parent = date_label.parent
        if parent:
            sibling = parent.find_next_sibling()
            if sibling:
                date_text = sibling.get_text(strip=True)
                if date_text:
                    release_date = date_text

    # Try to extract event name: DLsite often uses <span class="icon_EVT" title="..."> <a>イベント名</a> </span>
    evt_span = soup.find('span', class_=re.compile(r'icon_EVT'))
    if evt_span:
        a = evt_span.find('a')
        evt_text = None
        if a and a.get_text(strip=True):
            evt_text = a.get_text(strip=True)
        else:
            evt_text = evt_span.get('title') or (evt_span.get_text(strip=True) if evt_span.get_text(strip=True) else None)
        if evt_text:
            # Normalize: shorten 'コミックマーケット' to 'C' (e.g., 'コミックマーケット107' -> 'C107')
            evt_text = evt_text.replace('コミックマーケット', 'C')
            event_name = evt_text

    # If nothing found, leave fields as None
    return {
        '作品名': title,
        'サークル名': circle,
        '作家名': author,
        '発売日': release_date,
        'イベント名': event_name
    }
