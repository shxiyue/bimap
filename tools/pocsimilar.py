#-*-coding:utf-8-*-
import os
import datetime
import time
from estool import esagg
import multiprocessing
from elasticsearch import Elasticsearch
from elasticsearch import  helpers
import argparse
#import pdb

eshost=['84.239.97.141']
esport=9500
pocindex = 'bimap-sa-performance-*'
performanceindex = 'bimap-common-performance'
es_per_index = 'bimap-sa-performance-*'
performanceTypes = ['CPU_ALL','IO_ALL','IOPS']

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

def getPocData(startime,range,host,type,timezone='+08:00'):
    '''根据时间范围和主机名获取poc数据'''
    if type=='CPU_ALL':
        _type = type
        script = "doc['sys'].value + doc['user'].value + doc['wait'].value"
    elif type=='IO_ALL':
        _type = type
        script = "doc['readM'].value + doc['writeM'].value"
    elif type=='IOPS':
        _type = 'IO_ALL'
        script = "doc['rs'].value + doc['ws'].value"
    else:
        return []
    qbody= {
      "query":{
          "bool":{
              "must": [
                {"term": { "bimap_hostname": { "value": host } }},
                {"range": { "logtime": {
                    "gte": startime, "lte": "%s||%s" %(startime,range),
                    "format": "yyyy-MM-dd'T'HH:mm:ss",
                    "time_zone":timezone
                  }
                }}
              ]
          }
      },
      "script_fields": {
        "value": {
          "script": { "lang": "painless", "inline": script }
        }
      },
      "sort": [ { "logtime": { "order": "asc" } } ]
    }

    es = Elasticsearch(eshost,port=esport)
    #res = es.search(index=pocindex,doc_type=_type,body=qbody,size= 2000)
    res = es.search(index=pocindex,doc_type=_type,body=qbody,size= 2000,
                    filter_path = ['hits.hits.fields.value'])
    if not res:
        return []
    dtlist = []
    for r in res['hits']['hits']:
        dtlist.append(round(r['fields']['value'][0],4))
    return dtlist

def getBaseMod(nums):
    '''获取d算法的基础模型数据'''
    base = [0 for i in range(nums)]
    return base

def getBaseCosMod(nums):
    '''c算法基础模型数据'''
    base = [0.1 for i in range(nums)]
    return base

def calcOdisByTimeRange(host,startime,range,type):
    moddt = getPocData(startime,range,host,type)
    if moddt:
        o = distance(moddt,getBaseMod(len(moddt)))
        c = cos(moddt,getBaseCosMod(len(moddt)))
        rcount = len(moddt)
    else:
        o = 0
        c = 0
        rcount = 0
    return o,c,rcount

def calcOdis2Time(host,oneTime,twoTime,range,type):
    moddt = getPocData(oneTime,range,host,type)
    moddt2= getPocData(twoTime,range,host,type)
    if moddt and moddt2:
        o = distance(moddt,moddt2)
        c = cos(moddt,moddt2)
        rcount = len(moddt)
    else:
        o = 0
        c = 0
        rcount = 0
    return o,c,rcount

def calcModRank(dvalue,cvalue,starttime,ptype,hostname,timerange,timezone='+08:00'):
    if timerange == '+1d':
        rcount = 1439
    elif timerange =='+1h':
        rcount = 59
    else: rcount=0
    es = Elasticsearch(eshost,port=esport)
    qbody={
      "size":0,
      "query": {
        "bool": {
          "must": [
            {"term": {"ptype.keyword": {"value": ptype}}},
            {"term": {"bimap_hostname": {"value": hostname}}},
            {"term": {"timerange.keyword": {"value": timerange}}},
            {"range": {"rcount":{"gte":rcount}}},
            {"range": {"logtime": {"lte": starttime,"time_zone":timezone} }}
          ]
        }
      },
      "aggs": {
        "basedis": { "percentile_ranks": { "field": "basedis", "values": [dvalue] } },
        "basec": { "percentile_ranks": { "field": "basec", "values": [cvalue] } }
      }
    }
    res = es.search(index=performanceindex,doc_type=ptype,body=qbody,ignore=[404])
    if  (('status' in res.keys()) and res['status']==404 ) or res['hits']['total']==0 :
        return 10000,10000
    else:
        return round(res['aggregations']['basedis']['values']['%s'%(str(dvalue))],4), round(res['aggregations']['basec']['values']['%s'%(str(cvalue))],4)

