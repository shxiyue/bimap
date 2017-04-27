#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''自动生成filebeat配置文件
根据配置文件
    config,format(ip,filepath,type)
    template,filebeat.yml
example:
    >>> fb-cfgen.py -c <configfile> -t <templatefile> -o <outputdir>
    -c default is config
    -t default is filebeat.yml
    -o default is outout
# @Date : 20170420
# @Author:wudi
# @version:1.0
'''

import yaml
import getopt
import sys
import os

def readconfig(confiFile):
    if not os.path.exists(confiFile):
        sys.exit(1)
        print '%s is not exists' % (confiFile)
    f = open(confiFile)
    cfg = f.readlines()
    dict =[]
    for line in cfg:
        line = line.strip('\n')
        dt = line.split(',')
        dt2= {'ip':dt[0],'file':dt[1],'type':dt[2]}
        dict.append(dt2)
    dict2 = sorted(dict, key = lambda x:x['ip'])
    f.close()
    return dict2

def mkyaml(cfgfile,template,odir):
    #read templatefile
    if not os.path.exists(template):
        print '%s is not exists' % (template)
        sys.exit(1)
    tplfile = open(template)
    try:
        tpl = yaml.load(tplfile)
    except Exception, e:
        print str(e)
        sys.exit(1)

    # make prospectors
    cfgs = readconfig(cfgfile)
    ymls = []
    # [{'ip':84.239.99.6,'filebeat.prospectors':[]}]
    yml ={'ip':'','filebeat.prospectors':[]}
    tmyml = {}
    for cfg in cfgs:
        # ip change
        if yml['ip'] != cfg['ip']:
            # if have data
            if yml['filebeat.prospectors']:
                ymls.append(yml)
                yml ={'ip':'','filebeat.prospectors':[]}
                tmyml = {'input_type':'log','paths':cfg['file'],'document_type':cfg['type']}
                yml['ip'] = cfg['ip']
                yml['filebeat.prospectors'].append(tmyml)
            else:
                tmyml = {'input_type':'log','paths':cfg['file'],'document_type':cfg['type']}
                yml['filebeat.prospectors'].append(tmyml)
                yml['ip'] = cfg['ip']
        else:
            tmyml = {'input_type':'log','paths':cfg['file'],'document_type':cfg['type']}
            yml['filebeat.prospectors'].append(tmyml)
    ymls.append(yml)
    for a in ymls:
        tfilenm = '%s.yml' % (os.path.join(odir, a['ip']))
        w = open(tfilenm, 'w')
        #a['fields'] = {'host':a['ip'],'review':1,'level':'debug'}
        #a['output.redis'] = {'hosts':'84.239.97.140','key':'bimap'}
        tpl['fields']['host'] = a['ip']
        tpl['output.redis']['key'] = "bimap_%{[type]:fallback}"
        a.pop('ip',None)
        c = dict(a, **tpl)
        yaml.dump(c,w,default_flow_style = False)
        w.close()
        print '%s is create' % (tfilenm)


#mkyaml()
def usage():
    print ("Usage:%s -c <configfile> -t <templateFile> -o <outputdir>" % (sys.argv[0]))

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"c:t:o:")
    except getopt.GetoptError:
        print usage()
        sys.exit(2)
    cfgfile = 'config'
    tfile = 'filebeat.yml'
    odir = 'output'

    for opt, arg in opts:
        if opt == '-c':
            cfgfile = arg
        elif opt == '-t':
            tfile = arg
        elif opt == '-o':
            odir = arg
            if not os.path.exists(odir):
                os.mkdir(odir)
        else:
            print usage()
            sys.exit(1)

    print 'config file use:%s\ntemplate file use:%s'%(cfgfile,tfile)
    mkyaml(cfgfile, tfile, odir)

if __name__ == "__main__":
    main(sys.argv[1:])
