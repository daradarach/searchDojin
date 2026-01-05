import sys
import os
import re
from melon import clean_url, extract_product_info as extract_product_info_melon
from tora import extract_product_info as extract_product_info_tora
from google import get_first_search_url_from_booth, get_first_search_url_from_dlsite, get_first_search_url_from_toranoana, get_first_search_url_from_melonbooks, get_first_search_url_from_fanza
from dlsite import extract_product_info as extract_product_info_dlsite
from booth import extract_product_info as extract_product_info_booth
from fanza import extract_product_info as extract_product_info_fanza

# Prefer python output to use UTF-8 and replace unencodable chars to avoid crashes when capturing output on Windows
os.environ.setdefault('PYTHONIOENCODING', 'utf-8:replace')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    # reconfigure may not be available or may fail in some environments; fallback to safe printing below
    pass


def _safe_console_str(s):
    """Return a string that's safe to print to the current console encoding.

    - If s is None, returns '(なし)'.
    - Tries to encode with sys.stdout.encoding; on failure replaces unencodable chars.
    """
    if s is None:
        return '(なし)'
    try:
        enc = sys.stdout.encoding or 'utf-8'
        # if this succeeds, string is printable as-is
        s.encode(enc)
        return s
    except Exception:
        try:
            return s.encode(enc, errors='replace').decode(enc)
        except Exception:
            # very last resort: replace non-ascii with '?'
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
    """Normalize a date-like string to 'YYYY/MM/DD'.

    - If only year/month present, day defaults to '01'.
    - If unable to parse, returns original string.
    """
    if not s:
        return ''
    s2 = _to_ascii_digits(s)
    s2 = s2.strip()

    # Common patterns: 2025年10月19日 | 2025-10-19 | 2025/10/19 | 2025.10.19
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
    # fallback: try ISO-like 'YYYY-MM-DD'
    m3 = re.search(r"(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})", s2)
    if m3:
        y = m3.group('y')
        mo = int(m3.group('m'))
        d = int(m3.group('d'))
        return f"{y}/{mo:02d}/{d:02d}"
    # could not parse -> return original
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
    return "N/A"


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
        else:
            return None
    except Exception:
        return None


