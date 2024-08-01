#!/usr/bin/env python
# coding: utf-8

# In[62]:


# step1.패키지 설치
from bs4 import BeautifulSoup
from datetime import datetime

import os
import re
import json
import time
import random
import requests

import sqlite3

from nara.utils.utils import (convert_size, get_file_type_and_extension, insert_file_info, generate_unique_number,
                              generate_unique_filename, insert_bid_notice, generate_bidNo)
from nara.utils.err_handler import CustomException

from config import get_config
# 로그 기록
import sys
import logging


from dotenv import load_dotenv
load_dotenv()
# DB 접속 경로

MAIN_DB_PATH = get_config()['DATABASE']
print(MAIN_DB_PATH)

# 기본 로거 생성 후 출력 기준 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 스트림 핸들러 추가
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)

# 로그 형식 설정
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S %p')
stream_handler.setFormatter(formatter)

# 로거에 핸들러 추가
logger.addHandler(stream_handler)


# In[63]:




def dtl_fileDownload(fileSeq, fileName, ti_name, current_dir, industry_cd, notice_idx):
    # 파일 다운로드 URL 설정(/ep/co/fileDownload.do?fileTask=NOTIFY&fileSeq=)
    url = f"https://www.g2b.go.kr:8081/ep/co/fileDownload.do?fileTask=NOTIFY&fileSeq={fileSeq}"

    # 파일 다운로드 요청 보내기
    response = requests.get(url)
    current_dt = datetime.now().strftime("%Y-%m-%d")
    o_file_name = fileName
    # print("oneFileDownloadUrl : ", url)
    # 파일 저장
    if response.status_code == 200:
        
        conn = sqlite3.connect(MAIN_DB_PATH)
        c = conn.cursor()
        file_size = convert_size(len(response.content))
        file_type, file_ext = get_file_type_and_extension(fileName)

        # 문자열에서 숫자만 추출하여 리스트로 반환
        numbers = re.findall(r'\d+', fileName)
        # 리스트에 저장된 숫자들을 문자열로 결합
        fileName = ''.join(numbers)

        edit_S_f_Name = re.sub(r'[-_]', '', f"{fileName}")
        s_fileName = f"S_{edit_S_f_Name}{file_ext}"
        unique_s_fileName = generate_unique_filename(f'{current_dir}/Nattachment/{current_dt}/{industry_cd}/{ti_name}'
                                                     , s_fileName)
        f_path = f'{current_dir}/Nattachment/{current_dt}/{industry_cd}/{ti_name}/{unique_s_fileName}'
        # 파일을 바이너리 형식으로 저장
        current_dt = datetime.now().strftime("%Y-%m-%d %H:00")
        insert_file_info(c, o_file_name, unique_s_fileName, file_size, file_type, file_ext, f_path, url, current_dt)
        file_idx = c.lastrowid
        # idx가 존재할때만 중간 테이블에 데이터 삽입
        if file_idx > 0 and notice_idx > 0:
            c.execute('''INSERT INTO bid_file(file_idx, np_idx) VALUES (?,?)''', (file_idx, notice_idx))
        with open(f_path, 'wb') as f:
            f.write(response.content)
        conn.commit()
        conn.close()
    else:
        print(f"파일 다운로드에 실패했습니다. 상태 코드: {response.status_code}")


# In[64]:


# 첨부파일(eeOrderAttachFileDownload)
def extract_attachments(soup, ti_name, current_dir, industry_cd, notice_idx):
    # 첨부파일 정규표현식 패턴 설정(대소문자 구분 X)
    pattern = re.compile(r'fileDownload', re.IGNORECASE)
    attach_pattern = re.compile(r"'(.*?)'", re.IGNORECASE)
    attachments = []  # 첨부 파일명 리스트

    for link in soup.find_all('a', href=True):
        if pattern.search(link['href']):
            file_name = link.get_text(strip=True)
            attachments.append(file_name)

            # 파일 다운로드
            matches = attach_pattern.findall(link['href'])
            if len(matches) == 2:
                # dtl_fileDownload
                # print("ex_at",
                #       "fname: ", file_name,
                #       "matches[1]: ", matches[1],
                #       "ti_name: ", ti_name
                #       )
                dtl_fileDownload(matches[0], matches[1], ti_name, current_dir, industry_cd, notice_idx)
            else:
                # eeOrderAttachFileDownload
                eeOrderAttachFileDownload(matches[1], matches[2], matches[3], matches[4], file_name, ti_name,
                                          current_dir, industry_cd, notice_idx)

    return attachments


