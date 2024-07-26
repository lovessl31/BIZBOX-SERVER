# 디비 생성 및 관리 담당파일
import math
import os
import sqlite3
from nara.db.model.bzb_tbs import bzb_tbs
from werkzeug.security import generate_password_hash
from nara.db.insertDummyData import mb_dummy_data, df
from datetime import datetime
import pandas as pd



'''
1. main db 생성하기
'''

# DB 폴더 경로
MAIN_DB_PATH1 = os.getcwd()
# DB 파일 경로
MAIN_DB_PATH = os.path.join(MAIN_DB_PATH1, "bizbox.db")
current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def create_bzb_db():
    os.makedirs(MAIN_DB_PATH1, exist_ok=True)
    # 디비생성 ,연결
    conn = sqlite3.connect(MAIN_DB_PATH)
    cursor = conn.cursor()

    # 테이블 등록
    bzb_tbs(cursor)
    # 커밋 및 연결 종료

    # 사용자 및 회사 정보 삽입
    for user_info in mb_dummy_data:

        user_id, email, password, name, phone_number, company_name, createDate = user_info

        # 회사 정보 삽입
        cursor.execute('INSERT INTO bid_option (option_value, option_name, option_group, created_date) VALUES (?, ?, ?, ?)', (company_name, "회사명", 'company', current_datetime))
        # insert 한 아이디
        company_option_id = cursor.lastrowid
        if company_option_id is None:
            break
        # 사용자 정보 삽입
        cursor.execute('INSERT INTO member (mb_id, mb_email, mb_pw, mb_name, phone_number, created_date, update_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (user_id, email, generate_password_hash(password, method='pbkdf2:sha256'), name, phone_number, createDate, current_datetime, 'Y'))
        user_idx = cursor.lastrowid
        if user_idx is None:
            break
        # 회사의 ID 가져오기
        cursor.execute('INSERT INTO entity_option (entity_idx, entity_tbs, entity_type, option_idx) VALUES (?,?,?,?)', (user_idx, 'member', 'company', company_option_id))

    # 엑셀 데이터 읽어서 옵션 삽입
    for index, row in df.iterrows():

        # 데이터에서 NaN 값을 None으로 처리
        row = row.where(pd.notnull(row), None)
        industry_option_name = row['업종명']
        industry_option_value = row['업종코드']

        industry_area_name = row['지역명']
        industry_task_name = row['업무명']

        # 각 값이 None이 아닌 경우에만 데이터베이스에 삽입
        if industry_option_name is not None:
            cursor.execute('''INSERT INTO bid_option(option_value, option_name, option_group, created_date) 
                    VALUES (?,?,?,?)''', (industry_option_value, industry_option_name, 'industry', current_datetime))
        if industry_area_name is not None:
            industry_area_value = math.trunc(int(row['지역코드']))
            cursor.execute('''INSERT INTO bid_option(option_value, option_name, option_group, created_date) 
            VALUES (?,?,?,?)''', (industry_area_value, industry_area_name, 'industry_area', current_datetime))
        if industry_task_name is not None:
            industry_task_value = math.trunc(int(row['업무코드']))
            cursor.execute('''INSERT INTO bid_option(option_value, option_name, option_group, created_date) 
                    VALUES (?,?,?,?)''', (industry_task_value, industry_task_name, 'industry_taskClCds', current_datetime))
    conn.commit()
    print("db 생성완료")
    conn.close()

# DB 생성
if not os.path.exists("bizbox.db"):
    create_bzb_db()
else:
    print('db 파일 이미 존재 해서 생성 x')
