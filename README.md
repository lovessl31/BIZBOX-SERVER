# 비즈박스 리드미 파일



# 프로젝트 실행 방법

1. conda create -n <프로젝트명> python=3.8.19
2. git clone 으로 가상환경에 클론해온다.
3. .env 파일을 생성하고 환경변수를 읽어올수있게 load_dotenv()를 실행하고 암호키를 세팅한다.<br>
4. 의존성 목록을 pip install -r (루트 경로)/requirements.txt 를 사용하여 설치한다.<br>
   (루트 경로를 모른다면 리눅스 터미널창에서 pwd 를 입력해서 루트 경로를넣으면 된다.) <br>
5. 방법 1. 터미널 창에서 pwd 로 경로 확인 후 $env:PYTHONPATH = "프로젝트 경로" 를 등록한다 <br>
    방법 2. .env 파일에서 PROJECT_ROOT 변수에 프로젝트 경로를 입력한다.<br>
6. db_manager.py 파일을 실행하여 db 생성 및 더미 데이터 인서트 이미 파일이 있다면 생략<br>
7. 프로젝트 경로/nara/db 경로에 bizbox.db 및 dev_bizbox.db 파일이 생성 됐는지 확인<br>
8. env파일에서 프로젝트 환경 및 db경로 및 프로젝트 경로 입력
9. config.py 파일에 플라스크 환경설정이 있는데 SERVER NAME을 각 pc에 맡게 세팅 
10. init 파일에 서버네임 설정은 호스트 설정이 안되어있으면 ip:port 로 구성한다.
11. 프로젝트 경로/nara/__init__.py 파일을 실행하여 flask 서버 가동한다. <br>
    (리눅스 터미널창에서 pwd 를 입력해서 경로를 확인하고 넣으면 된다.)





<hr>

## directory 

#### crawl/
- 크롤링 소스
#### db/
- 데이터 베이스 소스
#### routes/
- 백엔드 서버 각 엔드포인트 api 소스
#### utils/
- 함수, 예외처리, 정규표현식 공통 함수들 정의 폴더
#### templates/
- flask jinja2 를 사용한 html 양식 저장 폴더
#### static/
- css 이미지 저장 폴더
<hr>

## file

#### init
- flask 서버 관리 및 모듈화 및 스케줄링 함수

#### send_bid_mail
- 크롤링한 데이터 메일링 서비스 하는 함수 저장 파일

#### scp 
- 외부 ip 파일 구조 확인 및 트리구조 읽어서 스케줄링으로 매시간마다 파일 다운로드하는 로직

#### jsonReader
- json 파일 읽는 파일



<hr>




