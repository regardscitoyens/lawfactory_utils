import re
import os
import time
import sys
from urllib.parse import urljoin, parse_qs, urlparse, urlunparse

from bs4 import BeautifulSoup

import requests
import requests_cache
from requests import ConnectionError, HTTPError


def cache_file():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requests_cache')


def enable_requests_cache():
    requests_cache.install_cache(cache_file())


def download(url, retry=5):
    try:
        resp = requests.get(url)
        # if 500 <= resp.status_code < 600:
        #    raise HTTPError('%s Server Error for url: %s' % (resp.status_code, url), response=resp)
        return resp
    except (ConnectionError, HTTPError) as e:
        if retry:
            time.sleep(1)
            return download(url, retry-1)
        raise e


def pre_clean_url(url):
    if url.startswith('www'):
        url = "http://" + url
    if url.startswith('/leg/http'):
        url = url[5:]
    return url


def get_redirected_url(url):
    """Returns redirected URL"""
    return download(url).url


def find_stable_link_for_CC_decision(url):
    resp = download(url)
    soup = BeautifulSoup(resp.text, 'lxml')

    breadcrumb = soup.select('#navpath a')
    if breadcrumb:
        return urljoin(url, breadcrumb[-1].attrs['href'])
    else:
        # TODO: use log_error
        print('[WARNING] INVALID CC URL - ', url, file=sys.stderr)
        return url


re_clean_ending_digits = re.compile(r"(\d+\.asp)[\dl]+$")
def clean_url(url):
    url = url.strip()

    # fix urls like 'pjl09-518.htmlhttp://www.assemblee-nationale.fr/13/ta/ta051`8.asp'
    if url.find('https://') > 0:
        url = 'https://' + url.split('https://')[1]
    if url.find('http://') > 0:
        url = 'http://' + url.split('http://')[1]

    # fix url like http://www.senat.fr/dossier-legislatif/www.conseil-constitutionnel.fr/decision/2012/2012646dc.htm
    if 'www.conseil-' in url:
        url = 'http://www.conseil-' + url.split('www.conseil-')[1]
        url = find_stable_link_for_CC_decision(url)

    scheme, netloc, path, params, query, fragment = urlparse(url)

    path = path.replace('//', '/')

    if 'legifrance.gouv.fr' in url:
        params = ''
        url_jo_params = parse_qs(query)

        if 'WAspad' in path:
            return clean_url(get_redirected_url(url))

        if 'cidTexte' in url_jo_params:
            query = 'cidTexte=' + url_jo_params['cidTexte'][0]

        if netloc == 'legifrance.gouv.fr':
            netloc = 'www.legifrance.gouv.fr'
        if 'jo_pdf.do' in path and 'id' in url_jo_params:
            path = 'affichTexte.do'
            query = 'cidTexte=' + url_jo_params['id'][0]

        # ensure to link initial version of the text and not furtherly modified ones
        if query.startswith('cidTexte'):
            query += '&categorieLien=id'

        path = path.replace('./affichTexte.do', 'affichTexte.do')

    if 'senat.fr' in netloc:
        path = path.replace('leg/../', '/')
        path = path.replace('dossierleg/', 'dossier-legislatif/')

        # normalize dosleg url by removing extra url parameters
        if 'dossier-legislatif/' in path:
            query = ''
            fragment = ''

    if netloc == 'webdim':
        netloc = 'www.assemblee-nationale.fr'

    # force https
    if 'assemblee-nationale.fr' not in netloc and 'conseil-constitutionnel.fr' not in netloc:
        scheme = 'https'

    # url like http://www.assemblee-nationale.fr/13/projets/pl2727.asp2727
    if 'assemblee-nationale.fr' in url:
        path = re_clean_ending_digits.sub(r"\1", path)

    if 'xtor' in fragment:
        fragment = ''

    return urlunparse((scheme, netloc, path, params, query, fragment))
