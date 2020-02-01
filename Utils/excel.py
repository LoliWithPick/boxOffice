import xlwt, time, xlrd, random
from os import path, makedirs, remove, listdir
from util import cprint

# save configuration
filePath = 'data'
fileName = 'mydata'
excel_header = {'CNName': 1, 'ENName': 2, 'year': 3, 'month': 4, 'day': 5, 
                'directors': 6, 'writers': 7, 'stars': 8, 'category': 9, 'country': 10, 
                'language': 11, 'dbMark': 12, 'db1m': 13, 'db2m': 14, 'db3m': 15,
                'db4m': 16, 'db5m': 17, 'dbNum': 18, 'imdbMark': 19, 'imdbNum': 20,
                'myMark': 21, 'myNum': 22, 'boxOffice': 23}

class Excel():
    def __init__(self, header=None):
        self.sheet_index = 0
        self.now_index = 1
        if header is None:
            self.header = excel_header
        else:
            self.header = header
        self.createExcel()

    def createExcel(self):
        cprint('{0} -----创建excel表格-----'.format(time.strftime('%a %b %d %Y %H:%M:%S', time.localtime())), 'cyan')
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('sheet' + str(self.sheet_index))
        self.sheet_index += 1
        for key in self.header.keys():
            self.sheet.write(0, self.header[key], key)

    def createSheet(self):
        cprint('{0} -----创建新表格-----'.format(time.strftime('%a %b %d %Y %H:%M:%S', time.localtime())), 'cyan')
        self.sheet = self.book.add_sheet('sheet' + str(self.sheet_index))
        self.sheet_index += 1
        for key in self.header.keys():
            self.sheet.write(0, self.header[key], key)

    def writeSheet(self, movie_list):
        cprint('{0} -----写入excel表格-----'.format(time.strftime('%a %b %d %Y %H:%M:%S', time.localtime())), 'cyan')
        for movie in movie_list:
            if self.now_index > 65500 :
                self.createSheet()
                self.now_index = 1
            for key in self.header.keys():
                if key in movie:
                    self.sheet.write(self.now_index, self.header[key], str(movie[key]).strip())
            self.now_index += 1

    def write(self, col, data):
        self.sheet.write(self.now_index, col, data)

    def saveExcel(self):
        savePath = path.join(filePath, fileName) +'.xls'
        if path.exists(savePath):
            remove(savePath)
        try:
            cprint('{0} -----保存excel表格-----'.format(time.strftime('%a %b %d %Y %H:%M:%S', time.localtime())), 'cyan')
            if not path.exists(filePath):
                makedirs(filePath)
            self.book.save(savePath)
        except Exception as args:
            cprint(args)
            input('数据保存失败!\nPress any key to exit!')
            sys.exit()

class Read():
    def __init__(self):
        self.workBook = None

    def load(self, filePath):
        if not path.exists(filePath):
            cprint('{} does not exists'.format(filePath))
        self.workBook = xlrd.open_workbook(filePath)
        cprint('sheet nums:{}\t'.format(self.workBook.nsheets), 'green')

    def openCheck(self):
        if self.workBook is None:
            cprint('Didn\'t open a xls file yet')

    def getSheets(self):
        self.openCheck()
        return self.workBook.sheets()

    def getSheetById(self, index=0):
        self.openCheck()
        if index >= self.workBook.nsheets:
            cprint('index out of bounds')
        return self.workBook.sheet_by_index(index)


if __name__ == "__main__":
    write = Excel()
    read = Read()
    # files = listdir('data')
    # for f in files:
    #     p = path.join(filePath, f)
    #     cprint('\tget {} data'.format(p), 'cyan')
    #     read.load(p)
    #     sheet_list = read.getSheets()
    #     for sheet in sheet_list:
    #         cprint('\tsheet {0}. row:{1}, col:{2}'.format(sheet.name, sheet.nrows, sheet.ncols), 'magenta')
    #         for i in range(1, sheet.nrows):
    #             if sheet.cell_value(i, 23) == '' or '无' in sheet.cell_value(i, 23):
    #                 continue
    #             if write.now_index > 65535 :
    #                 write.createSheet()
    #                 write.now_index = 1
    #             for j in range(1, sheet.ncols):
    #                 write.write(j, sheet.cell_value(i ,j))
    #             write.now_index += 1
    read.load('data\\filtedData.xls')
    sheet = read.getSheetById(0)
    maxIndex = sheet.nrows
    used_list = [0]
    for i in range(100):
        row = 0
        while row in used_list:
            row = random.randint(1, maxIndex)
        for j in range(0, sheet.ncols):
            write.write(j, sheet.cell_value(row ,j))
        write.now_index += 1
        used_list.append(row)
    write.saveExcel()