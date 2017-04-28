# bimap 部署管理服务器使用说明

## 使用方法
1. 上传所有介质到部署服务器
2. 安装ansible
    - 使用yum,apt-get等安装ansible，或
    - 使用./depkit目录中的ansible-2.2.1.0-1.el7.noarch.rpm　for centos7安装，

## 配置文件 hostlist 说明
此文件是ansible的host文件，主要定义如下：
- [elk]  group ，elk服务器列表，每个host必须包含esname用于设定elasticSearch nodename,这个组里的主机将会部署elk基础组件
- [redis] group ,redis服务器列表，一台或多台主机，可以和elk group
    重叠，这个组里的主机将会部署redis
- [bimap] group ,无须修改，包含elk,redis group 
- [bimap:vars],bimap集群基础变量，如果希望制定特定elk,redis主机的端口，可在主机后单独指定
- [all:vars] 基础变量，定义
    - srcbasedir,通常是当前目录，部署时，会从此目录寻找安装介质和脚本
    - dirs,目标服务器的目录结构
    - bimapuser
    - homedir,目标系统的home目录路径，一般为/home
    - ansible_ssh_user 部署连接使用用户
    - ansible_ssh_pass
    - someVersion,各种组件的版本定义

## base-deploy.yml

usage:ansible-playbook -i hostlist base-deploy.yml
使用root用户，在目标机器
- create bimap user
- add bimap user to sudo list
- change system kernel parmas

## deploy.yml
ELK集群部署脚本

usage: ansible-playbook -i hostlist deploy.yml
功能:
- create bimap dirs
- put install kit(elasticsearch,kibana,logstash),and unzip
- put some config
- put redis and make


# tools说明

## scan-redis.py
Usage:scan-redis.py -c <count> -t <waittime> -h <redisServer> -p <port>
说明：循环监控redis keys大小

## fb-cfgen
根据配置文件动态生成多台主机的filebeat配置文件
