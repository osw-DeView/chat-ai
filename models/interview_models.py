from pydantic import BaseModel, Field
from typing import List, Literal

EXAMPLE_PERFORMANCE = {
    "time_to_first_token_ms": 150.52,
    "total_generation_time_s": 2.75,
    "tokens_per_second": 120.45,
    "total_tokens": 331
}

EXAMPLE_CONVERSATION_FOR_NEXT_QUESTION = [
    {"role": "assistant", "content": "운영체제에서 프로세스와 스레드의 가장 근본적인 차이는 무엇이며, 이 차이가 시스템의 메모리 주소 공간 할당 및 자원 관리 측면에서 어떤 영향을 미치는지 구체적으로 설명해주세요."},
    {"role": "user", "content": "프로세스는 독립된 메모리 공간을 할당받는 실행의 단위이고, 스레드는 프로세스 내에서 자원을 공유하며 실행되는 흐름의 단위입니다. 때문에 프로세스 간 통신(IPC)은 복잡하지만, 같은 프로세스 내의 스레드 간 통신은 메모리를 공유하므로 훨씬 간단하고 빠릅니다."}
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
    },
    {
        "turn": 3,
        "question": "뮤텍스와 세마포어의 근본적인 차이점은 무엇이며, 각각 어떤 상황에서 더 적합하게 사용될 수 있는지 설명해 주십시오.",
        "score": 80,
        "feedback": "뮤텍스와 세마포어의 차이를 '잠금'과 '계수기'로 잘 설명했으나, 실제 사용 사례나 소유권(ownership)과 같은 더 깊이 있는 차이점을 언급했다면 더 좋은 답변이 되었을 것입니다."
    }
]

EXAMPLE_STRUCTURED_REPORT = {
    "overall_score": 85,
    "overall_feedback": "전반적으로 운영체제의 프로세스 및 스레드 관련 기본 개념이 매우 탄탄합니다. 특히 각 개념의 정의와 장단점을 명확하게 인지하고 있습니다. 다만, 동기화 기법에 대한 심층적인 이해나 실제 적용 사례에 대한 고민이 더해진다면 한 단계 더 성장할 수 있을 것입니다.",
    "improvement_keywords": ["임계 구역(Critical Section)", "스핀락(Spinlock)", "모니터(Monitor)"],
    "turn_evaluations": EXAMPLE_TURN_EVALUATION_LIST
}

class PerformanceMetrics(BaseModel):
    time_to_first_token_ms: float = Field(..., example=150.52)
    total_generation_time_s: float = Field(..., example=2.75)
    tokens_per_second: float = Field(..., example=120.45)
    total_tokens: int = Field(..., example=331)

class Message(BaseModel):
    role: Literal["user", "assistant"] = Field(..., example="user")
    content: str = Field(..., example="프로세스는 운영체제로부터 자원을 할당받는 작업의 단위입니다.")

class InterviewStartRequest(BaseModel):
    interviewType: str = Field(..., example="CS")

class InterviewStartResponse(BaseModel):
    response: str = Field(..., example="데이터베이스 정규화의 목적은 무엇이며, 정규화를 통해 얻을 수 있는 장점과 단점에 대해 설명해주세요.")

class InterviewNextRequest(BaseModel):
    interviewType: str = Field(..., example="CS")
    messages: List[Message] = Field(..., example=EXAMPLE_CONVERSATION_FOR_NEXT_QUESTION)

class InterviewNextResponse(BaseModel):
    response: str = Field(..., example="좋은 답변입니다. 그렇다면 스레드 간 동기화 문제를 해결하기 위한 구체적인 기법에는 어떤 것들이 있나요?")
    # performance: PerformanceMetrics = Field(..., example=EXAMPLE_PERFORMANCE)

class InterviewEvaluationRequest(BaseModel):
    interviewType: str = Field(..., example="Operating System")
    conversation: List[Message] = Field(..., example=EXAMPLE_CONVERSATION_FOR_EVALUATION)

class TurnEvaluation(BaseModel):
    turn: int = Field(..., example=1)
    question: str = Field(..., example="운영체제에서 프로세스와 스레드의 가장 근본적인 차이는 무엇인가요?")
    score: int = Field(..., example=90)
    feedback: str = Field(..., example="프로세스와 스레드의 핵심 차이인 '독립된 메모리 공간'과 '자원 공유'를 명확하게 설명했습니다. 훌륭합니다.")

class StructuredEvaluationReport(BaseModel):
    overall_score: int = Field(..., example=85)
    overall_feedback: str = Field(..., example="전반적으로 운영체제의 프로세스 및 스레드 관련 기본 개념이 매우 탄탄합니다.")
    improvement_keywords: List[str] = Field(..., example=["임계 구역(Critical Section)", "스핀락(Spinlock)"])
    turn_evaluations: List[TurnEvaluation] = Field(..., example=EXAMPLE_TURN_EVALUATION_LIST)

class InterviewEvaluationResponse(BaseModel):
    interviewType: str = Field(..., example="Operating System")
    evaluation_report: StructuredEvaluationReport = Field(..., example=EXAMPLE_STRUCTURED_REPORT)
    # performance: PerformanceMetrics = Field(..., example=EXAMPLE_PERFORMANCE)