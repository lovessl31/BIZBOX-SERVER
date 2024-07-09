import sqlite3
from jinja2 import Environment, FileSystemLoader
from flask import current_app

import os

# DB 접속 경로
MAIN_DB_PATH = r"C:\work\NARA_CRAWL\nara\db\bizbox.db"

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



            # 서브 쿼리를 사용하지않고 조인을 사용하면 업종코드 별로 데이터가 생성되기에 notice_list 를 여러번 도는 비효율적인 로직임으로 서브쿼리를 사용해
            # 유저가 속한 업종코드들을 하나의 컬럼으로 묶어서 가져와 해당하는 업종공고로 메일로 보내줄수 있어 최대 3배의 효율을 낼수 있음
            
            c.execute('''SELECT t.bms_name,
                                t.bms_email,                                 
                                t.bms_area,
                                t.bms_task,
                                t.bms_industry,                                
                                (
                                 SELECT GROUP_CONCAT(bk.keyword, ', ')
                                 FROM bms_keyword bk
                                 WHERE bk.bms_idx = t.bms_idx
                                )AS keyword_cd_list,  
                                t.mb_idx                                                           
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
                # 유저 서비스 테이블 값
                user_service_name = bms[0]
                user_area_cd = bms[2]
                user_task_cd = bms[3]
                user_industry_cd = bms[4]
                keywords_list = bms[5].split(',')

                mb_idx = bms[6]

                # 입찰 공고 조회

                '''
                7.02. 키워드를 가지고 조회하는 쿼리 생성해야함
                
                '''
                base_query = ('''SELECT b.np_idx,
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

                # 키워드가 있을 경우 조건 추가
                if keywords_list:
                    # 각 키워드를 np_title과 demand_agency에 대해 조건 추가
                    title_conditions = []
                    agency_conditions = []
                    for key in keywords_list:
                        title_conditions.append(f"b.np_title LIKE '%{key.strip()}%'")
                        agency_conditions.append(f"b.demand_agency LIKE '%{key.strip()}%'")

                    # 키워드 조건을 OR로 결합
                    title_condition_str = ' OR '.join(title_conditions)
                    agency_condition_str = ' OR '.join(agency_conditions)

                    # 최종 쿼리 생성 () 구분을 확실히 안하면 조회가 이상하게 되는걸 유념.
                    final_query = f"{base_query} AND ({title_condition_str} OR {agency_condition_str})"
                else:
                    # 키워드가 없을 경우 기본 쿼리 사용
                    final_query = base_query

                c.execute(final_query)
                notice_list = c.fetchall()
                print("키워드 검색한 입찰 공고 리스트", notice_list)

                for notice in notice_list:
                    # 업무 명 업무 코드로 전환
                    task_map = {
                        "물품": '1', "외자": '2', "공사": '3', "용역": '5',
                        "리스": '6', "비축": '11', "기타": '4', "민간": '20'
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

                    # html 문서에 들어갈 템플릿 정의
                    template_data = {
                        'bid_id': notice_idx,
                        'industry_cd': indusCd,
                        'bid_name': title,
                        'bid_agency': agency,
                        'bid_o_dt': tender_o_dt,
                        'bid_c_dt': tender_c_dt
                    }

                    # 모든 조건에 부합시 배열에 담기
                    if indusCd in user_industry_cd and area_g_cd in user_area_cd and task_Cd in user_task_cd:
                        temp_data_list.append(template_data)

                if temp_data_list:
                    print("temp_data_list--------", temp_data_list)
                    moduleTemplate = {
                        'customer_name': user_service_name,
                        'bids': temp_data_list
                    }
                    html_content = template.render(moduleTemplate, url_for=initUrlFor)
                    service_send_email(bms[1], f"맞춤 입찰 공고 안내", temp_data_list, "BMS", html_content, mb_idx)
                    print(1)
            conn.close()
        except Exception as e:
            print(str(e))
        finally:
            conn.close()