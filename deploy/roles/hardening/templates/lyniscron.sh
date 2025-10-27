#!/bin/sh
PERFORM_DIFF=0
DIFF_FILE={{ opt_folder }}lynis-diff-report.txt
# Step 1: Archive file
if [ -f /var/log/lynis-report.dat ]; then
     sudo cp /var/log/lynis-report.dat /var/log/lynis-report-previous.dat
     PERFORM_DIFF=1
fi
if [ -f ${DIFF_FILE} ]; then
     rm ${DIFF_FILE}
fi
# Step 2: Here you run Lynis (e.g. as a cron job)
cd {{ opt_folder }}lynis
sudo nice -n19 ./lynis --cronjob
# Step 3: Perform the difference (unless it is the first time)
if [ ${PERFORM_DIFF} -eq 1 ]; then
    DIFFERENCES=`sudo diff --ignore-matching-lines report_datetime /var/log/lynis-report.dat /var/log/lynis-report-previous.dat`
    if [ $? -gt 0 ]; then
        echo "Found differences:" > ${DIFF_FILE}
        echo "===========================================================================" >> ${DIFF_FILE}
        sudo diff --ignore-matching-lines -y /var/log/lynis-report-previous.dat /var/log/lynis-report.dat | grep -v "report_datetime" >> ${DIFF_FILE}
        echo "===========================================================================" >> ${DIFF_FILE}
        mail -s 'Daily lynis diff report' -r lynis@`uname -n` {{ admin_email }} < ${DIFF_FILE}
    fi
fi
