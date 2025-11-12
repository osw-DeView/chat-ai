# models.py (최종 수정 버전)

from pydantic import BaseModel, Field
from typing import List, Dict

# --- 공통으로 사용할 예시 데이터 ---

EXAMPLE_FOLLOW_UP_MESSAGES = [
    {"role": "system", "content": "당신은 최고의 IT 기술 면접 전문가입니다. 당신은 지원자와 심층적인 기술 대화를 나눌 수 있으며, 면접이 끝난 후 '# [지시]' 태그를 포함한 명확한 '평가' 지시를 받으면, 전체 대화 기록을 분석하여 상세한 최종 평가를 생성할 수 있습니다."},
    {"role": "assistant", "content": "프로세스와 스레드의 차이는 무엇인가요?"},
    {"role": "user", "content": "프로세스는 독립적인 실행 단위이고, 스레드는 프로세스 내에서 실행 흐름을 담당합니다."}
]

EXAMPLE_EVAL_CONVERSATION = [
    {
        "role": "assistant",
        "content": "프로세스와 스레드의 차이는 무엇인가요?"
    },
    {
        "role": "user",
        "content": "프로세스는 독립적인 실행 단위이고, 스레드는 프로세스 내에서 실행 흐름을 담당합니다."
    },
    {
        "role": "assistant",
        "content": "그렇다면 프로세스와 스레드는 메모리를 어떻게 공유하고 사용하는지에 대해 설명해주실 수 있나요?"
    },
    {
        "role": "user",
        "content": "같은 프로세스 내의 스레드들은 Code, Data, Heap 영역을 공유하고, 각자 별도의 Stack 영역을 가집니다."
    },
    {
        "role": "assistant",
        "content": "스레드들이 메모리를 공유하기 때문에 얻는 이점과, 반대로 발생할 수 있는 잠재적인 문제점은 무엇일까요?"
    },
    {
        "role": "user",
        "content": "이점은 데이터 공유가 쉽고 컨텍스트 스위칭 비용이 적다는 것입니다. 문제점은 여러 스레드가 동시에 공유 자원에 접근할 때 동기화 문제가 발생할 수 있다는 점입니다."
    }
]

EXAMPLE_FORMAT_CONVERSATION = [
    "프로세스와 스레드의 차이는 무엇인가요?",
    "프로세스는 실행 중인 프로그램이고 스레드는 그 안에서 돌아가는 작은 단위입니다.",
    "프로세스 간 데이터 공유를 위해 어떤 기술을 사용할 수 있을까요?",
    "공유 메모리를 사용할 수 있습니다."
]

# --- Pydantic 모델 정의 ---

class Message(BaseModel):
    """대화 메시지 하나를 나타내는 모델"""
    role: str = Field(..., example="user")
    content: str = Field(..., example="프로세스는 실행 중인 프로그램입니다.")

class FollowUpRequest(BaseModel):
    """꼬리질문 생성 API의 요청 모델"""
    messages: List[Message] = Field(..., example=EXAMPLE_FOLLOW_UP_MESSAGES)

class FollowUpResponse(BaseModel):
    """꼬리질문 생성 API의 응답 모델"""
    response_text: str = Field(..., example="좋은 설명입니다. 그렇다면 IPC 기법에는 무엇이 있나요?")

class EvaluateRequest(BaseModel):
    """최종 평가 생성 API의 요청 모델"""
    conversation: List[Message] = Field(..., example=EXAMPLE_EVAL_CONVERSATION)

# [신규 추가] 질문별 상세 평가를 위한 모델
class TurnEvaluation(BaseModel):
    turn: int = Field(..., example=1)
    question: str = Field(..., example="프로세스와 스레드의 차이는 무엇인가요?")
    score: int = Field(..., example=85)
    feedback: str = Field(..., example="개념을 잘 이해하고 있습니다.")

# [신규 추가] 구조화된 전체 평가 보고서를 위한 모델
class StructuredEvaluationReport(BaseModel):
    overall_score: int = Field(..., example=88)
    overall_feedback: str = Field(..., example="전반적으로 CS 지식이 뛰어납니다.")
    improvement_keywords: List[str] = Field(..., example=["동기화(Synchronization)", "MVCC"])
    turn_evaluations: List[TurnEvaluation]

# [수정됨] 최종 평가 응답 모델이 구조화된 보고서를 반환하도록 변경
class EvaluateResponse(BaseModel):
    evaluation_report: StructuredEvaluationReport