import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

def get_first_search_url_from_melonbooks(query):
    """
    Melonbooksで指定のクエリを検索し、最初の結果のURLを返す。
    """
    # クエリをURLエンコード
    encoded_query = urllib.parse.quote(query)
    
    # 検索URLを構築
    search_url = f"https://www.melonbooks.co.jp/search/search.php?mode=search&search_disp=&chara=&orderby=&disp_number=100&pageno=1&is_sp_view=0&name={encoded_query}&text_type=all&fromagee_flg=2&search_target_all=0&additional_all=1&is_end_of_sale%5B%5D=1&is_end_of_sale2=1&sale_date_before=&sale_date_after=&publication_date_before=&publication_date_after=&co_name=&ci_name=&price_low=0&price_high=0"
    
    # ヘッダーを設定（ボット検知回避）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 検索ページを取得
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # HTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 最初の商品リンクを探す（detail.phpを含むhref）
        # Melonbooksの構造を仮定：商品リスト内のaタグでdetail.phpを含むもの
        first_link_elem = soup.find('a', href=re.compile(r'detail\.php\?product_id='))
        
        if first_link_elem and first_link_elem.get('href'):
            href = first_link_elem['href']
            # 相対URLの場合、ベースURLを追加
            if href.startswith('/'):
                full_url = f"https://www.melonbooks.co.jp{href}"
            else:
                full_url = href
            return full_url
        else:
            return "N/A1"
    
    except requests.RequestException as e:
        return "N/A2"
    except Exception as e:
        return "N/A3"
    
def get_first_search_url_from_dlsite(query):
    """
    Melonbooksで指定のクエリを検索し、最初の結果のURLを返す。
    """
    # クエリをURLエンコード
    encoded_query = urllib.parse.quote(query)
    
    # 検索URLを構築
    search_url = f"https://www.dlsite.com/maniax/fsr/=/language/jp/sex_category%5B0%5D/male/keyword/{encoded_query}/work_category%5B0%5D/doujin/work_category%5B1%5D/books/work_category%5B2%5D/pc/work_category%5B3%5D/app/order%5B0%5D/trend/options_and_or/and/per_page/30/page/1/from/fs.header"
    
    # ヘッダーを設定（ボット検知回避）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 検索ページを取得
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # HTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 最初の商品リンクを探す（detail.phpを含むhref）
        # Melonbooksの構造を仮定：商品リスト内のaタグでdetail.phpを含むもの
        first_link_elem = soup.find('a', href=re.compile(r'https://www.dlsite.com/maniax/work/=/product_id/'))
        if first_link_elem and first_link_elem.get('href'):
            href = first_link_elem['href']
            # 相対URLの場合、ベースURLを追加
            if href.startswith('/'):
                full_url = f"https://www.dlsite.com/maniax/work/=/product_id/{href}"
            else:
                full_url = href
            return full_url
        else:
            return "N/A"
    
    except requests.RequestException as e:
        return "N/A"
    except Exception as e:
        return "N/A"
    
def get_first_search_url_from_toranoana(query):
    """
    Toranoanaで指定のクエリを検索し、最初の結果のURLを返す。
    """
    # クエリをURLエンコード
    encoded_query = urllib.parse.quote(query)
    
    # 検索URLを構築
    search_url = f"https://ec.toranoana.jp/tora_r/ec/app/catalog/list?searchWord={encoded_query}&_gl=1*12n0h8j*_gcl_au*MTczNDk4NDQxNi4xNzU3ODA2NTQ1"
    
    # ヘッダーを設定（ボット検知回避）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 検索ページを取得
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # HTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 最初の商品リンクを探す（detail.phpを含むhref）
        # Melonbooksの構造を仮定：商品リスト内のaタグでdetail.phpを含むもの
        first_link_elem = soup.find('a', href=re.compile(r'https://ec.toranoana.jp/tora_r/ec/item/'))
        if first_link_elem and first_link_elem.get('href'):
            href = first_link_elem['href']
            # 相対URLの場合、ベースURLを追加
            if href.startswith('/'):
                full_url = f"https://ec.toranoana.jp/tora_r/ec/item/{href}"
            else:
                full_url = href
            return full_url
        else:
            return get_first_search_url_from_toranoana_joshi(query)
        
    except requests.RequestException as e:
        return get_first_search_url_from_toranoana_joshi(query)
    except Exception as e:
        return get_first_search_url_from_toranoana_joshi(query)
    
