# scheduler.py
import time
import os
import sys
from nara import app
from flask import url_for
from nara.send_bid_mail import send_bid_mailing
from nara.crawl.nara_crawl_sorce import crawl_and_process
from dotenv import load_dotenv


load_dotenv()
if os.getenv('APP_ENV') == "dev":
    prj_loot = os.getenv("DEV_PJ_ROOT")
else:
    prj_loot = os.getenv('PROJECT_ROOT')


print("############################################")
print(prj_loot)
print("############################################")


# sys.path에 프로젝트 루트 디렉토리 추가

if prj_loot not in sys.path:
    print("경로:", prj_loot)
    sys.path.append(os.path.abspath(prj_loot))


# 백그라운드 작업 스케줄러
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger



# 예제 작업 정의
def your_job_function():
    print("작업이 실행되었습니다!")

initUrlFor = url_for

# 래퍼 함수 정의
def send_bid_mailing_wrapper():
    try:
        print("Sending bid mailing...")
        send_bid_mailing(app, initUrlFor)
        print("Bid mailing sent successfully.")
    except Exception as e:
        print(f"Error sending bid mailing: {e}")

# APScheduler 설정
scheduler = BackgroundScheduler()
scheduler.add_job(func=send_bid_mailing_wrapper, trigger=CronTrigger(hour='0/2')) # 0시부터 24시까지
scheduler.add_job(func=crawl_and_process, trigger=CronTrigger(minute='30'))
scheduler.start()


try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
