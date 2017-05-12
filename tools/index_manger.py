#!/usr/bin/python
# -*- coding: UTF-8 -*-

from estool import esagg
import argparse
import os
import shutil

tmppath = "/tmp"
def mkdir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)


def archiveindex():
    eshost = ["84.239.97.140","84.239.97.141","84.239.97.142"]
    esport = 9500
    esm = esagg(eshost,esport=esport)
    cfg = esm.readConfig(type='archivesetting')
    for c in cfg:
        list = esm.getindex(c['_source']['indexpattern'])
        idxlist=list[:-c['_source']['keep']]
        for idx in idxlist:
            if c['_source']['method'] == 'delete':
                if c['_source']['backupPath']:
                    #临时文件目录
                    dstpath = os.path.join(tmppath,idx)
                    mkdir(dstpath)
                    #临时文件名
                    bf = os.path.join(tmppath, idx,idx+".json")
                    dstfiles = esm.exportIndex(idx,bf)
                    dstfile = os.path.join(c['_source']['backupPath'],idx+"tar.gz")
                    #生成压缩文件
                    esm.tarfiles(dstfiles,dstfile)
                    #清空临时文件
                    shutil.rmtree(dstpath)
                    print 'export index:%s' %(idx)
                msg=esm.delIndex(idx)
                print 'delete index %s' %(idx)

            elif c['_source']['method'] == 'agg':
                #计算logtime
                if c['_source']['logtime'] == 'srcidx':
                    datestr= idx[-10:].replace('.','-')
                elif c['_source']['logtime'] == 'auto':
                    datestr = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                #读取数据
                groupby= c['_source']['groupby'][:]
                agg= c['_source']['agg'][:]
                rs = esm.readagg(c['_source']['query'],idx,groupby,agg)
                #根据日期删除目标表数据
                esm.delByDate('bimap-test',datestr)
                af=c['_source']['addfield']
                af['logtime'] = datestr
                #写入数据到目标index
                esm.write2Esbulk(c['_source']['targetidx'],c['_source']['targettype'],rs,
                                 addlogtime=False,addfield=af)
                print '%s agg is finish' % (idx)
                esm.delIndex(idx)
                print '%s  is delete' % (idx)

def test():
    eshost = ["84.239.97.140","84.239.97.141","84.239.97.142"]
    esport = 9500
    esm = esagg(eshost,esport=esport)
    #esm.exportIndex('bimap-sa-vmware-2017.05.11','aa.json')
    esm.zipFile('aa.json')
    #esm.importIndex('aa.json')
#archiveindex()



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--archive", help="archive index by config", action="store_true")
    parser.add_argument("-e", "--export", help="export elasticsearch index", action="store_true")
    parser.add_argument("-l", "--load", help="load files to es index", action="store_true")

    args = parser.parse_args()
    if args.archive:
        print 'start archive index'
        archiveindex()
        print "archive index fiinish" 

if __name__ == "__main__":
    main()
