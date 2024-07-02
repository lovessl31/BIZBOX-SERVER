# db 테이블 정의

def bzb_tbs(cursor):
    # 멤버 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS member
                     (mb_idx INTEGER PRIMARY KEY,       
                      mb_id VARCHAR NOT NULL UNIQUE,        -- 유저 아이디               
                      mb_email VARCHAR NOT NULL,            -- 이메일
                      mb_pw VARCHAR NOT NULL,               -- 비밀 번호
                      mb_name VARCHAR NOT NULL,             -- 멤버 이름
                      phone_number TEXT(11) NOT NULL UNIQUE,-- 멤버 번호
                      status VARCHAR(1) NOT NULL,           -- 가입 상태
                      created_date DATETIME NOT NULL,       -- 생성일
                      update_date DATETIME NOT NULL         -- 수정일
                      )                      
    ''')

    # 입찰 메일링 서비스 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS bms_tbs
                     (bms_idx INTEGER PRIMARY KEY,           -- 서비스 번호
                      mb_idx INTEGER NOT NULL UNIQUE,        -- 계정 번호    
                      bms_email VARCHAR NOT NULL UNIQUE,     -- 이용자 이메일                      
                      bms_name VARCHAR NOT NULL,             -- 이용자 이름                      
                      phone_number TEXT(11) NOT NULL UNIQUE, -- 이용자 번호                                                             
                      created_date DATETIME NOT NULL,        -- 신청 일자
                      FOREIGN KEY (mb_idx) REFERENCES member(mb_idx) ON DELETE CASCADE                      
                      )                      
    ''')

    # 입찰 메일링 서비스 중간 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS bms_industry
                     (  bms_idx INTEGER,                 -- 서비스 번호
                        industry_cd VARCHAR(2) NOT NULL, -- 업종 코드
                        FOREIGN KEY (bms_idx) REFERENCES bms_tbs(bms_idx) ON DELETE CASCADE                      
                      )                      
    ''')
    # 입찰 메일링 서비스 중간 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS bms_area
                         (  bms_idx INTEGER,                 -- 서비스 번호
                            bms_area VARCHAR(2) NOT NULL,    -- 지역 코드                      
                            FOREIGN KEY (bms_idx) REFERENCES bms_tbs(bms_idx) ON DELETE CASCADE                      
                          )                      
        ''')
    # 입찰 메일링 서비스 중간 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS bms_task
                         (  bms_idx INTEGER,                 -- 서비스 번호
                            bms_taskCd VARCHAR NOT NULL,  -- 업무 코드
                            FOREIGN KEY (bms_idx) REFERENCES bms_tbs(bms_idx) ON DELETE CASCADE                      
                          )                      
        ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS bms_keyword
                             (  bms_idx INTEGER,                 -- 서비스 번호
                                bms_keyword VARCHAR NOT NULL,   -- 키워드 
                                FOREIGN KEY (bms_idx) REFERENCES bms_tbs(bms_idx) ON DELETE CASCADE                      
                              )                      
            ''')


    # 입찰 공고 테이블
    # np_number 에 unique 걸어놓으면 다른 업종코드에 같은 공고번호에서 값을 넣을수없음.
    cursor.execute('''CREATE TABLE IF NOT EXISTS bid_notice
                      (np_idx INTEGER PRIMARY KEY,     -- 입찰 테이블 번호              
                       industry_cd VARCHAR(2) NOT NULL,-- 업종 코드
                       taskClCds VARCHAR(2) NOT NULL,  -- 업무 종류         
                       np_title VARCHAR,               -- 공고명                       
                       np_number VARCHAR,              -- 공고 번호                                       
                       demand_agency VARCHAR,          -- 수요 기관
                       tender_open_date DATE,          -- 입찰 시작                                        
                       tender_close_date DATE,         -- 입찰 마감
                       pj_amount VARCHAR,              -- 사업 금액
                       est_price VARCHAR,              -- 추정 가격
                       budget VARCHAR,                 -- 배정 예산
                       vat VARCHAR,                    -- 부가세                                 
                       created_date DATETIME           -- 생성 일자
                     )                    
    ''')
    # 입찰 지역 제한 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS bid_notice_area
                      (idx INTEGER PRIMARY KEY,       -- 입찰 제한 지역 테이블 번호
                       np_idx INTEGER NOT NULL,       -- 입찰 테이블 번호              
                       area_name VARCHAR NOT NULL,    -- 지역 명
                       area_g_cd VARCHAR(2) NOT NULL, -- 지역 그룹 코드                                                                                                  
                       created_date DATETIME,         -- 생성 일자
                       FOREIGN KEY (np_idx) REFERENCES bid_notice(np_idx) ON DELETE CASCADE                                   
                     )                    
    ''')

    # 옵션 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS bid_option
                     (option_idx INTEGER PRIMARY KEY,       -- 옵션 번호
                      option_value VARCHAR NOT NULL,        -- 옵션 값
                      option_name INTEGER,                  -- 옵션 명
                      option_group VARCHAR,                 -- 옵션 분류
                      created_date DATETIME                 -- 생성일   
                     )''')

    # 옵션 중간 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS entity_option
                         (entity_idx INTEGER,                  -- 연계 테이블 번호
                          entity_type VARCHAR NOT NULL,        -- 연계 테이블 유형
                          entity_tbs VARCHAR NOT NULL,         -- 연계 테이블 명(board, memeber 등등)
                          option_idx INTEGER,                  -- 옵션 번호
                          FOREIGN KEY (option_idx) REFERENCES bid_option(option_idx) ON DELETE CASCADE                            
                         )''')

    # 파일 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS file_info
                         (file_idx INTEGER PRIMARY KEY, -- 파일 번호
                          o_file_name VARCHAR NOT NULL, -- 원본 파일 명
                          s_file_name VARCHAR NOT NULL, -- 수정 파일 명
                          file_size INTEGER NOT NULL,   -- 파일 크기
                          file_type VARCHAR NOT NULL,   -- 파일 유형
                          file_ext VARCHAR NOT NULL,    -- 확장자
                          file_path VARCHAR NOT NULL,   -- 파일 경로
                          domain VARCHAR NOT NULL,      -- 도메인
                          upload_date DATETIME          -- 업로드 일                                   
                          )''')

    # 파일 중간 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS bid_file
                     (bf_idx INTEGER PRIMARY KEY,-- 중간 테이블 번호
                      file_idx INTEGER NOT NULL, -- 파일 번호
                      np_idx INTEGER NOT NULL,   -- 입찰 공고 번호
                      FOREIGN KEY (np_idx) REFERENCES bid_notice(np_idx) ON DELETE CASCADE,
                      FOREIGN KEY (file_idx) REFERENCES file_info(file_idx) ON DELETE CASCADE                                                                
                     )''')

    # 메일 기록 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS mail_log
                     (log_idx INTEGER PRIMARY KEY,  -- 메일 기록 번호                
                      subject VARCHAR NOT NULL,     -- 제목
                      body VARCHAR NOT NULL,        -- 내용
                      sender VARCHAR NOT NULL,      -- 보낸 이
                      recipient VARCHAR NOT NULL,   -- 받는 이
                      status VARCHAR NOT NULL,      -- 메세지 응답 상태
                      type VARCHAR NOT NULL,        -- 메일 유형
                      sent_time DATE,               -- 전송 시간                      
                      FOREIGN KEY (recipient) REFERENCES member(mb_email) ON DELETE CASCADE
                      )''')


    # 토큰 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS token
                     (token_idx INTEGER PRIMARY KEY,    -- 토큰 번호                
                      payload VARCHAR NOT NULL,         -- 페이로드
                      mb_idx integer NOT NULL,          -- 멤버 번호
                      status VARCHAR NOT NULL,          -- 토큰 상태
                      exp_date datetime NOT NULL,       -- 만료시간
                      created_date datetime NOT NULL    -- 생성시간
                      )''')
