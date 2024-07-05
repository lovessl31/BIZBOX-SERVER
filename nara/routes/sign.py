import datetime
import os
import sqlite3


from nara import app, jwt_blocklist

# jwt token
from flask_jwt_extended import (create_access_token, jwt_required, create_refresh_token, get_jwt,
                                decode_token, get_jwt_identity, set_access_cookies)

from flask import request, url_for
import json
from dotenv import load_dotenv

from flask_restx import Namespace, Resource
from werkzeug.security import check_password_hash, generate_password_hash
from nara.utils.utils import successMessage, errorMessage, crudQuery, send_email
from nara.utils.valid import is_valid_ep
from nara.utils.err_handler import CustomValidException, DetailErrMessageTraceBack
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature






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
        client_ip = request.remote_addr
        print(client_ip)
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
                # 해쉬된 비번 확인 후 로그인 성공한다면
                if check_password_hash(member[2], mb_pw):
                    #  유저의 인덱스와 아이디 값 할당
                    mIdx = member[0]
                    mId = member[1]
                    mName = member[3]
                    # jwt 토큰에 식별자를 넣고 토큰 생성.
                    user_info = {"idx": mIdx,
                                 "id": mId}
                    access_token = create_access_token(identity=user_info)
                    refresh_token = create_refresh_token(identity=user_info)

                    r_token_data = decode_token(refresh_token)
                    created_at = datetime.datetime.fromtimestamp(r_token_data.get('iat'))  # 토큰 생성일
                    expired_at = datetime.datetime.fromtimestamp(r_token_data.get('exp'))  # 토큰 만료일
                    status = 'N'  # 토큰 취소 여부
                    print("mIdx:::::", mIdx)
                    c.execute('''SELECT COUNT(*) FROM token WHERE mb_idx = ?''', (mIdx,))
                    existing_token = c.fetchone()[0]

                    if existing_token > 0:
                        c.execute('''
                            UPDATE token SET payload=?, created_date=?, exp_date=?, status=? WHERE mb_idx = ?
                        ''', (refresh_token, created_at, expired_at, status, mIdx))
                    else:
                        c.execute('''
                            INSERT INTO token (payload, mb_idx, created_date, exp_date, status) VALUES (?, ?, ?, ?, ?)
                        ''', (refresh_token, mIdx, created_at, expired_at, status))

                    conn.commit()
                    conn.close()

                    result = {
                        'loginMsg': "Y",
                        "accessToken": access_token,
                        "refreshToken": refresh_token,
                        "mail_auth": "Y",
                        'resultMsg': f'{mName}님 환영 합니다.'
                    }
                    if member[4] == 'N':
                        result["mail_auth"] = 'N'
                    # JWT를 쿠키에 설정
                    set_access_cookies(successMessage(result), access_token)
                    return successMessage(result)
                else:
                    return errorMessage(401, '로그인에 실패하였습니다.')
            except KeyError as e:
                return errorMessage(400, f"{str(e)} key가 누락되어 있습니다.")
            except Exception as e:
                DetailErrMessageTraceBack(e)
                return errorMessage(500, str(e))
        else:
            return errorMessage(400, 'parameter key Err!')



@sign_api.route('/logout')
class Logout(Resource):
    @sign_api.response(200, 'Success')
    @jwt_required()
    def post(self):
        try:
            jti = get_jwt()['jti']  # jti : 토큰을 고유ID로 저장
            rrr = get_jwt()
            print(rrr)
            jwt_blocklist.add(jti)  # jwt_blocklist : 토큰의 고유ID, 토큰 유지 기간, 토큰 유지 기간 설정 여부
            response = successMessage("로그아웃이 정상 처리 되었습니다.")
            # 쿠키에서 토큰 삭제
            response.set_cookie(app.config['JWT_ACCESS_COOKIE_NAME'], '', expires=0)
            response.set_cookie(app.config['JWT_REFRESH_COOKIE_NAME'], '', expires=0)
            return response  # jwt_bloacklist에 jti만 넣어주고 나머지 생략하면 토큰 즉시 파괴
        except sqlite3.Error as e:
            return errorMessage(str(e))
        except Exception as e:
            return errorMessage(500, str(e))





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
                # 문자 템플릿 유효성
                for v_type in required_fields:
                    if v_type == 'name':
                        continue
                    elif v_type == 'phone_number':
                        is_valid_ep('phone', data[v_type])
                    else:
                        is_valid_ep(v_type, data[v_type])

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
                user_idx = result[1]
                if isinstance(result, list):
                    # 이메일 인증 토큰 생성
                    mb_email = new_data['mb_email']
                    mb_id = new_data['mb_id']
                    token = serializer.dumps({'mb_email': mb_email, 'mb_id': mb_id}, salt='email-confirm')

                    # 인증 이메일 전송
                    link = url_for('sign_verify_email', token=token, _external=True)
                    print("link", link)
                    email_body = f'인증 링크: {link}'

                    send_email(new_data['mb_email'], '회원가입 이메일 인증', email_body, 'Auth', user_idx)
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
            data = serializer.loads(token, salt='email-confirm', max_age=3600)
            mb_email = data['mb_email']
            mb_id = data['mb_id']
            editData = {"status": "Y"}
            condition = 'mb_email = ? AND mb_id = ?'
            param = (mb_email, mb_id)
            get_db_data = crudQuery('u', MAIN_DB_PATH, editData, 'member', condition, None, param)

            # 인증 되지 않은 기존 같은 이메일 삭제
            delCondition = 'mb_email = ? AND status = ?'
            delParam = (mb_email, 'N')
            crudQuery('d', MAIN_DB_PATH, None, 'member', delCondition, None, delParam)

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
            curser.execute('''SELECT count(*) FROM member WHERE mb_email = ? AND status = 'Y' ''', (email,))
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





# 액세스 토큰 재발급 엔드포인트
@sign_api.route('/refresh')
class Refresh(Resource):
    @sign_api.response(200, 'Success')
    @jwt_required(refresh=True)
    def post(self):
        """
                        토큰 재발급

                        post 요청으로 토큰 재발급 처리합니다.
        """
        data = get_jwt_identity()
        refresh_payload = request.headers['Authorization'].replace('Bearer ', '')
        print(f"토큰 재발급:{data}")
        print(f"리프레시토큰:{refresh_payload}")
        if refresh_payload:
            try:
                conn = sqlite3.connect(MAIN_DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''SELECT payload FROM token WHERE payload = ?''', (refresh_payload,))
                is_rf_token = cursor.fetchone()[0]
                conn.commit()
                conn.close()
                user_info = {"idx": data['idx'],
                             "id": data['id']
                             }
                if is_rf_token == refresh_payload:
                    access_token = create_access_token(identity=user_info)
                    result = {"accessToken": access_token,
                              "resultCode": 200,
                              'resultDesc': "토큰을 재발급 하였습니다."}
                    set_access_cookies(successMessage(result), access_token)
                    return successMessage(result)
                else:
                    return errorMessage(400, "일치 하는 토큰이 존재하지않습니다.")
            except KeyError as e:
                return errorMessage(400, f"{str(e)} key가 누락되어 있습니다.")
            except sqlite3.Error as e:
                return errorMessage(str(e))
            except Exception as e:
                return errorMessage(500, str(e))
        else:
            return errorMessage(400)






