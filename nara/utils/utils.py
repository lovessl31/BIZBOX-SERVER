import sqlite3
import os
import mimetypes

from flask import jsonify, make_response
from datetime import datetime

# 이메일 기능
import smtplib
from email.message import EmailMessage
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


import random
import string

# DB 접속 경로
MAIN_DB_PATH = r"/nara/db/bizbox.db"


current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def convert_size(size_bytes):
    import math
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


# def file_upload(save_f_name, f_path, domain, idx, table, cul, db_path=None):
#     try:
#         if db_path is None:
#             db_path = DB.MAIN_DB_PATH
#
#         # 모든 파일을 가져옴
#         files = request.files.getlist('file')
#         print("file data 열어 봅니다.:", files)
#         print('CONFIG: ', CONFIG)
#         f_path = f"{CONFIG}\\{f_path}"
#
#         # 각 파일을 처리
#         for f in files:
#             # 파일 유효성 검사 및 처리
#             f = valid_file(f, field_name='file')
#             o_f_name = f.filename  # 원본 파일명
#             f_type = f.content_type  # 파일 유형
#             ext = o_f_name.split('.')[-1].lower()  # 확장자
#             filename = secure_filename(f"{save_f_name}.{ext}")
#             mkdir_p(f_path)
#             # 파일 저장
#             f.save(os.path.join(f_path, filename))
#             # 저장된 파일의 용량을 가져오기
#             f_size = convert_size(os.path.getsize(f"{f_path}\{filename}"))
#             print(o_f_name, save_f_name, f_size, f_type, ext, f_path, domain)
#             # 별다른 값이 없으면 메인 db 연결
#             conn = sqlite3.connect(db_path)
#             cursor = conn.cursor()
#             cursor.execute('''
#                                 INSERT INTO file_upload (o_f_name, s_f_name, f_size, f_type, f_ext, f_path, domain)
#                                 VALUES (?,?,?,?,?,?,?)
#                                 ''', (o_f_name, save_f_name, f_size, f_type, ext, f_path, domain))
#             f_idx = cursor.lastrowid
#             file_table = f'''
#                                 INSERT INTO {table} ({cul}, f_idx)
#                                 VALUES (?,?)
#                              '''
#             cursor.execute(file_table, (idx, f_idx))
#             conn.commit()
#             conn.close()
#             return True
#     except Exception as e:
#         return errorMessage(500, str(e))


def get_file_type_and_extension(file_name):
    # 확장자 추출
    _, file_ext = os.path.splitext(file_name)
    file_ext = file_ext.lower()

    # MIME 타입 추출
    file_type, _ = mimetypes.guess_type(file_name)

    return file_type, file_ext

def errorMessage(num, detailErrors=None):
    error_messages = {
        400: {
            "message": "잘못된 요청입니다.",
            "status_code": 400
        },
        401: {
            "message": "인증되지 않은 접근입니다. 로그인이 필요합니다.",
            "status_code": 401
        },
        403: {
            "message": "요청이 거부되었습니다. 해당 작업을 수행할 권한이 없습니다.",
            "status_code": 403
        },
        404: {
            "message": "요청한 리소스를 찾을 수 없습니다.",
            "status_code": 404
        },
        500: {
            "message": "서버에서 처리 중에 오류가 발생했습니다. 관리자에게 문의하세요.",
            "status_code": 500
        },
        450: {
            "message": "사용자 권한이 부족합니다.",
            "status_code": 450
        },
        "default": {
            "message": "알 수 없는 오류가 발생했습니다.",
            "status_code": 406
        }
    }

    error_data = {
        "result": "error",
        "error": {
            "message": error_messages.get(num, error_messages["default"])["message"],
            "code": num
        }
    }

    if detailErrors:
        error_data['error']['detailsError'] = detailErrors

    response = make_response(jsonify(error_data), error_messages.get(num, error_messages["default"])["status_code"])
    return response


