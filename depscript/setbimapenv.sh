export BIMAP_HOME={{homedir}}/{{bimapuser}}/bimap
export KIBANA_HOME={{homedir}}/{{bimapuser}}/bimap/opt/kibana-{{elkVersion}}
export ES_HOME={{homedir}}/{{bimapuser}}/bimap/opt/elasticsearch-{{elkVersion}}
export LOGSTASH_HOME={{homedir}}/{{bimapuser}}/bimap/opt/logstash-{{elkVersion}}
export JAVA_HOME={{homedir}}/{{bimapuser}}/bimap/opt/jdk-{{jdkVersion}}
export NODE_HOME={{homedir}}/{{bimapuser}}/bimap/opt/node-{{nodeVersion}}
export REDIS_HOME={{homedir}}/{{bimapuser}}/bimap/opt/redis-{{redisVersion}}/src

export PATH=$JAVA_HOME/bin:$ES_HOME/bin:$KIBANA_HOME/bin:$BIMAP_HOME/bin:$LOGSTASH_HOME/bin:$NODE_HOME/bin:$REDIS_HOME:$PATH
