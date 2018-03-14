import re
import os
import time
import sys
import json
import hashlib
from urllib.parse import urljoin, parse_qs, urlparse, urlunparse

from bs4 import BeautifulSoup

import requests
from requests import ConnectionError, HTTPError


def cache_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requests_cache')


CACHE_ENABLED = False
def enable_requests_cache():
    global CACHE_ENABLED
    CACHE_ENABLED = True


class FakeRequestsResponse:
    def __init__(self, text, status_code, url, encoding='utf-8'):
        self.text = text
        self.status_code = status_code
        self._encoding = encoding
        self.url = url

    def json(self):
        return json.loads(self.text)

    def __setattr__(self, attr, value):
        if attr == 'encoding':
            if self._encoding == value:
                return
            self.text = self.text.encode(self._encoding).decode(value)
            self._encoding = value
            return
        return super().__setattr__(attr, value)


def download(url, retry=5):
    try:
        if CACHE_ENABLED:
            file = os.path.join(cache_directory(), hashlib.sha224(url.encode('utf-8')).hexdigest())
            if os.path.exists(file):
                resp = json.load(open(file))
                return FakeRequestsResponse(**resp)

        resp = requests.get(url)
        if 500 <= resp.status_code < 600:
            raise HTTPError('%s Server Error for url: %s' % (resp.status_code, url), response=resp)

        if CACHE_ENABLED:
            if not os.path.exists(cache_directory()):
                os.makedirs(cache_directory())
            json.dump({
                'status_code': resp.status_code,
                'text': resp.text,
                'url': resp.url,
                'encoding': resp.encoding,
            }, open(file, 'w'))
        return resp
    except (ConnectionError, HTTPError) as e:
        if retry:
            time.sleep(1)
            return download(url, retry=retry-1)
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
    if url == 'http://www.conseil-constitutionnel.fr/decision.50309.html':
        return 'http://www.conseil-constitutionnel.fr/conseil-constitutionnel/francais/les-decisions/acces-par-date/decisions-depuis-1959/2010/2010-615-dc/decision-n-2010-615-dc-du-9-novembre-2010.50419.html'
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
            redirected_url = get_redirected_url(url)
            if url != redirected_url:
                return clean_url(redirected_url)

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
