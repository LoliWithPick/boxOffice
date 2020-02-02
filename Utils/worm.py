import requests, time, sys, json, font, re, json, proxyPool
from lxml import etree
from threading import Thread
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
from util import cprint
from excel import Excel, Read
from datetime import datetime, timedelta

# http Configuration
header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8,application/signed-exchange;v=b3',
        'accept-encoding': 'gzip',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cache-Control': 'max-age=0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
}
sslVerify = True
encoding = 'utf-8'
start_year = 2010
end_year = 2019
start_month = 6
end_month = 12


def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()

def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))

class Worm():
    def __init__(self, excel:Excel):
        self.excel = excel
        self.browser = None
        self.browser_TTL = 100
        self.proxy = None
        
    def connect(self, url, data=None, isGet=True, cookie=None, isEtree=True, timeout=5, useProxy=False):
        if useProxy:
            if self.proxy is None:        
                # self.proxy = get_proxy().get("proxy")
                self.proxy = proxyPool.get_proxy()
            proxy = {'https': "https://{}".format(self.proxy), 'http': "http://{}".format(self.proxy)}
            cprint('use proxy: {0}, openning\t{1}'.format(proxy['https'], url), 'cyan')
        else:
            proxy = {}
            cprint('openning\t{0}'.format(url), 'cyan')
        is_ok = False
        retry_count = 20
        while True:
            try:
                if isGet:
                    resp = requests.get(url, headers=header, verify=sslVerify, timeout=timeout, proxies=proxy)
                else:
                    resp = requests.post(url, data, headers=header, cookies=cookie, verify=sslVerify, timeout=timeout, proxies=proxy)
                is_ok = True
                break
            except requests.exceptions.RequestException:
                if useProxy:
                    # self.proxy = get_proxy().get("proxy")
                    self.proxy = proxyPool.get_proxy()
                    proxy = {'https': "https://{}".format(self.proxy), 'http': "http://{}".format(self.proxy)}
                    cprint('use proxy: {0}, reconnect\t{1}'.format(proxy['https'], url), 'yellow')
                else:
                    cprint('reconnect\t' + url, 'yellow')
                retry_count -= 1
                if retry_count == 0:
                    input('continue?')
                    retry_count = 10
        if is_ok:
            resp.encoding = encoding
            # print(resp.text)
            if isEtree:
                body = etree.HTML(resp.text)
            else:
                body = resp.text
            return body
        else:
            cprint('fail to open {0}'.format(url))
            return None

    def connect_test(self, url, proxy, timeout=7):
        cprint('proxy connect test {}'.format(proxy), 'cyan')
        cprint(url, 'cyan')
        retry_count = 3
        while retry_count > 0:
            try:
                resp = requests.get(url, headers=header, verify=sslVerify, timeout=timeout, proxies={'https':'https://{}'.format(proxy)})
                body = etree.HTML(resp.text)
                # item = body.xpath('//div[@class="global-nav-items"]')
                if resp.text.find('异常请求') > 0:
                    cprint('IP异常')
                # elif item is None or item == []:
                #     cprint('IP无效')
                #     return False
                else:
                    return True
            except requests.exceptions.RequestException:
                cprint('retry connect test', 'yellow')
            retry_count -= 1
        delete_proxy(proxy)
        return False

    def browser_connect(self, url):
        if self.browser_TTL == 0 or self.browser is None:
            if self.browser is not None:
                self.browser.quit()
                self.browser_TTL = 200
                time.sleep(1)
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            while True:
                # self.proxy = get_proxy().get("proxy")
                self.proxy = proxyPool.get_proxy()
                if self.connect_test(url, self.proxy):
                    options.add_argument('--proxy-server=http://{}'.format(self.proxy))
                    break
            options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images":2})
            self.browser = webdriver.Chrome(chrome_options=options)
            self.browser.set_page_load_timeout(20)
            self.browser.set_script_timeout(20)
            # self.browser.implicitly_wait(20)
        cprint('use browser openning {}'.format(url), 'cyan')
        isOk = True
        try:
            self.browser.get(url)
            self.browser_TTL -= 1
        except TimeoutException:
            self.browser_TTL -= 1
            cprint('timeout', 'yellow')
        except Exception:
            isOk = False
            cprint('browser error')
        return isOk
        # WebDriverWait(self.browser, timeout).until(
        #     EC.visibility_of(self.browser.find_element_by_class_name('_tn5r2q3fc')))

    def getFilms(self, start=1):
        global header
        cprint('start to get films', 'green')
        cur = start
        url_prefix = 'https://www.yugaopian.cn/movlist/__'
        for year in range(start_year, end_year + 1):
            for month in range(start_month, end_month + 1):
                while(True):
                    url = url_prefix + str(year) + '-' + str(month) + '__' + str(cur)
                    header['Referer'] = 'https://www.yugaopian.cn/movlist'
                    body = self.connect(url)
                    if body is None:
                        pass
                    data_list = body.xpath('body/div[@class="wrapper"]//div[@class="movlist"]//a')
                    move_list = []
                    for data in data_list:
                        movie_name = data.xpath('span[@class="item-title"]/text()')[0]
                        movie_date = data.xpath('span[@class="item-pubtime"]/text()')[0][:-2].split('-')
                        movie = {
                            'CNName': movie_name,
                            'year': movie_date[0],
                            'month': movie_date[1],
                            'day': movie_date[2],
                            'pubYear': self.getPubYear(data.attrib['href'])
                        }
                        move_list.append(movie)
                    self.getFilmInfo(move_list)
                    self.excel.writeSheet(move_list)
                    index_list = body.xpath('//p[@class="page-nav"]/a/text()')
                    if str.isdigit(index_list[-1]):
                        max_index = index_list[-1]
                    else:
                        max_index = index_list[-2]
                    if cur - int(max_index) == 0:
                        break
                    cur = cur + 1
                cur = 1
    
    def getPubYear(self, url):
        url_prefix = 'https://www.yugaopian.cn'
        url = url_prefix + url
        body = self.connect(url)
        if body is None:
            return ''
        date = body.xpath('string(//div[@class="movie-title-detail"])')
        pub_date = re.findall(r'([0-9]{4}-[0-9]{2}-[0-9]{2})+', date)
        if pub_date is None or pub_date == []:
            return ''
        return pub_date[-1][:4]

    def getFilmInfo(self, movie_list=[]):
        for movie in movie_list:
            self.getDouban(movie)
            self.getDBInfo(movie)
            if ('category' in movie and '电视' in movie['category']) or self.getMYInfo(movie):
                move_list.remove(movie)
            cprint(movie, 'magenta')
            print()
            # time.sleep(0.5)
            # for data in data_list:
            #     if movie['CNName'] in data.text and movie['year'] in data.text:
            #         db_url = data.attrib['href']
            #         print(data.text)

    def getDouban(self, movie:dict):
        global header
        url_prefix = 'https://search.douban.com/movie/subject_search?search_text='
        url_nextfix = '&cat=1002'
        url = url_prefix + movie['CNName'] + url_nextfix
        header['Referer'] = 'https://search.douban.com/movie'
        while True:
            self.browser_connect(url)
            title_list = self.browser.find_elements_by_xpath('//h1')
            if title_list is None or title_list == []:
                self.browser_TTL = 0
            else:
                break
        title_list = self.browser.find_elements_by_xpath('//div[@class="root"]//div[@class="title"]//a')
        url = ''
        for title in title_list:
            if movie['pubYear'] in title.text:
                url = title.get_attribute('href')
                break
        if url == '':
            for title in title_list:
                if title.text.startswith(movie['CNName']):
                    url = title.get_attribute('href')
                    break
        movie['url'] = url

    def getDBInfo(self, movie:dict):
        url = movie['url']
        if url == '':
            cprint(movie['CNName'] + ' douban url is None', 'red')
            return
        body = self.connect(url)
        if body is None:
            return
        dbMark = body.xpath('//strong[@property="v:average"]/text()')
        dbNum = body.xpath('//span[@property="v:votes"]/text()')
        movie['dbMark'] = '' if dbMark == [] else dbMark[0]
        movie['dbNum'] = '' if dbNum == [] else dbNum[0]
        rates = body.xpath('//div[@class="ratings-on-weight"]//span[@class="rating_per"]/text()')
        if rates != []:
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
        imdbUrl = body.xpath('//div[@id="info"]/a[last()]/@href')
        if imdbUrl is not None and imdbUrl != []:
            self.getImdbInfo(movie, imdbUrl[0])

    def getImdbInfo(self, movie:dict, url):
        global header
        header['Referer'] = 'https://www.imdb.com'
        body = self.connect(url)
        if body is None:
            return
        ENName = body.xpath('//div[@class="title_bar_wrapper"]//div[@class="title_wrapper"]/h1/text()')
        imdbMark = body.xpath('//div[@class="title_bar_wrapper"]//span[@itemprop="ratingValue"]/text()')
        idbmNum = body.xpath('//div[@class="title_bar_wrapper"]//span[@itemprop="ratingCount"]/text()')
        movie['ENName'] = '' if ENName == [] else ENName[0].replace('\xa0','')
        movie['imdbMark'] = '' if imdbMark == [] else imdbMark[0]
        movie['imdbNum'] = '' if idbmNum == [] else idbmNum[0].replace(',','')

    def getMYInfo(self, movie:dict):
        url_prefix = 'https://maoyan.com/query?kw='
        url_nextfix = '&type=0'
        url = url_prefix + movie['CNName'] + url_nextfix
        header['Referer'] = 'https://maoyan.com'
        body = self.connect(url, useProxy=True)
        if body is None:
            return False
        titile_list = body.xpath('//dl[@class="movie-list"]//div[@title]/a')
        url = ''
        date_list = body.xpath('//dl[@class="movie-list"]//div[@class="movie-item-pub"]/text()')
        for i in range(len(date_list)):
            if date_list[i].startswith(movie['year']):
                url = 'https://maoyan.com' + titile_list[i].attrib['href']
        if url == '':
            for title in titile_list:
                if title.text.endswith(movie['CNName']):
                    url = 'https://maoyan.com' + title.attrib['href']
                    break
        if url == '':
            cprint(movie['CNName'] + ' maoyan url is None', 'red')
            return False
        header['Referer'] = 'https://maoyan.com/films'
        over_time = 5
        while over_time > 0:
            resp = self.connect(url, isEtree=False, useProxy=True)
            if resp is None:
                return False
            font_dict = font.getFont(resp)
            if font_dict is None:
                over_time -= 1
                cprint('retry get {0} font'.format(movie['CNName']), 'yellow')
            else:
                break
        if over_time == 0:
            cprint('{0} maoyan is not validated'.format(movie['CNName']), 'red')
            return False
        cprint(font_dict, 'magenta')
        for key in font_dict.keys():
            resp = resp.replace(key, font_dict[key])
        body = etree.HTML(resp)
        categorys = body.xpath('string(//div[@class="ellipsis"])')
        if categorys != [] and '电视' in categorys:
            return True
        if 'ENName' not in movie:
            ENName = body.xpath('//div[@class="banner"]//div[contains(@class, "ename")]/text()')
            if ENName != []:
                movie['ENName'] = ENName[0]
        mark_info = body.xpath('//div[@class="movie-index"]/div')
        if mark_info is not None and mark_info != []:
            mark = mark_info[0].xpath('string(.)').replace(' ', '')
            mark = re.sub(r'\n+', '|', mark)[1:-1].split('|')
            if len(mark) == 0:
                myMark = ''
                myNum = ''
            elif len(mark) == 1:
                myMark = mark[0]
                myNum = ''
            else:
                myMark = mark[0]
                myNum = mark[1][:-3]
            boxOffice = mark_info[1].xpath('string(.)').replace(' ', '').replace('\n', '')
            movie['myMark'] = myMark
            movie['myNum'] = myNum
            movie['boxOffice'] = boxOffice
        return False

    def getEndata(self):
        global header
        header['dnt'] = '1'
        url = 'http://www.endata.com.cn/API/GetData.ashx'
        form_data = '&MethodName=BoxOffice_GetMovieData_List_Area'
        resp = self.connect(url, form_data, isGet=False, isEtree=False, useProxy=True)
        areas = json.loads(resp)['Data']['Table']
        area_list = []
        for area in areas:
            area_list.append(area['id'])
        print(area_list)
        form_data = 'areaId= {0} &typeId=0&year= {1} &initial=&pageIndex={2}&pageSize=10&MethodName=BoxOffice_GetMovieData_List'
        for year in range(start_year, end_year + 1):
            for area in area_list:
                page = 1
                movie_list = []
                while True:
                    resp = self.connect(url, form_data.format(area, year, page), isGet=False, isEtree=False, useProxy=True)
                    data = json.loads(resp)['Data']
                    box_none = False
                    for row in data['Table']:
                        if row['BoxOffice'] is None or row['BoxOffice'] == '' or row['BoxOffice'] == 0:
                            box_none = True
                            break
                        movie = {
                            'CNName': row['MovieName'],
                            'ENName': row['MovieEnName'],
                            'year': row['releaseYear'],
                            'boxOffice': row['BoxOffice']
                        }
                        movie_list.append(movie)
                    total = data['Table1'][0]['TotalPage']
                    cprint('curPage:{0}\ttotalPage:{1}\tyear:{2}'.format(page, total, year), 'magenta')
                    if page >= total or box_none:
                        break
                    page += 1
                self.excel.writeSheet(movie_list)

    def getmaoyan(self, name_list:[], year_list:[]):
        global header
        url_prefix = 'https://maoyan.com/query?kw='
        url_nextfix = '&type=0'
        for i in range(len(name_list)):
            name = name_list[i]
            url = url_prefix + name + url_nextfix
            header['Referer'] = 'https://maoyan.com'
            while True:
                body = self.connect(url, useProxy=True)
                test_info = body.xpath('//div[@class="search-box"]')
                if test_info is None or test_info == []:
                    self.proxy = None
                else:
                    break
            titile_list = body.xpath('//dl[@class="movie-list"]//div[@title]/a')
            date_list = body.xpath('//dl[@class="movie-list"]//div[@class="movie-item-pub"]')

            # while not self.browser_connect(url):
            #     self.browser_TTL = 0
            # while True:
            #     titile_list = self.browser.find_elements_by_xpath('//dl[@class="movie-list"]//div[@title]/a')
            #     date_list = self.browser.find_elements_by_xpath('//dl[@class="movie-list"]//div[@class="movie-item-pub"]')
            #     if titile_list is None or titile_list == []:
            #         itext = input('chosse 1.keep going\t2.reopen browser')
            #         if itext == 2:
            #             self.browser_TTL = 0
            #             self.browser_connect(url)
            #     else:
            #         break

            header['Referer'] = 'https://maoyan.com/films'
            movie_list = []
            cprint(name, 'green')
            isFind = False
            for j in range(len(titile_list)):
                title = titile_list[j]
                if title.text == name:
                    if date_list[j].text is not None:
                        try:
                            y = int(date_list[:5])
                        except:
                            continue
                        if y <= int(year_list[i]) and y >= int(year_list[i]) - 3:
                            isFind = True
                            url = 'https://maoyan.com' + title.attrib['href']
                            resp = None
                            retry_times = 10
                            while True:
                                resp = self.connect(url, isEtree=False, useProxy=True)
                                font_dict = font.getFont(resp)
                                if font_dict is None:
                                    self.proxy = None
                                    cprint('retry get {0} font'.format(name), 'yellow')
                                    if retry_times == 0:
                                        input('continue?')
                                        retry_times = 10
                                else:
                                    break
                                retry_times -= 1

                            # self.browser_connect(url)
                            # while True:
                            #     test_info = self.browser.find_elements_by_xpath('//div[@class="search-box"]/div')
                            #     if test_info is None or test_info == []:
                            #         itext = input('chosse 1.keep going\t2.reopen browser')
                            #         print(itext)
                            #         if itext == '2':
                            #             self.browser_TTL = 0
                            #             self.browser_connect(url)
                            #     else:
                            #         break
                            # retry_times = 10
                            # resp = self.browser.page_source
                            # while True:
                            #     font_dict = font.getFont(resp)
                            #     if font_dict is None:
                            #         if retry_times == 0:
                            #             input('continue?')
                            #             retry_times = 10
                            #     else:
                            #         break
                            #     retry_times -= 1

                            cprint(font_dict, 'magenta')
                            for key in font_dict.keys():
                                resp = resp.replace(key, font_dict[key])
                            body = etree.HTML(resp)
                            movie = {
                                'CNName': name,
                                'ENName': '',
                                'date': body.xpath('//div[@class="banner"]//div[contains(@class, "wrapper")]//li/text()')[-1],
                                'myMark': '',
                                'myNum': ''
                            }
                            ENName = body.xpath('//div[@class="banner"]//div[contains(@class, "ename")]/text()')
                            if ENName != []:
                                movie['ENName'] = ENName[0]
                            mark_info = body.xpath('//div[@class="movie-index"]/div')
                            if mark_info is not None and mark_info != []:
                                mark = mark_info[0].xpath('string(.)').replace(' ', '')
                                mark = re.sub(r'\n+', '|', mark)[1:-1].split('|')
                                if len(mark) == 0:
                                    myMark = ''
                                    myNum = ''
                                elif len(mark) == 1:
                                    myMark = mark[0]
                                    myNum = ''
                                else:
                                    myMark = mark[0]
                                    myNum = mark[1][:-3]
                                boxOffice = mark_info[1].xpath('string(.)').replace(' ', '').replace('\n', '')
                                movie['myMark'] = myMark
                                movie['myNum'] = myNum
                            movie_list.append(movie)
            if not isFind:
                for j in range(len(titile_list)):
                    title = titile_list[j]
                    if date_list[j].text is not None and date_list[j].text.startswith(year_list[i]):
                        url = 'https://maoyan.com' + title.attrib['href']
                        resp = None
                        retry_times = 10
                        while True:
                            resp = self.connect(url, isEtree=False, useProxy=True)
                            font_dict = font.getFont(resp)
                            if font_dict is None:
                                self.proxy = None
                                cprint('retry get {0} font'.format(name), 'yellow')
                                if retry_times == 0:
                                    input('continue?')
                                    retry_times = 10
                            else:
                                break
                            retry_times -= 1

                        # self.browser_connect(url)
                        # while True:
                        #     mark_info = self.browser.find_elements_by_xpath('//div[@class="movie-index"]/div')
                        #     if mark_info is None or mark_info == []:
                        #         itext = input('chosse 1.keep going\t2.reopen browser')
                        #         if itext == '2':
                        #             self.browser_TTL = 0
                        #             self.browser_connect(url)
                        #     else:
                        #         break
                        # retry_times = 10
                        # resp = self.browser.page_source
                        # while True:
                        #     font_dict = font.getFont(resp)
                        #     if font_dict is None:
                        #         if retry_times == 0:
                        #             input('continue?')
                        #             retry_times = 10
                        #     else:
                        #         break
                        #     retry_times -= 1

                        cprint(font_dict, 'magenta')
                        for key in font_dict.keys():
                            resp = resp.replace(key, font_dict[key])
                        body = etree.HTML(resp)
                        movie = {
                            'CNName': name,
                            'date': body.xpath('//div[@class="banner"]//div[contains(@class, "wrapper")]//li/text()')[-1]
                        }
                        ENName = body.xpath('//div[@class="banner"]//div[contains(@class, "ename")]/text()')
                        if ENName != []:
                            movie['ENName'] = ENName[0]
                        mark_info = body.xpath('//div[@class="movie-index"]/div')
                        if mark_info is not None and mark_info != []:
                            mark = mark_info[0].xpath('string(.)').replace(' ', '')
                            mark = re.sub(r'\n+', '|', mark)[1:-1].split('|')
                            if len(mark) == 0:
                                myMark = ''
                                myNum = ''
                            elif len(mark) == 1:
                                myMark = mark[0]
                                myNum = ''
                            else:
                                myMark = mark[0]
                                myNum = mark[1][:-3]
                            boxOffice = mark_info[1].xpath('string(.)').replace(' ', '').replace('\n', '')
                            movie['myMark'] = myMark
                            movie['myNum'] = myNum
                        movie_list.append(movie)
            self.excel.writeSheet(movie_list)

    def getdouban(self, name_list:[], year_list:[]):
        global header
        url_prefix = 'https://search.douban.com/movie/subject_search?search_text='
        url_nextfix = '&cat=1002'
        header['Referer'] = 'https://search.douban.com/movie'
        for i in range(len(name_list)):
            name = name_list[i]
            url = url_prefix + name + url_nextfix
            movie_list = []
            cprint(name, 'green')
            while True:
                self.browser_connect(url)
                title_list = self.browser.find_elements_by_xpath('//div[@class="global-nav-items"]')
                if title_list is None or title_list == []:
                    self.browser_TTL = 0
                else:
                    break
                
            title_list = self.browser.find_elements_by_xpath('//div[@class="root"]//div[@class="title"]//a')
            for title in title_list:
                text = title.text
                y = int(text[-5:-1])
                if test.startswith('{} '.format(name)) and y <= year_list[i] and y >= year_list[i] - 6:
                    url = title.get_attribute('href')
                    body = self.connect(url, useProxy=True)
                    movie = {'CNName': body.xpath('//span[@property="v:itemreviewed"]/text()')}
                    dbMark = body.xpath('//strong[@property="v:average"]/text()')
                    dbNum = body.xpath('//span[@property="v:votes"]/text()')
                    movie['dbMark'] = '' if dbMark == [] else dbMark[0]
                    movie['dbNum'] = '' if dbNum == [] else dbNum[0]
                    rates = body.xpath('//div[@class="ratings-on-weight"]//span[@class="rating_per"]/text()')
                    if rates != []:
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
                            movie['categorys'] = info.split(':')[1]
                        elif info.startswith('制片'):
                            movie['country'] = info.split(':')[1]
                        elif info.startswith('语言'):
                            movie['language'] = info.split(':')[1]
                        elif info.startswith('上映'):
                            movie['date'] = info.split(':')[1].split(' / ')[0]
                    interests = body.xpath('//div[@class="subject-others-interests-ft"]/a/text()')
                    if len(interests) == 2:
                        movie['want'] = interests[0]
                        movie['see'] = interests[1]
                    elif len(interests) == 1:
                        if interests[0].endswith('看过'):
                            movie['want'] = interests[0]
                        else:
                            movie['see'] = interests[0]
                    movie_list.append(movie)
            self.excel.writeSheet(movie_list)
        
    # def getBaidu(self, name_list:[], date_list:[]):
    #     global header
    #     header['dnt'] = '1'
    #     header['Cookie'] = ''
    #     header['Referer'] = 'https://index.baidu.com/v2/main/index.html'
    #     url = 'https://index.baidu.com/api/SearchApi/index?area=0&word={0}&startDate={1}&endDate={2}'
    #     for i in range(len(name_list)):
    #         name = name_list[i]
    #         endDate = datetime.strptime(date_list[i], '%Y-%m-%d')
    #         startDate = endDate - timedelta(days=30)
    #         endDate = datetime.date(endDate)
    #         startDate = datetime.date(startDate)

    #         resp = self.connect(url.format(name, startDate, endDate), isEtree=False)
    #         data = json.loads(resp)['Data']
    #         print(date)
    #         movie['CNName'] = name
    #         movie['baidu'] = data['generalRatio'][0]['all']['avg']
    #         self.excel.writeSheet([movie])

    def getMtime(self, name_list:[], year_list:[]):
        global header
        referer = 'http://search.mtime.com/search/?q={}'
        search_url = 'http://service.channel.mtime.com/Search.api?Ajax_CallBack=true&Ajax_CallBackType=Mtime.Channel.Services&Ajax_CallBackMethod=GetSearchResult&Ajax_CrossDomain=1&Ajax_RequestUrl={0}&t={1}&Ajax_CallBackArgument0={2}&Ajax_CallBackArgument1=0&Ajax_CallBackArgument2=290&Ajax_CallBackArgument3=0&Ajax_CallBackArgument4=1'
        movie_url = 'http://service.library.mtime.com/Movie.api?Ajax_CallBack=true&Ajax_CallBackType=Mtime.Library.Services&Ajax_CallBackMethod=GetMovieOverviewRating&Ajax_CrossDomain=1&Ajax_RequestUrl={0}&t={1}&Ajax_CallBackArgument0={2}'
        for i in range(len(name_list)):
            name = name_list[i]
            header['Referer'] = referer.format(parse.quote(name))
            t = time.strftime('%Y%m%d%H%M%S0000', time.localtime())
            while True:
                resp = self.connect(search_url.format(header['Referer'], t, name), isEtree=False, useProxy=True)
                try:
                    js_data = re.search(r'= (.*?});', resp).group(1)
                    break
                except Exception:
                    cprint('Invalid. Retry')
            search_datas = json.loads(js_data)['value']
            if 'movieResult' in search_datas and 'moreMovies' in search_datas['movieResult']:
                search_datas = search_datas['movieResult']['moreMovies']
            else:
                continue
            movie_list = []
            for search_data in search_datas:
                if search_data['movieTitle'].startswith('{} '.format(name)):
                    try:
                        y = int(search_data['movieTitle'][-5:-1])
                    except:
                        continue
                    if y <= int(year_list[i]) and y >= int(year_list[i]) - 3:
                        url = search_data['movieUrl']
                        movieId = url.split('/')[-2]
                        header['Referer'] = url
                        resp = self.connect(movie_url.format(url, t, movieId), isEtree=False, useProxy=True)
                        js_data = re.search(r'= (.*?});', resp).group(1)
                        movie_data = json.loads(js_data)['value']
                        movie = {
                            'CNName': movie_data['movieTitle'],
                            'mtimeMark': movie_data['movieRating']['RatingFinal'] if 'movieRating' in movie_data else '',
                            'mtimeNum': movie_data['movieRating']['Usercount'] if 'movieRating' in movie_data else '',
                            'mtimeWant': movie_data['movieRating']['AttitudeCount'] if 'movieRating' in movie_data else '',
                            'movieId': movieId
                        }
                        movie_list.append(movie)
                        cprint(movie, 'magenta')
            self.excel.writeSheet(movie_list)

