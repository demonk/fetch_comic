# coding:utf-8

import scrapy
from bs4 import BeautifulSoup
import urllib2
import os
from WorkPool import *


class Boruto(scrapy.Spider):
    name = "boruto"

    def __init__(self):
        self.base = "http://www.cartoonmad.com"
        self.cover = self.base + "/comic/5033"

        self.workPool = WorkPool(10)

    def start_requests(self):
        urls = [self.cover]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_chapter)


    def parse_chapter(self, response):
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        chapter_list_tag = soup.find_all('fieldset', id='info')[1].find('table').find('tbody').find_all('tr')
        for tr in chapter_list_tag:
            chapter_list_td = tr.find_all('td')
            for td in chapter_list_td:
                chapter_list_td_a = td.find('a', attrs={'href': True})
                if chapter_list_td_a:
                    self.log(chapter_list_td_a['href'])
                    chapter_url = self.base + chapter_list_td_a['href']
                    yield scrapy.Request(url=chapter_url, callback=self.parse_a_chapter)

    def parse_a_chapter(self, response):
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        title = soup.find('html').find('head').find('title').string
        content_tag = soup.find('tbody').find_all('tr')
        img_tag = content_tag[-4].find('td').find('a').find('img')
        cat_tag = content_tag[-3].find('td')
        cur_page = cat_tag.find('a', class_='onpage').string
        img_url = img_tag['src']

        self.workPool.add_task(self.save_img,cur_page,title,img_url)
        # self.save_img(cur_page, title, img_url)

        next_page = cat_tag.find_all('a', attrs={'href': True})[-1]
        next_page_url = next_page['href']

        if next_page_url != 'thend.asp':
            url = self.base + '/comic/' + next_page_url
            yield scrapy.Request(url=url, callback=self.parse_a_chapter)
        else:
            self.log(title + ' finished')

    def save_img(self, img_mun, title, img_url):
        self.log('saving pic: ' + img_url)
        document = './boruto'

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
