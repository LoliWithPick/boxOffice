import numpy as np
import pandas as pd
import random as rnd
import seaborn as sns
import matplotlib.pyplot as plt
from math import log
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
# from sklearn.cluster import KMeans

plt.rcParams['font.sans-serif'] = ['KaiTi'] # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False

num_rank = {5000 : 2, 10000 : 3, 50000 : 4, 100000 : 5, 250000 : 6, 500000 : 7, 750000 : 8}
star_rank = {100: 0, 500: 1, 1000: 2, 2500: 3, 5000: 4, 7500: 5, 10000: 6, 25000: 7, 50000: 8, 75000: 9, 1000000: 10, 1250000: 11, 1500000: 12, 2000000:13}
star_cont = [[1], [0.6, 0.4], [0.4, 0.3, 0.3], [0.3, 0.25, 0.25, 0.2]]
director_cont = [[1], [0.8, 0.2]]
date_rank = [111, 91, 34, 92, 37]

def eclidean_distance(base, comp, feature):
    dis = np.sqrt(np.sum(np.square((comp - base) * feature)))
    # print(dis)
    return dis

def init_centroid(dp, k):
    num, dim = dp.shape
    cp = np.zeros((k, dim))
    l = [i for i in range(num)]
    np.random.shuffle(l)
    for i in range(k):
        index = int(l[i])
        cp[i] = dp.iloc[index]
    return cp

def KMeans(dp, k, feature, max_iter=500):
    num, dim = dp.shape
    cluster = np.zeros((num, 2)) # 0:属于哪个簇 1:距离该簇中心点距离
    cluster[:,0] = -1
    cp = init_centroid(dp, k)
    change = True
    iter = 0
    while change and iter <= max_iter:
        iter+=1
        change = False
        for index, row in dp.iterrows():
            min_dis = 9999
            min_index = -1
            for i in range(k):
                dis = eclidean_distance(cp[i], row, feature)
                if dis < min_dis:
                    min_dis = dis
                    min_index = i
            if cluster[index, 0] != min_index:
                change = True
                cluster[index, :] = min_index, min_dis
        for i in range(k):
            p_cluster = dp.iloc[[j for j in range(num) if cluster[j, 0] == i]]
            cp[i] = p_cluster.mean()
    print('finish!')
    return cp, cluster

def dict_norm(dataDict:dict):
    minkey = min(dataDict, key=dataDict.get)
    maxkey = max(dataDict, key=dataDict.get)
    res = {}
    for key in dataDict.keys():
        res[key] = (dataDict[key] - dataDict[minkey]) / (dataDict[maxkey] - dataDict[minkey])
    return res

def list_norm(dataList:list):
    minValue = min(dataList)
    maxValue = max(dataList)
    res = []
    for value in dataList:
        res.append((value - minValue) / (maxValue - minValue))
    return res

def judgeBoxOffice(df):
    if '亿' in df['boxOffice']:
        num = float(df['boxOffice'].replace('亿','')) * 10000
        return int(num)
    elif '万' in df['boxOffice']:
        return int(df['boxOffice'].replace('万',''))
    else:
        num = float(df['boxOffice']) / 10000
        return int(num)

def judgeMYNum(df):
    if '万' in str(df['myNum']):
        num = float(str(df['myNum']).replace('万', '')) * 10000
        return num
    else:
        return float(df['myNum'])

def judgeLanguage(df):
    temp = str(df['language'])
    if '普通' in temp or '汉语' in temp or '粤语' in temp:
        return 1
    elif '英语' in temp:
        return 2
    else:
        return 0

def judgeCountry(df):
    temp = str(df['country'])
    if '中国' in temp:
        return 1
    else:
        return 0

def checkNum(num):
    try:
        temp = int(num)
        for key in num_rank.keys():
            if temp <= key:
                return num_rank[key]
        return 9
    except Exception:
        return 0

def judgeDBMark(df):
    num = checkNum(df['dbNum'])
    return num*df['dbMark']

def judgeMYMark(df):
    num = checkNum(df['myNum'])
    return num * float(df['myMark'])

def judgeDAndW(col, dwmap, smap):
    keys = str(col).strip().split('/')[0:2]
    res = 0
    for i in range(len(keys)):
        key = keys[i].strip()
        if key in dwmap.keys() and key in smap.keys():
            res += (dwmap[key] * director_cont[len(keys) - 1][i]) * 0.6 + (smap[key] * 0.4)
        elif key in dwmap.keys():
            res += dwmap[key] * director_cont[len(keys) - 1][i]
        else:
            res += 0
    return res

