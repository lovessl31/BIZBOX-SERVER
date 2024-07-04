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

def update_data(idx, table_name, data_list, key_name, cdt, param):
    """
    :type data_list: list
    """
    middle_data = {"bms_idx": idx}
    for data_item in data_list:
        middle_data[f"{key_name}"] = data_item
        edt_check = crudQuery('u', MAIN_DB_PATH, middle_data, table_name, cdt, None, param)
        if not isinstance(edt_check, list):
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
            if all(data[key] for key in required_fields if key != 'keyword') and 'keyword' in data:
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
                    keyword_list = data['keyword'].split(',')
                    # 변경할 키
                    key_mapping = {
                        'email': 'bms_email',
                        'name': 'bms_name',
                        'industry_code': 'bms_industry',
                        'task': 'bms_task',
                        'area': 'bms_area'
                    }
                    # 키를 변경한 튜플 리스트
                    select_key_data = {key_mapping.get(k, k): v for k, v in data.items()}

                    # 안쓰는 키 삭제
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

                            # 만약 키워드가 존재하지않으면 굳이 DB에 넣을 필요없으니 상태값을 할당
                            if not keyword_list:
                                keyInsert = True
                            # 키워드가 존재할때만 DB에 insert
                            else:
                                keyInsert = insert_data(bms_idx, 'bms_keyword', keyword_list, key_name="keyword")
                            if keyInsert is False:
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




    @bid_api.doc(description="서비스 조회")
    @jwt_required()
    def get(self):
        """
                서비스 조회

                GET 요청으로 사용자의 서비스를 조회합니다.
                """
        try:
            conn = sqlite3.connect(MAIN_DB_PATH)
            c = conn.cursor()
            tInfo = get_jwt_identity()
            mIdx = tInfo['idx']
            mId = tInfo['id']
            print(mIdx)
            print(mId)
            c.execute('''SELECT bt.bms_idx
                                               FROM member m
                                               LEFT JOIN bms_tbs bt
                                               ON m.mb_idx = bt.mb_idx
                                               WHERE bt.mb_idx = ?
                                               AND m.mb_id = ?'''
                      , (mIdx, mId))
            b = c.fetchone()
            print(b)
            if b is None:
                return errorMessage(404, '유저 정보가 없습니다.')
            bidx = b[0]
            if int(bidx) > 0:
                param = (mIdx,)
                c.execute('''select t.bms_idx,
                                    t.bms_email,
                                    t.bms_name,
                                    t.phone_number,
                                    t.bms_area,
                                    t.bms_task,
                                    t.bms_industry
                             from bms_tbs t
                             WHERE t.mb_idx = ?                
                ''', param)
                bms = c.fetchone()
                c.execute('''SELECT  keyword   
                                   FROM bms_keyword
                                   WHERE bms_idx = ?               
                                ''', (bidx, ))
                keyword_data = c.fetchall()
                if keyword_data:
                    keywords = [{'keyword': keyword[0]} for keyword in keyword_data]

                    bms_info = {
                        "idx": bms[0],
                        "email": bms[1],
                        "name": bms[2],
                        "phone_number": bms[3],
                        "area": bms[4],
                        "task": bms[5],
                        "industry": bms[6],
                        'x_keyword': keywords
                    }
                else:
                    bms_info = {
                        "idx": bms[0],
                        "email": bms[1],
                        "name": bms[2],
                        "phone_number": bms[3],
                        "area": bms[4],
                        "task": bms[5],
                        "industry": bms[6],
                        "x_keyword": ""
                    }
                return successMessage(bms_info)
            else:
                return errorMessage(404, '유저 정보가 존재하지않습니다.')
        except Exception as e:
            DetailErrMessageTraceBack(e)
            return errorMessage(500, str(e))

    @bid_api.doc(description="서비스 수정",
                 params={'idx': '인덱스',
                         'email': '이용 이메일',
                         'name': '이용자 명',
                         'phone_number': '이용자 번호',
                         'industry_code': "업종 번호",
                         'area': '지역 그룹 번호',
                         'task': '업무 명',
                         'keyword': '키워드'
                         }
                 )
    @jwt_required()
    def put(self):
        """
                서비스 수정

                PUT 요청으로 사용자의 서비스를 수정합니다.
                """
        data = json.loads(json.dumps(request.form, ensure_ascii=False))
        tInfo = get_jwt_identity()
        print("서비스 수정 data : ", data)
        if data is not None:
            try:
                for v_type in data:
                    if v_type in ['name', 'bms_idx', 'keyword']:
                        continue
                    elif v_type == 'industry_code':
                        is_valid_ep('industry', data[v_type])
                    else:
                        is_valid_ep(v_type, data[v_type])
                conn = sqlite3.connect(MAIN_DB_PATH)
                c = conn.cursor()

                mIdx = tInfo['idx']
                bidx = data['idx']
                if bidx is None:
                    return errorMessage(400, '필수 매개 변수 (idx) 가 존재하지않습니다.')

                # 토큰의 유저 idx와 이름으로 멤버 테이블과 서비스 테이블 확인.
                c.execute('''SELECT count(*)
                                   FROM bms_tbs                                                                      
                                   WHERE mb_idx = ?
                                   AND bms_idx = ?'''
                          , (mIdx, bidx))
                check = c.fetchone()[0]
                if check > 0:
                    key_mapping = {
                        'email': 'bms_email',
                        'name': 'bms_name',
                        'industry_code': 'bms_industry',
                        'area': 'bms_area',
                        'task': 'bms_task'
                    }
                    # 키를 변경한 튜플 리스트
                    select_key_data = {key_mapping.get(k, k): v for k, v in data.items()}
                    del select_key_data['idx']
                    # 공통 업데이트 함수 호출
                    for key, value in select_key_data.items():
                        if key in ['bms_email', 'bms_name', 'phone_number', 'bms_industry', 'bms_area', 'bms_task']:
                            result = {key: value}
                            udt = crudQuery('u', MAIN_DB_PATH, result, 'bms_tbs', "bms_idx = ?", None, (bidx,))
                            if udt.status_code >= 400:
                                return errorMessage(403, '업데이트 중 에러가 발생하였습니다. (service)')
                        else:
                            keyword_list = value.split(',')
                            print("keyword_list", keyword_list)
                            crudQuery('d', MAIN_DB_PATH, None, 'bms_keyword', "bms_idx = ?", None, (bidx,))
                            for keyword in keyword_list:
                                print("keyword", keyword)
                                result = {'keyword': keyword,
                                          'bms_idx': bidx}
                                udt = crudQuery('c', MAIN_DB_PATH, result, 'bms_keyword')
                                if udt[0].status_code >= 400:
                                    print('키워드 에러 발생', udt[0].status_code)
                                    return errorMessage(403, '업데이트 중 에러가 발생하였습니다. (keyword)')
                    return successMessage("데이터를 성공적으로 수정하였습니다.")
            except Exception as e:
                return errorMessage(500, str(e))
        else:
            errorMessage(400, "수정 할 파라미터가 존재하지 않습니다.")

    @bid_api.doc(description="서비스 해지")
    @jwt_required()
    def delete(self):
        """
                서비스 해지

                delete 요청으로 사용자의 서비스를 해지 합니다.
                """
        try:
            conn = sqlite3.connect(MAIN_DB_PATH)
            c = conn.cursor()
            tInfo = get_jwt_identity()
            mIdx = tInfo['idx']
            mId = tInfo['id']
            print(mIdx)
            print(mId)
            # 토큰의 유저 idx와 이름이 현재 유저 테이블에 존재하는지 확인.
            c.execute('''SELECT count(*) FROM member WHERE mb_idx = ? AND mb_id = ?'''
                      , (mIdx, mId))
            check = c.fetchone()[0]
            if check > 0:
                cdt = "mb_idx = ?"
                param = (mIdx,)
                result = crudQuery('d', MAIN_DB_PATH, None, 'bms_tbs', cdt, None, param)
                return result
        except Exception as e:
            return errorMessage(500, str(e))