# api 성공 메시지 호출
message = {"message":"요청을 성공적으로 처리하였습니다."}
def successMessage(data=message):
    success_message = {"result": "success",
                       "data": data,
                       "status_code": 200}
    response = make_response(jsonify(success_message))
    response.status_code = 200
    return response

def crudQuery(queryType, path, data, table, condition=None, col=None, paramQuery=None):
    conn = sqlite3.connect(path)
    conn.execute('PRAGMA foreign_keys = ON')
    cursor = conn.cursor()
# insert 구문
    if queryType == 'c':
        try:
            set_clause = ", ".join(data.keys())
            print(set_clause)
            set_Values = ", ".join(['?' for _ in range(len(data))])
            print(set_Values)
            set_clause_list = set_clause.split(", ")
            reqValue = tuple(data.values())
            print(reqValue)
            print(11111111, table, set_clause, set_Values, 11111111111)
            sql = f"INSERT INTO {table}({set_clause}) VALUES ({set_Values})"
            print(sql, reqValue)
            cursor.execute(sql, reqValue)
            idx = cursor.lastrowid
            print("crudqueryidxidxidxidxidxidxidxidxidxidx", idx)
            conn.commit()
            return [successMessage(), idx]
        except Exception as e:
            return errorMessage(500, str(e))
        finally:
            cursor.close()
            conn.close()
# select 구문
    elif queryType == 'r':
        try:
            # 복잡성이 커서 이렇게 처리했는데 추후 변경의사있음.

            if condition:
                if col:
                    sql = f'''SELECT {col}
                                   FROM {table}
                                   WHERE {condition}
                                    '''
                else:
                    sql = f"SELECT * FROM {table} WHERE {condition}"
                # 컬럼을 모두 가져와서 배열에 넣기
                # 만약 조인 문이 존재한다면
                table_parts = table.split(" JOIN")
                if len(table_parts) > 1:
                    # 예를 들어 약어로 FROM post as p라고 했으면 select절에는 p.컬럼명 이렇게 붙는데 앞에는 .을 기준으로 자르고 그뒤에 컬럼은
                    # ,를 기준으로 잘라서 배열에 담고 응답객체의 키값으로 사용함.
                    column_names = [k.split('.')[1].strip() for k in col.split(',') if k.strip()]
                    print(column_names)
                else:
                    # 조인문을 사용하지않으면 테이블의 컬럼명을 가져와서 배열에 담아 키값으로 사용함
                    columns = f"PRAGMA table_info({table})"
                    cursor.execute(columns)
                    selectCol = cursor.fetchall()
                    column_names = [column[1] for column in selectCol]
                    # 인자로 select 절의 col이 존재 한다면 select절에 담긴 문자만 배열에 담아 키값으로 사용함
                    if col:
                        col_list = col.split(', ')
                        column_names = [col_name for col_name in column_names if col_name in col_list]
                cursor.execute(sql, paramQuery)
                # 전부 조회하기
                selectValue = cursor.fetchall()
                selectList = []
                for row in selectValue:
                    val = list(row)
                    # 컬럼명과 결과값을 매칭하여 딕셔너리 생성
                    result_dict = dict(zip(column_names, val))
                    # 딕셔너리를 리스트에 추가
                    selectList.append(result_dict)
            else:
                if col:
                    sql = f"SELECT {col} FROM {table}"
                else:
                    sql = f"SELECT * FROM {table}"
                table_parts = table.split(" JOIN")
                # 만약 조인 문이 존재한다면
                if len(table_parts) > 1:
                    # 예를 들어 약어로 FROM post as p라고 했으면 select절에는 p.컬럼명 이렇게 붙는데 앞에는 .을 기준으로 자르고 그뒤에 컬럼은
                    # ,를 기준으로 잘라서 배열에 담고 응답객체의 키값으로 사용함.
                    column_names = [k.split('.')[1].strip() for k in col.split(',') if k.strip()]
                else:
                    # 조인문을 사용하지않으면 테이블의 컬럼명을 가져와서 배열에 담아 키값으로 사용함
                    columns = f"PRAGMA table_info({table})"
                    cursor.execute(columns)
                    selectCol = cursor.fetchall()
                    column_names = [column[1] for column in selectCol]
                    # 인자로 select 절의 col이 존재 한다면 select절에 담긴 문자만 배열에 담아 키값으로 사용함
                    if col:
                        col_list = col.split(', ')
                        column_names = [col_name for col_name in column_names if col_name in col_list]
                # 전부 조회하기
                cursor.execute(sql)
                selectValue = cursor.fetchall()
                selectList = []
                for row in selectValue:
                    val = list(row)
                    # 컬럼명과 결과값을 매칭하여 딕셔너리 생성
                    result_dict = dict(zip(column_names, val))
                    # 딕셔너리를 리스트에 추가
                    selectList.append(result_dict)
            conn.close()
            return successMessage(selectList)
        except Exception as e:
            return errorMessage(500, str(e))
        finally:
            conn.close()