def get_first_search_url_from_toranoana_joshi(query):
    """
    Toranoana(女子部)で指定のクエリを検索し、最初の結果のURLを返す。
    """
    # クエリをURLエンコード
    encoded_query = urllib.parse.quote(query)
    
    # 検索URLを構築
    search_url = f"https://ec.toranoana.jp/joshi_r/ec/app/catalog/list?searchWord={encoded_query}&_gl=1*12n0h8j*_gcl_au*MTczNDk4NDQxNi4xNzU3ODA2NTQ1"
    
    # ヘッダーを設定（ボット検知回避）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 検索ページを取得
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # HTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 最初の商品リンクを探す（detail.phpを含むhref）
        # Melonbooksの構造を仮定：商品リスト内のaタグでdetail.phpを含むもの
        first_link_elem = soup.find('a', href=re.compile(r'https://ec.toranoana.jp/joshi_r/ec/item/'))
        if first_link_elem and first_link_elem.get('href'):
            href = first_link_elem['href']
            # 相対URLの場合、ベースURLを追加
            if href.startswith('/'):
                full_url = f"https://ec.toranoana.jp/joshi_r/ec/item/{href}"
            else:
                full_url = href
            return full_url
        else:
            return "N/A1"
        
    except requests.RequestException as e:
        return "N/A2"
    except Exception as e:
        return "N/A3"


