import requests
from bs4 import BeautifulSoup
import urllib.parse
import re


def extract_product_info(product_url):
    """Extract basic product metadata from a Booth product page.

    Returns dict with keys: {'作品名','サークル名','作家名','発売日','イベント名'}
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        # First try to GET the page. If it contains an age-check block, set cookie and retry.
        resp = session.get(product_url, timeout=10)
        resp.raise_for_status()
    except Exception:
        raise

    text = resp.text
    soup = BeautifulSoup(text, 'html.parser')

    # If an R18 prompt exists and JS handler is present ('.js-approve-adult'), emulate by setting cookie and reloading
    if soup.select_one('.js-approve-adult') is not None:
        session.cookies.set('adult', 't', domain='booth.pm', path='/')
        try:
            resp = session.get(product_url, timeout=10)
            resp.raise_for_status()
            text = resp.text
            soup = BeautifulSoup(text, 'html.parser')
        except Exception:
            # fallthrough, continue parsing whatever we have
            pass

    title = None
    circle = None
    author = None
    release_date = None
    event_name = None

    # 1) Prefer og:title: pattern often '作品名 - サークル名 - BOOTH'
    og_title = soup.find('meta', attrs={'property': 'og:title'})
    if og_title and og_title.get('content'):
        content = og_title['content'].strip()
        # split by ' - ' and take first as title, second as circle if present
        parts = [p.strip() for p in content.split(' - ')]
        if len(parts) >= 1:
            title = parts[0]
        if len(parts) >= 2:
            # last part often is 'BOOTH', so if there are >=3, take the middle as circle
            if parts[-1].upper() == 'BOOTH' and len(parts) >= 3:
                circle = parts[1]
            elif parts[-1].upper() != 'BOOTH' and len(parts) >= 2:
                circle = parts[1]

    # Fallback: try <h1>
    if not title:
        h1 = soup.find('h1')
        if h1:
            t = h1.get_text(strip=True)
            if t:
                title = t

    # Try to find author/circle by anchors pointing to /users/ or /makers/
    for a in soup.find_all('a'):
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if not text:
            continue
        if '/users/' in href and 'sign_in' not in href.lower():
            # prefer this as author
            if not author:
                author = text
        if '/makers/' in href or '/users/' in href and not circle:
            # maker may correspond to circle
            if not circle:
                circle = text

    # meta author
    meta_author = soup.find('meta', attrs={'name': 'author'})
    if meta_author and meta_author.get('content'):
        if not author:
            author = meta_author['content'].strip()

    # Release date: look for common date patterns near keywords
    date_match = None
    # look for explicit labels
    for label in ['発売日', '販売日', '公開日', '公開', '更新日', '登録日']:
        m = soup.find(text=re.compile(label))
        if m:
            # attempt to find nearest date-like string around this occurrence
            s = m.parent.get_text(separator=' ', strip=True)
            dm = re.search(r'\d{4}[年\-/.]?\s?\d{1,2}[月\-/.]?\s?\d{1,2}', s)
            if dm:
                date_match = dm.group(0)
                break
    if not date_match:
        # search whole page for first date-like pattern
        dm = re.search(r'\d{4}[年\-/.]?\s?\d{1,2}[月\-/.]?\s?\d{1,2}|\d{4}-\d{2}-\d{2}', text)
        if dm:
            date_match = dm.group(0)
    if date_match:
        release_date = date_match

    # Event name: search for 'コミックマーケット' or 'コミケ' or patterns like C123 in page
    evt = None
    m = re.search(r'コミックマーケット\s*\d{1,4}|コミケ\s*\d{1,4}', text)
    if m:
        evt = m.group(0)
    else:
        # look for patterns like 'c123' in JS blobs and expand to C123
        m2 = re.search(r'"value"\s*:\s*"c(\d{1,4})"', text, re.I)
        if m2:
            evt = f"C{m2.group(1)}"
    if evt:
        # normalize 'コミックマーケット107' -> 'C107'
        mnum = re.search(r'\d{1,4}', evt)
        if mnum:
            event_name = f"C{mnum.group(0)}"
        else:
            event_name = evt

    return {
        '作品名': title,
        'サークル名': circle,
        '作家名': author,
        '発売日': release_date,
        'イベント名': event_name
    }