if __name__ == "__main__":
    # {'CNName':1, 'mtimeMark':2, 'mtimeNum': 3, 'mtimeWant': 4, 'mtimeDMark': 5, 'movieId': 6}
    # {'CNName': 1, 'date': 2, 'directors': 3, 'writers': 4, 'stars': 5
    # , 'categorys': 6, 'country': 7, 'language': 8, 'want': 9, 'see': 10, 'dbMark', 'dbNum'}
    excel = Excel(header={'CNName': 1, 'ENName': 2, 'date': 3, 'myMark': 4, 'myNum': 5})
    reader = Read()
    reader.load('data\\endata.xls')
    sheet = reader.getSheetById()
    # excel = None
    worm = Worm(excel)
    # movie = {
    #     'CNName': '星球大战8：最后的绝地武士',
    #     'year': '2018',
    #     'month': '01',
    #     'day': '25',
    #     'url': 'https://movie.douban.com/subject/27085923/'
    # }
    # ml = [movie]
    # worm.getFilmInfo(ml)
    # worm.connect('https://maoyan.com/films/588362', useProxy=True)
    # worm.getEndata()
    try:
        worm.getmaoyan(sheet.col_values(1)[1174:], sheet.col_values(3)[1174:])
    except Exception as args:
        args.with_traceback()
        cprint(args)
    finally:
        excel.saveExcel()
    # worm.browser_connect('http://httpbin.org/get')

    # try:
    #     worm.getFilms(3)
    # except Exception as args:
    #     args.with_traceback()
    #     cprint(args)
    # finally:
    #     excel.saveExcel()

    # worm.getDBInfo(movie)
    # worm.getImdbInfo(movie, 'https://www.imdb.com/title/tt3513548/')
    # worm.getMYInfo(movie)
    # cprint(movie, 'magenta')