# update 구문
    elif queryType == 'u':
        try:
            set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
            reqValue = tuple(data.values())
            print("set_clause:::", set_clause)
            print(reqValue)
            # 조회해서 확인 후 값이 없으면 에러메세지 호출
            cursor.execute(f"SELECT * FROM {table} WHERE {condition}", paramQuery)
            updated_records = cursor.fetchall()
            if updated_records:
                pass
            else:
                return errorMessage(400, 'Invalid header parameter')
            # 동적 SQL 생성
            if condition:
                sql = f"UPDATE {table} SET {set_clause} WHERE {condition}"
                reqValue = reqValue + paramQuery
                print("파라미터 결합 성공", reqValue)
                cursor.execute(sql, reqValue)
            else:
                sql = f"UPDATE {table} SET {set_clause}"
                cursor.execute(sql, reqValue)
                # 변경된 레코드 조회
            # 변경 사항 커밋
            conn.commit()
            # 연결 닫기
            conn.close()
            message = {"message": 'The requested data has been successfully updated.'}
            return successMessage(message)
        except Exception as e:
            return errorMessage(500, str(e))
        finally:
            conn.close()
# delete 구문
    elif queryType == 'd':
        try:
            # 조회해서 확인 후 값이 없으면 에러메세지 호출
            cursor.execute(f"SELECT * FROM {table} WHERE {condition}", paramQuery)
            updated_records = cursor.fetchall()
            if updated_records:
                pass
            else:
                return errorMessage(400, 'Invalid header parameter')
            if condition:
                sql = f"DELETE FROM {table} WHERE {condition}"
                if paramQuery:
                    cursor.execute(sql, paramQuery)
                else:
                    cursor.execute(sql)
                conn.commit()
                conn.close()
                message = {"message": 'The requested data has been successfully deleted.'}
                return successMessage(message)
            else:
                return errorMessage(401)
        except Exception as e:
            return errorMessage(500, str(e))
        finally:
            conn.close()


def insert_file_info(c, file_name, s_fileName, file_size, file_type, file_ext, f_path, url, current_dt):
    # # s_file_name 값이 이미 존재하는지 확인
    # c.execute("SELECT COUNT(*) FROM file_info WHERE s_file_name = ?", (s_fileName,))
    # result = c.fetchone()
    # existing_count = result[0]
    #
    # # s_file_name 값이 이미 존재하면 pass
    # if existing_count > 0:
    #     print(f"이미 존재하는 s_file_name: {s_fileName}, 건너뜁니다.")
    #     return

    # 존재하지 않으면 데이터 삽입
    c.execute('''INSERT INTO file_info(o_file_name, s_file_name, file_size, file_type, file_ext, file_path, domain, upload_date)
                    VALUES(?,?,?,?,?,?,?,?)        
                ''', (file_name, s_fileName, file_size, file_type, file_ext, f_path, url, current_dt))



