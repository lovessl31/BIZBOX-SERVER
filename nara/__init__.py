from flask import Flask, request, render_template
from flask_restx import Api
from flask_cors import CORS

import sqlite3
import os

from nara.send_bid_mail import send_bid_mailing
from nara.crawl.nara_crawl_sorce import crawl_and_process
from dotenv import load_dotenv
from nara.utils.err_handler import CustomValidException
from nara.utils.utils import errorMessage
# jwt
from flask_jwt_extended import JWTManager
# config
from config import get_config




load_dotenv()

if os.getenv('APP_ENV') == 'prod':
    prj_loot = os.getenv("PROJECT_ROOT")
else:
    prj_loot = os.getenv("DEV_PJ_ROOT")

# sys.path에 프로젝트 루트 디렉토리 추가
import sys
if prj_loot not in sys.path:
    print("경로:", prj_loot)
    sys.path.append(os.path.abspath(prj_loot))


app = Flask(__name__, template_folder=f'{prj_loot}/templates', static_folder=f'{prj_loot}/static')
CORS(app, resources={r"/*": {"origins": '*'}}, supports_credentials=True)
api = Api(app, title='bizbox api 문서', description='Swagger docs', doc="/docs")
jwt = JWTManager(app)



# Get configuration based on the environment
biz_config = get_config()
print(biz_config)
# Flask 앱 설정
app.config.update(biz_config)

# biz_config = get_config()
#
# # Flask 앱 설정
# app.config.update(biz_config)

@app.errorhandler(CustomValidException)
def handle_custom_valid_exception(error):
    print("handle_custom_valid_exception")
    return errorMessage(error.status_code, error.message)



# DB 접속 경로
MAIN_DB_PATH = app.config.get('DATABASE')  # Use .get() to avoid KeyError

@app.route('/detail/<int:bid_id>')
def detail(bid_id):
    conn = sqlite3.connect(MAIN_DB_PATH)
    c = conn.cursor()

    # 상세 데이터 조회
    c.execute('''SELECT b.*, ba.area_name, ba.area_g_cd
                 FROM bid_notice b
                 LEFT JOIN bid_notice_area ba
                 ON b.np_idx = ba.np_idx
                 WHERE b.np_idx = ?
                 ''', (bid_id,))
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

    c.execute('''SELECT fi.domain AS url,
                             fi.o_file_name AS file_name
                      FROM bid_file bf 
                      LEFT JOIN file_info fi
                      ON bf.file_idx = fi.file_idx
                      WHERE bf.np_idx = ?''', (bid_id,))
    file_data = c.fetchall()
    files = []
    for f in file_data:
        file_info = {
            'url': f[0],
            'file_name': f[1]
        }
        files.append(file_info)
    return render_template('biz_mail_detail.html', bid=bid_data, files=files)




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


from nara.routes.sign import sign_api
from nara.routes.add_industry import bid_api

# 네임 스페이스 api 연결
api.add_namespace(sign_api)
api.add_namespace(bid_api)

# 스케줄러 시작

if __name__ == '__main__':
   app.run(debug=False, use_reloader=False, port=3001, host='0.0.0.0')





