from flask import Flask, request, render_template, url_for
from flask_restx import Api
from flask_cors import CORS
from datetime import timedelta

import sqlite3
import os

from send_bid_mail import send_bid_mailing

from dotenv import load_dotenv
from nara.utils.err_handler import CustomValidException
from nara.utils.utils import errorMessage
# jwt
from flask_jwt_extended import JWTManager




app = Flask(__name__, template_folder=r'C:\work\NARA_CRAWL\templates', static_folder=r'C:\work\NARA_CRAWL\static')
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
app.config['DEBUG'] = os.getenv('DEBUG', default=False)
CORS(app, resources={r"/*": {"origins": ["http://192.168.0.17:3000", "http://localhost:3000"]}}, supports_credentials=True)
api = Api(app, title='bizbox api 문서', description='Swagger docs', doc="/docs")
jwt = JWTManager(app)

# 커스텀 예외 처리 사용 여부
app.config['PROPAGATE_EXCEPTIONS'] = True
# 서버 네임 설정
app.config['SERVER_NAME'] = '192.168.0.18:3001'

@app.errorhandler(CustomValidException)
def handle_custom_valid_exception(error):
    print("handle_custom_valid_exception")
    return errorMessage(error.status_code, error.message)


# DB 접속 경로
MAIN_DB_PATH = r"C:\work\NARA_CRAWL\nara\db\bizbox.db"
@app.route('/detail/<int:bid_id>')
def detail(bid_id):
    conn = sqlite3.connect(MAIN_DB_PATH)
    c = conn.cursor()

    # 상세 데이터 조회
    c.execute('''SELECT b.*, ba.area_name, ba.area_g_cd
                 FROM bid_notice b
                 LEFT JOIN bid_notice_area ba
                 ON b.np_idx = ba.np_idx
                 WHERE b.np_idx = ?''', (bid_id,))
    bid = c.fetchone()

    if not bid:
        return "Bid not found", 404

    bid_data = {
        'bid_id': bid[0],
        'industry_cd': bid[1],
        'bid_name': bid[3],
        'uniqueCd': bid[4],
        'bid_agency': bid[5],
        'area_name': bid[13],
        'bid_o_dt': bid[6],
        'bid_c_dt': bid[7],
        'amount': bid[8],
        'est_prise': bid[9],
        'budget': bid[10],
        'vat': bid[11]
    }
    print(bid_data)
    return render_template('biz_mail_detail.html', bid=bid_data)




jwt_blocklist = set()
@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    if request.endpoint == 'Sign_logout':
        print("토큰 파기")
        jti = jwt_payload['jti']
        print(jti)
        return jti in jwt_blocklist
    else:
        # 다른 요청에 대해서는 블록 리스트 확인하지 않음
        return False

# JWT 및 앱설정
app.config['JWT_SECRET_KEY'] = os.getenv("T_S_KEY")
app.config['SECRET_KEY'] = os.getenv("S_KEY")
access_exp = timedelta(minutes=1)
refresh_exp = timedelta(days=3)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = access_exp
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = refresh_exp

print(app.config)



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


# APScheduler 설정
scheduler = BackgroundScheduler()
# scheduler.add_job(func=send_bid_mailing, trigger="cron", minute=10)  # 매 시간 10분에 실행
# scheduler.add_job(func=send_bid_mailing, trigger=IntervalTrigger(seconds=10))  # 매 2시간마다 실행
scheduler.add_job(func=lambda: send_bid_mailing(app), trigger=CronTrigger(hour='0/2'))# 0시부터 24시까지

# 앱이 종료될 때 스케줄러를 종료합니다.


# app.before_request(lambda: send_bid_mailing(app))


# 넘겨주기 위한
initUrlFor = url_for

def test_send_bid_mailing(app, initUrlFor):
    with app.app_context():
        send_bid_mailing(app, initUrlFor)


# 스케줄러 시작
try:
    if __name__ == '__main__':
        test_send_bid_mailing(app, initUrlFor)
        scheduler.start()
        app.run(debug=False, use_reloader=False, port=3001, host='192.168.0.18')
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()

'''

스케줄러 2번 실행되는 문제 해결.
https://jakpentest.tistory.com/entry/Flask-Scheduling%EC%9D%B4-2%EB%B2%88-%EC%8B%A4%ED%96%89%EB%90%98%EB%8A%94-%ED%98%84%EC%83%81%EC%97%90-%EB%8C%80%ED%95%B4

'''



