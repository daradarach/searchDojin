import sys
import os
import re
from melon import clean_url, extract_product_info as extract_product_info_melon
from tora import extract_product_info as extract_product_info_tora
from google import get_first_search_url_from_booth, get_first_search_url_from_dlsite, get_first_search_url_from_toranoana, get_first_search_url_from_melonbooks, get_first_search_url_from_fanza, get_first_search_url_from_alicebooks
from dlsite import extract_product_info as extract_product_info_dlsite
from booth import extract_product_info as extract_product_info_booth
from fanza import extract_product_info as extract_product_info_fanza
from alicebooks import extract_product_info as extract_product_info_alicebooks

# Prefer python output to use UTF-8 and replace unencodable chars to avoid crashes when capturing output on Windows
os.environ.setdefault('PYTHONIOENCODING', 'utf-8:replace')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def _safe_console_str(s):
    """Return a string that's safe to print to the current console encoding."""
    if s is None:
        return ''
    try:
        enc = sys.stdout.encoding or 'utf-8'
        s.encode(enc)
        return s
    except Exception:
        try:
            return s.encode(enc, errors='replace').decode(enc)
        except Exception:
            return ''.join([c if ord(c) < 128 else '?' for c in s])


def _to_ascii_digits(s):
    """Convert full-width digits to ASCII digits to make regex parsing robust."""
    if not isinstance(s, str):
        return s
    fw = '０１２３４５６７８９'
    ascii_digits = '0123456789'
    trans = str.maketrans(fw, ascii_digits)
    return s.translate(trans)


def _normalize_date_to_ymd(s):
    """Normalize a date-like string to 'YYYY/MM/DD'."""
    if not s:
        return ''
    s2 = _to_ascii_digits(s)
    s2 = s2.strip()

    m = re.search(r"(?P<y>\d{4})\D+?(?P<m>\d{1,2})\D+?(?P<d>\d{1,2})", s2)
    if m:
        y = m.group('y')
        mo = int(m.group('m'))
        d = int(m.group('d'))
        return f"{y}/{mo:02d}/{d:02d}"
    m2 = re.search(r"(?P<y>\d{4})\D+?(?P<m>\d{1,2})", s2)
    if m2:
        y = m2.group('y')
        mo = int(m2.group('m'))
        return f"{y}/{mo:02d}/01"
    m3 = re.search(r"(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})", s2)
    if m3:
        y = m3.group('y')
        mo = int(m3.group('m'))
        d = int(m3.group('d'))
        return f"{y}/{mo:02d}/{d:02d}"
    return s


def _find_booth_url_with_fallback(title, circle, author):
    """Try multiple queries to find a booth URL when a plain title search fails."""
    tried = []
    candidates = [title, f"{title} {circle}" if circle else None, f"{title} {author}" if author else None, circle, author]
    for q in candidates:
        if not q:
            continue
        q = q.strip()
        if not q or q in tried:
            continue
        tried.append(q)
        url = get_first_search_url_from_booth(q)
        if url and isinstance(url, str) and url.startswith('http'):
            return url
    return None


def _normalize_title_for_similarity(title):
    """Normalize a title for robust similarity comparison."""
    if not title:
        return ''
    text = re.sub(r'[^\w\u3040-\u30ff\u4e00-\u9fff]+', '', title).lower()
    return text.strip()


def _title_similarity_score(candidate_title, reference_title):
    """Return a 0..1 similarity score for two titles."""
    if not candidate_title or not reference_title:
        return 1.0
    c = _normalize_title_for_similarity(candidate_title)
    r = _normalize_title_for_similarity(reference_title)
    if not c or not r:
        return 1.0
    if c == r:
        return 1.0
    if c in r or r in c:
        return 1.0
    if len(c) <= 2 or len(r) <= 2:
        return 0.0
    shared = 0
    for ch in set(c):
        if ch in r:
            shared += 1
    return shared / max(len(set(c)), len(set(r)))