def judgeDirectors(df, dmap):
    keys = str(df['directors']).strip().split('/')[0:2]
    res = 0
    for i in range(len(keys)):
        key = keys[i].strip()
        if key in dmap.keys():
            res += dmap[key] * director_cont[len(keys) - 1][i]
        else:
            res += 0
    return res

def judgeWriters(df, wmap):
    keys = str(df['writers']).strip().split('/')[0:2]
    res = 0
    for i in range(len(keys)):
        key = keys[i].strip()
        if key in wmap.keys():
            res += wmap[key] * director_cont[len(keys) - 1][i]
        else:
            res += 0
    return res

def judgeStars(df, smap):
    stars = str(df['stars']).strip().split('/')[0:4]
    res = 0
    for i in range(len(stars)):
        star = stars[i].strip()
        if star in smap.keys():
            res += smap[star] * star_cont[len(stars) - 1][i]
        else:
            res += 0
    return res

def judgeGenres(df, cmap):
    genres = str(df['category']).strip().split('/')[0:4]
    res = 0
    for genre in genres:
        genre = genre.strip()
        if genre in cmap.keys():
            res += cmap[genre]
        else:
            res += 0
    return res / len(genres)

def judgeDate(date, dlist):
    return dlist[date]

def getDate(df):
    month = df['month']
    day = df['day']
    res = 0
    if month > 11 or month < 3:
        res =  1
    elif month == 4 or (month == 5 and  day < 5):
        res =  2
    elif month > 5 and month < 9:
        res =  3
    elif month == 9 or (month == 10 and day < 8):
        res =  4
    else:
        res =  0
    return res

def getIE(db, my):
    amount = db + my
    res = (db / amount) * log(db / amount) + (my / amount) * log(my / amount)
    return -res

def countIE(col, ie):
    res, count = {}, {}
    for i in range(len(col)):
        vs = col.iloc[i]
        for v in str(vs).split('/'):
            v = v.strip()
            if v in count:
                count[v] += 1
                res[v] += ie.iloc[i]
            else:
                count[v] = 1
                res[v] = ie.iloc[i]
    for key in res.keys():
        res[key] = res[key] / count[key]
    return res

def countGenres(genres):
    count = dict()
    countg = dict()
    for index, row in genres.iterrows():
        for genre in str(row['category']).split('/'):
            genre = genre.strip()
            if genre in count:
                countg[genre] += 1
                count[genre] += row['boxOffice']
            else:
                countg[genre] = 1
                count[genre] = row['boxOffice']
    for key in count.keys():
        count[key] = count[key] / countg[key]
    return dict_norm(count)

def countMarkRelevance(col, dbMark, myMark):
    res, count = {}, {}
    for i in range(len(col)):
        vs = col.iloc[i]
        for v in str(vs).split('/'):
            v = v.strip()
            if v in count:
                count[v] += 1
                res[v] += (dbMark.iloc[i] + myMark.iloc[i]) / 2
            else:
                count[v] = 1
                res[v] = (dbMark.iloc[i] + myMark.iloc[i]) / 2
    for key in res.keys():
        res[key] = res[key] / count[key]
    return dict_norm(res)

def countNumRelevance(col, dbNum, myNum):
    res, count = {}, {}
    for i in range(len(col)):
        vs = col.iloc[i]
        for v in str(vs).split('/'):
            v = v.strip()
            if v in count:
                count[v] += 1
                res[v] += (dbNum.iloc[i] + myNum.iloc[i]) / 2
            else:
                count[v] = 1
                res[v] = (dbNum.iloc[i] + myNum.iloc[i]) / 2
    for key in res.keys():
        res[key] = res[key] / count[key]
    return dict_norm(res)

def countStars(df):
    count = dict()
    counts = dict()
    for index, row in df.iterrows():
        actors = str(row['stars']).split('/')[0:4]
        for i in range(len(actors)):
            star = actors[i].strip()
            if star in count:
                counts[star] += 1
                count[star] += row['boxOffice'] * star_cont[len(actors) - 1][i]
            else:
                counts[star] = 1
                count[star] = row['boxOffice'] * star_cont[len(actors) - 1][i]
    for key in count.keys():
        count[key] = count[key] / counts[key]
    return dict_norm(count)

