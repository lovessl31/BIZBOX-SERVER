import pysftp
import os
import schedule
import time
def download_file():

    #  기본 세팅
    host = '192.168.0.107'  # 호스트명만 입력. sftp:// 는 필요하지 않다.
    port = 24322  # 원격 서버의 포트 번호
    username = 'withfirst'  # 원격 서버 유저명
    password = 'As841126!@'  # 원격 서버 접속 비밀번호

    hostkeys = None

    # 서버에 저장되어 있는 모든 호스트키 정보를 불러오는 코드
    cnopts = pysftp.CnOpts()

    # 접속을 시도하는 호스트에 대한 호스트키 정보가 존재하는지 확인
    # 존재하지 않으면 cnopts.hostkeys를 None으로 설정해줌으로써 첫 접속을 가능하게 함
    if cnopts.hostkeys.lookup(host) == None:
        print("호스트키 for " + host + " doesn't exist")
        hostkeys = cnopts.hostkeys  # 혹시 모르니 다른 호스트키 정보들 백업
        cnopts.hostkeys = None

    # 첫 접속이 성공하면, 호스트에 대한 호스트키 정보를 서버에 저장.
    # 두번째 접속부터는 호스트키를 확인하며 접속하게 됨.

    # sftp 접속을 실행
    with pysftp.Connection(
            host,
            port=port,
            username=username,
            password=password,
            cnopts=cnopts) as sftp:
        # 접속이 완료된 후 이 부분이 호스트키를 저장하는 부분
        # 처음 접속 할 때만 실행되는 코드
        if hostkeys != None:
            print("새 호스트 입니다. 호스트 키를 캐시합니다 " + host)
            hostkeys.add(host, sftp.remote_server_key.get_name(), sftp.remote_server_key)  # 호스트와 호스트키를 추가
            hostkeys.save(pysftp.helpers.known_hosts())  # 새로운 호스트 정보 저장

        # 폴더 내에 있는 모든 파일을 한꺼번에 업로드 하고 싶을 땐 'put_d' 를 다운로드는 get_d
        # 예) sftp.put_d('업로드 할 파일들이 있는 폴더 경로', '/')

        # 여러 파일들을 개별로 업로드 하고 싶을 땐 'put'을 여러번 사용 다운로드는 get
        # 예) sftp.put('파일1 경로')
        #     sftp.put('파일2 경로')

        # 원격 서버에 있는 파일/폴더 구조 확인(Linux 의 ls, cmd shell 의 dir 과 유사)
        print(sftp.listdir('/home/withfirst'))
        # 원격 서버 json 파일 다운로드
        sftp.get('/home/withfirst/Narticles.json', r'./Narticles.json')
        # 원격 서버 경로
        remote_folder = '/home/withfirst/Nattachment'
        # 로컬 저장 경로
        local_folder = r'C:\work\NARA_CRAWL\nara\Nattachment'

        # 로컬 경로에 폴더가 없으면 폴더 생성
        if not os.path.exists(local_folder):
            os.makedirs(local_folder)

        def mkdir_p(local_path):
            """유닉스의 mkdir -p와 같은 기능을 수행"""
            if not os.path.exists(local_path):
                os.makedirs(local_path)

        def download_file_callback(remote_path):
            """파일을 다운로드하는 콜백 함수"""
            local_path = os.path.join(local_folder, os.path.relpath(remote_path, remote_folder))
            local_dir = os.path.dirname(local_path)
            mkdir_p(local_dir)
            print(f"다운로드 파일 : {remote_path} to {local_path}")
            sftp.get(remote_path, local_path, preserve_mtime=True)

        def mkdir_callback(remote_path):
            """디렉토리를 생성하는 콜백 함수"""
            local_path = os.path.join(local_folder, os.path.relpath(remote_path, remote_folder))
            print(f"생성된 디렉토리: {local_path}")
            mkdir_p(local_path)

        def ignore_callback(remote_path):
            """무시할 파일이나 디렉토리 콜백"""
            return False

        # 디렉토리 트리 탐색 및 파일 다운로드
        sftp.walktree(remote_folder, download_file_callback, mkdir_callback, ignore_callback, recurse=True)
        # 모든 작업이 끝나면 접속 종료
        sftp.close()


download_file()
# def main():
#     # 매 시간의 10분 후에 작업을 예약
#     schedule.every().hour.at(":10").do(download_file)
#     # 상태 설정
#     status = True
#     try:
#         while status:
#             print("작업 스케줄러 구동 시간 : ", time.ctime())
#             schedule.run_pending()
#             time.sleep(2)
#     except KeyboardInterrupt:
#         print("사용자의 의해 스크립트가 중단 되었습니다.")
#         time.sleep(1)
#
# import sys
#
# if __name__ == "__main__":
#     status = True
#     while status:
#         try:
#             main()
#             user_input = input("스크립트를 다시 시작하시겠습니까? (y/n): ").sys.stdin.buffer.read().decode('utf-8').strip().lower()
#             print("")
#         except UnicodeDecodeError:
#             print("예외 발생")
#             # 터미널 인코딩을 지정하여 입력 받기
#             user_input = input("스크립트를 다시 시작하시겠습니까? (y/n): ").strip().lower()
#             if user_input != 'y':
#                 print("스크립트를 종료합니다.")
#                 status = False
#                 break
#             else:
#                 print("스크립트를 재시작 합니다.")
#                 main()

