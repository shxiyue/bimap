#-*-coding:utf-8-*-
import os
from estool import esagg
import datetime

def distance(vector1,vector2):
    """ 欧式距离"""
    d=0;
    for a,b in zip(vector1,vector2):
        d+=(a-b)**2;
    return d**0.5;

def cos(vector1,vector2):
    """cos计算"""
    dot_product = 0.0;
    normA = 0.0;
    normB = 0.0;
    for a,b in zip(vector1,vector2):
        dot_product += a*b
        normA += a**2
        normB += b**2
    if normA == 0.0 or normB==0.0:
        return None
    else:
        return dot_product / ((normA*normB)**0.5)

def changeTime(tm):
    """日期减８小时"""
    tmp = datetime.datetime.strptime(tm,'%Y-%m-%d %H:%M:%S')
    tmp = tmp - datetime.timedelta(hours=8)
    return tmp.strftime('%Y-%m-%d %H:%M:%S')

def getSimilaryBase(eshost,esport,esindex,starttime,range,estype=None):
    esm = esagg(eshost,esport)
    starttime = changeTime(starttime)
    dlist = esm.readByTimeRange(esindex,starttime,range,type=estype)
    if not dlist:
        return {"distance":0,"cdistance":0,"record_count":0}
    res = []
    res2 = []
    for d in dlist:
        res.append( d['_source']['cpuuse'] + d['_source']['cpusys'])
        res2.append(100)

    d = round(distance(res,res2),4)
    c = round(cos(res,res2),4)
    return {"distance":d,"cdistance":c,"record_count":len(dlist)}

print getSimilaryBase(['84.239.97.140'],9500,'bimap-test-cpuall-*','2017-01-01 00:00:00','+1d',estype='CPU_ALL')
'''
def getSimilary(eshost,esport,esindex,basetime,tartime,dtrange,estype=None):
    """计算两个对比数据的"""
    esm = esagg(eshost,esport)
    basetime = changeTime(basetime)
    tartime = changeTime(tartime)
    dlist = esm.readByTimeRange(esindex,basetime,dtrange,type=estype)
    res = []
    for d in dlist:
        res.append( d['_source']['cpuuse'] + d['_source']['cpusys'])

    dlist2 = esm.readByTimeRange(esindex,tartime,dtrange,type=estype)
    res2 = []
    for d in dlist2:
        res2.append( d['_source']['cpuuse'] + d['_source']['cpusys'])
    d = round(distance(res,res2),4)
    c = round(cos(res,res2),4)
    return {"distance":d,"cdistance":c,"record_count":len(dlist)}
'''

def getAllSMDFromES():
    dtstr = "2016-12-01"
    dt = datetime.datetime.strptime(dtstr,"%Y-%m-%d")
    reslist = []
    for d in range(31):
        nd = dt + datetime.timedelta(days=d)
        nds = nd.strftime("%Y-%m-%d 00:00:00")
        nds2 = nd.strftime("%Y-%m-%d")
        a = getSimilaryBase("84.239.97.140",9500,"bimap-test-cpuall*",nds,'+1d',estype='CPU_ALL')
        a["logtime"] =nds2
        a['type'] = 'day'
        print nds2
        """
        for i in range(24):
            ndi = nd + datetime.timedelta(hours = i)
            ndis = ndi.strftime("%Y-%m-%d %H:%M:%S")
            x = getSimilaryBase("84.239.97.140",9500,"bimap-test-cpuall*",nds,'+1h',estype='CPU_ALL')
            a['hd'+str(i)] = x["distance"]
            a['hc'+str(i)] = x["cdistance"]
            a['hx'+str(i)] = x["record_count"]

            '''
            x["logtime"] = nds
            x["type"] = "hour"
            print x
            '''
        """
        reslist.append(a)

        #print a
    esm = esagg("84.239.97.140",9500)
    esm.write2Esbulk('bimap-common-smd','cpuall',reslist,addlogtime=False)

#getAllSMDFromES()

def getSimilaryFromES(eshost,esport,esindex,starttime,dtrange,estype=None):
    esm = esagg(eshost,esport)
    dlist = esm.readByTimeRange(esindex,starttime,dtrange,type=estype)
    if len(dlist) == 0:
        return {"distance":0,"cdistince":0,"record_count":0}
    res = []

    for d in dlist:
        res.append( d['_source']['cpuuse'] + d['_source']['cpusys'])
    base=[1 for i in range(len(res))]
    d = round(distance(base,res),4)
    c = round(cos(base,res),4)
    return {"distance":d,"cdistance":c,"record_count":len(dlist)}




#print getSimilary('84.239.97.140',9500,'bimap-test-cpuall*', "2016-03-25 16:00:00","2016-03-26 16:00:00",'+2h',estype='CPU_ALL')




#getAllSMDFromES()

def getfile(filename):
    f = open(filename)
    a = f.readlines()
    res = []
    ct = 0
    for i in a:
        ct = ct +1
        if ct == 1:
            continue
        x = i.split(',')
        v = float(x[1]) + float(x[2])
        res.append(v)
    f.close()
    return res

def listfile(rootdir,res):
    for lists in os.listdir(rootdir):
        path = os.path.join(rootdir, lists)
        #print path
        if os.path.isdir(path):
            listfile(path,res)
        else:
            res.append(path)
"""
prex= '/data/project/tmp/novplods01/'

res = []
listfile(prex,res)
x= getfile(res[0])
baseline = [1 for i in range(1439)]
for f in res:
    tar = getfile(f)
    co = cos(baseline,tar)
    dv = distance(baseline,tar)
    print '%s,%f,%f' % (f[-12:][:8],co,dv)

b = getfile('./base.txt')
x=[]
for file in filelist:
    x.append(getfile(prex+file))

print 'distance----------------'
for a in range(len(filelist)):
    print distance(b,x[a])

print 'cos----------------'
for a in range(len(filelist)):
    print cos(b,x[a])

"""