# In[65]:


# step3. 첨부 파일
def eeOrderAttachFileDownload(eeOrderAttachFileNo, eeOrderAttachFileSeq, rfpNo, rfpOrd, file_name, ti_name,
                              current_dir, industry_cd, notice_idx):
    # 파일 다운로드 URL 생성
    url = f"https://rfp.g2b.go.kr:8426/cmm/FileDownload.do?atchFileId={eeOrderAttachFileNo}&fileSn={eeOrderAttachFileSeq}&rfpNo={rfpNo}&rfpOrd={rfpOrd}"
    # 파일 다운로드 요청 보내기
    response = requests.get(url)
    # print("FileDownloadUrl : ", url)
    # print("eeOrderAttachFileNo", eeOrderAttachFileNo)
    # print("eeOrderAttachFileNo3", rfpNo)
    current_dt = datetime.now().strftime("%Y-%m-%d")
    # 파일 저장
    if response.status_code == 200:
        
        conn = sqlite3.connect(MAIN_DB_PATH)
        c = conn.cursor()
        file_size = convert_size(len(response.content))
        file_type, file_ext = get_file_type_and_extension(file_name)

        s_fileName = f"B_{eeOrderAttachFileNo}_{rfpNo}{file_ext}"
        # 중복된 파일네임이면 뒤에 뒤에 카운팅을 붙여 고유의 이름 생성
        unique_s_fileName = generate_unique_filename(f'{current_dir}/Nattachment/{current_dt}/{industry_cd}/{ti_name}'
                                                     , s_fileName)
        f_path = f'{current_dir}/Nattachment/{current_dt}/{industry_cd}/{ti_name}/{unique_s_fileName}'
        # 중복 데이터 건너뛰어서 insert 하는 함수
        current_dt = datetime.now().strftime("%Y-%m-%d %H:00")
        insert_file_info(c, file_name, unique_s_fileName, file_size, file_type, file_ext, f_path, url, current_dt)
        file_idx = c.lastrowid
        # idx가 존재할때만 중간 테이블에 데이터 삽입
        if file_idx > 0 and notice_idx > 0:
            c.execute('''INSERT INTO bid_file(file_idx, np_idx) VALUES (?,?)''', (file_idx, notice_idx))
        # 파일을 바이너리 형식으로 저장
        with open(f_path, 'wb') as f:
            f.write(response.content)
        conn.commit()
        conn.close()
    else:
        print(f"파일 다운로드에 실패했습니다. 상태 코드: {response.status_code}")


# In[66]:


# step5. 부가세
def calculate_vat(pa, ap):
    v_pa = int(pa.replace(",", "")) if pa else 0  # 사업금액
    v_ap = int(ap.replace(",", "")) if ap else 0  # 추정가격

    # 부가세 계산
    vat = v_pa - v_ap

    # 포매팅 (ex. 000,000원)
    format_vat = "{:,.0f}".format(vat)

    return format_vat + "원"


# In[67]:


# step5. 추정가격
def calculate_ep(ea, vat):
    v_ea = int(ea.replace(",", "")) if ea else 0  # 추정가격(부가세 불포)
    v_vat = int(vat.replace(",", "")) if vat else 0  # 부가세

    # 계산
    ep = v_ea + v_vat

    # 포매팅 (ex. 000,000원)
    format_ep = "{:,.0f}".format(ep)

    return format_ep + "원"



def is_number(s):
    # 숫자로만 이루어진지 판별하는 정규표현식
    return bool(re.match(r'^[0-9]+$', s))


