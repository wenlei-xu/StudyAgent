class AppException(Exception):
    def __init__(self, code: str, detail: str, status_code: int = 500):
        self.code = code
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class LLMTimeoutError(AppException):
    def __init__(self, detail: str = "LLM 调用超时"):
        super().__init__(code="LLM_TIMEOUT", detail=detail, status_code=502)


class SearchAPIError(AppException):
    def __init__(self, detail: str = "搜索服务不可用"):
        super().__init__(code="SEARCH_ERROR", detail=detail, status_code=502)


class RAGRetrievalError(AppException):
    def __init__(self, detail: str = "知识库检索失败"):
        super().__init__(code="RAG_ERROR", detail=detail, status_code=500)


class SessionNotFoundError(AppException):
    def __init__(self, session_id: str):
        super().__init__(
            code="SESSION_NOT_FOUND",
            detail=f"会话 {session_id} 不存在",
            status_code=404,
        )
