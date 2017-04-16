# coding:utf-8

import scrapy
from bs4 import BeautifulSoup
import os, urllib, zlib, urllib2
from WorkPool import *

top = 'http://www.xeall.com'
base = top + '/shenshi'


class Comics(scrapy.Spider):
    name = "comics"

    def __init__(self):
        self.workPool = WorkPool(10)

    def start_requests(self):
        urls = [base]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')
        listcon_tag = soup.find('ul', class_='listcon')
        com_a_list = listcon_tag.find_all('a', attrs={'href': True})

        comics_url_list = []
        for tag_a in com_a_list:
            url = base + tag_a['href']
            comics_url_list.append(url)

        page_tag = soup.find('ul', class_='pagelist')
        page_a_list = page_tag.find_all('a', attrs={'href': True})

        select_tag = soup.find('select', attrs={'name': 'sldd'})
        option_list = select_tag.find_all('option')

        last_option = option_list[-1]
        current_option = select_tag.find('option', attrs={'selected': True})

        is_last = (last_option.string == current_option.string)

        if not is_last:
            next_page = base + '/' + page_a_list[-2]['href']
            if next_page is not None:
                print '\n--------- parse next page ---------'
                yield scrapy.Request(next_page, callback=self.comics_cover_parse)

    def comics_cover_parse(self, response):
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        ul_tag = soup.find('ul', class_='listcon')

        li_tag = ul_tag.find_all('li')

        for li_a_tag in li_tag:
            a_tag = li_a_tag.find('a', attrs={'href': True})
            target_url = top + a_tag['href']
            yield scrapy.Request(target_url, callback=self.comics_parse)

    def comics_parse(self, response):
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        li_tag = soup.find('li', id='imgshow')
        img_tag = li_tag.find('img')
        img_url = img_tag['src']
        title = img_tag['alt']

        page_list_tag = soup.find('ul', class_='pagelist')
        current_li = page_list_tag.find('li', class_='thisclass')
        page_num = current_li.a.string

        self.workPool.add_task(self.save_img,page_num,title,img_url)

        a_tag_list = page_list_tag.find_all('a')
        next_page = a_tag_list[-1]['href']
        if next_page == '#':
            self.log('parse comics:' + title + 'finished.')
        else:
            next_page = base + '/' + next_page
            yield scrapy.Request(next_page, callback=self.comics_parse)

    def save_img(self, img_mun, title, img_url):
        self.log('saving pic: ' + img_url)
        document = './comics'

        comics_path = document + '/' + title
        exists = os.path.exists(comics_path)
        if not exists:
            self.log('create document: ' + title)
            os.makedirs(comics_path)

        pic_name = comics_path + '/' + img_mun + '.jpg'
        exists = os.path.exists(pic_name)

        if exists:
            self.log('pic exists: ' + pic_name)
            return

        try:
            # 请求返回到的数据
            data = self.readData(img_url)

            # 若返回数据为压缩数据需要先进行解压
            # if response.info().get('Content-Encoding') == 'gzip':
            #     data = zlib.decompress(data, 16 + zlib.MAX_WBITS)

            # 图片保存到本地
            fp = open(pic_name, "wb")
            fp.write(data)
            fp.close

            self.log('save image finished:' + pic_name)

        except Exception as e:
            print e.message
            self.log('save image error.')
            self.log(e)

    def openUrl(self, url):
        if url.strip():
            user_agent = 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
            header = {'User-Agent': user_agent}

            try:
                req = urllib2.Request(url, headers=header)
                res = urllib2.urlopen(req)
                return res
            except Exception, e:
                print u'error in %s' % (url)

    def readData(self, url):
        response = self.openUrl(url)

        if response:
            try:
                data = response.read()
                if response.info().get('Content-Encoding') == 'gzip':
                    data = zlib.decompress(data, 16 + zlib.MAX_WBITS)
                return data
            except Exception, e:
                self.log(e)
