from estool import esagg
import datetime

from elasticsearch import Elasticsearch
from elasticsearch import  helpers





#connect to es
es= Elasticsearch(['84.239.97.140'],port =9500, maxsize = 5)
def getExecv(epoch,counter):
    query_audit_execv={
      "query": {
        "bool": {
          "must": [
            { "term": { "audit_counter.keyword": { "value": counter } } },
            { "term": { "audit_epoch.keyword": { "value": epoch } } },
            { "term": { "audit_type.keyword": { "value": "EXECVE" } } }
          ]
        }
      }
    }
    searchres=[]
    res = es.search(index="bimap-sa-audit*",body=query_audit_execv ,scroll='1m',size=10000)
    sid = res['_scroll_id']
    scroll_size = res['hits']['total']
    while (scroll_size > 0 ):
        for hit in res['hits']['hits']:
            if 'command' in hit['_source'].keys():
                searchres.append(hit['_source']['command'].rstrip())
        res = es.scroll(scroll_id=sid,scroll='1m')
        sid = res['_scroll_id']
        scroll_size = len(res['hits']['hits'])
    return searchres

#print getExecv("1496203667.448","713505")

def getSyscall(logintime,logouttime,tty):
    query_syscall={
      "query": {
        "bool": {
          "must": [
            {"term": { "tty": { "value": tty} }},
            {"term": { "audit_type.keyword": { "value": "SYSCALL" }}},
            {"range": {
              "logtime": {
                "gte": logintime,
                "lte": logouttime
              }
            }
            }
          ]
        }
      }
    }
    searchres=[]
    res = es.search(index="bimap-sa-audit*",body=query_syscall ,scroll='1m',size=10000)
    sid = res['_scroll_id']
    scroll_size = res['hits']['total']
    while (scroll_size > 0 ):
        for hit in res['hits']['hits']:
            searchres.append({"epoch":hit['_source']['audit_epoch'],"counter":hit['_source']['audit_counter'],"comm":hit['_source']['comm']})
        res = es.scroll(scroll_id=sid,scroll='1m')
        sid = res['_scroll_id']
        scroll_size = len(res['hits']['hits'])
    return searchres

#print getSyscall("2017-05-31T04:07:26.000Z","2017-05-31T04:20:14.000Z","pts5")


def getlogin():
    query_login={
      "query":{
        "bool": {
          "must": [
            {"range": { "login_time": { "gte": "now-2d/d", "lte": "now/d" } }},
            {"term": { "login_type_num": { "value": "7" } }},
            { "exists":{ "field":"logout_time"}}
          ]
        }
      }
    }
    searchres=[]
    res = es.search(index="bimap-sa-login*",body=query_login ,scroll='1m',size=10000)
    sid = res['_scroll_id']
    scroll_size = res['hits']['total']
    tm = {}
    while (scroll_size > 0 ):
        for hit in res['hits']['hits']:
            tm['login_time'] = hit['_source']['login_time']
            tm['logout_time'] = hit['_source']['logout_time']
            tm['tty'] = hit['_source']['device'].replace('/','')
            searchres.append(hit)
        res = es.scroll(scroll_id=sid,scroll='1m')
        sid = res['_scroll_id']
        scroll_size = len(res['hits']['hits'])
    return searchres

login= getlogin()
actions=[]
es.indices.create(index="bimap-common-userbehavior",ignore=400)
for l in login:
    record={}
    record['login_time'] = l['_source']['login_time']
    record['logout_time'] = l['_source']['logout_time']
    record['login_user'] = l['_source']['login_user']
    record['login_userid'] = l['_source']['login_userid']
    record['remote_ip'] = l['_source']['remote_ip']
    record['tty'] = l['_source']['device'].replace('/','')
    record['stay_second'] = l['_source']['stay_second']
    record['stay_day'] = l['_source']['stay_day']
    sc = getSyscall(l['_source']['login_time'],l['_source']['logout_time'],record['tty'])
    cmds=[]
    comms=[]
    for s in sc:
        cmd = getExecv(s['epoch'],s['counter'])
        cmds.append(' '.join(cmd))
        comms.append(s['comm'])
    record['cmdlist'] = cmds
    record['comms'] = comms
    action = {
      "_index":"bimap-common-userbehavior",
      "_type":"userbh",
      "_id":"%d.%d.%s"%(l['_source']['epoch'],l['_source']['msec'],l['_source']['device']),
      "_source":record
    }
    #print action
    actions.append(action)
    del record
    del action
print helpers.bulk(es,actions)
