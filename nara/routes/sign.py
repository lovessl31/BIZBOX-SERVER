import datetime
import os
import sqlite3

# from nara.utils import verification_code
import re

from flask import request, url_for, session
import json
from dotenv import load_dotenv

from flask_restx import Namespace, Resource
from werkzeug.security import check_password_hash, generate_password_hash
from nara.utils.utils import successMessage, errorMessage, crudQuery, send_email
from nara.utils.valid import is_valid_ep
from nara.utils.err_handler import CustomValidException
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature






# from nara import smtp_port, smtp_server, email_user, email_password
load_dotenv()

sign_api = Namespace('sign', description='사용자 등록 API', path='/biz')


# DB 접속 경로
MAIN_DB_PATH = r"C:\work\NARA_CRAWL\nara\db\bizbox.db"

# 비밀키
serializer = URLSafeTimedSerializer(os.getenv("URL_TOKEN_KEY"))

@sign_api.route('/login')
@sign_api.doc(description="로그인", params={'id': '사용자 이메일', 'password': '사용자 비밀 번호'})
class login(Resource):
    def post(self):
        """
        로그인 (form)

        POST 요청으로 사용자의 login을 처리합니다.
        """
        form_data = request.form
        dump_data = json.dumps(form_data, ensure_ascii=False)
        data = json.loads(dump_data)
        print(data)
        if all(data[key] for key in ['id', 'password']):
            try:
                key_mapping = {
                    'id': 'mb_id',
                    'password': 'mb_pw'
                }
                # 키를 변경한 튜플 리스트
                new_data = {key_mapping.get(k, k): v for k, v in data.items()}

                # 받아온 데이터 에서 이메일, 비빌번호 추출
                mb_id = new_data.get('mb_id')
                mb_pw = new_data.get('mb_pw')
                # db 접속
                conn = sqlite3.connect(MAIN_DB_PATH)
                c = conn.cursor()
                # db 이메일로 확인
                c.execute('''SELECT mb_idx,
                                         mb_id,
                                         mb_pw,
                                         mb_name,
                                         status,
                                         mb_email                        
                                   FROM member 
                                   WHERE mb_id = ? ''', (mb_id,))

                member = c.fetchone()
                # 이메일이 존재하지않을때 에러 메세지
                if member is None:
                    return errorMessage(401, '로그인에 실패하였습니다.')
                # 이메일 가입상태가 N 일때
                elif member[4] == 'N':
                    return errorMessage(401, '인증되지 않은 계정입니다. 이메일 계정 인증이 필요합니다.')
                if check_password_hash(member[2], mb_pw):
                    # 세션 발급
                    session['user_idx'] = member[0]
                    session['user_id'] = member[1]
                    session['user_name'] = member[3]
                    result = {
                        'loginMsg': "Y",
                        "resultCode": 200,
                        'resultDesc': "Success",
                        'resultMsg': f'{member[3]}님 환영 합니다.',
                        'user_idx': member[0],
                        'user_id': member[1]
                    }
                    print(session)
                    return successMessage(result)
                else:
                    return errorMessage(401, '로그인에 실패하였습니다.')
            except KeyError as e:
                return errorMessage(400, f"{str(e)} key가 누락되어 있습니다.")
            except Exception as e:
                return errorMessage(500, str(e))
        else:
            return errorMessage(400, 'parameter key Err!')





