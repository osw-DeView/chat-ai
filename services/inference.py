import re
import logging
import httpx
from typing import List, Dict
from markdown_it import MarkdownIt

from core import config  # config.py에서 SYSTEM_PROMPT 등을 가져온다고 가정합니다.
from models.interview_models import Message, StructuredEvaluationReport, TurnEvaluation # Pydantic 모델을 가져온다고 가정합니다.
import os

# 로거 설정
logger = logging.getLogger("uvicorn")

class InterviewModel:
    def __init__(self):
        # LLM API 엔드포인트 설정 (환경 변수 또는 기본값)
        self.api_base = os.getenv("LLM_API_BASE", "http://localhost:8000/v1")
        # 비동기 HTTP 클라이언트 초기화 (타임아웃 900초)
        self.client = httpx.AsyncClient(base_url=self.api_base, timeout=900.0)
        # 마크다운 파서 초기화 (HTML 태그 제거용)
        self.md_parser = MarkdownIt()

    def _strip_markdown(self, text: str) -> str:
        """마크다운 텍스트를 일반 텍스트로 변환합니다."""
        html = self.md_parser.render(text)
        # HTML 태그 제거
        plain_text = re.sub('<[^<]+?>', '', html)
        # 과도한 개행 문자 정리
        return re.sub(r'\n{2,}', '\n', plain_text).strip()

    async def generate_response(self, messages: List[Dict], strip_markdown: bool = False) -> str:
        """LLM API에 요청을 보내고 응답 텍스트를 반환합니다."""
        
        # Pydantic 모델(Message) 객체를 딕셔너리로 변환
        processed_messages = [msg.dict() if isinstance(msg, Message) else msg for msg in messages]

        try:
            # LLM 서버의 /chat/completions 엔드포인트에 POST 요청
            response = await self.client.post(
                "/chat/completions",
                json={
                    # "model" 필드 없음 (서버 기본 설정 사용)
                    "messages": processed_messages,
                    "temperature": config.GENERATION_CONFIG.get("temperature", 0.1),
                    "top_p": config.GENERATION_CONFIG.get("top_p", 0.95),
                    "max_tokens": config.GENERATION_CONFIG.get("max_new_tokens", 1024),
                },
            )
            response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
            output = response.json()
            raw_content = output['choices'][0]['message']['content']

        except httpx.RequestError as e:
            logger.error(f"LLM 추론 서버({self.api_base}) 요청 실패: {e}")
            raise RuntimeError("LLM 추론 서버에 연결할 수 없습니다. './server'가 실행 중인지 확인하세요.")
        except Exception as e:
            logger.error(f"API 응답 처리 중 오류 발생: {e}", exc_info=True)
            raise

        # LLM이 생성한 불필요한 태그나 접두어 제거
        eval_start_index = raw_content.find("# 최종 종합 평가")
        if eval_start_index != -1:
            raw_content = raw_content[eval_start_index:]

        cleaned_content = raw_content.split("</think>")[0].split("<think>")[0].strip()

        if strip_markdown:
            return self._strip_markdown(cleaned_content)
        return cleaned_content

    def parse_evaluation_report(self, report_text: str) -> StructuredEvaluationReport:
        """LLM이 생성한 마크다운 리포트 텍스트를 파싱하여 Pydantic 객체로 변환합니다."""
        try:
            # 1. 전체 평가와 질문별 평가 분리
            report_parts = re.split(r'\n## 질문별 상세 평가\n', report_text, 1)
            overall_text = report_parts[0]
            turns_text = report_parts[1] if len(report_parts) > 1 else ""

            # 2. 전체 평가 파싱 (종합 점수, 피드백, 개선 키워드)
            score_match = re.search(r"\*\*- 종합 점수:\*\*\s*(\d+)", overall_text)
            feedback_match = re.search(r"\*\*- 종합 (?:평가|피드백):\*\*\s*(.*?)(?=\n\s*\*\*-|\Z)", overall_text, re.DOTALL)
            keywords_match = re.search(r"\*\*- 개선 키워드:\*\*(.*?)(?=\n\n---|\Z)", overall_text, re.DOTALL)

            overall_score = int(score_match.group(1)) if score_match else 0
            overall_feedback = feedback_match.group(1).strip() if feedback_match else "종합 피드백을 찾을 수 없습니다."

            keywords_text = keywords_match.group(1) if keywords_match else ""
            
            # 키워드 라인별로 분리 및 마크다운 제거
            processed_keywords = [
                self._strip_markdown(line.strip('- ').strip())
                for line in keywords_text.strip().split('\n')
            ]
            improvement_keywords = [keyword for keyword in processed_keywords if keyword]

            # 3. 질문별 상세 평가 파싱
            turn_evaluations = []
            if turns_text:
                # "### 턴 {i}:" 기준으로 각 턴을 분리
                turn_sections = re.split(r"### 턴 \d+:", turns_text)[1:]
                for i, section in enumerate(turn_sections, 1):
                    # [중요] 이 정규식이 `(첫 번째 질문 내용)` 대신 `실제 질문 텍스트`를 포착함
                    question_match = re.search(r"(.*?)\n\s*\*\*- 점수:", section, re.DOTALL)
                    turn_score_match = re.search(r"\*\*- 점수:\*\*\s*(\d+)", section)
                    turn_feedback_match = re.search(r"\*\*- (?:평가|피드백):\*\*\s*(.*?)(?=\n### 턴|\Z)", section, re.DOTALL)

                    turn_evaluations.append(TurnEvaluation(
                        turn=i,
                        # [중요] question_match.group(1)이 실제 질문 텍스트가 됨
                        question=self._strip_markdown(question_match.group(1).strip() if question_match else "질문을 찾을 수 없습니다."),
                        score=int(turn_score_match.group(1)) if turn_score_match else 0,
                        feedback=turn_feedback_match.group(1).strip() if turn_feedback_match else "피드백을 찾을 수 없습니다."
                    ))

            return StructuredEvaluationReport(
                overall_score=overall_score,
                overall_feedback=overall_feedback,
                improvement_keywords=improvement_keywords,
                turn_evaluations=turn_evaluations
            )
        except Exception as e:
            logger.error(f"평가 보고서 파싱 실패: {e}", exc_info=True)
            # 파싱 실패 시 오류 리포트 반환
            return StructuredEvaluationReport(
                overall_score=0,
                overall_feedback=f"리포트 파싱 중 오류가 발생했습니다. 모델이 생성한 원본 텍스트를 확인해주세요:\n\n{report_text}",
                improvement_keywords=[],
                turn_evaluations=[]
            )

    # [수정된 메소드]
    def format_for_evaluation(self, conversation: List[Message]) -> List[Dict]:
        """대화 기록을 LLM 평가용 프롬프트 형식으로 변환합니다."""
        
        interview_record = ""
        # 'assistant'(질문자)와 'user'(답변자) 역할만 필터링
        dialogue = [msg for msg in conversation if msg.role in ["assistant", "user"]]
        turn = 1
        
        # [핵심 수정 1] 실제 질문 텍스트를 순서대로 저장할 리스트
        extracted_questions: List[str] = []

        # 1. 면접 기록 생성 및 동시에 질문 추출
        for i in range(0, len(dialogue), 2):
            if i + 1 < len(dialogue): # 질문(i)과 답변(i+1)이 쌍을 이루는지 확인
                question, answer = dialogue[i].content, dialogue[i+1].content
                
                # [면접 기록] 부분 생성
                interview_record += f"### 턴 {turn}\n**[질문]**\n{question}\n\n**[답변]**\n{answer}\n---\n\n"
                
                # [핵심 수정 2] 추출한 질문 텍스트를 리스트에 저장
                extracted_questions.append(question)
                turn += 1

        # [핵심 수정 3] 질문별 상세 평가 템플릿을 '동적으로' 생성
        turn_evaluation_template = ""
        for i, question_text in enumerate(extracted_questions, 1):
            # 질문에 포함된 개행 문자가 마크다운 헤더(#)를 방해하지 않도록 공백으로 치환
            safe_question_text = question_text.replace('\n', ' ').strip()
            
            # 실제 질문 텍스트를 템플릿에 삽입
            turn_evaluation_template += f"""
### 턴 {i}: {safe_question_text}
**- 점수:** (1-100 사이의 점수)
**- 피드백:** ({i}번째 답변에 대한 구체적인 피드백)
"""

        # [핵심 수정 4] 최종 프롬프트 조립 (f-string 사용)
        # [출력 형식]의 '## 질문별 상세 평가' 부분에 
        # 위에서 동적으로 생성한 'turn_evaluation_template'을 삽입
        final_instruction = f"""# [면접 기록]
{interview_record}
---
# [지시]
위 [면접 기록]을 바탕으로, 지원자에 대한 최종 종합 평가를 아래 [출력 형식]에 맞춰 마크다운으로 생성하십시오.

# [출력 형식]
# 최종 종합 평가
**- 종합 점수:** (1-100 사이의 종합 점수)
**- 종합 피드백:** (종합적인 강점과 약점 요약)
**- 개선 키워드:**
    - (핵심 개선 키워드 1)
    - (핵심 개선 키워드 2)
    - (핵심 개선 키워드 3)
---
## 질문별 상세 평가
{turn_evaluation_template.strip()}
"""
        # 시스템 프롬프트와 사용자 지시사항을 리스트에 담아 반환
        return [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": final_instruction}
        ]

# 클래스 인스턴스 생성 (애플리케이션의 다른 곳에서 사용 가능)
interview_model = InterviewModel()