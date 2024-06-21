import re
from nara.utils.err_handler import CustomValidException
'''
(?=.*[a-z]): 적어도 하나의 소문자가 포함되어야 함을 확인하는 긍정형 전방 탐색
(?=.*\d): 적어도 하나의 숫자가 포함되어야 함을 확인하는 긍정형 전방 탐색
(?=.*[@$!%*?&]): 적어도 하나의 특수문자(@, $, !, %, *, ?, &)가 포함되어야 함을 확인하는 긍정형 전방 탐색
[A-Za-z\d@$!%*?&]{8,}: 소문자, 숫자, 특수문자 중 하나 이상을 포함한 총 길이 8자 이상의 문자열
'''
def is_valid_ep(t, v):
    e_regex = r'^[a-zA-Z0-9]{3,20}@[a-zA-Z0-9-]{3,12}\.[a-zA-Z]{2,12}(\.[a-zA-Z]{2,12})?$'
    pw_regex = r'^(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    i_regex = r'^[a-zA-Z0-9]{5,20}'
    p_regex = r'^[0-9]{10,11}'
    industry_regex = r'^(\d+)(,\d+){0,2}$'
    if t == 'email' and re.match(e_regex, v) is None:
        raise CustomValidException('email regex err!', 400)
    elif t == 'password' and re.match(pw_regex, v) is None:
        raise CustomValidException('pw regex err', 400)
    elif t == 'id' and re.match(i_regex, v) is None:
        raise CustomValidException('id regex err', 400)
    elif t == 'phone' and re.match(p_regex, v) is None:
        raise CustomValidException('phone number regex err', 400)
    elif t == 'industry' and re.match(industry_regex, v) is None:
        raise CustomValidException('산업 코드는 하나에서 세 개의 숫자로 구성되며, 두 개 이상일 때는 쉼표로 구분되어야 합니다', 400)
    return