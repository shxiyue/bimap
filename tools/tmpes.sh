index=.bimap
pt=?pretty
baseurl=http://84.239.97.140:9500
#url=$index/$type
#delete index
curl -XDELETE ${baseurl}/${index}/${pt}
# create index
curl -XPUT ${baseurl}/${index}/${pt}

body='{
  "source": {
    "index": "bimap-was-2017.05.02"
  },
  "dest": {
    "index": "bimap-sa-was-2017.05.02"
  }
}'

curl -POST ${baseurl}/reindex -d '$body'
