import re
import logging
import httpx
from typing import List, Dict
from markdown_it import MarkdownIt

from core import config
from models.interview_models import Message, StructuredEvaluationReport, TurnEvaluation

logger = logging.getLogger("uvicorn")

class InterviewModel:
    def __init__(self):
        self.api_base = "http://localhost:8000/v1"
        self.client = httpx.AsyncClient(base_url=self.api_base, timeout=900.0)
        self.md_parser = MarkdownIt()

    def _strip_markdown(self, text: str) -> str:
        html = self.md_parser.render(text)
        plain_text = re.sub('<[^<]+?>', '', html)
        return re.sub(r'\n{2,}', '\n', plain_text).strip()

    async def generate_response(self, messages: List[Dict], strip_markdown: bool = False) -> str:
        processed_messages = [msg.dict() if isinstance(msg, Message) else msg for msg in messages]

        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    # [FIX] "model" 필드를 제거하여 서버의 전역 --chat-template 설정을 따르도록 함
                    # "model": config.GGUF_MODEL_PATH, 
                    "messages": processed_messages,
                    "temperature": config.GENERATION_CONFIG.get("temperature", 0.1),
                    "top_p": config.GENERATION_CONFIG.get("top_p", 0.95),
                    "max_tokens": config.GENERATION_CONFIG.get("max_new_tokens", 1024),
                },
            )
            response.raise_for_status()
            output = response.json()
            raw_content = output['choices'][0]['message']['content']

        except httpx.RequestError as e:
            logger.error(f"LLM 추론 서버({self.api_base}) 요청 실패: {e}")
            raise RuntimeError("LLM 추론 서버에 연결할 수 없습니다. './server'가 실행 중인지 확인하세요.")
        except Exception as e:
            logger.error(f"API 응답 처리 중 오류 발생: {e}", exc_info=True)
            raise

        eval_start_index = raw_content.find("# 최종 종합 평가")
        if eval_start_index != -1:
            raw_content = raw_content[eval_start_index:]

        cleaned_content = raw_content.split("</think>")[0].split("<think>")[0].strip()

        if strip_markdown:
            return self._strip_markdown(cleaned_content)
        return cleaned_content

    def parse_evaluation_report(self, report_text: str) -> StructuredEvaluationReport:
        try:
            report_parts = re.split(r'\n## 질문별 상세 평가\n', report_text, 1)
            overall_text = report_parts[0]
            turns_text = report_parts[1] if len(report_parts) > 1 else ""

            score_match = re.search(r"\*\*- 종합 점수:\*\*\s*(\d+)", overall_text)
            feedback_match = re.search(r"\*\*- 종합 (?:평가|피드백):\*\*\s*(.*?)(?=\n\s*\*\*-|\Z)", overall_text, re.DOTALL)
            keywords_match = re.search(r"\*\*- 개선 키워드:\*\*(.*?)(?=\n\n---|\Z)", overall_text, re.DOTALL)

            overall_score = int(score_match.group(1)) if score_match else 0
            overall_feedback = feedback_match.group(1).strip() if feedback_match else "종합 피드백을 찾을 수 없습니다."

            keywords_text = keywords_match.group(1) if keywords_match else ""
            
            processed_keywords = [
                self._strip_markdown(line.strip('- ').strip())
                for line in keywords_text.strip().split('\n')
            ]
            improvement_keywords = [keyword for keyword in processed_keywords if keyword]

            turn_evaluations = []
            if turns_text:
                turn_sections = re.split(r"### 턴 \d+:", turns_text)[1:]
                for i, section in enumerate(turn_sections, 1):
                    question_match = re.search(r"(.*?)\n\s*\*\*- 점수:", section, re.DOTALL)
                    turn_score_match = re.search(r"\*\*- 점수:\*\*\s*(\d+)", section)
                    turn_feedback_match = re.search(r"\*\*- (?:평가|피드백):\*\*\s*(.*?)(?=\n### 턴|\Z)", section, re.DOTALL)

                    turn_evaluations.append(TurnEvaluation(
                        turn=i,
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
            return StructuredEvaluationReport(
                overall_score=0,
                overall_feedback=f"리포트 파싱 중 오류가 발생했습니다. 모델이 생성한 원본 텍스트를 확인해주세요:\n\n{report_text}",
                improvement_keywords=[],
                turn_evaluations=[]
            )

    def format_for_evaluation(self, conversation: List[Message]) -> List[Dict]:
        interview_record = ""
        dialogue = [msg for msg in conversation if msg.role in ["assistant", "user"]]
        turn = 1
        for i in range(0, len(dialogue), 2):
            if i + 1 < len(dialogue):
                question, answer = dialogue[i].content, dialogue[i+1].content
                interview_record += f"### 턴 {turn}\n**[질문]**\n{question}\n\n**[답변]**\n{answer}\n---\n\n"
                turn += 1

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
### 턴 1: (첫 번째 질문 내용)
**- 점수:** (1-100 사이의 점수)
**- 피드백:** (첫 번째 답변에 대한 구체적인 피드백)

### 턴 2: (두 번째 질문 내용)
**- 점수:** (1-100 사이의 점수)
**- 피드백:** (두 번째 답변에 대한 구체적인 피드백)

### 턴 3: (세 번째 질문 내용)
**- 점수:** (1-100 사이의 점수)
**- 피드백:** (세 번째 답변에 대한 구체적인 피드백)
"""
        return [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": final_instruction}
        ]

interview_model = InterviewModel()