def _is_title_similar(candidate_title, reference_title, threshold=0.90):
    """Return True when two titles are sufficiently similar."""
    return _title_similarity_score(candidate_title, reference_title) >= threshold


def _filter_site_urls_by_title_similarity(site_urls, site_infos, reference_title, preserved_site=None):
    """Drop candidate URLs whose extracted title looks unrelated to the reference title."""
    if not reference_title:
        return site_urls
    filtered = {}
    for site_name, url in site_urls.items():
        if not url:
            continue
        if preserved_site and site_name == preserved_site:
            filtered[site_name] = url
            continue
        info = site_infos.get(site_name)
        if not info:
            filtered[site_name] = url
            continue
        candidate_title = info.get('作品名') or ''
        if _is_title_similar(candidate_title, reference_title):
            filtered[site_name] = url
        else:
            filtered[site_name] = ''
    return filtered


def _detect_site_from_url(url):
    """Detect a supported site from a URL for direct-input handling."""
    if not url or not isinstance(url, str):
        return None
    lowered = url.lower()
    if 'melonbooks' in lowered:
        return 'melonbooks'
    if 'toranoana' in lowered:
        return 'toranoana'
    if 'dlsite' in lowered:
        return 'dlsite'
    if 'booth.pm' in lowered or 'booth' in lowered:
        return 'booth'
    if 'alice-books' in lowered:
        return 'alicebooks'
    if 'dmm.co.jp' in lowered or 'fanza' in lowered:
        return 'fanza'
    return None


def _get_direct_url_output_value(site_name, original_url, cleaned_url):
    """Return the value to place in the per-site URL column for a direct URL input."""
    if site_name == 'melonbooks':
        return cleaned_url or original_url
    return original_url


def _build_site_url_candidates(title_q, info, results=None, excluded_site=None):
    """Build a site-url mapping from either search results or fresh title-based searches."""
    site_urls = {'dlsite': '', 'melonbooks': '', 'toranoana': '', 'booth': '', 'fanza': '', 'alicebooks': ''}

    if isinstance(results, dict) and results:
        for key in site_urls:
            site_urls[key] = results.get(key) or ''
        return site_urls

    def set_if_allowed(site_key, value):
        if excluded_site and site_key == excluded_site:
            return
        if value:
            site_urls[site_key] = value

    if not excluded_site or excluded_site != 'dlsite':
        set_if_allowed('dlsite', get_first_search_url_from_dlsite(title_q))
    if not excluded_site or excluded_site != 'melonbooks':
        set_if_allowed('melonbooks', get_first_search_url_from_melonbooks(title_q))
    if not excluded_site or excluded_site != 'toranoana':
        set_if_allowed('toranoana', get_first_search_url_from_toranoana(title_q))
    if not excluded_site or excluded_site != 'booth':
        set_if_allowed('booth', _find_booth_url_with_fallback(title_q, info.get('サークル名'), info.get('作家名')))
    if not excluded_site or excluded_site != 'alicebooks':
        set_if_allowed('alicebooks', get_first_search_url_from_alicebooks(title_q))
    if not excluded_site or excluded_site != 'fanza':
        site_urls['fanza'] = ''
    return site_urls


def _pick_metadata(site_infos, info, pref=None):
    """Pick the best available metadata from a site-info mapping."""
    if pref is None:
        pref = ['melonbooks', 'toranoana', 'alicebooks', 'dlsite', 'fanza', 'booth']

    def pick(field):
        for s in pref:
            si = site_infos.get(s)
            if si and si.get(field):
                return si.get(field)
        return info.get(field)

    return {
        'サークル名': pick('サークル名'),
        '作家名': pick('作家名'),
        '作品名': pick('作品名'),
        '発売日': pick('発売日'),
        'イベント名': pick('イベント名'),
    }


