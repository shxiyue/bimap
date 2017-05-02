#!/usr/bin/python
# -*- coding: UTF-8 -*-

from elasticsearch import Elasticsearch
import sys
import time
import getopt

def readEsBySearch(query):
    es = Elasticsearch(["84.239.97.140","84.239.97.141","84.239.97.142"],port = 9500, maxsize = 20)
    qbody = {"query": {
                  "match": {
                      "program": "sshd"
                  }
             }
            }
    res = es.search(index="bimap-messages-2017.04*",body= qbody,scroll='1m',size=1000)
    print res['hits']['total']
    sid = res['_scroll_id']
    scroll_size = res['hits']['total']
    while (scroll_size > 0 ):
        #print 'scrolling...'
        res = es.scroll(scroll_id=sid,scroll='1m')
        sid = res['_scroll_id']
        scroll_size = len(res['hits']['hits'])
        for hit in res['hits']['hits']:
            print hit['_source']['msg']

readEsBySearch(0)
