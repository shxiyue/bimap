#/usr/bin/bash
LS_HOME=/home/bimap/bimap/opt/logstash-5.3.0
EXEC_PATH=$LS_HOME
EXEC=logstash  
DAEMON=$EXEC_PATH/bin/$EXEC  
PID_FILE=/home/bimap/bimap/run
ServiceName='logstash 5.3.0'  
JAVA_HOME=/home/bimap/bimap/opt/jdk-1.8.0_111
LS_LOGDIR=/home/bimap/bimap/logs/logstash
CONF=/home/bimap/bimap/conf/logstash

. /etc/rc.d/init.d/functions


#base function
_help()
{
cat <<!

Usage
     logstash_init.sh <param> <logstash file>
exp
     sh logstash_init.sh -list
     sh logstash_init.sh -start cpuall 

Parameters of the usage:
     <param>:
     -init_confile Initialize the configuration file
     -list List all files can be processed 
     -start Start logstash
     -stop Stop logstash
     -restart Restart logstash
     -status Check logstash status
     -startall Start all logstash
     -stopall Stop all logstash
!

exit 21
}


_stop()  
{  
       echo "Stoping $ServiceName ..."  
       #ps aux | grep "$DAEMON" | kill -9 `awk '{print $2}'` >/dev/null 2>&1  
       cat $PID_FILE/logstash_$1.pid | xargs kill -TERM
       rm -f $PID_FILE/logstash_$1.pid  
       usleep 100  
       echo "Shutting down $ServiceName: [  successful  ]"  
}  
  
_start()
{  
       echo "Starting $ServiceName ..."  
       $DAEMON -f $CONF/$1 -l $LS_LOGDIR --path.settings $CONF/logstash_jvm/$1 > $LS_LOGDIR/logstash.stdout 2>$LS_LOGDIR/logstash.err &  
       sleep 5 
#       PID=`$JAVA_HOME/bin/jps | grep Main | grep -v grep | awk '{print $1}'` 
       PID=`ps -aux |grep "$LS_HOME"|grep -v grep |grep $1 |awk '{print $2}'`
       echo $PID> $PID_FILE/logstash_$1.pid 
       usleep 100  
       echo "Starting $ServiceName: [  successful  ]; pid is : $PID"  
}

  
_restart()  
{  
    _stop $1
    _start $1
} 

_mkdir()
{
u_Patch=$1
if [ ! -d ${u_Patch} ]
then
      #echo ${u_Patch}
    mkdir -p ${u_Patch}
    chmod -R 775 ${u_Patch}
    echo `date "+%Y/%m/%d %H:%M:%S"` "Create directory [${u_Patch}] successful"
else
    echo `date "+%Y/%m/%d %H:%M:%S"` "Directory [${u_Patch}] already exist"
fi
}



_cpfile()
{
src_file=$1
tgt_file=$2
 for file in `ls $1`
 do
   if [ -f $1"/"$file ]
   then cp $1/$file $2/$file
        echo `date "+%Y/%m/%d %H:%M:%S"` "copy file $1/$file to $2/$file"
   fi
 done
}

if [ ! -x $DAEMON ] ; then  
       echo "ERROR: $DAEMON not found"  
       exit 1  
fi 


if [ $1X = "-list"X ]
 then ls -l ${CONF}|grep '^d' |grep -v "logstash_jvm" |awk '{print $9}'
 else case $1 in
          -start)
          echo "start logstash"
             if [ -n $2 ];then
             lsarray=`echo ${@:2}`
             for i in ${lsarray[@]}
             do
               lsname=$i
               _start $lsname
               echo `date "+%Y/%m/%d %H:%M:%S"` "Start logstash filename=$lsname"
             done
             fi                
             ;;
          -stop)
          echo "stop logstash"
             if [ -n $2 ];then
             lsarray=`echo ${@:2}`
             for i in ${lsarray[@]}
             do
               lsname=$i
               _stop $lsname
               echo `date "+%Y/%m/%d %H:%M:%S"` "Stop logstash filename=$lsname"
             done
             fi 
             ;;
          -restart)
           echo "restart logstash"
             if [ -n $2 ];then
             lsarray=`echo ${@:2}`
             for i in ${lsarray[@]}
             do
               lsname=$i
               _restart $lsname
               echo `date "+%Y/%m/%d %H:%M:%S"` "Restart logstash filename=$lsname"
             done
             fi 
             ;;
          -status)
             echo "Check logstash status"
             if [ -n $2 ];then
             lsarray=`echo ${@:2}`
             for i in ${lsarray[@]}
             do 
               lsname=$i
             status -p $PID_FILE/logstash_$lsname.pid $DAEMON 
               echo `date "+%Y/%m/%d %H:%M:%S"` "Check logstash status filename=$lsname"
             done
             fi             
             ;;
          -startall)
             lsarray=`ls -l ${CONF} |grep '^d' |grep -v "logstash_jvm" |awk '{print $9}'|tr '\n' ' '`
             for i in ${lsarray[@]}
             do
               lsname=$i
               _start $lsname
               echo `date "+%Y/%m/%d %H:%M:%S"` "Start logstash filename=$lsname"
             done
             ;;
          -stopall)
             lsarray=`ls -l ${CONF} |grep '^d' |grep -v "logstash_jvm" |awk '{print $9}'|tr '\n' ' '`
             for i in ${lsarray[@]}
             do
               lsname=$i
               _stop $lsname
               echo `date "+%Y/%m/%d %H:%M:%S"` "Start logstash filename=$lsname"
             done    
             ;;
          -init_confile)
             filearray=`echo ${@:2}`
             for i in ${filearray[@]}
             do
             _mkdir ${CONF}/logstash_jvm/$i
             _cpfile $LS_HOME/config $CONF/logstash_jvm/$i
             done 
             ;;               
           *)
             echo `date "+%Y/%m/%d %H:%M:%S"` "Did not identify the parameters!"
             _help
             ;;
      esac
fi
