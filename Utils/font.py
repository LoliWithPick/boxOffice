from fontTools.ttLib import TTFont
from os import path, makedirs, getcwd
import re, requests, time
from util import cprint

maoyan_dict = {
        'uniF816': '1',
        'uniE069': '2',
        'uniE9FA': '8',
        'uniEFD2': '0',
        'uniE7CF': '3',
        'uniE26F': '6',
        'uniF6D9': '5',
        'uniEFF5': '7',
        'uniEFD4': '9',
        'uniEADF': '4',
}
write_path = 'cache'
cur_path = ''

def getAxis(font):
    uni_list = font.getGlyphOrder()[2:]
    font_axis = []
    for uni in uni_list:
        axis = []
        for i in font['glyf'][uni].coordinates:
            axis.append(i)
        font_axis.append(axis)
    return font_axis
    
base_font = TTFont('font\\maoyan.woff')
uni_base_list = base_font.getGlyphOrder()[2:]
base_axis = getAxis(base_font)
base_font = None

def getFont(response):
    font_url = 'http:' + re.search(r"url\('(.*\.woff)'\)", response).group(1)
    cprint('download:\t' + font_url, 'cyan')
    font_file = requests.get(font_url).content
    writeFont(font_file)
    return parseFont()

def writeFont(font_file):
    global cur_path
    if not path.exists(write_path):
        makedirs(write_path)
    cur_path = path.join(write_path, str(time.time()) + '.woff')
    with open(cur_path, 'wb') as f:
        f.write(font_file)

def parseFont():
    cprint('open:\t' + cur_path, 'green')
    cur_font = TTFont(cur_path)
    uni_list = cur_font.getGlyphOrder()[2:]
    cur_axis = getAxis(cur_font)
    font_dict = {}
    for i in range(len(uni_list)):
        max_count, uni = 0, None
        for j in range(len(uni_base_list)):
            count = compare_axis(cur_axis[i], base_axis[j])
            if count > max_count:
                max_count = count
                uni = uni_base_list[j]
        font_dict['&#x' + uni_list[i][3:].lower() +';'] = maoyan_dict[uni]
    return font_dict

def compare_axis(axis1, axis2):
    length = len(axis1) if len(axis1) < len(axis2) else len(axis2)
    count = 0
    for i in range(length):
        if abs(axis1[i][0] - axis2[i][0]) < 20 and abs(axis1[i][1] - axis2[i][1]) < 20:
            count += 1
    return count

# def test():
#     global cur_path
#     cur_path = 'cache\\1579335848.6232693.woff'
#     cprint(parseFont(), 'yellow')
#     cur_path = 'cache\\1579335941.607262.woff'
#     cprint(parseFont(), 'yellow')
#     cur_path = 'cache\\1579336167.706107.woff'
#     cprint(parseFont(), 'yellow')

# if __name__ == "__main__":
#     test()
    