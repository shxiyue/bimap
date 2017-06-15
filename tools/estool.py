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
import json
import gzip
import StringIO
import multiprocessing
import os
import tarfile
#from datetime import datetime

def readFile2ES(fname,eshost,esport):
    es = Elasticsearch(eshost,port =esport, maxsize = 5)
    actions = []
    f = open(fname,'rU')
    buffsize = 10000
    i = 0
    while 1:
        line = f.readline()
        if line:
            dt=json.loads(line)
            actions.append(dt)
            i += 1
            if i== buffsize:
                helpers.bulk(es,actions)
                i = 0
                del actions[:]
        else:
            break
    a=helpers.bulk(es,actions)
    f.close()


class esagg:
    def __init__(self, eshost='localhost', esport= 9200):
        self._eshost = eshost
        self._esport = esport
        self._connect()

    def __del__(self):
        pass

    def _connect(self):
        """连接es"""
        self.__es = Elasticsearch(self._eshost,port =self._esport, maxsize = 5)


    def zipFile(self,fname):
        """使用gzip压缩文件"""
        g = gzip.GzipFile(filename="", mode="wb", compresslevel=5,
                              fileobj=open(fname+'.gz', 'wb'))
        g.write(open(fname).read())
        g.close()

    def unzipFile(self,fname,tarfname):
        """使用gzip解压文件"""
        g = gzip.GzipFile(mode="rb", fileobj=open(fname, 'rb'))
        open(tarfname, "wb").write(g.read())


    def tarfiles(self,filelist,tarnm):
        """使用tar压缩文件"""
        tar = tarfile.open(tarnm,"w:gz")
        for f in filelist:
            tar.add(f)
        tar.close()

    def unzipTar(self,fname,dstpath):
        """解压tar.gz"""
        tar = tarfile.open(fname,"r:gz")
        for f in tar.getnames():
            tar.extract(f,dstpath)
        tar.close()

    def readConfig(self,type,index='.bimap'):
        """读取.bimap配置"""
        qbody={ "query": { "match_all": {} } }
        res = self.__es.search(index=index,doc_type=type,body=
                               qbody,scroll='1m',size=1000)
        sid = res['_scroll_id']
        scroll_size = res['hits']['total']
        cfglist=[]
        while (scroll_size > 0 ):
            cfglist.extend(res['hits']['hits'])
            res = self.__es.scroll(scroll_id=sid,scroll='1m')
            sid = res['_scroll_id']
            scroll_size = len(res['hits']['hits'])
        return cfglist


    def readByTimeRange(self,index,starttime,dtrange,type=None):
        searchres=[]
        endtime  = '%s||%s' %(starttime,dtrange)
        qbody= {"query": {
                  "range": {
                    "logtime":{ "gt": starttime,
                                "lt": endtime,
                                "format": "yyyy-MM-dd HH:mm:ss"
                     }
                   }
                 }
                 , "sort": [ { "logtime": { "order": "asc" } } ]
        }
        res = self.__es.search(index=index,doc_type=type,body=
                               qbody,scroll='1m',size=10000)
        sid = res['_scroll_id']
        scroll_size = res['hits']['total']
        while (scroll_size > 0 ):
            for hit in res['hits']['hits']:
                searchres.append(hit)
            res = self.__es.scroll(scroll_id=sid,scroll='1m')
            sid = res['_scroll_id']
            scroll_size = len(res['hits']['hits'])
        return searchres

    def readByQuery(self,index,qbody,type=None):
        searchres=[]
        #qbody= {"query": {
        #          "match_all": {}
        #         }
        #}
        res = self.__es.search(index=index,doc_type=type,body=
                               qbody,scroll='1m',size=10000)
        sid = res['_scroll_id']
        scroll_size = res['hits']['total']
        while (scroll_size > 0 ):
            for hit in res['hits']['hits']:
                searchres.append(hit)
            res = self.__es.scroll(scroll_id=sid,scroll='1m')
            sid = res['_scroll_id']
            scroll_size = len(res['hits']['hits'])
        return searchres

    def exportIndex(self,index,fname,filesize=50000,type=None):
        """export index数据到文件"""
        dstfiles=[]
        qbody={ "query": { "match_all": {} } }
        res = self.__es.search(index=index,doc_type=type,body=
                               qbody,scroll='1m',size=10000)
        sid = res['_scroll_id']
        scroll_size = res['hits']['total']
        i = 0
        j = 1
        f = open(fname,'w')
        dstfiles.append(fname)
        while (scroll_size > 0 ):
            for hit in res['hits']['hits']:
                json.dump(hit,f)
                f.write('\n')
                i += 1
                if i==filesize:
                    f.close()
                    dstfiles.append(fname+'.'+str(j))
                    f=open(fname+'.'+str(j),'w')
                    j += 1
                    i = 0
            res = self.__es.scroll(scroll_id=sid,scroll='1m')
            sid = res['_scroll_id']
            scroll_size = len(res['hits']['hits'])
        f.close()
        return dstfiles

    def loadFile(self,fname):
        readFile2ES(fname,self._eshost,self._esport)


    def loadFiles(self,fname):
        d,f=os.path.split(fname)
        flst=[]
        for lists in os.listdir(d):
            if lists.find(f)==0:
                flst.append(lists)
        print flst
        pool = multiprocessing.Pool(processes=5)
        for f in flst:
            fullfm=os.path.join(d,f)
            print fullfm
            pool.apply_async(readFile2ES,(fullfm,self._eshost,self._esport))
        pool.close()
        pool.join()

    def delByDate(self,idx, dt,datefield='logtime'):
        """按照日期删除索引数据"""
        bd = { "query":{ "match":{ datefield:dt } } }
        return self.__es.delete_by_query(index=idx,body=bd, ignore=404, timeout='5m')


    def delBySearch(self,idx,search):
        return self.__es.delete_by_query(index=idx,body=search, ignore=404)


    def delIndex(self,idx):
        return self.__es.indices.delete(index=idx, ignore=[400,404])


    def getindex(self,idx_pattern):
        """根据patter获取index列表"""
        res = self.__es.cat.indices(index=idx_pattern)
        x = res.split('\n')
        list = []
        for a in x:
            if a:
                list.append(a.split()[2])
        return sorted(list)


    def __getagg(self,dt,dgree,gb,agg,tmpr,dts):
        """递归实现,解析es agg api data"""
        dgree = dgree +1
        for x in dt[gb[dgree-1]]['buckets']:
            tmpr[dgree-1] = x['key']
            if dgree == len(gb):
                tmpr[dgree]=x['doc_count']
                if agg:
                    for a in range(len(agg)):
                        tmpr[dgree+a+1]=x[agg[a]]['value']
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
            else:
                self.__getagg(x,dgree,gb,agg,tmpr,dts)


    def readagg(self, query,idx,gropuby,agg):
        """读取es汇总数据"""
        res = self.__es.search(index=idx,body= query,size= 10000,filter_path=['aggregations'])
        tmpr = [0 for i in range(len(gropuby)+len(agg)+1)]
        dts = []
        self.__getagg(res['aggregations'],0,gropuby,agg,tmpr,dts)
        return dts


    def write2Es(self,idx,type,dts):
        """逐行写入es"""
        self.__es.indices.create(index=idx,ignore=400)
        for dt in dts:
            self.__es.index(index=idx,doc_type=type,body=dt)


    def write2Esbulk(self,idx,type,dts,addlogtime=True,addfield={}):
        """创建索引，已存在忽略400错误"""
        self.__es.indices.create(index=idx,ignore=400)
        actions = []
        for dt in dts:
            dtmerge = dict(dt, **addfield)
            if addlogtime:
                dt["logtime"] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            action = {"_index":idx,
                      "_type":type,
                      "_source":dtmerge
                     }
            actions.append(action)
        helpers.bulk(self.__es,actions)




"""
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
esm = esagg(eshost,esport=esport)
esm.readConfig('archivesetting')
ls = esm.getindex('bimap-sa-asa*')
print ls
#剔除最后两天的数据
#ls.pop()
#ls.pop()
for i in ls:
    #计算yyyy-mm-dd格式的日期
    date = i[-10:].replace('.','-')
    #读取数据

    rs = esm.readagg(qbody,i,gb,agg)
    #删除数据
    esm.delByDate('bimap-test',date)
    # write2Es(targetindex,rs)
    af={"bimap_hostname":"84.238.4.133","bimap_hostip":"84.238.4.133","logtime":date}
    esm.write2Esbulk('bimap-test','avgasa',rs, af)
    print '%s agg is finish' % (date)
    #esm.delIndex(i)
    #print '%s  is delete' % (date)
"""
