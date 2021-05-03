#!/bin/sh

$RILEC_HOME=$HOME

${RILEC_HOME}/get_siemens_logs.sh 2> /dev/null > /dev/null
${RILEC_HOME}/siemens-spica-rilec/siemens_to_spool.py
today=$(date --iso)
${RILEC_HOME}/siemens-spica-rilec/add_fix.py --time "${today} 23:00" --type "odhod" ${RILEC_HOME}/spool/023*/fixes.csv
${RILEC_HOME}/siemens-spica-rilec/fix_events.py
${RILEC_HOME}/siemens-spica-rilec/spool_to_spica.py --commit
# ${RILEC_HOME}/siemens-spica-rilec/spool_to_spica.py
