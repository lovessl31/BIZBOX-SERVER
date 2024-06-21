import sqlite3
from jinja2 import Environment, FileSystemLoader
from nara.utils.utils import service_send_email


# DB 접속 경로
MAIN_DB_PATH = r"C:\work\NARA_CRAWL\nara\db\bizbox.db"

# service_send_email(receiver_email, subject, body, mail_type, html_content)
def send_bid_mailing():
    try:
        conn = sqlite3.connect(MAIN_DB_PATH)
        c = conn.cursor()
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('biz_mail_tamplate.html')
        notice = c.execute('''SELECT * FROM bid_notice WHERE created_date >= DATE('now', '-2 hour')''')
        notice_list = notice.fetchall()
        for notice in notice_list:
            notice_idx = notice[0]
            indusCd = notice[1]
            title = notice[2]
            uniqueCd = notice[3]
            agency = notice[4]
            tender_o_dt = notice[5]
            tender_c_dt = notice[6]
            amount = notice[7]
            est_prise = notice[8]
            budget = notice[9]
            vat = notice[10]

            c.execute('''SELECT t.bms_name,
                                t.bms_email,                                
                                i.industry_cd
                                FROM bms_tbs t
                                LEFT JOIN bms_industry i
                                ON t.bms_idx = i.bms_idx
                                WHERE i.industry_cd = ?
                                ''', (indusCd,))
            bms_data_list = c.fetchall()
            print('_', bms_data_list)
            for bms in bms_data_list:
                print('bms: ', bms)
                template_data = {
                    'customer_name': bms[0],
                    'industry_cd': indusCd,
                    'bid_name': title,
                    'bid_num': uniqueCd,
                    'bid_agency': agency,
                    'bid_o_dt': tender_o_dt,
                    'bid_c_dt': tender_c_dt,
                    'amount': amount,
                    'est': est_prise,
                    'budget': budget,
                    'vat': vat
                }
                html_content = template.render(template_data)
                if bms[2] == indusCd:
                    service_send_email(bms[1], "맞춤 입찰 공고 안내", template_data, "BMS", html_content)
    except Exception as e:
        print(e)


