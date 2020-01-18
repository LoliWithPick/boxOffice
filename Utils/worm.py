import requests, time, sys, json, font
from lxml import etree
from threading import Thread
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
from util import cprint
from excel import Excel

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

class Worm():
    def __init__(self, excel:Excel):
        self.excel = excel
        self.browser = None
        
    def connect(self, url, data=None, isGet=True, cookie=None, isEtree=True):
        cprint('openning ' + url, 'cyan')
        if isGet:
            resp = requests.get(url, headers=header, verify=sslVerify)
        else:
            resp = requests.post(url, data, headers=header, cookies=cookie, verify=sslVerify)
        resp.encoding = encoding
        # print(resp.text)
        if isEtree:
            body = etree.HTML(resp.text)
        else:
            body = resp.text
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
        self.excel.saveExcel()

    def getFilmInfo(self, movie_list=[]):
        for movie in movie_list:
            self.getDouban(movie)
            print('movie:', movie)
            # for data in data_list:
            #     if movie['CNName'] in data.text and movie['year'] in data.text:
            #         db_url = data.attrib['href']
            #         print(data.text)

    def getDouban(self, movie:dict):
        url_prefix = 'https://search.douban.com/movie/subject_search?search_text='
        url_nextfix = '&cat=1002'
        url = url_prefix + movie['CNName'] + url_nextfix
        self.browser_connect(url)
        print(self.browser.find_element_by_xpath('//div[@class="root"]'))
        title = self.browser.find_elements_by_xpath('//div[@class="root"]//div[@class="title"]/a')[0]
        movie['url'] = title.get_attribute('href')

    def getDBInfo(self, movie:dict):
        url = movie['url']
        body = self.connect(url)
        movie['dbMark'] = body.xpath('//strong[@property="v:average"]/text()')[0]
        movie['dbNum'] = body.xpath('//span[@property="v:votes"]/text()')[0]
        rates = body.xpath('//div[@class="ratings-on-weight"]//span[@class="rating_per"]/text()')
        for i in range(5):
            movie['db%dm' % (i + 1)] = rates[4 - i]
        info_list = body.xpath('string(//div[@id="info"])').replace(' ','').split('\n')
        for info in info_list:
            if info.startswith('导演'):
                movie['directors'] = info.split(':')[1]
            elif info.startswith('编剧'):
                movie['writers'] = info.split(':')[1]
            elif info.startswith('主演'):
                movie['stars'] = info.split(':')[1]
            elif info.startswith('类型'):
                movie['category'] = info.split(':')[1]
            elif info.startswith('制片'):
                movie['country'] = info.split(':')[1]
            elif info.startswith('语言'):
                movie['language'] = info.split(':')[1]
        imdbUrl = body.xpath('//div[@id="info"]/a[last()]/@href')[0]

    def getImdbInfo(self, movie:dict, url):
        body = self.connect(url)
        title = body.xpath('//div[@class="vital"]//div[@class="title_bar_wrapper"]')[0]
        movie['ENName'] = title.xpath('//div[@class="title_wrapper"]/h1/text()')[0].replace('\xa0','')
        movie['imdbMark'] = title.xpath('//span[@itemprop="ratingValue"]/text()')[0]
        movie['imdbNum'] = title.xpath('//span[@itemprop="ratingCount"]/text()')[0].replace(',','')

    def getMYInfo(self, movie:dict):
        url_prefix = 'https://maoyan.com/query?kw='
        url = url_prefix + movie['CNName']
        body = self.connect(url)
        item_list = body.xpath('//dl[@class="movie-list"]//div[@title]/a')
        for item in item_list:
            if item.text.endswith(movie['CNName']):
                url = 'https://maoyan.com' + item.attrib['href']
                break
        body = self.connect(url, isEtree=False)
        font_dict = font.getFont(body)
        print(font_dict)
        for key in font_dict.keys():
            body.replace(key, font_dict[key])
        print(body)
        body = etree.HTML(body)
        mark_info = body.xpath('//div[@class="movie-index"]//span[@class="stonefont"]/text()')
        print(mark_info)
        
        

if __name__ == "__main__":
    #excel = Excel()
    excel = None
    worm = Worm(excel)
    movie = {
        'CNName': '死侍',
        'year': '2018',
        'month': '01',
        'day': '25',
        'url': 'https://movie.douban.com/subject/25842038/'
    }
    # ml = [movie]
    # worm.getFilmInfo(ml)
    # worm.getFilms()
    # worm.getDBInfo(movie)
    # worm.getImdbInfo(movie, 'https://www.imdb.com/title/tt3513548/')
    worm.getMYInfo(movie)
    print(movie)