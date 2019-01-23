from proxy_custom_requests import ProxyRequests
from bs4 import BeautifulSoup
import re, os, csv, math
import pandas as pd

class ScrapingUnit():

    def __init__(self, filename, csvname):
        self.url = "https://www.amazon.com"
        self.request = ProxyRequests(self.url)
        self.ASINs = []
        self.excel = filename
        self.csv = csvname

    def readExcel(self):
        lists = []
        data = pd.read_excel(self.excel)
        for key in data.values:
            lists.append(key[0])
        self.ASINs = lists

    def getPrice_Seller(self, soup):
        divs   = soup.find_all('div', {'class' : 'a-row a-spacing-mini olpOffer'})
        price  = ''
        seller = 'amazon.com'
        if divs:
            for dv in divs:
                div = dv
                break
            pricediv = div.find('span', {'class' : 'a-size-large a-color-price olpOfferPrice a-text-bold'})
            price = pricediv.text.lstrip().rstrip() if pricediv else ''
            sellerdiv = div.find('div',{'class' : 'a-column a-span2 olpSellerColumn'})
            seller = sellerdiv.find('a').text.lstrip().rstrip() if sellerdiv and sellerdiv.find('a') else 'amazon.com'
        seller = seller.lstrip().rstrip()
        seller = 'amazon.com' if seller == '' else seller
        return price, seller

    def getsize(self, soup):
        size = ""
        sizeDivs = soup.find_all('div', {'class': 'a-section a-spacing-micro'})
        if sizeDivs:
            for div in sizeDivs:
                if 'Size:' in div.text:
                    size = div.text.replace('Size:','')
        return size.lstrip().rstrip()

    def getListfromDropdown(self, soup):
        list = []
        options = soup.find_all('option', {'class' : 'dropdownAvailable'})
        for opt in options:
            value = opt['value'].lstrip().rstrip() if opt['value'] !='-1' else ''
            list.append(value.split(',')[1])  if value!='' else None
        return list

    def getListfromEle(self, soup):
        list = []
        for div in soup.findChildren():
            try:
                asinurl = div['data-dp-url'].lstrip().rstrip()
                list.append(asinurl.split("/")[2]) if asinurl != "" else None
            except:
                pass
        return list

    # .encode('utf-8')
    def export(self, imasin, asin, title, size ,price, seller):
        header = ['Imported ASIN', 'ASIN', 'Title', 'Size Variation', 'Price','Seller'] if not os.path.exists(self.csv) else None
        row = [imasin, asin, title, size, price, seller]
        file = open(self.csv, 'a')
        with file:
            writer = csv.writer(file)
            writer.writerow(header) if header else None
            writer.writerow(row)
        file.close()

    def getAsinList(self, imasin):
        self.request.url = "https://www.amazon.com/gp/product/%s?th=1" % (imasin)
        print(self.request.url)
        self.request.get()
        soup = BeautifulSoup(re.findall('<html(.*?)</html>', self.request.raw_content, re.DOTALL)[0], "lxml")
        asinlist = [imasin]
        """ First case """ #https://www.amazon.com/gp/product/B01D8F5NDM?th=1
        form = soup.find(id='twisterContainer')
        if form:
            for div in form.find_all('div'):
                try:
                    datadpurl = div['data-dp-url'] if div['data-dp-url'] else None
                    asinlist.append(datadpurl.split('/')[2].lstrip().rstrip()) if datadpurl else None
                except:
                    continue

            for div in form.find_all('li'):
                try:
                    datadpurl = div['data-dp-url'] if div['data-dp-url'] else None
                    asinlist.append(datadpurl.split('/')[2].lstrip().rstrip()) if datadpurl else None
                except:
                    continue

            for option in form.find_all('option', {'class' : 'dropdownAvailable'}):
                try:
                    value = option['value'].lstrip().rstrip() if option['value'] != '-1' else ''
                    list.append(value.split(',')[1]) if value != '' else None
                except:
                    pass
            print asinlist
        return asinlist

    def Unit(self, imasin, asin):
        self.request.url = "https://www.amazon.com/gp/offer-listing/%s" %(asin)
        print(self.request.url)
        self.request.get()

        if self.request.raw_content == '':
            self.export(imasin, asin, 'Sorry! Something went wrong!', '', '', '')
            return

        soup =BeautifulSoup(re.findall('<html(.*?)</html>', self.request.raw_content, re.DOTALL)[0], "lxml")
        try:
            productTitle = soup.find('h1',{'class': "a-size-large a-spacing-none"}).text.encode('utf-8').lstrip().rstrip()
        except:
            productTitle = ""

        """ get size data """
        size = self.getsize(soup).encode('utf-8')
        print(size)
        """ get price data """
        price, seller = self.getPrice_Seller(soup)
        price = price.encode('utf-8')
        seller = seller.encode('utf-8')

        print(price + ":" + seller)
        self.export(imasin, asin, productTitle, size, price, seller)

    def process(self):
        self.readExcel()
        for imasin in self.ASINs:
            imasin = imasin.encode('utf-8')
            asinList = self.getAsinList(imasin)
            for asin in asinList:
                self.Unit(imasin, asin.encode('utf-8'))

    # devide tagets to multi threads
    def getRangesByThreads(self, threads, start, end):
        interval = math.ceil((end - start) / threads)
        toReturn = []
        current = start
        while (current < end):
            endRow = current + interval if (current + interval < end) else end
            toReturn.append([current, endRow])
            current += interval
        return toReturn