# 부가세 자체적 으로 빼는 함수
def calculate_empty_vat(price):
    # 가격 문자열에서 불필요한 문자 제거
    cleaned_price = re.sub(r'\D', '', price)

    # 정수로 변환
    v_price = int(cleaned_price) if cleaned_price else 0

    # 부가세 10% 빼기
    no_vat_price = v_price / 1.1

    # 소수점 반올림
    rounded_price = round(no_vat_price)
    # 포매팅 (ex. 000,000원)
    format_p = "{:,.0f}".format(rounded_price) + '원'
    
    return format_p


# In[68]:


# step4. 입찰공고 상세
def extract_details(sb_soup):
    details = {}  # 일반 정보 딕셔너리
    epx = {}  # 추정가격(부가세 불포함) 딕셔너리
    for th in sb_soup.select('table.table_info > tr > th > p'):
        th_text = th.get_text(strip=True)

        # search 변경(table.table_info > tr > th > td)
        td = th.find_parent('th').find_next_sibling('td')

        if td and td.find('div'):
            td_text = td.find('div').get_text(strip=True)
        else:
            td_text = None
        # 일치하는 th와 맞는 td값을 저장
        if th_text == '입찰개시일시':
            details['입찰개시일시'] = td_text
        elif th_text == '입찰마감일시':
            details['입찰마감일시'] = td_text
        elif th_text == '제안서제출시작일시':
            details['제안서제출시작일시'] = td_text
        elif th_text == '제안서제출마감일시':
            details['제안서제출마감일시'] = td_text
        elif th_text == '사업금액(추정가격 + 부가세)':
            details['사업금액(추정가격 + 부가세)'] = td_text
        elif th_text == '추정가격':
            # (ex."000,000원")까지 출력
            ap = td_text
            index = ap.find('원')
            if index != -1:
                ap = ap[:index + 1].strip()
            details['추정가격'] = ap
        elif th_text == '추정금액':
            details['추정금액'] = td_text[1:]
        elif th_text == '배정예산':
            if len(td_text) > 1 and is_number(td_text[0]):
                details['배정예산'] = td_text
            else:
                details['배정예산'] = td_text[1:]
        elif th_text == '부가가치세':
            details['부가세'] = td_text[1:]
        elif th_text == '추정가격(부가가치세 불포함)':
            epx['추정가격(부가가치세 불포함)'] = td_text[1:]
        elif th_text == '부가가치세포함여부':
            details['추정가격'] = ""
            details['부가가치세포함여부'] = td_text
        elif th_text == '참가가능지역':
            print("참가가능지역. : ", td_text)
            details['참가가능지역'] = td_text

    # 부가세 계산(부가가치세로 이미 들어온 경우 X)
    if '부가세' not in details and '사업금액(추정가격 + 부가세)' in details and '추정가격' in details:
        pa = details.get('사업금액(추정가격 + 부가세)')[:-1]
        ap = details.get('추정가격')[:-1]
        vat = calculate_vat(pa, ap)
        details['부가세'] = vat

    # 추정가격(부가세 불포함) 계산
    if '추정가격' not in details:
        print('222', )
        ea = epx.get('추정가격(부가가치세 불포함)')[:-1]
        vat = details.get('부가세')[:-1]
        ep = calculate_ep(ea, vat)
        details['추정가격'] = ep



    if '부가가치세포함여부' in details:
        print("부가가치세포함여부", details.get('부가가치세포함여부'))
        vatyn = details.get('부가가치세포함여부')[:6]
        print("vatyn: ", vatyn)
        if vatyn.strip() == '부가세 포함':
            # 사업 금액이 추정가격 계산에 더 정확함
            amount = details.get('사업금액(추정가격 + 부가세)', None)
            if amount is not None:
                details['추정가격'] = amount
            else:
                details['추정가격'] = details.get('배정예산', '')
        else:
            amount = details.get('사업금액(추정가격 + 부가세)', None)
            if amount is not None:
                emptyPrice = calculate_empty_vat(amount)
            else:
                emptyPrice = calculate_empty_vat(details.get('배정예산', ''))
            details['추정가격'] = emptyPrice
    return details


# In[69]:


