# curl -DELETE http://84.239.97.140:9500/_template/bimap
curl -PUT http://84.239.97.140:9500/_template/bimap -d '
{
  "template" : "bimap-*",
  "version" : 50001,
  "settings" : {
    "index.refresh_interval" : "5s"
  },
  "mappings" : {
    "_default_" : {
      "_all" : {"enabled" : true, "norms" : false},
      "dynamic_templates" : [ {
        "message_field" : {
          "path_match" : "message",
          "match_mapping_type" : "string",
          "mapping" : {
            "type" : "text",
            "norms" : false
          }
        }
      }, {
        "string_fields" : {
          "match" : "*",
          "match_mapping_type" : "string",
          "mapping" : {
            "type" : "text", "norms" : false,
            "fields" : {
              "keyword" : { "type": "keyword" }
            }
          }
        }
      } ],
      "properties" : {
        "@timestamp": { "type": "date", "include_in_all": false },
        "logtime": { "type": "date", "include_in_all": false },
        "bimap_hostname":{"type":"text","include_in_all": false },
        "bimap_hostip":{"type":"ip","include_in_all": false },
        "@version": { "type": "keyword", "include_in_all": false },
        "geoip"  : {
          "dynamic": true,
          "properties" : {
            "ip": { "type": "ip" },
            "location" : { "type" : "geo_point" },
            "latitude" : { "type" : "half_float" },
            "longitude" : { "type" : "half_float" }
          }
        }
      }
    }
  }
}
'
