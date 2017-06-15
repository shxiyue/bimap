#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
bimap elasticsearch 管理工具
Notes:
'''

from elasticsearch import Elasticsearch
import time
import getopt
from elasticsearch import  helpers
#from datetime import datetime


#global tmpr

def deleteByQuery(idx,dt):
    """按照日期删除索引数据"""
    es = Elasticsearch(eshost,port = esport, maxsize = 20)
    bd = { "query":{ "match":{ "logtime":dt } } }
    a=es.delete_by_query(index=idx,body=bd, ignore=404)


def deleteBySearch(idx,search):
    es = Elasticsearch(eshost,port = esport, maxsize = 20)
    a=es.delete_by_query(index=idx,body=search, ignore=404)

def deleteIndex(idx):
    es = Elasticsearch(eshost,port = esport, maxsize = 20)
    es.indices.delete(index=idx, ignore=[400,404])


def getindex(idx_pattern):
    """根据patter获取index列表"""
    es = Elasticsearch(eshost,port = esport, maxsize = 20)
    res = es.cat.indices(index=idx_pattern)
    #print res
    x = res.split('\n')
    list = []
    for a in x:
        if a:
            list.append(a.split()[2])
    return sorted(list)



def getdt(dt,dgree,tmpr,dts):
    #global tmpr
    dgree = dgree +1
    for x in dt[gb[dgree-1]]['buckets']:
        tmpr[dgree-1] = x['key']
        if dgree == len(gb):
            tmpr[dgree]=x['doc_count']
            if agg:
                for a in range(len(agg)):
                    tmpr[dgree+a+1]=x[agg[a]]['value']
            #print tmpr
            #t = tmpr[:]
            x= {}
            i = 0
            for fname in gb:
                x[fname] = tmpr[i]
                i = i+1
            x['count'] = tmpr[i]
            for fname in agg:
                i = i+1
                x[fname] = tmpr[i]
            dts.append(x)
            #dts.append(t)
        else:
            getdt(x,dgree,tmpr,dts)


def readavg(query,idx):
    """读取es汇总数据"""
    es = Elasticsearch(eshost,port = esport, maxsize = 20)
    res = es.search(index=idx,body= query,size= 10000,filter_path=['aggregations'])
    #tmpr = [0 for i in range(len(gb))]
    tmpr = [0,0,0,0,0,0,0]
    dts = []
    getdt(res['aggregations'],0,tmpr,dts)
    #for dt in dts:
    #    print dt
    return dts


def write2Es(idx,dts):
    """逐行写入es"""
    es = Elasticsearch(eshost,port = esport, maxsize = 20)
    es.indices.create(index=idx,ignore=400)
    for dt in dts:
        es.index(index=idx,doc_type="asaavg",body=dt)

def write2Esbulk(idx,type,dts,date):
    es = Elasticsearch(eshost,port = esport, maxsize = 20)
    """创建索引，已存在忽略400错误"""
    es.indices.create(index=idx,ignore=400)
    actions = []
    for dt in dts:
        #dt["avgdt"] = datetime.now()
        dt["logtime"] = date
        dt["bimap_hostname"] = '84.239.4.133'
        dt["bimap_hostip"] = '84.239.4.133'
        action = {"_index":idx,
                  "_type":type,
                  "_source":dt
                 }
        actions.append(action)
    helpers.bulk(es,actions)



## man ##
qbody= {
  "aggs": {
    "src_interface":{
      "terms": {"field": "src_interface.keyword","size": 100},
      "aggs": {
        "src_ip": {
          "terms": {"field": "src_ip.keyword","size": 10000}, "aggs": {
            "dst_interface": {
              "terms": {"field": "dst_interface.keyword","size": 100},
              "aggs": {
                "dst_ip": {
                  "terms": {"field": "dst_ip.keyword","size": 10000},
                  "aggs": {
                  "action": {
                    "terms": {"field": "action.keyword","size": 100},
                    "aggs": {"bytes": {"sum": {"field": "bytes"}}}
                  }
                }
                }
              }
            }
          }
        }
      }
    }
  }
}

eshost = ["84.239.97.140","84.239.97.141","84.239.97.142"]
esport = 9500
gb = ['src_interface','src_ip','dst_interface','dst_ip','action']
agg = ['bytes']
#获取对应index列表
ls = getindex('bimap-ciscoasa*')
#剔除最后两天的数据
ls.pop()
ls.pop()
for i in ls:
    #计算yyyy-mm-dd格式的日期
    date = i[-10:].replace('.','-')
    #读取数据
    rs = readavg(qbody,i)
    #删除数据
    deleteByQuery('bimap-agg-asa',date)
    # write2Es(targetindex,rs)
    write2Esbulk('bimap-agg-asa','avgasa',rs, date)
    print '%s agg is finish' % (date)
    deleteIndex(i)
    print '%s  is delete' % (date)

"""
dasa6={
  "query": {
     "match": { "severity": 6 }
  }
}
"""