from nara.utils.err_handler import CustomException
def insert_bid_notice(c, industry_cd, title, np_number, demand_agency, tender_open_date, tender_close_date, pj_amount,
                      est_price, budget, vat, taskClCds, area):
    # s_file_name 값이 이미 존재하는지 확인
    c.execute("SELECT COUNT(*) FROM bid_notice WHERE np_number = ? AND industry_cd = ?", (np_number, industry_cd))
    result = c.fetchone()
    existing_count = result[0]
    print("existing_count", existing_count)

    # s_file_name 값이 이미 존재하면 pass
    if existing_count > 0:
        print(f"이미 존재하는 공고 번호: {title} {np_number}, 건너뜁니다.")
        raise CustomException("자식 함수에서 예외 발생")
    else:
        # 존재하지 않으면 데이터 삽입
        c.execute('''INSERT INTO bid_notice(industry_cd, np_title, np_number, demand_agency, tender_open_date,
                         tender_close_date, pj_amount, est_price, budget, vat, taskClCds, created_date) 
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                  ''', (industry_cd, title, np_number, demand_agency, tender_open_date, tender_close_date, pj_amount,
                        est_price, budget, vat, taskClCds, current_time))
        # 입찰 번호 가져오기
        bid_notice_idx = c.lastrowid
        # 입찰 번호가 존재하며 지역도 존재 했을때 실행
        if bid_notice_idx > 0 and area is not None:
            area_list = generate_area_list(area)
            # 딕셔너리를 읽으면서 지역 테이블에 삽입
            for k, v in area_list.items():
                print(f'''
                area code key : {k}
                area name val : {v}
                ''')
                c.execute('''INSERT INTO bid_notice_area(np_idx, area_g_cd, area_name, created_date)VALUES(?,?,?,?)
                ''', (bid_notice_idx, k, v, current_time))


import re

def generate_area_list(area):
    if not area == '':
        # original_str = '[전주] [광주] [경남]'
        #
        # # 대괄호 제거
        # modified_str = original_str.replace('[', '').replace(']', '')
        #
        # # 결과 출력
        # print(modified_str.split(' '))  # ['전주', '광주', '경남']

        # 앞부분 추출
        first_str_matches = re.findall(r'\[?([^ \[\]]+)\]?', area)
        match_value = []
        # 전체 추출
        matches = re.findall(r'\[([^]]+)\]', area)

        # 키 값을 담은 객체 만들고
        area_map = {
            '서울특별시': '11',
            '부산광역시': '26',
            '대구광역시': '27',
            '인천광역시': '28',
            '광주광역시': '29',
            '울산광역시': '31',
            '대전광역시': '30',
            '세종특별자치시': '36',
            '경기도': '41',
            '경상남도': '48',
            '충청북도': '43',
            '충청남도': '44',
            '전라남도': '46',
            '경상북도': '47',
            '제주특별자치도': '50',
            '강원특별자치도': '51',
            '강원도': '51',
            '전라북도': '52',
            '전북특별자치도': '52'
        }
        # 크롤링한 데이터와 일치하는 코드 추출해서 배열에 담기
        for v in first_str_matches:
            if v in area_map:
                code = area_map[v]
                match_value.append(code)
        print("matches", matches)

        area_list = {key: value for key, value in zip(match_value, matches)}
        print(area_list)
        return area_list
    else:
        area_list = {}
        area_list['00'] = '전국(제한없음)'
        return area_list




def generate_unique_number(url):
    # URL에서 각 쿼리 매개변수의 값 추출
    bidno_match = re.search(r'bidno=(\d+)', url)
    bidseq_match = re.search(r'bidseq=(\d+)', url)
    taskClCd_match = re.search(r'taskClCd=(\d+)', url)

    # 추출된 값들 조합
    bidno_digits = bidno_match.group(1) if bidno_match else ""
    bidseq_digits = bidseq_match.group(1) if bidseq_match else ""
    taskClCd_digits = taskClCd_match.group(1) if taskClCd_match else ""

    # 추출된 숫자를 조합하여 하나의 문자열로 만듦
    combined_string = bidno_digits + bidseq_digits + taskClCd_digits

    return combined_string

