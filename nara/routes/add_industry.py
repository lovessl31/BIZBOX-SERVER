import sqlite3

from flask import request, session
import json
from datetime import datetime
from flask_restx import Namespace, Resource
from nara.utils.utils import errorMessage, crudQuery
from nara.utils.valid import is_valid_ep
from nara.utils.err_handler import CustomValidException
bid_api = Namespace('bid', description='사용자 등록 API', path='/biz')

# DB 접속 경로
MAIN_DB_PATH = r"C:\work\NARA_CRAWL\nara\db\bizbox.db"





@bid_api.route('/get-bms')
class Bms(Resource):
    @bid_api.doc(description="서비스 등록",
                  params={'email': '이용 이메일',
                          'name': '이용자 명',
                          'phone_number': '이용자 번호',
                          'industry_code': "업종 번호",
                          'area': '지역 그룹 번호'
                          })
    def post(self):
        form_data = request.form
        dump_data = json.dumps(form_data, ensure_ascii=False)
        data = json.loads(dump_data)
        required_fields = ['email', 'name', 'phone_number', 'industry_code', 'area']
        if 'user_idx' in session:
            if all(data[key] for key in required_fields):
                # 업종 코드 양식 검증
                try:
                    is_valid_ep('email', data["email"])
                    is_valid_ep('industry', data['industry_code'])
                    is_valid_ep('phone', data['phone_number'])
                    # 변경할 키
                    key_mapping = {
                        'email': 'bms_email',
                        'name': 'bms_name',
                        'industry_code': 'industry_cd'
                    }
                    # 키를 변경한 튜플 리스트
                    select_key_data = {key_mapping.get(k, k): v for k, v in data.items()}
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    member_idx = session["user_idx"]
                    member_id = session["user_id"]
                    print(member_idx)
                    print(member_id)
                    # 세션의 유저 idx와 이름이 현재 유저 테이블에 존재하는지 확인.
                    conn = sqlite3.connect(MAIN_DB_PATH)
                    c = conn.cursor()
                    c.execute('''SELECT count(*) FROM member WHERE mb_idx = ? AND mb_id = ?'''
                              , (member_idx, member_id))
                    check = c.fetchone()[0]
                    print(check)
                    middle_data = {}
                    industry_list = [int(num) for num in select_key_data['industry_cd'].split(',')]

                    # 안쓰는 키 삭제
                    del select_key_data['industry_cd']

                    if check > 0:
                        # 서비스 테이블 데이터 삽입
                        select_key_data['mb_idx'] = member_idx
                        select_key_data['created_date'] = current_time
                        result = crudQuery('c', MAIN_DB_PATH, select_key_data, 'bms_tbs')
                        # 중간 테이블 데이터 삽입
                        if result[1] is not None:
                            middle_data["bms_idx"] = result[1]
                            for industry in industry_list:
                                middle_data["industry_cd"] = industry
                                crudQuery('c', MAIN_DB_PATH, middle_data, 'bms_industry')
                            return result[0]
                        else:
                            conn.rollback()
                    else:
                        errorMessage("존재 하지 않는 사용자 입니다.")
                except CustomValidException as e:
                    return errorMessage(e.status_code, e.message)
                except Exception as e:
                    return errorMessage(500, str(e))
            else:
                errorMessage(400, "잘못된 파라미터 입니다.")
        else:
            return errorMessage(401, "세션이 존재하지 않습니다. 다시 로그인하여 주세요.")



    # @bid_api.doc(description="서비스 등록",
    #               params={'email': '이용 이메일',
    #                       'name': '이용자 명',
    #                       'phone_number': '이용자 번호',
    #                       'industry_code': "업종 번호",
    #                       'area': '지역 그룹 번호',
    #                       })
    # def get(self):
