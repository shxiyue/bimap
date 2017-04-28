#!/usr/bin/python
# -*- coding: UTF-8 -*-

import redis
import sys
import time
import getopt

def usage():
    print ("Usage:%s -c <count> -t <waittime> -h <redisServer> -p <port> " % (sys.argv[0]))

def scanRedis(server,port):
    pass

def loopscan(count,wtime,server,port):
    r = redis.Redis(host=server,port=port, db=0)
    for i in range(count):
        keylist = r.keys()
        ds = r.dbsize()
        for k in r.keys():
            print ds, k, r.llen(k)
        #scanRedis(server,port)
        time.sleep(wtime)


def main(argv):
    try:
        opts, args = getopt.getopt(argv,"c:t:h:p:")
    except getopt.GetoptError:
        print usage()
        sys.exit(2)
    count = 1
    wtime = 1
    server = '127.0.0.1'
    port = 6379

    for opt, arg in opts:
        if opt == '-c':
            count = int(arg)
        elif opt == '-t':
            wtime = int(arg)
        elif opt == '-h':
            server = arg
        elif opt == '-p':
            port = int(arg)
        else:
            print usage()
            sys.exit(1)
    loopscan(count,wtime,server,port)

if __name__ == "__main__":
    main(sys.argv[1:])