def countDirectors(df):
    count = dict()
    counts = dict()
    for index, row in df.iterrows():
        directors = str(row['directors']).strip().split('/')[0:2]
        for i in range(len(directors)):
            director = directors[i].strip()
            if director in count:
                counts[director] += 1
                count[director] += row['boxOffice'] * director_cont[len(directors) - 1][i]
            else:
                counts[director] = 1
                count[director] = row['boxOffice'] * director_cont[len(directors) - 1][i]
    for key in count.keys():
        count[key] = count[key] / counts[key]
    return dict_norm(count)

def countWriters(df):
    count = dict()
    counts = dict()
    for index, row in df.iterrows():
        writers = str(row['writers']).strip().split('/')[0:2]
        for i in range(len(writers)):
            writer = writers[i].strip()
            if writer in count:
                counts[writer] += 1
                count[writer] += row['boxOffice'] * director_cont[len(writers) - 1][i]
            else:
                counts[writer] = 1
                count[writer] = row['boxOffice'] * director_cont[len(writers) - 1][i]
    for key in count.keys():
        count[key] = count[key] / counts[key]
    return dict_norm(count)

def countDate(df):
    count = [0, 0, 0, 0, 0]
    for index, row in df.iterrows():
        date = row['date']
        count[date] += row['boxOffice']
    for i in range(len(count)):
        count[i] /= date_rank[i]
    # amount = sum(count)
    # for i in range(len(count)):
    #     count[i] /= amount
    return list_norm(count)



# def judgeMY(df):
#     if '亿' in df['boxOffice']:
#         num = float(df['boxOffice'].replace('亿','')) * 10000
#         return num
#     elif '万' in df['boxOffice']:
#         return float(df['boxOffice'].replace('万',''))
#     else:
#         num = float(df['boxOffice']) / 10000
#         return num

train_df = pd.read_excel('data\\train.xls')
test_df = pd.read_excel('data\\test.xls')
train_df = train_df.dropna(subset=['myNum', 'dbNum', 'stars'])
# train_df = train_df.drop(train_df[train_df.year == 2014].index)
# train_df = train_df.drop(train_df[train_df.year == 2019].index)
train_df = train_df.drop(train_df[train_df.dbNum < 100].index)
# for i in range(1, 6):
#     train_df['db{}m'.format(i)] = train_df['db{}m'.format(i)].fillna('0')
#     train_df['db{}m'.format(i)] = (train_df['db{}m'.format(i)].str)[0]
#     train_df['db{}m'.format(i)] = train_df['db{}m'.format(i)].astype('float')
train_df['boxOffice'] = train_df.apply(lambda r:judgeBoxOffice(r), axis=1)
train_df['lan'] = train_df.apply(lambda r:judgeLanguage(r), axis=1)
train_df['coun'] = train_df.apply(lambda r:judgeCountry(r), axis=1)
train_df['dbmark1'] = train_df.apply(lambda r:judgeDBMark(r), axis=1)
train_df['myNum'] = train_df.apply(lambda r:judgeMYNum(r), axis=1)
# train_df = train_df.drop(train_df[train_df.boxOffice < 10].index)
train_df = train_df.drop(train_df[train_df.myNum < 100].index)
train_df['mymark1'] = train_df.apply(lambda r:judgeMYMark(r), axis=1)
train_df['myMark'] = train_df['myMark'].astype('float')
train_df['date'] = train_df.apply(lambda r:getDate(r), axis=1)
train_df = train_df.drop(['ENName', 'year', 'month', 'day', 'country', 'language', 'imdbMark', 'imdbNum'], axis=1)

actors_rank = countStars(train_df)
genres_rank = countGenres(train_df)
writers_rank = countWriters(train_df)
directors_rank = countDirectors(train_df)
date_list = countDate(train_df)
# actors_mark = countMarkRelevance(train_df['stars'], train_df['dbMark'], train_df['myMark'])
# genres_mark = countMarkRelevance(train_df['category'], train_df['dbMark'], train_df['myMark'])
# writers_mark = countMarkRelevance(train_df['writers'], train_df['dbMark'], train_df['myMark'])
# directors_mark = countMarkRelevance(train_df['directors'], train_df['dbMark'], train_df['myMark'])
# actors_num = countNumRelevance(train_df['stars'], train_df['dbNum'], train_df['myNum'])
# genres_num = countNumRelevance(train_df['category'], train_df['dbNum'], train_df['myNum'])
# writers_num = countNumRelevance(train_df['writers'], train_df['dbNum'], train_df['myNum'])
# directors_num = countNumRelevance(train_df['directors'], train_df['dbNum'], train_df['myNum'])

