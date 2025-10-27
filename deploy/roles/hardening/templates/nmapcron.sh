#!/bin/sh
TARGETS="localhost"
OPTIONS="-v -T4 -F -sV"
date=`date +%F`
cd {{ opt_folder }}nmap-scans
nice -n19 nmap $OPTIONS $TARGETS -oA scan-$date > /dev/null
if [ -e scan-prev.xml ]; then
        ndiff scan-prev.xml scan-$date.xml > diff-$date
        sed -i '/scan initiated/d' diff-$date
        if [ -s diff-$date ]
        then
            mail -s 'Daily nmap diff report' -r nmap@`uname -n` {{ admin_email }} < {{ opt_folder }}nmap-scans/diff-$date
        fi
fi
ln -sf scan-$date.xml scan-prev.xml