def generate_bidNo(url):
    # 공고번호 , 공고차수 가져오기
    bidno_match = re.search(r'bidno=(\d+)', url)
    bidseq_match = re.search(r'bidseq=(\d+)', url)

    # 조합
    bidno_digits = bidno_match.group(1) if bidno_match else ""
    bidseq_digits = bidseq_match.group(1) if bidseq_match else ""

    combined_string = f"{bidno_digits}_{bidseq_digits}"

    return combined_string

# 중복 파일명 없애고 새로운 파일명
def generate_unique_filename(base_path, filename):
    base_name, ext = os.path.splitext(filename)
    new_filename = filename
    count = 1
    while os.path.exists(os.path.join(base_path, new_filename)):
        new_filename = f"{base_name}_{count}{ext}"
        count += 1
    return new_filename



# 랜덤한 6자리 인증 코드 생성
verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
# def send_email(receiver_email):
#     # 이메일 설정
#     smtp_server = 'smtp.worksmobile.com'
#     smtp_port = 587
#     email_user = 'cmh0713@withfirst.com'
#     email_password = 'oS4CxVMlWFZ1'
#     email_user.encode('utf-8')
#     receiver_email.encode('utf-8')
#     # smtp_server = 'smtp.gmail.com'
#     # smtp_port = 465
#     # email_user = 'mywork9431@gmail.com'
#     # email_password = 'uwrb ulgz jvsp zjvl'
#     print(1)
#     # SSLContext 객체 생성
#     context = ssl.create_default_context()
#     # 인증서 로드
#     context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
#     # 서버 연결
#     smtp = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
#
#     # SMTP 객체 생성
#     smtp = smtplib.SMTP(smtp_server, smtp_port)
#
#     # STARTTLS 보안 연결 시작
#     smtp.starttls()
#
#     # SMTPUTF8 활성화
#     smtp.ehlo()
#     smtp.esmtp_features['SMTPUTF8'] = ''
#
#
#     # 로그인
#     print(2)
#     smtp.login(email_user, email_password)
#
#     print(3)
#
#
#     # 이메일 내용 작성
#     subject = "회원가입 이메일 인증"
#     body = f"회원가입을 완료하려면 다음 인증 코드를 입력하세요: {verification_code}"
#     # message = EmailMessage()
#     message = MIMEMultipart()
#     message["From"] = f"비즈박스 {email_user}"
#     message["To"] = receiver_email
#     message["Subject"] = subject
#
#     # mime 형태의 메세지 작성
#     # message.set_content(body)
#     message.attach(MIMEText(body, 'plain'))
#     smtp.send_message(message)
#     # smtp.sendmail(message['From'], message['To'], message.as_string())
#     smtp.quit()




# def send_email(receiver_email):
#     # 이메일 설정
#     smtp_server = 'smtp.worksmobile.com'
#     smtp_port = 587
#     email_user = 'cmh0713@withfirst.com'
#     email_password = 'oS4CxVMlWFZ1'
#     print(1)
#     yag = yagmail.SMTP(email_user, email_password, smtp_server, smtp_port)
#     print(2)
#     # 이메일 내용 작성
#     subject = "회원가입 이메일 인증"
#     body = f"회원가입을 완료하려면 다음 인증 코드를 입력하세요: {verification_code}"
#     yag.send(receiver_email, subject, body)
#     print(3)
#     yag.close()





import idna
from dotenv import load_dotenv
load_dotenv()

def convert_ascii_email(email):
    # 이메일 주소를 '@'를 기준으로 분리
    local_part, domain_part = email.split('@')

    # IDN을 ASCII로 변환
    ascii_domain = idna.encode(domain_part).decode('ascii')

    # ASCII 이메일 주소로 조합
    ascii_email = f"{local_part}@{ascii_domain}"

    return ascii_email

