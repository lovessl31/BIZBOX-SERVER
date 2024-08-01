#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/var/www/bizbox-server

# Conda 초기화 스크립트 소스
source ~/anaconda3/etc/profile.d/conda.sh

# Conda 가상 환경 활성화
conda activate bizbox

# Gunicorn 실행
cd /var/www/bizbox-server
$(which gunicorn) -c gunicorn_config.py nara:app

