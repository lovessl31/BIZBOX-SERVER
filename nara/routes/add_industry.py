import sqlite3
import json
from datetime import datetime
import requests
# flask 라이브러리
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restx import Namespace, Resource
# 함수 모음
from nara.utils.utils import errorMessage, crudQuery, successMessage
from nara.utils.valid import is_valid_ep
from nara.utils.err_handler import CustomValidException, DetailErrMessageTraceBack

bid_api = Namespace('bid', description='사용자 등록 API', path='/biz')

# DB 접속 경로
MAIN_DB_PATH = r"C:\work\NARA_CRAWL\nara\db\bizbox.db"




# 중복 코드 함수화
def insert_data(idx, table_name, data_list, key_name):
    """
    :type data_list: list
    """
    middle_data = {"bms_idx": idx}
    for data_item in data_list:
        middle_data[f"{key_name}"] = data_item
        insert_check = crudQuery('c', MAIN_DB_PATH, middle_data, table_name)
        if not isinstance(insert_check, list):
            return False
    return True

@bid_api.route('/get-bms')
class Bms(Resource):
    @bid_api.doc(description="서비스 등록",
                 params={'email': '이용 이메일',
                         'name': '이용자 명',
                         'phone_number': '이용자 번호',
                         'industry_code': "업종 번호",
                         'area': '지역 그룹 번호',
                         'task': '업무 명',
                         'keyword': '키워드'
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
        required_fields = ['email', 'name', 'phone_number', 'industry_code', 'area', 'task', 'keyword']
        print(data)
        if 'idx' in tInfo and 'id' in tInfo:
            print(tInfo['idx'], tInfo['id'])
            if all(data[key] for key in required_fields):
                # 업종 코드 양식 검증
                try:
                    conn = sqlite3.connect(MAIN_DB_PATH)
                    c = conn.cursor()

                    # 문자 템플릿 유효성
                    for v_type in required_fields:
                        if v_type == 'name':
                            continue
                        elif v_type == 'industry_code':
                            is_valid_ep('industry', data[v_type])
                        else:
                            is_valid_ep(v_type, data[v_type])

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

                    # 중간 테이블에 삽입할 각각의 리스트 가져오기
                    area_list = data['area'].split(',')
                    task_list = data['task'].split(',')
                    keyword_list = data['keyword'].split(',')
                    print(f'''
                    {industry_codes},
                    {industry_list},
                    {area_list},
                    {task_list},
                    {keyword_list},
                    ''')
                    # 변경할 키
                    key_mapping = {
                        'email': 'bms_email',
                        'name': 'bms_name'
                    }
                    # 키를 변경한 튜플 리스트
                    select_key_data = {key_mapping.get(k, k): v for k, v in data.items()}

                    # 안쓰는 키 삭제
                    del select_key_data['industry_code']
                    del select_key_data['task']
                    del select_key_data['area']
                    del select_key_data['keyword']

                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    mIdx = tInfo['idx']
                    mId = tInfo['id']
                    print(mIdx)
                    print(mId)
                    # 토큰의 유저 idx와 이름이 현재 유저 테이블에 존재하는지 확인.
                    c.execute('''SELECT count(*) FROM member WHERE mb_idx = ? AND mb_id = ?'''
                              , (mIdx, mId))
                    check = c.fetchone()[0]

                    if check > 0:
                        # 서비스 테이블 데이터 삽입
                        select_key_data['mb_idx'] = mIdx
                        select_key_data['created_date'] = current_time
                        result = crudQuery('c', MAIN_DB_PATH, select_key_data, 'bms_tbs')

                        # 중간 테이블 데이터 삽입
                        if isinstance(result, list):
                            bms_idx = result[1]
                            # 삽입할 데이터 리스트
                            indusInsert = insert_data(bms_idx, 'bms_industry', industry_list, key_name="industry_cd")
                            areaInsert = insert_data(bms_idx, 'bms_area', area_list, key_name='bms_area')
                            taskInsert = insert_data(bms_idx, 'bms_task', task_list, key_name='bms_taskCd')
                            keyInsert = insert_data(bms_idx, 'bms_keyword', keyword_list, key_name="bms_keyword")
                            if False in [indusInsert, areaInsert, taskInsert, keyInsert]:
                                return errorMessage(403, "중간 테이블 데이터 삽입이 잘못되었습니다.")
                            # 모두 삽입시 성공 메세지 출력
                            return successMessage()
                        
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
