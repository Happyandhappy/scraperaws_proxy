import requests
import re
from bs4 import BeautifulSoup
from lxml.html import fromstring

class ProxyRequests:
    def __init__(self, url):
        self.sockets = []
        self.url = url
        self.request = ''
        self.proxy_used, self.raw_content = '', ''
        self.status_code, self.try_count = 0, 100
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"}
        self.__acquire_sockets()
        self.current_socket = ''

    # get a list of sockets from sslproxies.org
    def __acquire_sockets(self):
        response = requests.get('https://www.us-proxy.org/')
        parser = fromstring(response.text)
        for i in parser.xpath('//tbody/tr'):
            if i.xpath('.//td[7][contains(text(),"yes")]'):
                proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
                self.sockets.append(proxy)
        self.try_count = len(self.sockets)

    def __try_count_succeeded(self):
        message = "Unable to make proxied request. "
        message += "Please check the validity of your URL."
        print(message)

    def __set_request_data(self, req, socket):
        self.request = req.text
        self.raw_content = req.text
        self.proxy_used = socket

    # recursively try proxy sockets until successful GET
    def get(self):
        self.raw_content = ''
        while len(self.sockets) > 0 and self.try_count > 0:
            if len(self.sockets) < 10:
                self.__acquire_sockets()
            if self.current_socket == '':
                self.current_socket = self.sockets.pop(0)

            proxies = {
                "http": "http://" + self.current_socket,
                "https": "https://" + self.current_socket
            }
            try:
                request = requests.get(
                    self.url,
                    timeout=5.0,
                    proxies=proxies,
                    headers=self.headers
                )
                soup = BeautifulSoup(request.text, "html.parser")
                if soup.find('title') == None or soup.find('title').text=='Amazon.com Page Not Found':
                    break

                if soup.find('title').text == 'Robot Check' or soup.find('title').text == 'Sorry! Something went wrong!':
                    self.current_socket = self.sockets.pop(0)
                    self.try_count -= 1
                else:
                    self.__set_request_data(request, self.current_socket)
                    print(self.current_socket)
                    break
            except:
                self.current_socket = self.sockets.pop(0)
                self.try_count -= 1

    def get_status_code(self):
        return self.status_code

    def get_proxy_used(self):
        return str(self.proxy_used)

    def get_raw(self):
        return self.raw_content

    def __str__(self):
        return str(self.request)
