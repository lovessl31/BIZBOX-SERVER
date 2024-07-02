import sqlite3
from jinja2 import Environment, FileSystemLoader
from flask import current_app

import os

# DB 접속 경로
MAIN_DB_PATH = r"C:\work\NARA_CRAWL\nara\db\bizbox.db"

# service_send_email(receiver_email, subject, body, mail_type, html_content)
def send_bid_mailing(app, initUrlFor):
    with app.app_context():
        try:
            # init에서 실행할때 순환종속성 문제가 생기기때문에 함수가 필요할때 가져오기
            from nara.utils.utils import service_send_email
            from nara.utils.err_handler import DetailErrMessageTraceBack

            conn = sqlite3.connect(MAIN_DB_PATH)
            c = conn.cursor()
            # env = Environment(loader=FileSystemLoader('nara/resources/html'))
            # # 파일 가져오기
            # template = env.get_template('biz_mail_list.html')
            # 현재 파일의 디렉토리 경로
            env = Environment(loader=FileSystemLoader(r'C:\work\NARA_CRAWL\templates'))

            # 템플릿 로딩
            template = env.get_template('biz_mail_list.html')


            # notice = c.execute('''SELECT * FROM bid_notice WHERE created_date >= DATE('now', '-2 hour')''')
            notice = c.execute('''SELECT b.np_idx,
                                         b.industry_cd,
                                         b.taskClCds,
                                         b.np_title,                                     
                                         b.demand_agency,
                                         b.tender_open_date,
                                         b.tender_close_date,
                                         ba.area_g_cd
                                  FROM bid_notice b 
                                  LEFT JOIN bid_notice_area ba
                                  ON b.np_idx = ba.np_idx
                                  WHERE b.created_date >= DATETIME('now', '-2 hour', 'localtime')''')

            notice_list = notice.fetchall()
            print("notice_list", notice_list)
            if not notice_list:
                print("No notices found")
                return

            # 서브 쿼리를 사용하지않고 조인을 사용하면 업종코드 별로 데이터가 생성되기에 notice_list 를 여러번 도는 비효율적인 로직임으로 서브쿼리를 사용해
            # 유저가 속한 업종코드들을 하나의 컬럼으로 묶어서 가져와 해당하는 업종공고로 메일로 보내줄수 있어 최대 3배의 효율을 낼수 있음
            
            c.execute('''SELECT t.bms_name,
                                t.bms_email, 
                                t.bms_area,     
                                t.bms_taskCd,
                                (
                                 SELECT GROUP_CONCAT(i.industry_cd, ', ')
                                 FROM bms_industry i
                                 WHERE i.bms_idx = t.bms_idx
                                )AS industry_cd_list
                                
                         FROM bms_tbs t
                         ''')
            bms_data_list = c.fetchall()

            print('_', bms_data_list)
            if not bms_data_list:
                print("No recipients found")
                return

            for bms in bms_data_list:
                temp_data_list = []
                print('bms: ', bms)
                for notice in notice_list:
                    # 업무 명 업무 코드로 전환
                    task_map = {
                        "물품": 1, "외자": 2, "공사": 3, "용역": 5,
                        "리스": 6, "비축": 11, "기타": 4, "민간": 20
                    }
                    print(notice)
                    notice_idx = notice[0]
                    indusCd = notice[1]
                    task = notice[2]
                    task_Cd = task_map[task]
                    title = notice[3]
                    agency = notice[4]
                    tender_o_dt = notice[5]
                    tender_c_dt = notice[6]
                    area_g_cd = notice[7]

                    # print(type(task_Cd))
                    # print("task_Cd", task_Cd)


                    # 유저 서비스 테이블 값
                    user_industry_cd = bms[4]
                    user_task_cd = bms[3]
                    user_area_cd = bms[2]
                    user_service_name = bms[0]
                    # html 문서에 들어갈 템플릿 정의
                    template_data = {
                        'bid_id': notice_idx,
                        'industry_cd': indusCd,
                        'bid_name': title,
                        'bid_agency': agency,
                        'bid_o_dt': tender_o_dt,
                        'bid_c_dt': tender_c_dt
                    }

                    # 업무 전체
                    if int(user_task_cd) == 0:
                        if indusCd in user_industry_cd and user_area_cd == area_g_cd:
                            temp_data_list.append(template_data)
                    # 특정 업무
                    else:
                        if indusCd in user_industry_cd and user_area_cd == area_g_cd and user_task_cd == task_Cd:
                            temp_data_list.append(template_data)

                if temp_data_list:
                    print("temp_data_list--------", temp_data_list)
                    moduleTemplate = {
                        'customer_name': user_service_name,
                        'bids': temp_data_list
                    }
                    html_content = template.render(moduleTemplate, url_for=initUrlFor)
                    print("html_content", html_content)
                    service_send_email(bms[1], f"맞춤 입찰 공고 안내", temp_data_list, "BMS", html_content)
                    print(1)
            conn.close()
        except Exception as e:
            print(str(e))
        finally:
            conn.close()