# step6. 크롤링
def crawl_website(response, soup, current_dir, industry_cd, last_five_urls):
    if response.status_code == 200:
        articles = []  # 입찰공고 저장
        invalid_characters = r'[<>:"/\\|?*]'  # 폴더명 부정 특수 기호

        # 웹 페이지에서 제목과 링크를 가져와서 articles 리스트에 추가
        for article in soup.select('#resultForm > div.results > table > tbody > tr'):
            address = article.select_one('td.tl > div > a')['href']  # 주소값
            print(address)
            # 이전 페이지 마지막 값과 같으면 다음걸 넘어가서 다음걸 읽음
            if address in last_five_urls:
                continue
            taskClCds = article.select_one('td > div').get_text()     # 업무명
            title = article.select_one('td.tl > div > a').get_text()  # 공고명
            agency = article.select_one('td:nth-child(6) > div')  # 수요기관
            unique_id = f"D_{generate_unique_number(address)}"
            # 날짜
            path_dt = datetime.now().strftime("%Y-%m-%d")
            # 공고명에 따른 값 저장
            # sub_아이템
            sb_response = requests.get(address)
            time.sleep(1 + random.random())
            if sb_response.status_code == 200:
                # BeautifulSoup을 사용하여 HTML 파싱
                sb_soup = BeautifulSoup(sb_response.text, 'html.parser')
                # 세부 정보 추출
                details = extract_details(sb_soup)
                # 세부 정보 분리
                bidNo = generate_bidNo(address) # 얘는 분리 데이터 아니고 공고 번호 추출 하는 함수 사용
                demand_agency = agency.get_text()
                print("details:", details)
                tender_open_date = details.get('입찰개시일시')
                tender_close_date = details.get('입찰마감일시')
                # 존재하지 않으면 빈 문자열
                pj_amount = details.get('사업금액(추정가격 + 부가세)', "0원")
                est_price = details.get('추정가격', "0원")
                budget = details.get('배정예산', "0원")
                vat = details.get('부가세', "0원")
                area = details.get('참가가능지역', '')
                #  만약 추정가격이 존재하지않고 '추정가격(부가가치세 불포함)' 라면 부가세를 더해서 추정가격을 만들어서 할당.
                if '추정가격(부가가치세 불포함)' in details:
                    isNonVatPrice = details.get('추정가격(부가가치세 불포함)')
                    # 문자열 이기에 숫자만 추출해서 정수로 변환
                    none_est_price_num = int(isNonVatPrice.replace(',', '').replace('원', ''))
                    vat_num = int(vat.replace(',', '').replace('원', ''))
                    # 정수끼리 합해주기
                    price_sum = none_est_price_num + vat_num
                    # 원래의 형식으로 다시 변환
                    est_price = "{:,}원".format(price_sum)
                    print("부가세 포함 결합 완료 : ", est_price)


                # 첨부파일을 불러오기전에 DB에 데이터를 삽입하고 그 삽입한 idx를 첨부파일 저장 함수에 인자로 넘겨줘서
                # 파일정보를 DB에 insert할때 중간 테이블에 입찰정보의 idx 정보와 파일의 idx 정보를 넣어줘야한다.
                conn = sqlite3.connect(MAIN_DB_PATH)
                cursor = conn.cursor()
                # 중복 건너뛰고 데이터 삽입
                insert_bid_notice(cursor, industry_cd, title, bidNo, demand_agency, tender_open_date, tender_close_date, pj_amount
                                  , est_price, budget, vat, taskClCds, area)
                # insert 한 idx 추출
                notice_idx = cursor.lastrowid
                # # 현재 어떤 업종 코드인지 파악하고 삽입
                # cursor.execute('''SELECT option_idx FROM bid_option WHERE option_group = ? AND option_value = ?''',
                #                ('industry', industry_cd))
                # indus_option_idx = cursor.fetchone()[0]
                # if indus_option_idx and notice_idx > 0:
                #     cursor.execute('''INSERT INTO entity_option(entity_idx, entity_type, option_idx)VALUES(?, ?, ?)''',
                #                    (notice_idx, 'bid_notice', indus_option_idx))
                conn.commit()
                conn.close()

                count = 1  # 폴더명 겹침 방지
                try:
                    # ti_name = re.sub(invalid_characters, '_', title)
                    os.makedirs(f'{current_dir}/Nattachment/{path_dt}/{industry_cd}/{unique_id}')
                except FileExistsError:  # 폴더명 겹침
                    unique_id = f'{unique_id}_{count}'
                    os.makedirs(f'{current_dir}/Nattachment/{path_dt}/{industry_cd}/{unique_id}')
                    count += 1

                # 세부 첨부파일
                attachments = extract_attachments(sb_soup, unique_id, current_dir, industry_cd, notice_idx)
                # 저장
                articles.append({
                    '주소': address,
                    '공고명': title,
                    '수요기관': demand_agency,
                    **details,  # 세부 정보 추가(**unpacking)
                    '첨부파일': attachments
                })
                current_dt = datetime.now().strftime("%Y-%m-%d")
                save_to_json(articles, current_dir, current_dt, industry_cd)
            else:
                # 요청이 실패한 경우 에러 메시지 출력
                print('Failed to retrieve the webpage. Status code:', response.status_code)
        return articles
    else:
        # 요청이 실패한 경우 에러 메시지 출력
        print('Failed to retrieve the webpage. Status code:', response.status_code)
        return None


