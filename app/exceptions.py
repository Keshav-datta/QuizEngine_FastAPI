class AppException(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


class UserAlreadyExists(AppException):
    pass


class InvalidCredentials(AppException):
    pass


class UserNotFound(AppException):
    pass


class QuizNotFound(AppException):
    pass


class QuizNotOwned(AppException):
    pass


class QuizNotPublished(AppException):
    pass


class QuizNotDraft(AppException):
    pass


class QuizEmpty(AppException):
    pass


class QuestionNotFound(AppException):
    pass


class InvalidQuestionData(AppException):
    pass


class QuestionNotOwned(AppException):
    pass


class AttemptNotFound(AppException):
    pass


class AttemptNotOwned(AppException):
    pass


class AttemptAlreadyActive(AppException):
    pass


class AttemptNotActive(AppException):
    pass


class AttemptExpired(AppException):
    pass


class InvalidAnswer(AppException):
    pass