def execute_url(url):
    """Fetch product metadata from a given product URL and return (info_dict, cleaned_url).

    This no longer prints; callers should handle printing and cross-site aggregation.
    """
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
    # Defensive: if info is not set, it means the URL was unsupported or invalid
    if not info:
        raise ValueError(f"Unsupported or invalid URL: {url}")
    return info, cleaned_url


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path or URL>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]

    if 'https://' in file_path:
        # 直接URLが渡された場合
        try:
            info, cleaned = execute_url(file_path)
            # Build search URLs for related sites based on extracted title
            title_q = info.get('作品名') or ''
            site_urls = {
                'dlsite': get_first_search_url_from_dlsite(title_q),
                'melonbooks': get_first_search_url_from_melonbooks(title_q),
                'toranoana': get_first_search_url_from_toranoana(title_q),
                'booth': _find_booth_url_with_fallback(title_q, info.get('サークル名'), info.get('作家名')),
                'fanza': get_first_search_url_from_fanza(title_q)
            }

            # Fetch metadata from available sites
            site_infos = {k: _fetch_site_info(k, u) for k, u in site_urls.items()}

            # Priority for metadata: melonbooks > toranoana > dlsite = fanza > booth
            pref = ['melonbooks', 'toranoana', 'dlsite', 'fanza', 'booth']
            def pick(field):
                for s in pref:
                    si = site_infos.get(s)
                    if si and si.get(field):
                        return si.get(field)
                # fallback to primary info
                return info.get(field)

            circle = pick('サークル名')
            author = pick('作家名')
            title = pick('作品名')
            release = pick('発売日')
            event = pick('イベント名')

            # Normalize release date to YYYY/MM/DD when possible
            release_norm = _normalize_date_to_ymd(release)

            dlsiteurl = site_urls.get('dlsite') or 'N/A'
            fanza = ''
            boothurl = site_urls.get('booth') or 'N/A'
            toraurl = site_urls.get('toranoana') or 'N/A'
            melonurl = site_urls.get('melonbooks') or 'N/A'

            # Print with safe encoding
            print(f"{_safe_console_str(circle)}\t{_safe_console_str(author)}\t{_safe_console_str(title)}\t{_safe_console_str(release_norm)}\t{_safe_console_str(event)}\t{dlsiteurl}\t{fanza}\t{boothurl}\t{toraurl}\t{melonurl}\t{cleaned}")

        except Exception as e:
            print(f"Error processing {_safe_console_str(file_path)}: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                value = line.strip()
                if not value:
                    continue
                # If the line looks like a URL, process it directly
                if value.startswith('http'):
                    target_url = value
                else:
                    # Treat as a search query (fallback): try multiple search helpers and collect all candidate URLs
                    search_fns = [
                        ('melonbooks', get_first_search_url_from_melonbooks),
                        ('toranoana', get_first_search_url_from_toranoana),
                        ('dlsite', get_first_search_url_from_dlsite),
                        ('booth', get_first_search_url_from_booth),
                    ]
                    results = {}
                    for name, fn in search_fns:
                        try:
                            candidate = fn(value)
                        except Exception:
                            candidate = None
                        if candidate and isinstance(candidate, str) and candidate.startswith('http'):
                            results[name] = candidate

                    # If no candidate links found yet, try FANZA as a last resort before giving up
                    if not results:
                        try:
                            fz = get_first_search_url_from_fanza(value)
                            if fz and isinstance(fz, str) and fz.startswith('http'):
                                results['fanza'] = fz
                        except Exception:
                            pass
                    if not results:
                        print(f"Warning: no search result for query: {_safe_console_str(value)}", file=sys.stderr)
                        # エラー時も空行を出力する
                        print(f"\t\t{_safe_console_str(value)}\t\t\t\t\t{None}")
                        continue
                    else:
                        # Prefer a primary source for extraction: dlsite > booth > melonbooks > toranoana
                        preferred = ['dlsite', 'booth', 'melonbooks', 'toranoana']
                        primary = None
                        for p in preferred:
                            if p in results:
                                primary = results[p]
                                primary_name = p
                                break
                        # Ensure we also record fanza if present in results
                        if 'fanza' in results:
                            # already present
                            pass
                        else:
                            # try to populate fanza as well using query
                            try:
                                fz = get_first_search_url_from_fanza(value)
                                if fz and isinstance(fz, str) and fz.startswith('http'):
                                    results['fanza'] = fz
                            except Exception:
                                pass
                        # fallback to any found
                        if primary is None:
                            primary_name, primary = next(iter(results.items()))

                        # Log all found candidate URLs
                        found_list = ', '.join([f"{k}:{v}" for k, v in results.items()])
                        print(f"Found URLs for query: {_safe_console_str(value)} -> {found_list}", file=sys.stderr)

                        target_url = primary
                        found_source = primary_name
                try:
                    # If the chosen primary source is FANZA, use the dedicated extractor
                    if 'found_source' in locals() and found_source == 'fanza':
                        try:
                            info = extract_product_info_fanza(target_url)
                            cleaned = target_url
                        except Exception:
                            raise ValueError(f"Unsupported or invalid URL: {target_url}")
                    else:
                        info, cleaned = execute_url(target_url)

                    # Build site_urls mapping: prefer previously discovered `results` (if present), otherwise search by title
                    title_q = info.get('作品名') or ''
                    site_urls = {}
                    # If we started from a raw query and found some candidate URLs, only use those sites' URLs.
                    # Do NOT try to re-query other sites based on the title (this avoids spurious matches).
                    if 'results' in locals() and isinstance(results, dict) and results:
                        site_urls['dlsite'] = results.get('dlsite')
                        site_urls['melonbooks'] = results.get('melonbooks')
                        site_urls['toranoana'] = results.get('toranoana')
                        site_urls['booth'] = results.get('booth')
                        site_urls['fanza'] = results.get('fanza')
                    else:
                        # No initial search results; perform fresh site searches by title
                        site_urls['dlsite'] = get_first_search_url_from_dlsite(title_q)
                        site_urls['melonbooks'] = get_first_search_url_from_melonbooks(title_q)
                        site_urls['toranoana'] = get_first_search_url_from_toranoana(title_q)
                        site_urls['booth'] = _find_booth_url_with_fallback(title_q, info.get('サークル名'), info.get('作家名'))
                        # Ensure FANZA slot exists even if empty
                        site_urls['fanza'] = None

                    # Fetch metadata from each available site
                    site_infos = {k: _fetch_site_info(k, u) for k, u in site_urls.items()}

                    # Priority for metadata: melonbooks > toranoana > dlsite = fanza > booth
                    pref = ['melonbooks', 'toranoana', 'dlsite', 'fanza', 'booth']
                    def pick(field):
                        for s in pref:
                            si = site_infos.get(s)
                            if si and si.get(field):
                                return si.get(field)
                        return info.get(field)

                    circle = pick('サークル名')
                    author = pick('作家名')
                    title = pick('作品名')
                    release = pick('発売日')
                    event = pick('イベント名')

                    # Normalize release date to YYYY/MM/DD when possible
                    release_norm = _normalize_date_to_ymd(release)

                    dlsiteurl = site_urls.get('dlsite') or 'N/A'
                    fanza = site_urls.get('fanza') or ''
                    boothurl = site_urls.get('booth') or 'N/A'
                    toraurl = site_urls.get('toranoana') or 'N/A'
                    melonurl = site_urls.get('melonbooks') or 'N/A'

                    print(f"{_safe_console_str(circle)}\t{_safe_console_str(author)}\t{_safe_console_str(title)}\t{_safe_console_str(release_norm)}\t{_safe_console_str(event)}\t{dlsiteurl}\t{fanza}\t{boothurl}\t{toraurl}\t{melonurl}")

                except Exception as e:
                    # Use safe string formatting for URLs or error messages that may contain unicode
                    print(f"Error processing {_safe_console_str(target_url)}: {e}", file=sys.stderr)
    except FileNotFoundError:
        print(f"File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)