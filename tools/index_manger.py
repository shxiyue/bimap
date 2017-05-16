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


def archiveindex(args):
    eshost = args.host.split(',')
    esport = args.port
    #eshost = ["84.239.97.140","84.239.97.141","84.239.97.142"]
    #esport = 9500
    esm = esagg(eshost,esport=esport)
    cfg = esm.readConfig(type='archivesetting')
    if args.view:
        for c in cfg:
            print '%s\t%s\t%d'\
            %(c['_source']['indexpattern'],c['_source']['method'],c['_source']['keep'])

    if not args.do:
        return

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

def export(args):
    eshost = args.host.split(',')
    print eshost
    esport = int(args.port)
    idx = args.index
    type = args.type
    fsize = args.filerow
    output = args.output

    esm = esagg(eshost,esport=esport)
    eflist = esm.exportIndex(idx,output,fsize,type)
    print 'export %s to %s is finish' %(idx,output)
    if args.tar:
        esm.tarfiles(eflist,output+'.tar.gz')
        for f in eflist:
            os.remove(f)


def importFiles(args):
    eshost = args.host.split(',')
    esport = int(args.port)
    file = args.file
    esm = esagg(eshost,esport=esport)
    esm.loadFiles(file)
    print '%s is load to ES' %(file)


def main():
    # create the top-level parser
    # 公共连接参数，并设置默认值
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', default="84.239.97.140,84.239.97.141,84.239.97.142", help='elasticsearch host')
    parser.add_argument('-port', default=9500,type=int, help='elasticsearch port')

    #添加子命令
    subparsers = parser.add_subparsers(title="subcommands",description="valid subcommands",help='sub-command help')
    # create the parser for the "archive" command
    # 归档
    parser_a = subparsers.add_parser('archive', help='archive help')
    parser_a.add_argument('-do',action='store_true',help='exec archive')
    parser_a.add_argument('-view',action='store_true',help='view archive config')
    parser_a.set_defaults(func=archiveindex)

    #export 设置
    # create the parser for the "export" command
    parser_b = subparsers.add_parser('export', help='export help')
    parser_b.add_argument('-index', required=True, help='elasticsearch index pattern')
    parser_b.add_argument('-type',  default=None,help='elasticsearch type,if not set ,return all type')
    parser_b.add_argument('-filerow',  default=50000,type=int,help='number rows per file,default is 50000')
    parser_b.add_argument('-output',  default='./export.json',help='output file name,default is export.json')
    parser_b.add_argument('-tar', action='store_true',default=False,help='defautl is close')
    parser_b.set_defaults(func=export)

    # create the parser for the "import" command
    parser_c = subparsers.add_parser('import', help='import help')
    parser_c.add_argument('-file', required=True, help='files')
    parser_c.set_defaults(func=importFiles)
    args = parser.parse_args()

    args.func(args)

if __name__ == "__main__":
    main()

