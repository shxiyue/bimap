#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
计算login对应的logouttime
Notes:
    '''

from estool import esagg
import datetime
from elasticsearch import Elasticsearch
from elasticsearch import  helpers
import time
import argparse

eshost=['84.239.97.140']
esport=9500
loginindex='bimap-sa-login-*'


def gethostlist():
    '''获取hostname列表'''
    query={
      "size": 0,
      "aggs": { "NAME": { "terms": { "field": "bimap_hostname", "size": 1000 }}}
    }
    es = Elasticsearch(eshost,port=esport)
    res = es.search(index=loginindex,doc_type='loginbeat',body=query)
    hlist=[]
    for r in res["aggregations"]["NAME"]["buckets"]:
        hlist.append(r["key"])
    return hlist

#print gethostlist()

def getLogintime(hostname,device,logouttime,timezone='+00:00'):
    '''获取login 信息'''
    #根据logout的时间，查找最近的，相同设备号的登录记录
    q={
      "size": 1,
      "query": {
        "bool": {
          "must": [
            {"term": { "bimap_hostname": { "value": hostname} }},
            {"term": { "device.keyword": { "value": device} }},
            {"term": { "login_type_num": { "value": "7" } }},
            {"range": { "logtime": { "lte": logouttime,"time_zone":timezone}}}
          ]
        }
      },
      "sort": [
        {
          "logtime": { "order": "desc" }
        }
      ]
    }
    es = Elasticsearch(eshost,port=esport)
    res = es.search(index=loginindex,doc_type='loginbeat',body=q)
    if res['hits']['total'] > 0 :
        return res["hits"]["hits"][0]['_source']
    else:
        return None

#print getLogintime("NOVULOPF04","pts/6","2017-05-31T22:15:15||-8h")

def calcLogoutTime(hostname,starttm,timerange,taridx,tartype,timezone='+08:00'):
    '''根据主机名计算时间范围内的login信息'''
    querylogout={
      "query": {
        "bool": {
          "must": [
            {"term": { "bimap_hostname": { "value": hostname} }},
            {"term": { "login_type_num": { "value": 8} }},
            {"range":{"logtime":{"lte":starttm,"gte":"%s||%s"%(starttm,timerange),
                                 "time_zone":timezone}}}
          ]
        }
      }
    }
    #按照主机名获取指定时间段logout列表
    esm = esagg(eshost=eshost,esport=esport)
    res = esm.readByQuery(loginindex,querylogout,type='loginbeat')

    #排序
    res2 = sorted(res,key = lambda x:(x['_source']['logtime'],x['_source']['msec'],x['_source']['login_type_num']))
    lst =[]
    for r in res2:
        v={}
        #r['_source']['device'] = r['_source']['device'].replace('/','')

        if not r['_source']['device']:
            continue
        x = getLogintime(hostname,r['_source']['device'],r['_source']['logtime'])

        v['bimap_hostname'] = hostname
        v['bimap_hostip']= x['bimap_hostip']
        v['login_time'] = x['logtime']
        v['logout_time'] = r['_source']['logtime']
        v['device'] = r['_source']['device']
        v['login_user']= x['login_user']
        stime = datetime.datetime.strptime(v['login_time'],"%Y-%m-%dT%H:%M:%S.%fZ")
        otime = datetime.datetime.strptime(v['logout_time'],"%Y-%m-%dT%H:%M:%S.%fZ")

        v['stay_second'] = (otime-stime).seconds
        v['stay_day'] = (otime-stime).days
        action = {
            "_index":taridx,
            "_type":tartype,
            "_id": "%s_%s_%d:%dto%d:%d" %(v['bimap_hostname'],v['device'],x['epoch'],x['msec'], r['_source']['epoch'],r['_source']['msec']),
            "_source":v
        }
        lst.append(action)
    es= Elasticsearch(eshost,port =esport, maxsize = 5)
    a=helpers.bulk(es,lst)
    return lst

#print calcLogoutTime('NOVULOPF04',"2017-05-31T00:00:00","-1d","aa",'bb',timezone='+08:00')

def createLogin(args):
    for h in gethostlist():
        print 'Calculation %s...' % (h)
        tmp = calcLogoutTime(h,args.datetime,"-"+args.range,'bimap-common-linuxlogin','linuxlogin')
        print 'host:%s have %d logout'%(h,len(tmp))



def main():
    # create the top-level parser
    # 公共连接参数，并设置默认值
    parser = argparse.ArgumentParser()
    parser.add_argument('-datetime',
                        default=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                        help='format is yyyy-mm-ddThh:mm:ss,default is now')
    parser.add_argument('-range', default='1d', help='you can use <n>d,<n>h,<n>m;defautl 1d')
    parser.set_defaults(func=createLogin)

    args = parser.parse_args()

    args.func(args)

if __name__ == "__main__":
    main()
