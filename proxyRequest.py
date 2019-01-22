from proxy_custom_requests import ProxyRequests
from bs4 import BeautifulSoup
import re, os, csv, math
import threading
import pandas as pd
import uuid
import datetime

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

    def getPrice(self, soup):
        span = soup.find('span', id='priceblock_ourprice')
        price = span.text.lstrip().rstrip() if span else ""
        if price == "":
            div = soup.find('div', id='olp-upd-new')
            div = soup.find('div', id='olp-upd-new-used') if div is None else div
            priceText = div.text.lstrip().rstrip() if div else ""
            price = priceText.split(" ")[len(priceText.split(" "))-1]
        if price == "":
            priceSpan = soup.find('span', {'class': 'a-color-price'})
            if priceSpan:
                price = priceSpan.text.lstrip().rstrip()
        return price

    def getsize(self, soup):
        try:
            sizeSpan = soup.find(id='shelf-label-size_name').find('span',{'class':'shelf-label-variant-name'})
            size = sizeSpan.text.rstrip().lstrip() if sizeSpan else ""
        except:
            size=""
        if size == "":
            div = soup.find('div', {'class' :  'disclaim'})
            sizeText = div.text.lstrip().rstrip().split("|")[0] if div else ""
            size = sizeText.split(":")[1] if sizeText != "" and "size" in sizeText.lower() else ""
        if size == "" :
            sizeSpan = soup.find('li',{'class':'swatchSelect'})
            size = sizeSpan.find('span', {'class' : 'a-size-base'}).text.rstrip().lstrip() if sizeSpan and sizeSpan.find('span', {'class' : 'a-size-base'}) else ""
        if size=="":
            table = soup.find(id='productDetails_techSpec_section_1')
            trs = table.find_all('tr') if table else []
            for tr in trs:
                header = tr.find('th').text.lstrip().rstrip() if tr.find('th') else ''
                if header=='Size':
                    size = tr.find('td').text if tr.find('td') else ''
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

    def export(self, imasin, asin, title, size ,price, seller):
        header = ['Imported ASIN', 'ASIN', 'Title', 'Size Variation', 'Price','Seller'] if not os.path.exists(self.csv) else None
        row = [imasin, asin, title, size, price, seller]
        file = open(self.csv, 'a', newline='')
        with file:
            writer = csv.writer(file)
            writer.writerow(header) if header else None
            writer.writerow(row)
        file.close()

    def Unit(self, imasin, asin, first=False):
        self.request.url = "https://www.amazon.com/gp/product/%s?th=1&psc=1" %(asin)
        print(self.request.url)
        self.request.get()

        soup =BeautifulSoup(re.findall('<html(.*?)</html>', self.request.raw_content, re.DOTALL)[0], "lxml")
        productTitle = soup.find(id="productTitle").text.lstrip().rstrip()
        asinlist = []   #Asin list
        if first:
            sizesDiv = soup.find(id='native_dropdown_selected_size_name')
            if sizesDiv:
                asinlist = self.getListfromDropdown(sizesDiv)
            else:
                sizesDiv = soup.find(id='shelfSwatchSection-size_name')
                if sizesDiv:
                    asinlist = self.getListfromEle(sizesDiv)
                else:
                    div = soup.find(id='variation_size_name')
                    sizesDiv = div.find('ul') if div else None
                    if sizesDiv:
                        asinlist = self.getListfromEle(sizesDiv)
                    else:
                        div = soup.find(id='variation_color_name')
                        sizesDiv = div.find('ul') if div else None
                        if sizesDiv:
                            asinlist = self.getListfromEle(sizesDiv)
        """ get size data """
        size = self.getsize(soup)
        """ get price data """
        price = self.getPrice(soup)
        self.export(imasin, asin, productTitle, size, price, "seller")
        return [asin] + asinlist

    def process(self):
        self.readExcel()
        for imasin in self.ASINs:
            asinList = self.Unit(imasin, imasin, True)
            for asin in asinList[1:]:
                self.Unit(imasin, asin)

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