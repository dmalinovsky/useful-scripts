#!/usr/bin/env python
# encoding=utf-8
"""Gets the trial version of the most recent book in LitRes user basket."""

from __future__ import unicode_literals

import ConfigParser
import getpass
import gzip
import os.path
import StringIO
import subprocess
import urllib
import urllib2
import webbrowser
from xml.dom.minidom import parseString


CONFIG = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'litres.ini')
BASKET_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'basket.html')

API_URL = 'http://robot.litres.ru/pages/'
AUTHORIZE_URL = API_URL + 'catalit_authorise/'
CATALOG_URL = API_URL + 'catalit_browser/'
DOWNLOAD_TRIAL_URL = 'http://robot.litres.ru/static/trials/'

AUTHORIZATION_OK_TAG = 'catalit-authorization-ok'
AUTHORIZATION_FAILED_TAG = 'catalit-authorization-failed'
BOOK_TAG = 'fb2-book'
BOOK_TITLE_TAG = 'book-title'
BOOK_AUTHOR_TAG = 'author'

DOWNLOAD_DIR = os.path.expanduser('~/Downloads')


class LitresAPI(object):
    def __init__(self):
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(CONFIG)
        try:
            self.sid = self.config.get('DEFAULT', 'sid')
        except ConfigParser.NoOptionError:
            self.sid = ''

    def login(self):
        sid_authorized = False
        if self.sid:
            try:
                self.authorize_sid()
                sid_authorized = True
            except ValueError:
                pass
        if sid_authorized:
            return

        self.sid = self.authorize_login_password()
        self._save_config()

    def authorize_sid(self):
        self._read_xml(AUTHORIZE_URL, {}, AUTHORIZATION_OK_TAG)

    def authorize_login_password(self):
        login = raw_input('Enter login: ')
        password = getpass.getpass('Enter password: ')

        reply = self._read_xml(AUTHORIZE_URL, {'login': login, 'pwd': password},
                AUTHORIZATION_OK_TAG)
        return reply[0].getAttribute('sid')

    def get_basket_items(self):
        reply = self._read_xml(CATALOG_URL, {'basket': 1}, BOOK_TAG)
        return reply

    def get_book_title(self, book):
        return book.getElementsByTagName(BOOK_TITLE_TAG)[0].childNodes[0].data

    def get_book_author(self, book):
        author = book.getElementsByTagName(BOOK_AUTHOR_TAG)[0]
        author.normalize()
        name = '%s %s' % (
            author.getElementsByTagName('first-name')[0].childNodes[0].data,
            author.getElementsByTagName('last-name')[0].childNodes[0].data,
        )
        return name

    def download_trial(self, book):
        book_id = '%08d' % int(book.getAttribute('hub_id'))
        url = '%s%s/%s/%s/%s.epub' % (DOWNLOAD_TRIAL_URL, book_id[0:2],
                book_id[2:4], book_id[4:6], book_id)
        subprocess.Popen(['wget', '-P', DOWNLOAD_DIR, url])
        print 'Downloading "%s"' % self.get_book_title(book)

    def get_book_url(self, book):
        book_id = '%08d' % int(book.getAttribute('hub_id'))
        url = '%s%s/%s/%s/%s' % (DOWNLOAD_TRIAL_URL, book_id[0:2],
                book_id[2:4], book_id[4:6], book_id)
        return url

    def generate_html(self, books):
        html = '<html><head><meta charset="utf-8"></head><body>'
        for book in books:
            url = self.get_book_url(book)
            title = self.get_book_title(book)
            author = self.get_book_author(book)
            html += """
                <p>%s. «%s» <a href="%s.fb2">FB2</a> | <a href="%s.epub">ePub</a></p>
            """ % (author, title, url, url)

        html += '</body></html>'
        with open(BASKET_FILE, 'wb') as fp:
            fp.write(html.encode('utf8'))

        webbrowser.open_new_tab('file://%s' % BASKET_FILE)

    def _read_xml(self, url, data, desired_tag):
        """
        Return fetched XML data for the `desired_tag`.  Return False on error.
        Raises an exception after authorization failure.
        """
        if self.sid:
            data['sid'] = self.sid
        request = urllib2.Request(url)
        request.add_header('Accept-Encoding', 'gzip')
        response = urllib2.urlopen(request, urllib.urlencode(data))
        xml = response.read()

        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO.StringIO(xml)
            f = gzip.GzipFile(fileobj=buf)
            xml = f.read()

        dom = parseString(xml)
        if dom.firstChild.tagName == AUTHORIZATION_FAILED_TAG:
            self.sid = ''
            self._save_config()
            raise ValueError('Authorization failed, consider re-login')

        return dom.getElementsByTagName(desired_tag)

    def _load_config(self):
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(CONFIG)

        try:
            self.sid = self.config.get('DEFAULT', 'sid')
        except ConfigParser.NoOptionError:
            self.sid = ''

    def _save_config(self):
        self.config.set('DEFAULT', 'sid', self.sid)
        with open(CONFIG, 'w') as cfg_file:
            self.config.write(cfg_file)


if __name__ == '__main__':
    api = LitresAPI()
    api.login()
    basket = api.get_basket_items()
    api.generate_html(basket)
