from faker import Faker
import pandas as pd
import os

# 랜덤한 더미 데이터 생성.

fk = Faker('ko-KR')

# 회원 정보 데이터 생성

mb_dummy_data = \
    [(f"{fk.unique.email().split('@')[0]}{fk.unique.pyint(min_value=111, max_value=999)}", fk.unique.email(), '1q2w3e4r', fk.name(), fk.unique.phone_number(), fk.unique.company(), fk.date_time()) for i in range(50)]

test_data = [(fk.date_time(), fk.credit_card_full()) for j in range(10)]
print(mb_dummy_data)



# 업종 코드 옵션 데이터 가져오기


# 현재 파일의 디렉토리 경로
current_dir = os.path.dirname(os.path.abspath(__file__))

# 엑셀 파일의 절대 경로
excel_path = os.path.join(current_dir, 'industry_code.xlsx')

# 엑셀 파일 읽기
df = pd.read_excel(excel_path)


