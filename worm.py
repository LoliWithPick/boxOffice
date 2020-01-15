import requests
from lxml import etree
header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8,application/signed-exchange;v=b3',
        'Referer': 'https://www.yugaopian.cn',
        'accept-encoding': 'gzip, deflate, br',
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

def connect(url, data=None, isGet=True, cookie=None):
    if isGet == True:
        resp = requests.get(url, headers=header, verify=sslVerify)
    else:
        resp = requests.post(url, data, headers=header, cookies=cookie, verify=sslVerify)
    resp.encoding = encoding
    html_parse = etree.HTML(resp.text)
    return html_parse

def getFilms():
    url_prefix = 'https://www.yugaopian.cn/movlist/__'
    cur = 1
    # for year in range(start_year, end_year + 1):
    #     for month in range(start_month, end_month + 1):
    #         while(true):
            # url = url_prefix + year + '-' + month + '__' + cur
    url = 'https://www.yugaopian.cn/movlist/__2019-1__'
    body = connect(url)
    
    max_index = body.xpath('//p[@class="page-nav"]/a[last()-1]/test()')[0]
    

    

if __name__ == "__main__":
    getFilms()
