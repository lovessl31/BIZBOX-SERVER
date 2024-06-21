class CustomException(Exception):
    pass

class CustomValidException(Exception):
    def __init__(self, msg="custom error occurred", status_code=400):
        super().__init__(msg)
        self.message = msg
        self.status_code = status_code