def _fetch_site_info(site_name, url):
    """Given a site identifier and URL, call the corresponding extractor and return its info dict or None."""
    try:
        if not url or not isinstance(url, str) or not url.startswith('http'):
            return None
        if site_name == 'dlsite':
            return extract_product_info_dlsite(url)
        elif site_name == 'melonbooks':
            return extract_product_info_melon(url)
        elif site_name == 'toranoana':
            return extract_product_info_tora(url)
        elif site_name == 'booth':
            return extract_product_info_booth(url)
        elif site_name == 'fanza':
            return extract_product_info_fanza(url)
        elif site_name == 'alicebooks':
            return extract_product_info_alicebooks(url)
        else:
            return None
    except Exception:
        return None


def execute_url(url):
    """Fetch product metadata from a given product URL and return (info_dict, cleaned_url)."""
    cleaned_url = url
    info = None
    if 'melonbooks' in url:
        cleaned_url = clean_url(url)
        info = extract_product_info_melon(cleaned_url)
    elif 'toranoana' in url:
        info = extract_product_info_tora(cleaned_url)
    elif 'dlsite' in url or 'dlsite.com' in url:
        info = extract_product_info_dlsite(cleaned_url)
    elif 'booth' in url or 'booth.pm' in url:
        info = extract_product_info_booth(cleaned_url)
    elif 'alice-books' in url or 'alice-books.com' in url:
        info = extract_product_info_alicebooks(cleaned_url)
    if not info:
        raise ValueError(f"Unsupported or invalid URL: {url}")
    return info, cleaned_url


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print("Usage: python script.py <file_path or URL>", file=sys.stderr)
        sys.exit(1)

    file_path = argv[0]

    if file_path.startswith('http'):
        try:
            info, cleaned = execute_url(file_path)
            detected_site = _detect_site_from_url(file_path)
            title_q = info.get('作品名') or ''
            site_urls = _build_site_url_candidates(title_q, info, results=None, excluded_site=None)
            if detected_site:
                site_urls[detected_site] = _get_direct_url_output_value(detected_site, file_path, cleaned)

            site_infos = {k: _fetch_site_info(k, u) for k, u in site_urls.items() if u}
            site_urls = _filter_site_urls_by_title_similarity(site_urls, site_infos, info.get('作品名'), preserved_site=detected_site)
            filtered_site_infos = {k: site_infos[k] for k in site_urls if site_urls.get(k)}
            picked = _pick_metadata(filtered_site_infos, info)
            circle = picked['サークル名'] or info.get('サークル名') or ''
            author = picked['作家名'] or info.get('作家名') or ''
            title = picked['作品名'] or info.get('作品名') or ''
            release = picked['発売日'] or info.get('発売日') or ''
            event = picked['イベント名'] or info.get('イベント名') or ''
            release_norm = _normalize_date_to_ymd(release)

            dlsiteurl = site_urls.get('dlsite') or ''
            fanza = site_urls.get('fanza') or ''
            boothurl = site_urls.get('booth') or ''
            toraurl = site_urls.get('toranoana') or ''
            melonurl = site_urls.get('melonbooks') or ''
            alicebooksurl = site_urls.get('alicebooks') or ''
            print(f"{_safe_console_str(circle)}\t{_safe_console_str(author)}\t{_safe_console_str(title)}\t{_safe_console_str(release_norm)}\t{_safe_console_str(event)}\t{dlsiteurl}\t{fanza}\t{boothurl}\t{toraurl}\t{melonurl}\t{alicebooksurl}\t{cleaned}")
        except Exception as e:
            print(f"Error processing {_safe_console_str(file_path)}: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    try:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='shift_jis', errors='strict') as f:
                lines = f.readlines()

        for line in lines:
            value = line.strip()
            if not value:
                continue
            detected_site = None
            search_fns = [
                ('melonbooks', get_first_search_url_from_melonbooks),
                ('toranoana', get_first_search_url_from_toranoana),
                ('dlsite', get_first_search_url_from_dlsite),
                ('booth', get_first_search_url_from_booth),
                ('alicebooks', get_first_search_url_from_alicebooks),
            ]
            if value.startswith('http'):
                target_url = value
                detected_site = _detect_site_from_url(value)
                results = {}
                primary_name = detected_site or 'direct'
                primary = value
                found_source = primary_name
                found_list = f"{primary_name}:{value}"
            else:
                results = {}
                for name, fn in search_fns:
                    try:
                        candidate = fn(value)
                    except Exception:
                        candidate = None
                    if candidate and isinstance(candidate, str) and candidate.startswith('http'):
                        results[name] = candidate

                if not results:
                    try:
                        fz = get_first_search_url_from_fanza(value)
                        if fz and isinstance(fz, str) and fz.startswith('http'):
                            results['fanza'] = fz
                    except Exception:
                        pass
                if not results:
                    print(f"Warning: no search result for query: {_safe_console_str(value)}", file=sys.stderr)
                    print(f"\t\t{_safe_console_str(value)}\t\t\t\t")
                    continue
                else:
                    preferred = ['melonbooks', 'toranoana', 'dlsite', 'booth', 'alicebooks']
                    primary = None
                    for p in preferred:
                        if p in results:
                            primary = results[p]
                            primary_name = p
                            break
                    if primary is None:
                        primary_name, primary = next(iter(results.items()))

                    found_list = ', '.join([f"{k}:{v}" for k, v in results.items()])
                    print(f"Found URLs for query: {_safe_console_str(value)} -> {found_list}", file=sys.stderr)

                    target_url = primary
                    found_source = primary_name

            try:
                if 'found_source' in locals() and found_source == 'fanza':
                    try:
                        info = extract_product_info_fanza(target_url)
                        cleaned = target_url
                    except Exception:
                        raise ValueError(f"Unsupported or invalid URL: {target_url}")
                else:
                    info, cleaned = execute_url(target_url)

                title_q = info.get('作品名') or ''
                if detected_site and not results:
                    for name, fn in search_fns:
                        if name == detected_site:
                            continue
                        try:
                            candidate = fn(title_q)
                        except Exception:
                            candidate = None
                        if candidate and isinstance(candidate, str) and candidate.startswith('http'):
                            results[name] = candidate

                site_urls = _build_site_url_candidates(title_q, info, results=(results if results else None), excluded_site=None)
                if detected_site:
                    site_urls[detected_site] = _get_direct_url_output_value(detected_site, target_url, cleaned)

                site_infos = {k: _fetch_site_info(k, u) for k, u in site_urls.items() if u}
                site_urls = _filter_site_urls_by_title_similarity(site_urls, site_infos, info.get('作品名'), preserved_site=detected_site)
                filtered_site_infos = {k: site_infos[k] for k in site_urls if site_urls.get(k)}
                if detected_site:
                    picked = {
                        'サークル名': info.get('サークル名'),
                        '作家名': info.get('作家名'),
                        '作品名': info.get('作品名'),
                        '発売日': info.get('発売日'),
                        'イベント名': info.get('イベント名'),
                    }
                else:
                    picked = _pick_metadata(filtered_site_infos, info)
                circle = picked['サークル名'] or info.get('サークル名') or ''
                author = picked['作家名'] or info.get('作家名') or ''
                title = picked['作品名'] or info.get('作品名') or ''
                release = picked['発売日'] or info.get('発売日') or ''
                event = picked['イベント名'] or info.get('イベント名') or ''
                release_norm = _normalize_date_to_ymd(release)

                dlsiteurl = site_urls.get('dlsite') or ''
                fanza = site_urls.get('fanza') or ''
                boothurl = site_urls.get('booth') or ''
                toraurl = site_urls.get('toranoana') or ''
                melonurl = site_urls.get('melonbooks') or ''
                alicebooksurl = site_urls.get('alicebooks') or ''

                print(f"{_safe_console_str(circle)}\t{_safe_console_str(author)}\t{_safe_console_str(title)}\t{_safe_console_str(release_norm)}\t{_safe_console_str(event)}\t{dlsiteurl}\t{fanza}\t{boothurl}\t{toraurl}\t{melonurl}\t{alicebooksurl}")

            except Exception as e:
                print(f"Error processing {_safe_console_str(target_url)}: {e}", file=sys.stderr)
    except FileNotFoundError:
        print(f"File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
