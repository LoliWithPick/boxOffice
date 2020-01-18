from fontTools.ttLib import TTFont
from os import path, makedirs, getcwd
import re, requests, time
from util import cprint
import numpy as np
import matplotlib.pyplot as plt

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
plt.rcParams['axes.unicode_minus'] = False

def getAxis(font):
    uni_list = font.getGlyphOrder()[2:]
    
    font_axis = []
    x_list = []
    y_list = []
    for uni in uni_list:
        axis = []
        for i in font['glyf'][uni].coordinates:
            axis.append(i)
        x_list.append(axis[0])
        y_list.append(axis[1])
        font_axis.append(axis)
    epochs = range(1, len(x_list) + 1)
    plt.plot(epochs, x_list, 'bo')
    plt.plot(epochs, y_list, 'r')
    plt.legend()
    plt.show()
    return font_axis
    
base_font = TTFont('font\\maoyan.woff')
uni_base_list = base_font.getGlyphOrder()[2:]
base_axis = getAxis(base_font)
base_font = None

def downLoadMYFont(response):
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
    length = 0
    for i in range(len(uni_list)):
        for j in range(len(uni_base_list)):
            if len(cur_axis[i]) == len(base_axis[j]):
                length += 1
            # cprint(uni_list[i]+'\t'+uni_base_list[j], 'cyan')
            # if compare_axis(cur_axis[i], base_axis[j]):
            #     font_dict[uni_list[i]] = maoyan_dict[uni_base_list[j]]
    print(length)
    return font_dict

def compare_axis(axis1, axis2):
    np_axis1 = np.array(axis1)
    np_axis2 = np.array(axis2)
    distance = np.sqrt(np.sum(np.square(np_axis1 - np_axis2)))
    print(distance)
    return False

def test():
    global cur_path
    cur_path = 'cache\\1579335848.6232693.woff'
    cprint(parseFont(), 'yellow')
    cur_path = 'cache\\1579335941.607262.woff'
    cprint(parseFont(), 'yellow')
    cur_path = 'cache\\1579336167.706107.woff'
    cprint(parseFont(), 'yellow')

if __name__ == "__main__":
    test()
    