def get_first_search_url_from_booth(query):
    """
    Boothで指定のクエリを検索し、最初の結果のURLを返す。年齢確認ページが出た場合は「はい」を選択して検索を継続する。
    """
    # クエリをURLエンコード
    encoded_query = urllib.parse.quote(query)

    # Boothの検索URL（adult を含め、在庫有りに絞る）
    search_url = f"https://booth.pm/ja/search/{encoded_query}?adult=include&in_stock=true"

    # ヘッダーを設定（ボット検知回避）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        # 検索ページを取得
        response = session.get(search_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # 年齢確認ページが表示されているか判定する（簡易判定）
        age_keywords = ['年齢確認', '18歳', '18 才', '年齢を確認', 'Are you 18', 'age verification']
        page_text = response.text
        is_age_page = any(k in page_text for k in age_keywords)

        if is_age_page:
            # まずは JS ハンドラ（.js-approve-adult）が存在するか確認。
            # Booth のフロントエンドはクリック時に cookie('adult','t') をセットして location.reload() しているため、
            # ここでも同様に cookie をセットして再取得すれば同様の挙動を得られる。
            if soup.select_one('.js-approve-adult') is not None:
                # ドメイン指定で cookie をセット
                session.cookies.set('adult', 't', domain='booth.pm', path='/')
                try:
                    response = session.get(search_url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                except requests.RequestException:
                    return "N/A"
            else:
                # 年齢確認フォームがある場合は既存のフォーム送信で回避を試みる
                form = None
                for f in soup.find_all('form'):
                    text = ''.join(f.stripped_strings)
                    if any(k in text for k in ['年齢', '18', 'adult', 'age', 'はい', 'yes']):
                        form = f
                        break
                if form is None:
                    # fallback: 最初の form を使う
                    form = soup.find('form')

                if form is not None:
                    action = urllib.parse.urljoin(response.url, form.get('action') or '')

                    # フォームの input を集めて送信データを作成
                    data = {}
                    radios = {}
                    for inp in form.find_all('input'):
                        name = inp.get('name')
                        if not name:
                            continue
                        itype = (inp.get('type') or '').lower()
                        val = inp.get('value', '')

                        if itype == 'radio':
                            radios.setdefault(name, []).append((val, inp))
                        else:
                            data[name] = val

                    for name, opts in radios.items():
                        chosen = None
                        for val, inp in opts:
                            v = (val or '').strip()
                            if re.search(r'^(はい|yes|true|1|18)', v, re.I):
                                chosen = v
                                break
                            iid = inp.get('id')
                            if iid:
                                lbl = form.find('label', attrs={'for': iid})
                                if lbl and 'はい' in ''.join(lbl.stripped_strings):
                                    chosen = v
                                    break
                        if chosen is None and opts:
                            chosen = opts[0][0]
                        if chosen is not None:
                            data[name] = chosen

                    for btn in form.find_all(['input', 'button']):
                        btype = (btn.get('type') or '').lower()
                        bval = (btn.get('value') or '')
                        btext = ''.join(btn.stripped_strings)
                        if re.search(r'^(はい|yes|confirm|adult)', bval, re.I) or 'はい' in btext or 'Yes' in btext:
                            name = btn.get('name')
                            if name:
                                data[name] = bval or btext
                                break

                    try:
                        session.post(action, data=data, timeout=10, headers={'Referer': response.url})
                    except requests.RequestException:
                        pass

                    try:
                        response = session.get(search_url, timeout=10)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'html.parser')
                    except requests.RequestException:
                        return "N/A"

        # 年齢確認通過後または最初から確認がない場合、結果の最初のリンクを取得する
        # data-tracking 属性の a タグ優先、なければ /ja/items/ を含む href を探す
        first_link_elem = soup.find('a', attrs={'data-tracking': 'click_item'}) or soup.find('a', href=re.compile(r'/ja/items/|booth\.pm/.*/items/'))
        if first_link_elem and first_link_elem.get('href'):
            href = first_link_elem['href']
            full_url = urllib.parse.urljoin('https://booth.pm', href)
            return full_url
        else:
            return "N/A"

    except requests.RequestException:
        return "N/A"
    except Exception:
        return "N/A"


def get_first_search_url_from_fanza(query):
    """
    FANZA(DMM)で指定のクエリを検索し、最初の結果のURLを返す。年齢確認ページが出た場合は「はい」を選択して検索を継続する。
    """
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.dmm.co.jp/dc/doujin/-/list/narrow/=/word={encoded_query}/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        response = session.get(search_url, timeout=10, allow_redirects=True)
        response.raise_for_status()

        # If redirected to age_check page or content indicates age check, find the 'はい' link and follow it
        soup = BeautifulSoup(response.text, 'html.parser')
        if '/age_check/' in response.url or any(k in response.text for k in ['年齢', '18歳', 'Age verification']):
            # prefer an anchor with 'はい' or declared=yes
            yes_link = None
            for a in soup.find_all('a', href=True):
                if 'declared=yes' in a['href'] or 'はい' in ''.join(a.stripped_strings):
                    yes_link = a['href']
                    break
            if yes_link:
                yes_link = urllib.parse.urljoin(response.url, yes_link)
                try:
                    session.get(yes_link, timeout=10)
                except requests.RequestException:
                    pass
                # re-fetch the search page (the rurl parameter in the yes link often points back to the listing)
                try:
                    response = session.get(search_url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                except requests.RequestException:
                    return "N/A"

        # Now find the first product link - prefer links under /dc/doujin/ to avoid unrelated '/detail/' help pages
        first_link = None
        for a in soup.find_all('a', href=True):
            href = a['href']
            # convert to absolute
            full_href = urllib.parse.urljoin(response.url, href)
            p = urllib.parse.urlparse(full_href)
            if 'dmm.co.jp' not in (p.netloc or '') and p.netloc != '':
                # skip external domains (help.dmm.co.jp etc.)
                continue
            if p.path.startswith('/dc/doujin/'):
                # prefer detailed product links with 'detail' in path
                if '/detail/' in p.path:
                    first_link = full_href
                    break
                # otherwise keep first /dc/doujin/ as fallback
                if first_link is None:
                    first_link = full_href
        if first_link:
            return first_link
        return "N/A"
    except requests.RequestException:
        return "N/A"
    except Exception:
        return "N/A"


def get_first_search_url_from_alicebooks(query):
    """
    AliceBooks (alice-books.com) で指定のクエリを検索し、最初の結果のURLを返す。
    """
    # クエリをURLエンコード
    encoded_query = urllib.parse.quote(query)
    
    # 検索URLを構築
    search_url = f"https://alice-books.com/item/list/all?keyword={encoded_query}&on_sale=1"
    
    # ヘッダーを設定（ボット検知回避）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 検索ページを取得
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # HTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 最初の商品リンクを探す
        # Alice Books の商品リンク形式: /item/show/XXXX-YY
        first_link_elem = soup.find('a', href=re.compile(r'/item/show/\d+'))
        
        if first_link_elem and first_link_elem.get('href'):
            href = first_link_elem['href']
            # 相対URLの場合、ベースURLを追加
            if href.startswith('/'):
                full_url = f"https://alice-books.com{href}"
            else:
                full_url = href
            return full_url
        else:
            return "N/A"
    
    except requests.RequestException as e:
        return "N/A"
    except Exception as e:
        return "N/A"