train_df['dmark'] = train_df.apply(lambda r:judgeDAndW(r['directors'], directors_rank, actors_rank), axis=1)
train_df['wmark'] = train_df.apply(lambda r:judgeDAndW(r['writers'], writers_rank, actors_rank), axis=1)
train_df['smark'] = train_df.apply(lambda r:judgeStars(r, actors_rank), axis=1)
train_df['cmark'] = train_df.apply(lambda r:judgeGenres(r, genres_rank), axis=1)
train_df['dateMark'] = train_df.apply(lambda r:judgeDate(r['date'], date_list), axis=1)

# train_df['dmrele'] = train_df.apply(lambda r:judgeDirectors(r, directors_mark), axis=1)
# train_df['wmrele'] = train_df.apply(lambda r:judgeWriters(r, writers_mark), axis=1)
# train_df['smrele'] = train_df.apply(lambda r:judgeStars(r, actors_mark), axis=1)
# train_df['cmrele'] = train_df.apply(lambda r:judgeGenres(r, genres_mark), axis=1)

# train_df['dnrele'] = train_df.apply(lambda r:judgeDirectors(r, directors_num), axis=1)
# train_df['wnrele'] = train_df.apply(lambda r:judgeWriters(r, writers_num), axis=1)
# train_df['snrele'] = train_df.apply(lambda r:judgeStars(r, actors_num), axis=1)
# train_df['cnrele'] = train_df.apply(lambda r:judgeGenres(r, genres_num), axis=1)
# train_df['IE_Vol'] = train_df.apply(lambda r:getIE(r['dbNum'], r['myNum']), axis=1)
# train_df['IE_Val'] = train_df.apply(lambda r:getIE(r['dbMark'], r['myMark']), axis=1)

# actors_vol = countIE(train_df['stars'], train_df['IE_Vol'])
# genres_vol = countIE(train_df['category'], train_df['IE_Vol'])
# writers_vol = countIE(train_df['writers'], train_df['IE_Vol'])
# directors_vol = countIE(train_df['directors'], train_df['IE_Vol'])
# actors_val = countIE(train_df['stars'], train_df['IE_Val'])
# genres_val = countIE(train_df['category'], train_df['IE_Val'])
# writers_val = countIE(train_df['writers'], train_df['IE_Val'])
# directors_val = countIE(train_df['directors'], train_df['IE_Val'])
# train_df['dvol'] = train_df.apply(lambda r:judgeDirectors(r, directors_vol), axis=1)
# train_df['wvol'] = train_df.apply(lambda r:judgeWriters(r, writers_vol), axis=1)
# train_df['svol'] = train_df.apply(lambda r:judgeStars(r, actors_vol), axis=1)
# train_df['cvol'] = train_df.apply(lambda r:judgeGenres(r, genres_vol), axis=1)
# train_df['dval'] = train_df.apply(lambda r:judgeDirectors(r, directors_val), axis=1)
# train_df['wval'] = train_df.apply(lambda r:judgeWriters(r, writers_val), axis=1)
# train_df['sval'] = train_df.apply(lambda r:judgeStars(r, actors_val), axis=1)
# train_df['cval'] = train_df.apply(lambda r:judgeGenres(r, genres_val), axis=1)

# train_df = train_df.drop(['directors', 'writers', 'stars', 'category'], axis=1)
train_df = train_df.drop(['directors', 'writers', 'stars', 'category', 'dbMark', 'db1m', 'db2m', 'db3m', 'db4m', 'db5m', 'dbNum', 'myMark', 'myNum'], axis=1)

test_df['date'] = test_df.apply(lambda r:getDate(r), axis=1)
test_df['boxOffice'] = test_df.apply(lambda r:judgeBoxOffice(r), axis=1)
test_df['lan'] = test_df.apply(lambda r:judgeLanguage(r), axis=1)
test_df['coun'] = test_df.apply(lambda r:judgeCountry(r), axis=1)
test_df['dmark'] = test_df.apply(lambda r:judgeDAndW(r['directors'], directors_rank, actors_rank), axis=1)
test_df['wmark'] = test_df.apply(lambda r:judgeDAndW(r['writers'], writers_rank, actors_rank), axis=1)
test_df['smark'] = test_df.apply(lambda r:judgeStars(r, actors_rank), axis=1)
test_df['cmark'] = test_df.apply(lambda r:judgeGenres(r, genres_rank), axis=1)
test_df['dateMark'] = test_df.apply(lambda r:judgeDate(r['date'], date_list), axis=1)