import json

def service_send_email(receiver_email, subject, body, mail_type, html_content):
    # 이메일 설정
    smtp_server = 'smtp.worksmobile.com'
    smtp_port = 587
    email_user = 'cmh0713@withfirst.com'
    email_password = os.getenv('EMAIL_SECRET_KEY')

    # SSLContext 생성
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  # TLSv1.2 이상 사용

    # 이메일 내용 작성
    message = MIMEMultipart('alternative')
    message["From"] = email_user
    message["To"] = receiver_email
    message["Subject"] = f"[BIZBOX] {subject}"

    # 서비스의 바디는 딕셔너리 형태이므로 문자열로 바꿔주기
    # 메일링이 아닌 메일로그때문에
    # body = {key: str(value) for key, value in body.items()} # 안에 있는 키값만 문자열이 돼서 사용불가
    body = json.dumps(body, ensure_ascii=False)
    # Attach the HTML content to the email
    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)

    try:
        # SMTP 서버에 연결
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            # STARTTLS 보안 연결 시작
            smtp.starttls(context=context)
            # 로그인
            smtp.login(email_user, email_password)
            # SMTPUTF8 활성화
            smtp.ehlo()
            smtp.esmtp_features['SMTPUTF8'] = ''
            smtp.sendmail(email_user, receiver_email, message.as_string())
            save_to_database(email_user, receiver_email, subject, body, mail_type, 'Y')
    except Exception as e:
        print(f"메일 발송 실패: {e}")
        err_body = (f"이메일 발송 에러 : {e}"
                    f"body : {body}")
        err_subject = f"Err:{subject}"
        save_to_database(email_user, receiver_email, err_subject, err_body, mail_type, 'N')





def send_email(receiver_email, subject, body, mail_type):
    # 이메일 설정
    smtp_server = 'smtp.worksmobile.com'
    smtp_port = 587
    email_user = 'cmh0713@withfirst.com'
    email_password = os.getenv('EMAIL_SECRET_KEY')

    # SSLContext 생성
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  # TLSv1.2 이상 사용
    try:
        # SMTP 서버에 연결
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            # STARTTLS 보안 연결 시작
            smtp.starttls(context=context)
            # 로그인
            smtp.login(email_user, email_password)
            # SMTPUTF8 활성화
            smtp.ehlo()
            smtp.esmtp_features['SMTPUTF8'] = ''

            # 이메일 내용 작성
            subject = subject
            body = body
            message = EmailMessage()
            # message = MIMEMultipart()
            message["From"] = f"비즈박스 <{email_user}>"
            message["To"] = receiver_email
            message["Subject"] = f"[BIZBOX] {subject}"

            # mime 형태의 메세지 작성
            message.set_content(body)
            # message.attach(MIMEText(body, 'plain'))
            smtp.send_message(message)
            # smtp.sendmail(message['From'], message['To'], message.as_string())
            smtp.quit()

            save_to_database(email_user, receiver_email, subject, body, mail_type, 'Y')
    except Exception as e:
        print(f"메일 발송 실패: {e}")
        err_body = (f"이메일 발송 에러 : {e}"
                    f"body : {body}")
        err_subject = f"Err:{subject}"
        save_to_database(email_user, receiver_email, err_subject, err_body, mail_type, 'N')


def save_to_database(From, to, subject, body, mail_type, status):
    try:
        print("body", body)
        # 데이터 베이스 연결
        conn = sqlite3.connect(MAIN_DB_PATH)
        cursor = conn.cursor()
        # 데이터 베이스에 삽입
        cursor.execute('''INSERT INTO mail_log (sender, recipient, subject, body, status, type, sent_time)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (From, to, subject, body, status, mail_type, current_time))
        conn.commit()
        conn.close()
        print("데이터베이스에 기록 완료")
    except sqlite3.Error as e:
        print(f"데이터베이스 오류 발생: {e}")
    except Exception as e:
        print(f"기타 오류 발생: {e}")




