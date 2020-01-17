import requests, xlwt, time, sys
from lxml import etree
from threading import Thread
from os import path, makedirs
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# http Configuration
header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8,application/signed-exchange;v=b3',
        'accept-encoding': 'gzip',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
}
sslVerify = True
encoding = 'utf-8'
start_year = 2016
end_year = 2018
start_month = 1
end_month = 12

# save configuration
filePath = 'D:\CUDA\boxOffice'
fileName = 'movData'
excel_header = ['CNName', 'ENName', 'year', 'month', 'day', 
                'directors', 'writers', 'stars', 'category', 'country', 
                'language', 'dbMark', 'db1m', 'db2m', 'db3m',
                'db4m', 'db5m', 'dbNum', 'imdbMark', 'imdbNum',
                'toMark', 'toNum', 'toFresh', 'toBad','toAMark',
                'toANum', 'myMark', 'myNum','boxOffice']
# excel
class Excel():
    def __init__(self):
        self.sheet_index = 0
        self.now_index = 0
        self.createExcel()

    def createExcel(self):
        print('{0} -----创建excel表格-----'.format(time.strftime('%a %b %d %Y %H:%M:%S', time.localtime())))
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('sheet' + str(self.sheet_index))
        self.sheet_index += 1
        for index in range(len(excel_header)):
            self.sheet.write(0, index, excel_header[index])

    def createSheet(self):
        print('{0} -----创建新表格-----'.format(time.strftime('%a %b %d %Y %H:%M:%S', time.localtime())))
        self.sheet = self.book.add_sheet('sheet' + str(self.sheet_index))
        self.sheet_index += 1
        for index in range(len(excel_header)):
            self.sheet.write(0, index, excel_header[index])

    def writeSheet(self, movie):
        if self.now_index > 65500 :
            self.createSheet()
            self.now_index = 1
        for index in range(len(excel_header)):
            self.sheet.write(self.now_index, index, movie[excel_header[index]])
        self.now_index += 1

    def saveExcel(self):
        try:
            print('{0} -----保存excel表格-----'.format(time.strftime('%a %b %d %Y %H:%M:%S', time.localtime())))
            if not path.exists(filePath):
                makedirs(filePath)
            self.book.save(path.join(filePath, fileName) +'.xls')
        except Exception as args:
            print(args)
            input('数据保存失败!\nPress any key to exit!')
            sys.exit()

class Worm():
    def __init__(self, excel=None):
        self.excel = excel
        self.browser = None
        
    def connect(self, url, data=None, isGet=True, cookie=None, isEtree=True):
        if isGet:
            resp = requests.get(url, headers=header, verify=sslVerify)
        else:
            resp = requests.post(url, data, headers=header, cookies=cookie, verify=sslVerify)
        resp.encoding = encoding
        # print(resp.text)
        body = resp.text
        if isEtree:
            body = etree.HTML(body)
        return body
    
    def browser_connect(self, url, timeout=20):
        if self.browser is None:
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            self.browser = webdriver.Chrome(chrome_options=options)
            # self.browser.implicitly_wait(20)
        self.browser.get(url)
        # WebDriverWait(self.browser, timeout).until(
        #     EC.visibility_of(self.browser.find_element_by_class_name('_tn5r2q3fc')))

    def getFilms(self):
        url_prefix = 'https://www.yugaopian.cn/movlist/__'
        for year in range(start_year, end_year + 1):
            for month in range(start_month, end_month + 1):
                cur = 1
                while(True):
                    url = url_prefix + str(year) + '-' + str(month) + '__' + str(cur)
                    body = self.connect(url)
                    data_list = body.xpath('body/div[@class="wrapper"]//div[@class="movlist"]//a')
                    move_list = []
                    for data in data_list:
                        movie_name = data.xpath('span[@class="item-title"]/text()')[0]
                        movie_date = data.xpath('span[@class="item-pubtime"]/text()')[0][:-2].split('-')
                        movie = {
                            'CNName': movie_name,
                            'year': movie_date[0],
                            'month': movie_date[1],
                            'day': movie_date[2]
                        }
                        move_list.append(movie)
                    max_index = body.xpath('//p[@class="page-nav"]/a[last()-1]/text()')[0]
                    if not str.isdigit(max_index) or cur == max_index:
                        break
                    cur = cur + 1

    def getFilmInfo(self, movie_list=[]):
        for movie in movie_list:
            self.getDouban(movie)
            print('movie:', movie)
            # for data in data_list:
            #     if movie['CNName'] in data.text and movie['year'] in data.text:
            #         db_url = data.attrib['href']
            #         print(data.text)

    def getDouban(self, movie):
        url_prefix = 'https://search.douban.com/movie/subject_search?search_text='
        url_nextfix = '&cat=1002'
        url = url_prefix + movie['CNName'] + url_nextfix
        self.browser_connect(url)
        print(self.browser.find_element_by_xpath('//div[@class="root"]'))
        title = self.browser.find_elements_by_xpath('//div[@class="root"]//div[@class="title"]/a')[0]
        
        


if __name__ == "__main__":
    #excel = Excel()
    excel = None
    worm = Worm(excel)
    movie = {
        'CNName': '死侍2：我爱我家',
        'year': '2018',
        'month': '01',
        'day': '25'
    }
    ml = [movie]
    worm.getFilmInfo(ml)
    # worm.getFilms()
