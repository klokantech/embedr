#!/bin/sh
#
# This is unsupport sample deleting cache files script.
# So s3fs's local cache files(stats and objects) grow up,
# you need to delete these.
# This script deletes these files with total size limit
# by sorted atime of files.
# You can modify this script for your system.
#
# [Usage] script <bucket name> <cache path> <limit size> <sleep time>
#

func_usage()
{
  echo ""
  echo "Usage:  $1 <bucket name> <cache path> <limit size> <sleep time>"
  echo "        $1 -h"
  echo "Sample: $1 mybucket /tmp/s3fs/cache 1073741824"
  echo ""
  echo "  bucket name = bucket name which specified s3fs option"
  echo "  cache path  = cache directory path which specified by"
  echo "                use_cache s3fs option."
  echo "  limit size  = limit for total cache files size."
  echo "                specify by BYTE"
  echo ""
}

PRGNAME=`basename $0`

if [ "X$1" = "X-h" -o "X$1" = "X-H" ]; then
  func_usage $PRGNAME
  exit 0
fi
if [ "X$1" = "X" -o "X$2" = "X" -o "X$3" = "X" -o "X$4" = "X" ]; then
  func_usage $PRGNAME
  exit -1
fi

BUCKET=$1
CDIR=$2
LIMIT=$3
SLEEP_TIME=$4

FILES_CDIR=$CDIR/$BUCKET
STATS_CDIR=$CDIR/\.$BUCKET\.stat

while true; do
  #
  # Check total size
  #
  act_size=`du -sb $FILES_CDIR | awk '{print $1}'`
  
  if [ $LIMIT -ge $act_size ]; then
    sleep $SLEEP_TIME
  else
    #
    # Make file list by sorted access time
    #
    ALL_STATS_ATIMELIST=`find $STATS_CDIR -type f -exec echo -n {} \; -exec echo -n " " \; -exec stat -c %X {} \; | awk '{print $2"*"$1}' | sort`

    #
    # Remove loop
    #
    TMP_ATIME=0
    TMP_SIZE=0
    TMP_STATS=""
    TMP_CFILE=""
    
    for part in $ALL_STATS_ATIMELIST; do
      TMP_ATIME=`echo $part | sed 's/*/ /g' | awk '{print $1}'`
      TMP_STATS=`echo $part | sed 's/*/ /g' | awk '{print $2}'`
      TMP_CFILE=`echo $TMP_STATS | sed s/\.$BUCKET\.stat/$BUCKET/`
      TMP_SIZE=`stat -c %s $TMP_CFILE`
      
      if [ `stat -c %X $TMP_STATS` -eq $TMP_ATIME ]; then
        rm -f $TMP_STATS $TMP_CFILE > /dev/null 2>&1
        act_size=$(( $act_size - $TMP_SIZE ))
        
        if [ $LIMIT -ge $act_size  ]; then
          break
        fi
      fi
    done
  fi
done

#
# End
#