# In[70]:


# step7. 전체 크롤링
def to_more(page_no, current_dt, industry_cd):
    # 현재 페이지 번호와 증가할 페이지 번호를 설정
    curr_page_no = page_no
    max_page_view_no = curr_page_no
    today = current_dt.split("/")
    year = today[0]
    month = today[1]
    day = today[2]

    # 현재 페이지의 URL 설정
    curr_list_url = f"https://www.g2b.go.kr:8101/ep/tbid/tbidList.do?bidSearchType=1&currentPageNo=1&fromBidDt={year}%2F{month}%2F{day}&industryCd={industry_cd}&radOrgan=1&recordCountPerPage=30&regYn=Y&searchDtType=1&searchType=1&toBidDt={year}%2F{month}%2F{day}"

    # URL을 구성하여 다음 페이지로 이동
    main_url = curr_list_url[:curr_list_url.index("?") + 1]
    param_url = curr_list_url[curr_list_url.index("?") + 1:]
    req_array = param_url.split("&")
    next_url = main_url

    for item in req_array:
        if "currentPageNo" in item:
            next_url += f"currentPageNo={curr_page_no}&"
        elif "maxPageViewNoByWshan" in item:
            next_url += f"maxPageViewNoByWshan={max_page_view_no}&"
        else:
            next_url += item + "&"

    # 현재 페이지 번호가 URL에 없으면 추가
    if "currentPageNo" not in next_url:
        next_url += f"currentPageNo={curr_page_no}&"

    # maxPageViewNoByWshan가 URL에 없으면 추가
    if "maxPageViewNoByWshan" not in next_url:
        next_url += f"maxPageViewNoByWshan={max_page_view_no}&"

    return next_url


# In[71]:

def save_to_json(articles, current_dir, current_dt, industry_cd):
    # JSON 파일 저장할 디렉토리 생성
    json_dir = os.path.join(current_dir, 'json', current_dt)
    json_dir = json_dir.replace("\\", "/")
    os.makedirs(json_dir, exist_ok=True)

    # 기존 JSON 파일 읽어오기
    json_filename = f'Narticles_{industry_cd}.json'
    json_path = f"{json_dir}/{json_filename}"

    existing_articles = []
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='UTF-8') as f:
            existing_articles = json.load(f)

    # 새로운 데이터를 기존 데이터에 추가하고 중복 제거
    combined_articles = existing_articles + articles
    unique_articles = {article['주소']: article for article in combined_articles}.values()

    # 중복 제거된 데이터를 JSON 파일에 저장
    with open(json_path, 'w', encoding='UTF-8') as f:
        json.dump(list(unique_articles), f, ensure_ascii=False, indent=4)

    print(f"데이터가 성공적으로 JSON 파일에 저장되었습니다: {json_path}")