def writeOdis(starttime,range,tarindex):
    qhost={
      "size":1000,
      "aggs": {
        "distinct_hostname": {
          "terms": {
            "field": "bimap_hostname"
          }
        }
      }
    }
    es = Elasticsearch(eshost,port=esport)
    hostlist = es.search(index=pocindex,body=qhost,filter_path=['aggregations.distinct_hostname.buckets'])
    today = datetime.datetime.strptime(starttime,'%Y-%m-%dT%H:%M:%S')
    yestoday = today - datetime.timedelta(days=1)
    yestodayStr = yestoday.strftime('%Y-%m-%dT%H:%M:%S')
    epoch = int(time.mktime(today.timetuple()))
    actions = []
    for h in hostlist['aggregations']['distinct_hostname']['buckets']:
        for p in  performanceTypes:
            data = {}
            #计算和基础模型的距离
            o,c,rcount= calcOdisByTimeRange(h['key'],starttime,range,p)
            if rcount == 0:
                continue
            o=round(o,4)
            c=round(c,4)
            #ro=calcModRank(o,starttime,p,h['key'],range)
            #rc=calcModRank(c,starttime,p,h['key'],range)

            data['basedis'] = o
            data['basec'] = c
            data['timerange'] = range
            data['ptype']= p
            data['rcount']= rcount
            data['hour'] = today.hour
            data['bimap_hostname'] = h['key']
            data['logtime'] = (today-datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M:%S')
            #data['ranko'] = ro
            #data['rankc'] = rc

            #计算和和昨天的对比
            o2,c2,rcount= calcOdis2Time(h['key'],starttime,yestodayStr,range,p)
            data['comYesd'] = round(o2,4)
            data['comYesc'] = round(c2,4)
            data['id'] = '%s_%d_%s_%s' %(h['key'],epoch,p,range)
            action={
                "_index":tarindex,
                "_type":p,
                "_id":data['id'],
                "_source":data
            }
            actions.append(action)
    helpers.bulk(es,actions)
    print starttime

#def calcModRank(value,starttime,ptype,hostname,timerange,timezone='+08:00'):

def upRankByDateRange(args):
    starttime=args.startdate
    endtime=args.enddate
    qbase={
        "query":{
            "range":{
                "logtime":{ "time_zone": "+08:00", "gte":starttime, "lte": endtime,"format":"yyyyMMdd" }
            }
        }
    }
    esm = esagg(eshost,esport)
    res = esm.readByQuery(performanceindex,qbase)
    actions=[]
    for r in res:
        ro,rc= calcModRank(r['_source']['basedis'],r['_source']['basec'], r['_source']['logtime'],r['_source']['ptype'],r['_source']['bimap_hostname'],r['_source']['timerange'],timezone='+00:00')
        action = {"_op_type":"update",
          "_index":performanceindex,
          "_type":r['_source']['ptype'],
          "_id":r['_id'],
          "doc":{ "ranko":ro,"rankc":rc }
          }
        #print ro,rc,r['_source']['bimap_hostname'],r['_source']['logtime']
        actions.append(action)
    es=Elasticsearch(eshost,port=esport)
    helpers.bulk(es,actions)


def upRankByMissing():
    qbase={
        "query": {
            "bool": {
                "must_not": {
                    "exists": {
                        "field": "ranko"
                    }
                }
            }
        }
    }
    esm = esagg(eshost,esport)
    res = esm.readByQuery(performanceindex,qbase)
    actions=[]
    for r in res:
        ro,rc= calcModRank(r['_source']['basedis'],r['_source']['basec'], r['_source']['logtime'],r['_source']['ptype'],r['_source']['bimap_hostname'],r['_source']['timerange'],timezone='+00:00')
        action = {"_op_type":"update",
          "_index":performanceindex,
          "_type":r['_source']['ptype'],
          "_id":r['_id'],
          "doc":{ "ranko":ro,"rankc":rc }
          }
        #print ro,rc,r['_source']['bimap_hostname'],r['_source']['logtime']
        actions.append(action)
    es=Elasticsearch(eshost,port=esport)
    helpers.bulk(es,actions)
#writeOdis('2017-01-01T00:00:00','+1h',performanceindex)
#writeOdis('2017-01-02T00:00:00','+1h',performanceindex)
#writeOdis('2017-01-03T00:00:00','+1h',performanceindex)

def calcFullMod(args):
    startdt=args.startdate
    enddt=args.enddate
    sdt = datetime.datetime.strptime(str(startdt),'%Y%m%d')
    edt = datetime.datetime.strptime(str(enddt),'%Y%m%d')
    days = (edt-sdt).days
    pool = multiprocessing.Pool(processes=10)
    for i in range(days+1):
        #sdt = (sdt + datetime.timedelta(days=nw)).strftime('%Y-%m-%dT%H:%M:%S')
        curdt = (sdt + datetime.timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%S')
        pool.apply_async(writeOdis,(curdt,'+1d',performanceindex))
        #计算每个小时的
        for j in range(24):
            curh = sdt + datetime.timedelta(days=i) + datetime.timedelta(hours = j)
            pool.apply_async(writeOdis,(curh.strftime('%Y-%m-%dT%H:%M:%S'),'+1h',performanceindex))
            #writeOdis(curh.strftime('%Y-%m-%dT%H:%M:%S'),'+1h',performanceindex)

    pool.close()
    pool.join()

def writemod(args):
    writeOdis(args.start,args.range,performanceindex)
    time.sleep(10)
    upRankByMissing()

def main():
    # create the top-level parser
    # 公共连接参数，并设置默认值
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', default="84.239.97.140,84.239.97.141,84.239.97.142", help='elasticsearch host')
    parser.add_argument('-port', default=9500,type=int, help='elasticsearch port')

    #添加子命令
    subparsers = parser.add_subparsers(title="subcommands",description="valid subcommands",help='sub-command help')
    # 
    parser_a = subparsers.add_parser('writeallmod', help='writemod help')
    parser_a.add_argument('-startdate',help='date format:YYYYMMDD')
    parser_a.add_argument('-enddate',help='date format:YYYYMMDD')
    parser_a.set_defaults(func=calcFullMod)

    parser_a = subparsers.add_parser('writemod', help='writemod help')
    parser_a.add_argument('-start',help='yyyy-mm-ddTHH:MM:SS')
    parser_a.add_argument('-range',help='+[n][day,hour]')
    parser_a.set_defaults(func=writemod)

    parser_a = subparsers.add_parser('upallrank', help='uprank help')
    parser_a.add_argument('-startdate',help='exec writemod')
    parser_a.add_argument('-enddate',help='exec writemod')
    parser_a.set_defaults(func=upRankByDateRange)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()



############旧代码################################
def changeTime(tm):
    """日期减８小时"""
    tmp = datetime.datetime.strptime(tm,'%Y-%m-%d %H:%M:%S')
    tmp = tmp - datetime.timedelta(hours=8)
    return tmp.strftime('%Y-%m-%dT%H:%M:%S')

def chgTime(tm,hour):
    """日期减指定小时"""
    tmp = datetime.datetime.strptime(tm,'%Y-%m-%d %H:%M:%S')
    tmp = tmp + datetime.timedelta(hours=hour)
    return tmp.strftime('%Y-%m-%dT%H:%M:%S')

#print chgTime('2016-03-04 12:00:00',-8)
def calcSMDBase(starttime,range,host,smdtype):
    esm = esagg(eshost,esport)
    starttime = changeTime(starttime)
    qbody={
      "query": {
        "bool": {
          "must": [
            {"term": { "bimap_hostname": { "value": host } }},
            {"range": { "logtime": {
                "gte": starttime, "lte": "%s||%s" %(starttime,range),
                "format": "yyyy-MM-dd'T'HH:mm:ss"
              }
            }}
          ]
        }
      }
    }
    dlist = esm.readByQuery(es_per_index,qbody,type=smdtype)
    if not dlist:
        return {"type":smdtype,"basedist":0,"rcount":0}
    res = []
    res2 = []
    for d in dlist:
        if smdtype == 'CPU_ALL':
            all = d['_source']['user'] + d['_source']['sys']
            if  d['_source']['wait']:
                all += d['_source']['wait']
            res.append( all)
            res2.append(0)
        elif smdtype == 'IO_ALL':
            all = d['_source']['readM'] + d['_source']['writeM']
            res.append(all)
            res2.append(0)

    d = round(distance(res,res2),4)
    #c = round(cos(res,res2),4)
    return {"type":smdtype,"basedis":d,"rcount":len(dlist)}

#print calcSMDBase('2017-01-01 00:00:00','+1d','nopplbds04','CPU_ALL')

def calcAllSMDbyHost(startday,days,hostname,stype):
    dt = datetime.datetime.strptime(startday,"%Y%m%d")
    for d in range(days):
        reslist = []
        calcdt = dt + datetime.timedelta(days=d)
        a=calcSMDBase(calcdt.strftime("%Y-%m-%d %H:%M:%S"),'+1d',hostname,stype)
        #print a
        if a['rcount'] == 0:
            continue
        a["logtime"] = changeTime(calcdt.strftime("%Y-%m-%d %H:%M:%S"))
        a['type'] = 'day'
        a['stype'] = stype
        a['bimap_hostname'] = hostname
        reslist.append(a)
        #计算每个小时的
        for i in range(24):
            ndi = calcdt + datetime.timedelta(hours = i)
            ndis = ndi.strftime("%Y-%m-%d %H:%M:%S")
            x=calcSMDBase(ndis,'+1h',hostname,stype)
            if x['rcount']==0 :
                continue
            x["logtime"] = changeTime(ndi.strftime("%Y-%m-%d %H:%M:%S"))
            x["type"]= 'hour'
            x["stype"]= stype
            x['bimap_hostname'] = hostname
            x['hours'] = i
            reslist.append(x)
        print calcdt.strftime("%Y-%m-%d %H:%M:%S"),stype,hostname

        esm = esagg(eshost,esport)
        esm.write2Esbulk('bimap-common-performance',stype,reslist,addlogtime=False)
        del reslist


def calcRank(value,starttime,stype,hostname,timezone):
    es = Elasticsearch(eshost,port=esport)
    qbody={
      "size":0,
      "query": {
        "bool": {
          "must": [
            {"term": {"stype.keyword": {"value": stype}}},
            {"term": {"bimap_hostname": {"value": hostname}}},
            {"term": {"type.keyword": {"value": "day"}}},
            {"range": {"rcount":{"gte":1439}}},
            {"range": {"logtime": {"lte": starttime,"time_zone":timezone} }}
          ]
        }
      },
      "aggs": {
        "NAME": {
          "percentile_ranks": {
            "field": "basedis",
            "values": [value]
          }
        }
      }
    }
    res = es.search(index='bimap-common-performance',doc_type=stype,body=qbody)
    #print res
    return round(res['aggregations']['NAME']['values']['%s'%(value)],4)

#calcRank(638.56,"2017-02-21T00:00:00",'CPU_ALL','nopplbds03')
def calcAllRank(hostname,stype,starttime,days,timezone):
    esm = esagg(eshost,esport)
    qbody = {
      "query":{
          "bool":{
              "must":[
                  {"term":{"bimap_hostname":hostname}},
                  {"term":{"type":'day'}},
                  {"range": {"logtime": {"gte": starttime,"time_zone":timezone} }}
              ]
          }
      },
      "sort": [ { "logtime": { "order": "asc" } } ]
    }
    res = esm.readByQuery('bimap-common-performance',qbody,type=stype)
    actions = []
    for r in res:
        logtime = r['_source']['logtime']
        value = r['_source']['basedis']
        id = r['_id']
        v2 = calcRank(value,logtime,stype,hostname,"+00:00")
        print logtime,value,v2,id
        action = {"_op_type":"update",
          "_index":"bimap-common-performance",
          "_type":stype,
          "_id":id,
          "doc":{ "baserank":v2
                }
          }
        actions.append(action)
    es=Elasticsearch(eshost,port=esport)
    a=helpers.bulk(es,actions)
    print a

#run code
#print '开始计算基础相似度'
#pool = multiprocessing.Pool(processes=10)
#pool.apply_async(calcAllSMDbyHost,('20161101',300,'nopplbds04','CPU_ALL'))
#pool.apply_async(calcAllSMDbyHost,('20161101',300,'nopplbds04','IO_ALL'))
#pool.apply_async(calcAllSMDbyHost,('20161101',300,'nopplbds03','CPU_ALL'))
#pool.apply_async(calcAllSMDbyHost,('20161101',300,'nopplbds03','IO_ALL'))
#pool.apply_async(calcAllSMDbyHost,('20160201',550,'NOVPLODS01','CPU_ALL'))
#pool.apply_async(calcAllSMDbyHost,('20160201',550,'NOVPLODS01','IO_ALL'))

#print '开始计算相似度范围'

#pool.apply_async(calcAllRank,('nopplbds03','CPU_ALL','2016-01-01T00:00:00',0,"+08:00"))
#pool.apply_async(calcAllRank,('nopplbds03','IO_ALL','2016-01-01T00:00:00',0,"+08:00"))
#pool.apply_async(calcAllRank,('nopplbds04','CPU_ALL','2016-01-01T00:00:00',0,"+08:00"))
#pool.apply_async(calcAllRank,('nopplbds04','IO_ALL','2016-01-01T00:00:00',0,"+08:00"))
#pool.apply_async(calcAllRank,('NOVPLODS01','CPU_ALL','2016-01-01T00:00:00',0,"+08:00"))
#pool.apply_async(calcAllRank,('NOVPLODS01','IO_ALL','2016-01-01T00:00:00',0,"+08:00"))
#pool.close()
#pool.join()

#calcAllRank('nopplbds03','CPU_ALL','2016-01-01T00:00:00',0,"+08:00")
#calcAllRank('nopplbds03','IO_ALL','2016-01-01T00:00:00',0,"+08:00")
#calcAllRank('nopplbds04','CPU_ALL','2016-01-01T00:00:00',0,"+08:00")
#calcAllRank('nopplbds04','IO_ALL','2016-01-01T00:00:00',0,"+08:00")
#calcAllRank('NOVPLODS01','CPU_ALL','2016-01-01T00:00:00',0,"+08:00")
#calcAllRank('NOVPLODS01','IO_ALL','2016-01-01T00:00:00',0,"+08:00")
############tmpcode上面是正在使用的代码,下面是之前的代码#######################

def getSimilaryBase(eshost,esport,esindex,starttime,range,host,estype=None):
    esm = esagg(eshost,esport)
    starttime = changeTime(starttime)
    qbody={
      "query": {
        "bool": {
          "must": [
            {"term": { "bimap_hostname": { "value": host } }},
            {"range": { "logtime": {
                "gte": starttime,
                "lte": "%s||%s" %(starttime,range),
                "format": "yyyy-MM-dd'T'HH:mm:ss"
              }
            }}
          ]
        }
      }
    }
    dlist = esm.readByQuery(esindex,qbody,type=estype)
    if not dlist:
        return {"s1":0,"s2":0,"record_count":0}
    res = []
    res2 = []
    for d in dlist:
        cpuall = d['_source']['user'] + d['_source']['sys']
        if  d['_source']['wait']:
            cpuall += d['_source']['wait']
        res.append( cpuall)
        res2.append(100)

    d = round(distance(res,res2),4)
    c = round(cos(res,res2),4)
    return {"s1":d,"s2":c,"record_count":len(dlist)}

def getSimilarByHost(hostname,startday,days):
    dt = datetime.datetime.strptime(startday,"%Y%m%d")
    reslist = []
    for d in range(days):
        calcdt = dt + datetime.timedelta(days=d)
        a= getSimilaryBase(['84.239.97.140'],9500,'bimap-sa-performance-*',calcdt.strftime("%Y-%m-%d %H:%M:%S"),'+1d',hostname,estype='CPU_ALL')
        #print a
        if a['record_count'] == 0:
            continue
        a["logtime"] = changeTime(calcdt.strftime("%Y-%m-%d %H:%M:%S"))
        a['type'] = 'day'
        a['bimap_hostname'] = hostname
        reslist.append(a)
        #计算每个小时的
        for i in range(24):
            ndi = dt + datetime.timedelta(hours = i)
            ndis = ndi.strftime("%Y-%m-%d %H:%M:%S")
            x= getSimilaryBase(['84.239.97.140'],9500,'bimap-sa-performance-*',ndis,'+1h',hostname,estype='CPU_ALL')
            if x['record_count']==0 :
                continue
            x["logtime"] = changeTime(ndi.strftime("%Y-%m-%d %H:%M:%S"))
            x["type"]= 'hour'
            x['bimap_hostname'] = hostname
            reslist.append(x)
        print calcdt.strftime("%Y-%m-%d %H:%M:%S")

    esm = esagg("84.239.97.140",9500)
    esm.write2Esbulk('bimap-common-performance','cpuall',reslist,addlogtime=False)

#getSimilarByHost('nopplbds04','20170101',1)
#print getSimilaryBase(['84.239.97.140'],9500,'bimap-sa-performance-*','2017-01-01 00:00:00','+1d','NOVPLODS01',estype='CPU_ALL')

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
