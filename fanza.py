import requests
from bs4 import BeautifulSoup
import re
import urllib.parse


def _maybe_follow_age_check(session, response, original_url):
    """If the response is an age check page, try to follow the 'はい' / declared=yes link and re-fetch original_url.
    Returns the new response object (may be the same if no action taken).
    """
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        # detect age-check by URL or by page text/title
        if '/age_check/' in response.url or any(k in response.text for k in ['年齢認証', '年齢確認', '18歳']):
            yes_link = None
            for a in soup.find_all('a', href=True):
                href = a['href']
                txt = ''.join(a.stripped_strings)
                if 'declared=yes' in href or 'はい' in txt or 'Yes' in txt:
                    yes_link = urllib.parse.urljoin(response.url, href)
                    break
            if yes_link:
                try:
                    session.get(yes_link, timeout=10)
                except Exception:
                    pass
                # re-fetch original product URL
                try:
                    new_resp = session.get(original_url, timeout=10)
                    return new_resp
                except Exception:
                    return response
        return response
    except Exception:
        return response


def extract_product_info(product_url):
    """Extract basic product metadata from a FANZA (DMM) product detail page.

    Returns dict with keys: {'作品名','サークル名','作家名','発売日','イベント名'}
    Event is not attempted per request.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    session = requests.Session()
    session.headers.update(headers)

    try:
        resp = session.get(product_url, timeout=10)
        resp.raise_for_status()
    except Exception:
        raise

    # If this is an age check page, follow the flow and re-fetch
    resp = _maybe_follow_age_check(session, resp, product_url)

    # Ensure we have a text string. Some DMM pages are mis-labeled or contain Shift_JIS/cp932 bytes
    b = resp.content
    try:
        text = b.decode(resp.encoding or 'utf-8', errors='replace')
    except Exception:
        text = resp.text

    # If text looks garbled (many replacement chars), try cp932/shift_jis
    if text.count('\ufffd') > 2 or (len(text) > 0 and sum(1 for c in text if ord(c) > 0x7ff) / max(1, len(text)) > 0.3):
        try:
            text = b.decode('cp932', errors='replace')
        except Exception:
            try:
                text = b.decode('shift_jis', errors='replace')
            except Exception:
                pass

    soup = BeautifulSoup(text, 'html.parser')

    title = None
    circle = None
    author = None
    release_date = None
    event_name = None

    # 1) Try JSON-LD structured data
    try:
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                j = script.string
                if not j:
                    continue
                # simple look for datePublished or name or author in JSON-LD string
                m_name = re.search(r'"name"\s*:\s*"([^"]+)"', j)
                if m_name and not title:
                    title = m_name.group(1).strip()
                m_date = re.search(r'"datePublished"\s*:\s*"([^"]+)"', j)
                if m_date and not release_date:
                    release_date = m_date.group(1).strip()
                m_author = re.search(r'"author"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"', j)
                if m_author and not author:
                    author = m_author.group(1).strip()
                if title and (release_date or author):
                    break
            except Exception:
                continue
    except Exception:
        pass

    # 2) Try extracting raw <title> bytes from the original content first - this reliably contains the product name
    try:
        m = re.search(rb'<title>(.*?)</title>', resp.content, flags=re.I | re.S)
        if m:
            raw = m.group(1)
            try:
                raw_txt = raw.decode('utf-8', errors='replace')
            except Exception:
                raw_txt = raw.decode('cp932', errors='replace')
            # prefer parenthetical title: "FullName (Title) - FANZA"
            p = re.search(r'[（\(]([^）\)]{1,200})[）\)]', raw_txt)
            if p:
                title = p.group(1).strip()
            else:
                title = re.sub(r'\s*[\-|｜].*FANZA.*$', '', raw_txt).strip()
    except Exception:
        pass

    # 3) Try meta og:title if still missing
    if not title:
        og = soup.find('meta', property='og:title')
        if og and og.get('content'):
            title = og['content'].strip()

    # 3) Try h1 or title tag
    if not title:
        h1 = soup.find('h1')
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)
    if not title:
        if soup.title and soup.title.get_text(strip=True):
            title = soup.title.get_text(strip=True)

    # 3.5) FANZA uses a specific anchor class for circle links on product pages
    try:
        a_circle = soup.find('a', class_='circleName__txt')
        if a_circle and a_circle.get_text(strip=True):
            circle = a_circle.get_text(strip=True)
    except Exception:
        pass

    # 4) Extract author/circle: look for table rows or labels
    try:
        # look for labels like '作者' or 'サークル' and take next sibling
        for label in ['作者', 'サークル', 'サークル名', 'ブランド', 'メーカー']:
            # find element with the label text
            elems = soup.find_all(text=re.compile(label))
            for e in elems:
                parent = e.parent
                # try next sibling
                sib = parent.find_next_sibling()
                if sib and sib.get_text(strip=True):
                    v = sib.get_text(strip=True)
                    # heuristic: if contains author-like characters, assign
                    if label in ['作者']:
                        author = v
                        break
                    else:
                        # only overwrite circle if we haven't already extracted it from anchor
                        if not circle:
                            circle = v
                        # sometimes author is also present in v separated by '/'
                        # if pattern like "circle / author"
                        if '/' in v and not author:
                            parts = [p.strip() for p in v.split('/')]
                            if len(parts) >= 2:
                                if not circle:
                                    circle = parts[0]
                                author = parts[1]
                        break
                # sometimes the label and value are separated by ':' in the same string
                s = e.strip()
                m = re.search(rf'{label}\s*[:：]\s*(.+)', s)
                if m:
                    v = m.group(1).strip()
                    if label == '作者':
                        author = v
                    else:
                        if not circle:
                            circle = v
                    break
            if author and circle:
                break
    except Exception:
        pass

    # 5) Fallback: try to find a maker link
    if not circle:
        maker = soup.find('a', href=re.compile(r'/maker/|/circle/|/company/|/brand/'), text=True)
        if maker:
            circle = maker.get_text(strip=True)

    # 6) Release date: search for nearby labels and date patterns
    try:
        text_all = soup.get_text(separator=' ', strip=True)
        # common patterns: 2025/12/28 00:00 or 2025年12月28日 00:00
        m = re.search(r'(20\d{2}[年/.-]\s?\d{1,2}[月/.-]\s?\d{1,2}日?\s*(?:\d{2}:\d{2})?)', text_all)
        if not m:
            m = re.search(r'(20\d{2}/\d{1,2}/\d{1,2}\s*\d{2}:\d{2})', text_all)
        if m:
            release_date = m.group(1).strip()
        else:
            # try label-based capture for '配信開始日'
            m2 = re.search(r'配信開始日\s*[:：]?\s*([0-9０-９年/月\-\.\s:：]+)', text_all)
            if m2:
                release_date = m2.group(1).strip()
    except Exception:
        pass

    # Clean up release_date: normalize full-width digits to ASCII and pad times if missing
    try:
        if release_date:
            # convert full-width digits
            trans = str.maketrans('０１２３４５６７８９', '0123456789')
            release_date = release_date.translate(trans)
            release_date = release_date.replace('年', '/').replace('月', '/').replace('日', '').replace('.', '/').replace('-', '/').strip()
            # ensure time exists: if only date, add '00:00'
            if re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', release_date):
                release_date = release_date + ' 00:00'
    except Exception:
        pass

    # If author not found but title contains parentheses with author, attempt extraction such as 'タイトル（作者）'
    if not author and title:
        m = re.search(r'^(.*?)（(.*?)）', title)
        if m:
            # sometimes og:title contains 'タイトル（サークル）' so interpret second as circle
            if not circle:
                circle = m.group(2).strip()

    return {
        '作品名': title,
        'サークル名': circle,
        '作家名': author,
        '発売日': release_date,
        'イベント名': event_name
    }
