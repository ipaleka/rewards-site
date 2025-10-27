#!/bin/bash
if [ -f /var/run/reboot-required ]; then
    echo "A reboot is required following updates to server `hostname`" | mail -s "Reboot Required" root
fi
