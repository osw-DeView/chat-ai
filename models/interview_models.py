from pydantic import BaseModel, Field
from typing import List

EXAMPLE_CONVERSATION_FOR_NEXT_QUESTION = [
    {"role": "assistant", "content": "운영체제에서 프로세스와 스레드의 가장 근본적인 차이는 무엇인가요?"},
    {"role": "user", "content": "프로세스는 독립된 메모리 공간을 할당받는 실행의 단위이고, 스레드는 프로세스 내에서 자원을 공유하며 실행되는 흐름의 단위입니다."}
]

EXAMPLE_CONVERSATION_FOR_EVALUATION = [
    {"role": "assistant", "content": "운영체제에서 프로세스와 스레드의 가장 근본적인 차이는 무엇인가요?"},
    {"role": "user", "content": "프로세스는 독립된 메모리 공간을 할당받는 실행의 단위이고, 스레드는 프로세스 내에서 자원을 공유하며 실행되는 흐름의 단위입니다."},
    {"role": "assistant", "content": "그렇다면 스레드들이 자원을 공유하기 때문에 발생하는 잠재적인 문제점은 무엇이며, 이를 해결하기 위한 대표적인 방법들을 설명해주세요."},
    {"role": "user", "content": "여러 스레드가 동시에 공유 자원에 접근하면 경쟁 상태(Race Condition)가 발생하여 데이터의 일관성이 깨질 수 있습니다. 이를 해결하기 위해 뮤텍스(Mutex)나 세마포어(Semaphore)와 같은 동기화 기법을 사용해야 합니다."},
    {"role": "assistant", "content": "뮤텍스와 세마포어의 근본적인 차이점은 무엇이며, 각각 어떤 상황에서 더 적합하게 사용될 수 있는지 설명해 주십시오."},
    {"role": "user", "content": "뮤텍스는 하나의 스레드만 임계 구역에 접근할 수 있도록 하는 잠금 메커니즘이고, 세마포어는 정해진 개수만큼의 스레드가 접근할 수 있도록 허용하는 계수기입니다. 따라서 화장실이 하나일 땐 뮤텍스, 여러 개일 땐 세마포어를 쓰는 것과 같습니다."}
]

EXAMPLE_TURN_EVALUATION_LIST = [
    {
        "turn": 1,
        "question": "운영체제에서 프로세스와 스레드의 가장 근본적인 차이는 무엇인가요?",
        "score": 90,
        "feedback": "프로세스와 스레드의 핵심 차이인 '독립된 메모리 공간'과 '자원 공유'를 명확하게 설명했습니다. 훌륭합니다."
    },
    {
        "turn": 2,
        "question": "스레드들이 자원을 공유하기 때문에 발생하는 잠재적인 문제점은 무엇이며, 이를 해결하기 위한 대표적인 방법들을 설명해주세요.",
        "score": 85,
        "feedback": "경쟁 상태(Race Condition)라는 핵심 문제와 뮤텍스, 세마포어라는 해결책을 정확히 제시했습니다. 동기화의 중요성을 잘 이해하고 있습니다."
    }
]

EXAMPLE_STRUCTURED_REPORT = {
    "overall_score": 88,
    "overall_feedback": "전반적으로 운영체제의 프로세스 및 스레드 관련 기본 개념이 매우 탄탄합니다. 동기화 기법에 대한 심층적인 이해를 더한다면 훌륭한 개발자로 성장할 것입니다.",
    "improvement_keywords": ["임계 구역(Critical Section)", "스핀락(Spinlock)", "모니터(Monitor)"],
    "turn_evaluations": EXAMPLE_TURN_EVALUATION_LIST
}

class Message(BaseModel):
    """대화 메시지 하나를 나타내는 모델"""
    role: str = Field(..., example="user")
    content: str = Field(..., example="프로세스는 실행 중인 프로그램입니다.")

class InterviewStartRequest(BaseModel):
    """면접 시작 API의 요청 모델"""
    interviewType: str = Field(..., example="CS", description="면접 유형")

class InterviewStartResponse(BaseModel):
    """면접 시작 API의 응답 모델"""
    response: str = Field(..., example="운영체제에서 프로세스와 스레드의 차이는 무엇인가요?")

class InterviewNextRequest(BaseModel):
    """다음 꼬리질문 생성 API의 요청 모델"""
    interviewType: str = Field(..., example="CS", description="면접 유형")
    messages: List[Message] = Field(..., example=EXAMPLE_CONVERSATION_FOR_NEXT_QUESTION)

class InterviewNextResponse(BaseModel):
    """다음 꼬리질문 생성 API의 응답 모델"""
    response_text: str = Field(..., example="좋은 설명입니다. 그렇다면 IPC 기법에는 무엇이 있나요?")

class InterviewEvaluationRequest(BaseModel):
    """최종 평가 생성 API의 요청 모델"""
    conversation: List[Message] = Field(..., example=EXAMPLE_CONVERSATION_FOR_EVALUATION)

class TurnEvaluation(BaseModel):
    """질문별 상세 평가를 위한 모델"""
    turn: int = Field(..., example=1)
    question: str = Field(..., example="프로세스와 스레드의 차이는 무엇인가요?")
    score: int = Field(..., example=90)
    feedback: str = Field(..., example="개념을 정확히 이해하고 있습니다.")

class StructuredEvaluationReport(BaseModel):
    """구조화된 전체 평가 보고서를 위한 모델"""
    overall_score: int = Field(..., example=88)
    overall_feedback: str = Field(..., example="전반적으로 CS 지식이 뛰어납니다.")
    improvement_keywords: List[str] = Field(..., example=["동기화(Synchronization)", "MVCC"])
    turn_evaluations: List[TurnEvaluation] = Field(..., example=EXAMPLE_TURN_EVALUATION_LIST)

class InterviewEvaluationResponse(BaseModel):
    """최종 평가 생성 API의 응답 모델"""
    evaluation_report: StructuredEvaluationReport = Field(..., example=EXAMPLE_STRUCTURED_REPORT)