# test_df['dmrele'] = test_df.apply(lambda r:judgeDirectors(r, directors_mark), axis=1)
# test_df['wmrele'] = test_df.apply(lambda r:judgeWriters(r, writers_mark), axis=1)
# test_df['smrele'] = test_df.apply(lambda r:judgeStars(r, actors_mark), axis=1)
# test_df['cmrele'] = test_df.apply(lambda r:judgeGenres(r, genres_mark), axis=1)

# test_df['dnrele'] = test_df.apply(lambda r:judgeDirectors(r, directors_num), axis=1)
# test_df['wnrele'] = test_df.apply(lambda r:judgeWriters(r, writers_num), axis=1)
# test_df['snrele'] = test_df.apply(lambda r:judgeStars(r, actors_num), axis=1)
# test_df['cnrele'] = test_df.apply(lambda r:judgeGenres(r, genres_num), axis=1)
# test_df['dvol'] = test_df.apply(lambda r:judgeDirectors(r, directors_vol), axis=1)
# test_df['wvol'] = test_df.apply(lambda r:judgeWriters(r, writers_vol), axis=1)
# test_df['svol'] = test_df.apply(lambda r:judgeStars(r, actors_vol), axis=1)
# test_df['cvol'] = test_df.apply(lambda r:judgeGenres(r, genres_vol), axis=1)
# test_df['dval'] = test_df.apply(lambda r:judgeDirectors(r, directors_val), axis=1)
# test_df['wval'] = test_df.apply(lambda r:judgeWriters(r, writers_val), axis=1)
# test_df['sval'] = test_df.apply(lambda r:judgeStars(r, actors_val), axis=1)
# test_df['cval'] = test_df.apply(lambda r:judgeGenres(r, genres_val), axis=1)
test_df = test_df.drop(['ENName', 'directors', 'writers', 'stars', 'category', 'country', 'language', 'dbMark', 'db1m', 'db2m', 'db3m', 'db4m', 'db5m', 'dbNum', 'imdbMark', 'imdbNum', 'myMark', 'myNum'], axis=1)

# print(train_df.info())
# print(train_df[['dvol', 'wvol', 'svol', 'sval']].describe())
# print(test_df.info())
# y1 = train_df[['db5m', 'boxOffice']].groupby(['db5m'], as_index=False).mean().sort_values(by='boxOffice', ascending=False)
# print(train_df['dbmark1'].describe())
# print(countGenres(train_df))
# print(train_df.sort_values('boxOffice', ascending=False)[['CNName', 'category', 'boxOffice']][0:10])
# print(test_df.head())
# sns.heatmap(train_df.corr(), annot=True, vmax=1, square=True, cmap="Blues")
# sns.regplot(x='dbmark1', y='boxOffice', data=train_df, x_jitter=.1, color='y')
# genres = pd.Series(countGenres(train_df)).sort_values()
# actors = pd.Series(countStars(train_df)).sort_values()
# by_actor = pd.DataFrame(actors, index=actors.index, columns=['box'])
# by_actor.box.sort_values().tail(10).plot(kind ='barh')
# genres_avg = genres / 10000
# genres.plot(kind = 'barh', title = '11')
# genres_by_year = train_df.groupby('year').
# plt.show()