# json 저장
def main(industry_cd):
    try:
        current_dir = f"{os.getcwd()}/crawl"
        # 백슬래시를 슬래시로 교체
        current_dir = current_dir.replace("\\", "/")

        # 현재 디렉토리
        if os.getenv('APP_ENV') == 'prod':
            current_dir = f"{current_dir}/prod"
        elif os.getenv('APP_ENV') == 'dev':
            current_dir = f"{current_dir}/dev"
        print("current_dir: ", current_dir)
        path_dt = datetime.now().strftime("%Y-%m-%d")

        # # 크롤링 전 파일 초기화 → 중복 파일 방지
        # if os.path.exists(f"{current_dir}/Nattachment/{path_dt}/{industry_cd}"):
        #     shutil.rmtree(f"{current_dir}/Nattachment/{path_dt}/{industry_cd}")

        # 오늘 날짜 데이터 → 데이터 검색을 위함
        current_dt = datetime.now().strftime("%Y/%m/%d")

        check = 0  # 페이지 별 데이터 값 체크

        # 사이트(최신화)
        url = f"https://www.g2b.go.kr:8101/ep/tbid/tbidList.do?searchType=1&bidSearchType=1&searchDtType=1&radOrgan=1&regYn=Y&recordCountPerPage=30&fromBidDt={current_dt}&toBidDt={current_dt}&industryCd={industry_cd}&currentPageNo=1"
        print(url)
        page_no = 2  # 페이지 조회 번호
        articles = []
        last_five_urls = []
        while True:
            response = requests.get(url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 페이지별 데이터 유무 확인
                if '검색된 데이터가 없습니다.' in soup.get_text():
                    print(1)
                    break
                else:
                    print(9)
                    data = crawl_website(response, soup, current_dir, industry_cd, last_five_urls)

                    # 다음 페이지로 넘어갈때 나라장터에서 새로운 데이터가 생기면 이전 페이지의 마지막 데이터가 다음페이지의 첫번째가 되서 중복 에러가 생김
                    # 그래서 배열의 마지막 객체의 특정 키 값 가져와서 다음 페이지의 첫번째값과 비교해서 같으면 pass 처리
                    if data:
                        print("data: ", data)
                        last_object_value = data[-5:]
                        last_five_urls = [obj['주소'] for obj in last_object_value]
                        current_date = datetime.now().strftime("%Y-%m-%d")
                        save_to_json(data, current_dir, current_date, industry_cd)

                    next_url = to_more(page_no, current_dt, industry_cd)
                    page_no += 1
                    url = next_url

                    check += 1
            else:
                print(f"Failed to fetch data from {url}")
                return None

        # 데이터가 없는 경우 → 폴더 & json 초기화
        if check == 0:
            current_dt = datetime.now().strftime("%Y-%m-%d")
            if not os.path.exists(f"{current_dir}/Nattachment/{current_dt}/{industry_cd}"):
                os.makedirs(f"{current_dir}/Nattachment/{current_dt}/{industry_cd}")
            # # os.makedirs(f"{current_dir}/Nattachment/{current_dt}/{industry_cd}")
            # empty_data = {}
            # with open(f'{current_dir}/Narticles.json', 'w') as file:
            #     json.dump(empty_data, file)
            logger.info(f'업종 코드 : {industry_cd} 는 현재 데이터가 없습니다.')
        # # 크롤링 데이터 저장(JSON)
        # if articles:
        #     save_articles(articles, current_dir, current_dt, industry_cd)
    except CustomException as e:
        print(f"데이터 중복값으로 인한 메인에서의 예외처리: {e}")
        raise


    # In[72]:









def crawl_and_process():
    conn = sqlite3.connect(MAIN_DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT bms_industry AS '업종코드' FROM bms_tbs''')

    # 데이터를 중복 없이 결합하기 위한 세트 초기화
    unique_data = set()
    industry_list = c.fetchall()
    # 각 줄의 데이터를 세트에 추가
    for idt in industry_list:
        items = idt[0].split(',')
        unique_data.update(items)
    unique_data_list = sorted(unique_data, key=int)
    identifiers = unique_data_list  # 작업할 identifier 목록
    for identifier in identifiers:
        try:
            print("identifier :", identifier)
            main(identifier)
        except CustomException:
            logger.info(f"{identifier} 작업 중 중복값이 발견되어 종료되었습니다.")
            print(f"{identifier} 작업 중 중복값이 발견되어 종료되었습니다.")
        except TimeoutError:
            main(identifier)  # [WinError 10060] → 너무 빠른 크롤링으로 인한 로봇으로 판단 => 재요청
