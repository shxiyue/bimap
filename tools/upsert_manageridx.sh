index=.bimap
pt=?pretty
baseurl=http://84.239.97.140:9500
#url=$index/$type
#delete index
curl -XDELETE ${baseurl}/${index}/${pt}

# create index
curl -XPUT ${baseurl}/${index}/${pt}

type=ipmap
# create test data
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"ip":"84.238.4.133","env":"TEST", "system":"base","devicetype":" firewall","memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"ip":"84.238.29.161","env":"TEST", "system":"OPF","devicetype":"was server","memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"ip":"84.239.87.9","env":"TEST", "system":"base","devicetype":"esxi","memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"ip":"84.239.87.43","env":"TEST", "system":"base","devicetype":"esxi","memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"ip":"84.239.87.42","env":"TEST", "system":"base","devicetype":"esxi","memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"ip":"84.239.87.17","env":"TEST", "system":"base","devicetype":"esxi","memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"ip":"84.239.87.18","env":"TEST", "system":"base","devicetype":"esxi","memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"ip":"84.239.87.44","env":"TEST", "system":"base","devicetype":"esxi","memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"ip":"84.238.35.1","env":"TEST", "system":"base","devicetype":"switch","memo":""}'     

type=archivesetting
# 删除类归档
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"indexpattern":"bimap-was*","method":"delete" ,"backupPath":"/data/backupindex",          "keep":7,"memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"indexpattern":"bimap-vmware-*","method":"delete", "backupPath":"/data/backupindex",   "keep":1,"memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"indexpattern":"bimap-sa-was-*","method":"delete", "backupPath":"/data/backupindex",   "keep":7,"memo":""}'     
curl -XPOST ${baseurl}/${index}/${type}${pt} -d '{"indexpattern":"bimap-sa-vmware-*","method":"delete", "backupPath":"/data/backupindex",   "keep":7,"memo":""}'     
#汇总类归档

curl -XPOST ${baseurl}/${index}/${type}${pt} -d '
{
  "addfield": {
    "bimap_hostip": "84.238.4.133",
    "bimap_hostname": "84.238.4.133"
  },
  "agg": [
    "bytes"
  ],
  "groupby": [
    "src_interface",
    "src_ip",
    "dst_interface",
    "dst_ip",
    "action"
  ],
  "indexpattern": "bimap-sa-asa*",
  "keep": 1,
  "logtime": "srcidx",
  "memo": "",
  "method": "agg",
  "query": {
    "aggs": {
      "src_interface": {
        "aggs": {
          "src_ip": {
            "aggs": {
              "dst_interface": {
                "aggs": {
                  "dst_ip": {
                    "aggs": {
                      "action": {
                        "aggs": {
                          "bytes": {
                            "sum": {
                              "field": "bytes"
                            }
                          }
                        },
                        "terms": {
                          "field": "action.keyword",
                          "size": 100
                        }
                      }
                    },
                    "terms": {
                      "field": "dst_ip.keyword",
                      "size": 10000
                    }
                  }
                },
                "terms": {
                  "field": "dst_interface.keyword",
                  "size": 100
                }
              }
            },
            "terms": {
              "field": "src_ip.keyword",
              "size": 10000
            }
          }
        },
        "terms": {
          "field": "src_interface.keyword",
          "size": 100
        }
      }
    }
  },
  "targetidx": "bimap-agg-asa",
  "targettype": "aggasa"
}'
#{"indexpattern":"bimap-sa-asa*","method":"agg", "targetidx":"bimap-test-asa","keep":2,"addfield":{"bimap_hostname":"84.238.4.133","bimap_hostip":"84.238.4.133"},"logtime":"srcidx","memo":"",
#"query": {
#  "aggs": {
#    "src_interface":{
#      "terms": {"field": "src_interface.keyword","size": 100},
#      "aggs": {
#        "src_ip": {
#          "terms": {"field": "src_ip.keyword","size": 10000}, "aggs": {
#            "dst_interface": {
#              "terms": {"field": "dst_interface.keyword","size": 100},
#              "aggs": {
#                "dst_ip": {
#                  "terms": {"field": "dst_ip.keyword","size": 10000},
#                  "aggs": {
#                  "action": {
#                    "terms": {"field": "action.keyword","size": 100},
#                    "aggs": {"bytes": {"sum": {"field": "bytes"}}}
#                  }
#                }
#                }
#              }
#            }
#          }
#        }
#      }
#    }
#  }
#},
#"groupby":["src_interface","src_ip","dst_interface","dst_ip","action"],
#"agg":["bytes"],
#"targettype":"aggasa"
#}' 