# X_train = train_df.drop(['CNName', 'dbMark', 'db1m', 'db2m', 'db3m', 'db4m', 'db5m', 'dbNum', 'myMark', 'myNum', 'boxOffice', 'dbmark1', 'mymark1'], axis=1)
# X_train = train_df[['lan', 'coun', 'dmark', 'wmark', 'smark', 'cmark', 'dateMark', 'dmrele', 'wmrele', 'smrele', 'cmrele', 'dnrele', 'wnrele', 'snrele', 'cnrele', 'dvol', 'wvol', 'svol', 'cvol', 'dval', 'wval', 'sval', 'cval']]
X_train = train_df[['dmark', 'wmark', 'smark', 'cmark']].reset_index(drop=True)
Y_train = train_df['boxOffice'].reset_index(drop=True)
# X_test = test_df.drop(['CNName', 'boxOffice'], axis=1).copy()
# X_test = test_df[['lan', 'coun', 'dmark', 'wmark', 'smark', 'cmark', 'dateMark', 'dmrele', 'wmrele', 'smrele', 'cmrele', 'dnrele', 'wnrele', 'snrele', 'cnrele', 'dvol', 'wvol', 'svol', 'cvol', 'dval', 'wval', 'sval', 'cval']]
X_test = test_df[['dmark', 'wmark', 'smark', 'cmark']].reset_index(drop=True)
# print(X_train.head())
# print(Y_train.head())
# print(X_test.head())
# print(X_train.shape, X_test.shape, Y_train.shape)
model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, Y_train)
y_pre = model.predict(X_test)
max = 0
min = 9999
avg = 0
for index, row in test_df.iterrows():
    sum = abs(round((row['boxOffice'] - y_pre[index]) / row['boxOffice'] * 100, 2))
    if sum > max:
        max = sum
    elif sum < min:
        min = sum
    avg += sum
print('------avg:{0}\tmin:{1}\tmax:{2}'.format(avg / len(y_pre), min, max))
print(model.score(X_train, Y_train))
print('------import------')
title = ['dmark', 'wmark', 'smark', 'cmark']
feature = model.feature_importances_
for i in range(len(feature)):
    # if model.feature_importances_[i] * 100 > :
    print(title[i] + ':', feature[i])

cp, cluster = KMeans(X_train * 10, 4, feature, 1000)
# kmodel = KMeans(n_clusters=5, max_iter=1000)
# kmodel.fit_predict(X_train, feature=feature)
print(cp)
print(pd.Series(cluster[:,0]).value_counts())

xtrain0 = X_train.iloc[[i for i in range(len(cluster)) if cluster[i, 0] == 0]]
xtrain1 = X_train.iloc[[i for i in range(len(cluster)) if cluster[i, 0] == 1]]
xtrain2 = X_train.iloc[[i for i in range(len(cluster)) if cluster[i, 0] == 2]]
xtrain3 = X_train.iloc[[i for i in range(len(cluster)) if cluster[i, 0] == 3]]

ytrain0 = Y_train.iloc[[i for i in range(len(cluster)) if cluster[i, 0] == 0]]
ytrain1 = Y_train.iloc[[i for i in range(len(cluster)) if cluster[i, 0] == 1]]
ytrain2 = Y_train.iloc[[i for i in range(len(cluster)) if cluster[i, 0] == 2]]
ytrain3 = Y_train.iloc[[i for i in range(len(cluster)) if cluster[i, 0] == 3]]

model0 = RandomForestRegressor(n_estimators=100)
model0.fit(xtrain0, ytrain0)
model1 = RandomForestRegressor(n_estimators=100)
model1.fit(xtrain1, ytrain1)
model2 = RandomForestRegressor(n_estimators=100)
model2.fit(xtrain2, ytrain2)
model3 = RandomForestRegressor(n_estimators=100)
model3.fit(xtrain3, ytrain3)

model_list = [model0, model1, model2, model3]


def judgeDistance(df):
    min_dis = 999
    min_index = -1
    for i in range(4):
        dis = eclidean_distance(cp[i], df, feature)
        if dis < min_dis:
            min_dis = dis
            min_index = i
    return min_index

test_df['group'] = test_df.apply(lambda r:judgeDistance(r[['dmark', 'wmark', 'smark', 'cmark']]), axis=1)

test0 = test_df[test_df['group'] == 0].reset_index(drop=True)
test1 = test_df[test_df['group'] == 1].reset_index(drop=True)
test2 = test_df[test_df['group'] == 2].reset_index(drop=True)
test3 = test_df[test_df['group'] == 3].reset_index(drop=True)
test_list = [test0, test1, test2, test3]

maxP, minP, avgP = 0, 9999, 0
for i in range(len(test_list)):
    if len(test_list[i]) > 0:
        y_pre = model_list[i].predict(test_list[i][['dmark', 'wmark', 'smark', 'cmark']])
        for index, row in test_list[i].iterrows():
            sum = abs(round((row['boxOffice'] - y_pre[index]) / row['boxOffice'] * 100, 2))
            if sum > maxP:
                maxP = sum
            elif sum < minP:
                minP = sum
            avgP += sum
print('------avg:{0}\tmin:{1}\tmax:{2}'.format(avgP / len(test_df), minP, maxP))