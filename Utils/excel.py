import xlwt, time
from os import path, makedirs
from util import cprint

# save configuration
filePath = 'D:\\CUDA\\boxOffice'
fileName = 'movData'
excel_header = {'CNName': 1, 'ENName': 2, 'year': 3, 'month': 4, 'day': 5, 
                'directors': 6, 'writers': 7, 'stars': 8, 'category': 9, 'country': 10, 
                'language': 11, 'dbMark': 12, 'db1m': 13, 'db2m': 14, 'db3m': 15,
                'db4m': 16, 'db5m': 17, 'dbNum': 18, 'imdbMark': 19, 'imdbNum': 20,
                'toMark': 21, 'toNum': 22, 'toFresh': 23, 'toBad': 24,'toAMark': 25,
                'toANum': 26, 'myMark': 27, 'myNum': 28, 'boxOffice': 29, 'url': 30}

class Excel():
    def __init__(self):
        self.sheet_index = 0
        self.now_index = 0
        self.createExcel()

    def createExcel(self):
        cprint('{0} -----创建excel表格-----'.format(time.strftime('%a %b %d %Y %H:%M:%S', time.localtime())), 'cyan')
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('sheet' + str(self.sheet_index))
        self.sheet_index += 1
        for index in range(len(excel_header)):
            self.sheet.write(0, index, excel_header[index])

    def createSheet(self):
        cprint('{0} -----创建新表格-----'.format(time.strftime('%a %b %d %Y %H:%M:%S', time.localtime())), 'cyan')
        self.sheet = self.book.add_sheet('sheet' + str(self.sheet_index))
        self.sheet_index += 1
        for index in range(len(excel_header)):
            self.sheet.write(0, index, excel_header[index])

    def writeSheet(self, movie_list):
        for movie in movie_list:
            if self.now_index > 65500 :
                self.createSheet()
                self.now_index = 1
            for key in movie.keys():
                self.sheet.write(self.now_index, excel_header[key], movie[key])
            self.now_index += 1

    def saveExcel(self):
        try:
            cprint('{0} -----保存excel表格-----'.format(time.strftime('%a %b %d %Y %H:%M:%S', time.localtime())), 'cyan')
            if not path.exists(filePath):
                makedirs(filePath)
            self.book.save(path.join(filePath, fileName) +'.xls')
        except Exception as args:
            cprint(args)
            input('数据保存失败!\nPress any key to exit!')
            sys.exit()