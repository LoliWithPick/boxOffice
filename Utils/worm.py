import requests, time, sys, json, font, re
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
start_year = 2018
end_year = 2018
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
        
    def connect(self, url, data=None, isGet=True, cookie=None, isEtree=True, timeout=3, useProxy=False):
        if useProxy:
            proxy = {'https': "https://{}".format(get_proxy().get("proxy"))}
            cprint('use proxy: {0}, openning\t{1}'.format(proxy['https'], url), 'cyan')
        else:
            proxy = {}
            cprint('openning\t{0}'.format(url), 'cyan')
        is_ok = False
        retry_count = 15
        while retry_count > 0:
            try:
                if isGet:
                    resp = requests.get(url, headers=header, verify=sslVerify, timeout=timeout, proxies=proxy)
                else:
                    resp = requests.post(url, data, headers=header, cookies=cookie, verify=sslVerify, timeout=timeout, proxies=proxy)
                is_ok = True
                break
            except requests.exceptions.RequestException:
                if useProxy:
                    delete_proxy(proxy['https'])
                    proxy = {'https': "https://{}".format(get_proxy().get("proxy"))}
                    cprint('use proxy: {0}, reconnect\t{1}'.format(proxy['https'], url), 'yellow')
                else:
                    cprint('reconnect\t' + url, 'yellow')
                retry_count -= 1
        if is_ok:
            resp.encoding = encoding
            # print(resp.text)
            if isEtree:
                body = etree.HTML(resp.text)
            else:
                body = resp.text
            return body
        else:
            cprint('fail to open {0}'.format(url), 'red')
            return None

    def connect_test(self, url, proxy, timeout=7):
        cprint('proxy connect test {}'.format(proxy), 'cyan')
        print(url)
        retry_count = 3
        while retry_count > 0:
            try:
                resp = requests.get(url, headers=header, verify=sslVerify, timeout=timeout, proxies={'https':'https://{}'.format(proxy)})
                body = etree.HTML(resp.text)
                item = body.xpath('//meta[@name="description"]')
                if resp.text.find('异常请求') > 0:
                    cprint('IP异常')
                elif item is None or item == []:
                    cprint('IP无效')
                    return False
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
                self.browser_TTL = 100
                time.sleep(1)
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            while True:
                proxy = get_proxy().get("proxy")
                if self.connect_test(url, proxy):
                    options.add_argument('--proxy-server=http://{}'.format(proxy))
                    break
            options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images":2})
            self.browser = webdriver.Chrome(chrome_options=options)
            self.browser.set_page_load_timeout(35)
            self.browser.set_script_timeout(35)
            # self.browser.implicitly_wait(20)
        cprint('use browser openning {}'.format(url), 'cyan')
        while True:
            try:
                self.browser.get(url)
                self.browser_TTL -= 1
                break
            except Exception:
                cprint('reconnect browser', 'yellow')
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

if __name__ == "__main__":
    excel = Excel()
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

    # worm.browser_connect('http://httpbin.org/get')
    try:
        worm.getFilms(3)
    except Exception as args:
        args.with_traceback()
        cprint(args)
    finally:
        excel.saveExcel()

    # worm.getDBInfo(movie)
    # worm.getImdbInfo(movie, 'https://www.imdb.com/title/tt3513548/')
    # worm.getMYInfo(movie)
    # cprint(movie, 'magenta')