@sign_api.route('/signup')
class signup(Resource):
    @sign_api.doc(description="회원 등록",
                  params={'email': '사용자 이메일',
                          'password': '사용자 비밀번호',
                          'name': '사용자 명',
                          'phone_number': "회원 번호"
                          })
    def post(self):
        """
                회원등록 (form)

                POST 요청으로 사용자의 회원등록을 처리합니다.
                """
        form_data = request.form
        dump_data = json.dumps(form_data, ensure_ascii=False)
        data = json.loads(dump_data)
        required_fields = ['id', 'email', 'password', 'name', 'phone_number']
        print("data: ", data)
        if all(data[key] for key in required_fields):
            try:
                is_valid_ep('email', data['email'])
                is_valid_ep('password',  data['password'])
                is_valid_ep('id', data['id'])
                is_valid_ep('phone', data['phone_number'])
                current_time = datetime.datetime.now()
                data["created_date"] = current_time.strftime('%Y-%m-%d %H:%M:%S')
                data["update_date"] = current_time.strftime('%Y-%m-%d %H:%M:%S')
                hashPw = generate_password_hash(data['password'])
                data['password'] = hashPw

                # 변경할 키
                key_mapping = {
                    'id': 'mb_id',
                    'email': 'mb_email',
                    'password': 'mb_pw',
                    'name': 'mb_name'
                }
                # 키를 변경한 튜플 리스트
                new_data = {key_mapping.get(k, k): v for k, v in data.items()}
                # 일단 가입 보류 상태를 키값으로 주기
                new_data['status'] = 'N'
                print("new_data", new_data)
                result = crudQuery('c', MAIN_DB_PATH, new_data, 'member')
                print(result[1])
                if isinstance(result, list):
                    # 이메일 인증 토큰 생성
                    token = serializer.dumps(new_data['mb_email'], salt='email-confirm')

                    # 인증 이메일 전송
                    link = url_for('sign_verify_email', token=token, _external=True)
                    print("link", link)
                    email_body = f'인증 링크: {link}'

                    send_email(new_data['mb_email'], '회원가입 이메일 인증', email_body, 'Auth')
                    print("이메일 발송 성공")
                    return result[0]
                else:
                    return result[0]
            except CustomValidException as e:
                return errorMessage(e.status_code, e.message)
            except KeyError as e:
                return errorMessage(400, f"{str(e)} key가 누락되어 있습니다.")
            except sqlite3.Error as e:
                return errorMessage(str(e))
            except Exception as e:
                return errorMessage(500, str(e))


@sign_api.route('/verify/<string:token>')
class VerifyEmail(Resource):
    def get(self, token):
        try:
            email = serializer.loads(token, salt='email-confirm', max_age=3600)
            print(email)
            data = {"status": "Y"}
            condition = 'mb_email = ?'
            param = (email,)
            get_db_data = crudQuery('u', MAIN_DB_PATH, data, 'member', condition, None, param)
            if isinstance(get_db_data, dict):
                return successMessage(f"이메일이 성공적으로 인증되었습니다. Token: {token}")
            else:
                return get_db_data
        except SignatureExpired:
            return errorMessage(400, "The token is expired")
        except BadSignature:
            return errorMessage(400, "Invalid token")

@sign_api.route('/check-email')
@sign_api.doc(description="이메일 체크",
              params={'email': '사용자 이메일'
                      })
class CheckEmail(Resource):
    def get(self):
        """
                이메일 체크

                GET 요청으로 사용자의 이메일 중복 체크를 처리합니다.
                """
        email = request.args.get("email")
        print("email", email)
        try:
            # Validate email format
            is_valid_ep('email', email)
            conn = sqlite3.connect(MAIN_DB_PATH)
            curser = conn.cursor()
            curser.execute('''SELECT count(*) FROM member WHERE mb_email = ?''', (email,))
            check = curser.fetchone()[0]
            if check > 0:
                print('x')
                return successMessage("이미 존재하는 이메일 입니다.")
            else:
                print('o')
                return successMessage("존재하지 않는 이메일 이므로 사용 가능합니다.")
        except CustomValidException as e:
            return errorMessage(e.status_code, e.message)
        except Exception as e:
            return errorMessage(500, str(e))



@sign_api.route('/check-id')
@sign_api.doc(description="아이디 체크",
              params={'id': '사용자 id'})
class CheckId(Resource):
    def get(self):
        """
                아이디 체크

                GET 요청으로 사용자의 아이디 중복 체크를 처리합니다.
                """
        id = request.args.get("id")
        print("id", id)
        try:
            # Validate email format
            is_valid_ep('id', id)
            conn = sqlite3.connect(MAIN_DB_PATH)
            curser = conn.cursor()
            curser.execute('''SELECT count(*) FROM member WHERE mb_id = ?''', (id,))
            check = curser.fetchone()[0]
            if check > 0:
                print('x')
                return successMessage("이미 존재하는 아이디 입니다.")
            else:
                print('o')
                return successMessage("존재하지 않는 아이디 이므로 사용 가능합니다.")
        except CustomValidException as e:
            return errorMessage(e.status_code, e.message)
        except Exception as e:
            return errorMessage(500, str(e))




@sign_api.route('/logout')
class logout(Resource):
    def get(self):
        try:
            # 세션에서 사용자 정보 제거
            session.pop('user_idx', None)
            session.pop('user_name', None)
            return successMessage("로그아웃을 완료하였습니다.")
        except Exception as e:
            return errorMessage(500, str(e))






