This folder holds files which are necessary to configure a IIIF server. Important information are included in the private installation protocol https://docs.google.com/document/d/1OK0WziJ2Z-_lAiBJcWxRazL5se27OQ7WUcqnpVRE7fg/edit#

*s3fs_delete_cache.sh*
It is a bash script which will periodically clean s3fs local cache. It is designed to run in the infinite loop. It should be started by supervisor on the IIIF server. 

Usage:  s3fs_delete_cache.sh <bucket name> <cache path> <limit size> <sleep time>
        s3fs_delete_cache.sh -h
Sample: s3fs_delete_cache.sh mybucket /tmp/s3fs/cache 1073741824 60

Where limit size is in bytes and sleep time is in seconds.
