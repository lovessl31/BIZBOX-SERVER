#!/bin/bash
set -e

LOGFILE=/var/log/bizbox-service.log
ERRORLOGFILE=/var/log/bizbox-service-error.log

echo "Starting Gunicorn..." >> $LOGFILE
export PYTHONPATH=$PYTHONPATH:/var/www/bizbox-server

# Conda 초기화 스크립트 소스
echo "Sourcing conda.sh..." >> $LOGFILE
source /root/anaconda3/etc/profile.d/conda.sh || { echo 'Failed to source conda.sh' >> $ERRORLOGFILE; exit 1; }

# Conda 가상 환경 활성화
echo "Activating conda environment..." >> $LOGFILE
conda activate bizbox || { echo 'Failed to activate conda environment' >> $ERRORLOGFILE; exit 1; }

# Gunicorn 실행
echo "Starting Gunicorn with configuration..." >> $LOGFILE
cd /var/www/bizbox-server || { echo 'Failed to change directory to /var/www/bizbox-server' >> $ERRORLOGFILE; exit 1; }
/root/anaconda3/envs/bizbox/bin/gunicorn -c gunicorn_config.py nara:app >> $LOGFILE 2>> $ERRORLOGFILE || { echo 'Failed to start Gunicorn' >> $ERRORLOGFILE; exit 1; }

