# -*- coding: UTF-8 -*-
import ssl

import traceback

import scrapy
from bs4 import BeautifulSoup
import os, urllib, zlib, urllib2
from WorkPool import *

top = 'http://www.xeall.com'
base = top + '/shenshi'


class volmoe(scrapy.Spider):
    name="volmoe"

    def __init__(self):
        self.base="http://vol.moe/"
        self.list=self.base+"list/all,all,all,sortpoint,all,all"
        self.workPool = WorkPool(10)


    def start_requests(self):
        for i in xrange(1,281):
            url=self.list+"/"+str(i)+".htm"
            yield scrapy.Request(url=url,callback=self.parse_list)


    def parse_list(self,response):
        content = response.body

        soup=BeautifulSoup(content, 'lxml')

        img_tags=soup.find_all('img',{'class':'img_book'})

        for img in img_tags:
            img_name=img['alt']
            img_url=img['src']
            self.save_img(img_name,img_url)
            # self.workPool.add_task(self.save_img , img_name , img_url)

    def save_img(self,title,img_url):
        self.log('saving pic: ' + img_url)
        document = './volmoe/'

        comics_path = document #+ '/' + title
        exists = os.path.exists(comics_path)
        if not exists:
            self.log('create document: ' + title)
            os.makedirs(comics_path)

        pic_name = comics_path + title+'.png'
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
            self.log('save image error.')
            self.log(e)

    def openUrl(self, url):
        if url.strip():
            user_agent = 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
            referer='http://vol.moe'
            header = {'User-Agent': user_agent,'Referer':referer}

            try:
                req = urllib2.Request(url, headers=header)
                res = urllib2.urlopen(req)
                return res
            except Exception, e:
                traceback.print_exc()
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





