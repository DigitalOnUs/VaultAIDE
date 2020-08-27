from re import search
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from sys import exit
from logging import warning

class Github:
    def __init__(self):
        self.url = 'https://github.com/hashicorp/vault/releases'

    def simple_get(self, url):
        """
        Attempts to get the content at `url` by making an HTTP GET request.
        If the content-type of response is some kind of HTML/XML, return the
        text content, otherwise return None.
        """
        try:
            with closing(get(url, stream=True)) as resp:
                if self.is_good_response(resp):
                    return resp.content
                else:
                    return None

        except RequestException as e:
            self.log_error('Error during requests to {0} : {1}'.format(url, str(e)))
            return None


    def is_good_response(self, resp):
        """
        Returns True if the response seems to be HTML, False otherwise.
        """
        content_type = resp.headers['Content-Type'].lower()
        return (resp.status_code == 200
                and content_type is not None
                and content_type.find('html') > -1)


    def log_error(self, e):
        """
        It is always a good idea to log errors.
        This function just prints them, but you can
        make it do anything.
        """
        warning(e)

    def get_latest_releases(self):
        response = self.simple_get(self.url)

        if response is None:
            exit()

        html = BeautifulSoup(response, 'html.parser')

        versions = []
        for a in html.select('a'):
            href = a.get('href')
            match = search(r"releases[/]tag[/]v", href)
            if match:
                url = href.split('/')

                m = search(r"beta", url[-1])
                if not m:
                    versions.append(url[-1])
        return versions
