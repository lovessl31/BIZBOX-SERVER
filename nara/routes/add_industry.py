import sqlite3
import json
from datetime import datetime
import requests
# flask 라이브러리
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restx import Namespace, Resource
# 함수 모음
from nara.utils.utils import errorMessage, crudQuery
from nara.utils.valid import is_valid_ep
from nara.utils.err_handler import CustomValidException, DetailErrMessageTraceBack



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
                          'area': '지역 그룹 번호',
                          'task': '업무 명'
                          })
    @jwt_required()
    def post(self):
        """
                서비스 신청 (form)

                POST 요청으로 사용자의 서비스를 처리합니다.
                """
        form_data = request.form
        dump_data = json.dumps(form_data, ensure_ascii=False)
        data = json.loads(dump_data)
        # 토큰에서 데이터 추출
        tInfo = get_jwt_identity()
        required_fields = ['email', 'name', 'phone_number', 'industry_code', 'area', 'task']
        print(data)
        if 'idx' in tInfo and 'id' in tInfo:
            print(tInfo['idx'], tInfo['id'])
            if all(data[key] for key in required_fields):
                # 업종 코드 양식 검증
                try:
                    conn = sqlite3.connect(MAIN_DB_PATH)
                    c = conn.cursor()

                    # 문자 템플릿 유효성
                    is_valid_ep('email', data["email"])
                    is_valid_ep('industry', data['industry_code'])
                    is_valid_ep('phone', data['phone_number'])

                    # 업종 코드 유효성 검사
                    industry_codes = data['industry_code'].split(',')  # 문자열을 콤마로 분리하여 리스트로 변환
                    industry_list = [int(code) for code in industry_codes]  # 문자열을 정수형으로 변환한 리스트 생성

                    query = f"SELECT option_value FROM bid_option WHERE option_group = 'industry' AND option_value IN ({','.join('?' for _ in industry_list)})"
                    c.execute(query, industry_list)

                    existing_industries = [result[0] for result in c.fetchall()]

                    # 존재하지 않는 업종 코드 찾기
                    non_existing_industries = [code for code in industry_codes if code not in existing_industries]

                    # 모든 업종 코드가 존재하는지 확인
                    if len(non_existing_industries) > 0:
                        non_existing_codes = ','.join(map(str, non_existing_industries))
                        return errorMessage(403, f"존재하지 않는 업종 코드가 포함되어 있습니다 : {non_existing_codes}")

                    # 변경할 키
                    key_mapping = {
                        'email': 'bms_email',
                        'name': 'bms_name',
                        'industry_code': 'industry_cd',
                        'task': 'bms_taskCd',
                        'area': 'bms_area'
                    }
                    # 키를 변경한 튜플 리스트
                    select_key_data = {key_mapping.get(k, k): v for k, v in data.items()}
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    mIdx = tInfo['idx']
                    mId = tInfo['id']
                    print(mIdx)
                    print(mId)
                    # 토큰의 유저 idx와 이름이 현재 유저 테이블에 존재하는지 확인.
                    c.execute('''SELECT count(*) FROM member WHERE mb_idx = ? AND mb_id = ?'''
                              , (mIdx, mId))
                    check = c.fetchone()[0]
                    middle_data = {}

                    # 안쓰는 키 삭제
                    del select_key_data['industry_cd']

                    if check > 0:
                        # 서비스 테이블 데이터 삽입
                        select_key_data['mb_idx'] = mIdx
                        select_key_data['created_date'] = current_time
                        result = crudQuery('c', MAIN_DB_PATH, select_key_data, 'bms_tbs')

                        # 중간 테이블 데이터 삽입
                        if isinstance(result, list):
                            middle_data["bms_idx"] = result[1]
                            for industry in industry_list:
                                # DB에서 검증
                                middle_data["industry_cd"] = industry
                                crudQuery('c', MAIN_DB_PATH, middle_data, 'bms_industry')
                            return result[0]
                        elif result.status_code >= 400:
                            conn.rollback()
                            return errorMessage(403, "이미 서비스에 등록된 사용자 입니다.")
                        else:
                            return errorMessage(403, "예상하지 못한 문제가 발생하였습니다.")
                    else:
                        return errorMessage(400, "존재 하지 않는 사용자 입니다.")
                except CustomValidException as e:
                    print(500)
                    return errorMessage(e.status_code, e.message)
                except Exception as e:
                    DetailErrMessageTraceBack(e)
                    return errorMessage(500, str(e))
            else:
                return errorMessage(400, "잘못된 파라미터 입니다.")
        else:
            return errorMessage(401, "토큰이 존재하지 않습니다. 다시 로그인하여 주세요.")





    # @bid_api.doc(description="서비스 등록",
    #               params={'email': '이용 이메일',
    #                       'name': '이용자 명',
    #                       'phone_number': '이용자 번호',
    #                       'industry_code': "업종 번호",
    #                       'area': '지역 그룹 번호',
    #                       })
    # def get(self):


