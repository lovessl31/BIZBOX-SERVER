from flask import Flask, request
from flask_restx import Api
from flask_cors import CORS
from datetime import timedelta
import os
from dotenv import load_dotenv
from nara.utils.err_handler import CustomValidException
from nara.utils.utils import errorMessage


app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
app.config['DEBUG'] = os.getenv('DEBUG', default=False)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
api = Api(app, title='bizbox api 문서', description='Swagger docs', doc="/docs")


app.config['PROPAGATE_EXCEPTIONS'] = True

@app.errorhandler(CustomValidException)
def handle_custom_valid_exception(error):
    print("handle_custom_valid_exception")
    return errorMessage(error.status_code, error.message)


# 세션 쿠키의 만료 시간 설정
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# app.config['SESSION_COOKIE_SAMESITE'] = 'None'
# app.config['SESSION_COOKIE_DOMAIN'] = '192.168.0.17:3000'

from nara.routes.sign import sign_api
from nara.routes.add_industry import bid_api

# 네임 스페이스 api 연결
api.add_namespace(sign_api)
api.add_namespace(bid_api)

# 백그라운드 작업 스케줄러
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import atexit

def test():
    print(test)

# APScheduler 설정
scheduler = BackgroundScheduler()
# scheduler.add_job(func=test, trigger="cron", minute=10)  # 매 시간 10분에 실행
# scheduler.add_job(func=test, trigger=IntervalTrigger(seconds=10))  # 매 2시간마다 실행
scheduler.add_job(func=test, trigger=CronTrigger(hour='0/2'))# 0시부터 24시까지

# 앱이 종료될 때 스케줄러를 종료합니다.

# 스케줄러 시작
try:
    if __name__ == '__main__':
        scheduler.start()
        # app.run(debug=True, port=3001, host='192.168.0.18', ssl_context=('cert.pem', 'key.pem'))
        app.run(debug=False, use_reloader=False, port=3001, host='192.168.0.18')
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()

'''

스케줄러 2번 실행되는 문제 해결.
https://jakpentest.tistory.com/entry/Flask-Scheduling%EC%9D%B4-2%EB%B2%88-%EC%8B%A4%ED%96%89%EB%90%98%EB%8A%94-%ED%98%84%EC%83%81%EC%97%90-%EB%8C%80%ED%95%B4

'''



