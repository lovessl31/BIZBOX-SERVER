import traceback
class CustomException(Exception):
    pass

class CustomValidException(Exception):
    def __init__(self, msg="custom error occurred", status_code=400):
        super().__init__(msg)
        self.message = msg
        self.status_code = status_code


def DetailErrMessageTraceBack(e):
    # 예외가 발생한 경우, 예외 정보와 스택 트레이스를 출력
    print("에러가 발생했습니다.:")
    print(f"에러 유형: {type(e).__name__}")
    print(f"에러 메세지: {e}")
    # 스택 트레이스 출력
    traceback.print_exc()
