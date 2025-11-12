# services/inference.py

import re
import logging
from llama_cpp import Llama
from typing import List, Dict
from markdown_it import MarkdownIt

# 로컬 모듈 임포트 (경로에 맞게 수정 필요)
from core import config
from models.interview_models import Message, StructuredEvaluationReport, TurnEvaluation

logger = logging.getLogger("uvicorn")

class InterviewModel:
    def __init__(self):
        self.model = None
        self.md_parser = MarkdownIt()
        # lifespan에서 모델을 로드하므로 __init__에서는 호출하지 않습니다.

    def load_gguf_model(self):
        logger.info(f"'{config.GGUF_MODEL_PATH}' GGUF 모델 로드를 시작합니다...")
        try:
            # --------------------------------------------------------------------------
            # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ GPU 사양에 맞춰 이 값을 조절하세요 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
            # --------------------------------------------------------------------------
            gpu_layers_to_offload = 25 # <<< 사용자의 GPU에 맞게 이 숫자를 수정하세요!
            # --------------------------------------------------------------------------
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
            # --------------------------------------------------------------------------
            self.model = Llama(
                model_path=config.GGUF_MODEL_PATH, n_ctx=2048,
                n_gpu_layers=gpu_layers_to_offload, n_batch=512, verbose=True,
            )
            logger.info("✅ GGUF 모델 로드 및 GPU 오프로딩 완료.")
        except Exception as e:
            logger.error(f"GGUF 모델 로드 중 심각한 오류 발생: {e}")
            raise e

    def _strip_markdown(self, text: str) -> str:
        html = self.md_parser.render(text)
        plain_text = re.sub('<[^<]+?>', '', html)
        return re.sub(r'\n{2,}', '\n', plain_text).strip()

    def generate_response(self, messages: List[Dict], strip_markdown: bool = False) -> str:
        if not self.model: raise RuntimeError("모델이 로드되지 않았습니다.")
        
        processed_messages = [msg.dict() if isinstance(msg, Message) else msg for msg in messages]
        
        output = self.model.create_chat_completion(
            messages=processed_messages,
            temperature=config.GENERATION_CONFIG.get("temperature", 0.1),
            top_p=config.GENERATION_CONFIG.get("top_p", 0.95),
            max_tokens=config.GENERATION_CONFIG.get("max_new_tokens", 1024),
        )
        
        raw_content = output['choices'][0]['message']['content']
        
        # [수정] 모델의 출력에서 '# 최종 종합 평가' 부분을 찾아 그 부분부터 사용하도록 처리
        # 이렇게 하면 평가 이전에 나오는 <think> 태그나 다른 불필요한 텍스트를 자연스럽게 제거할 수 있습니다.
        eval_start_index = raw_content.find("# 최종 종합 평가")
        if eval_start_index != -1:
            raw_content = raw_content[eval_start_index:]

        # [수정] 모델이 결과 생성 후 추가적인 생각을 출력하는 경우를 대비해 <think> 또는 </think>를 기준으로 잘라냅니다.
        # 이렇게 하면 평가 마크다운 뒤에 따라오는 불필요한 텍스트를 제거할 수 있습니다.
        cleaned_content = raw_content.split("</think>")[0].split("<think>")[0].strip()

        if strip_markdown:
            return self._strip_markdown(cleaned_content)
        return cleaned_content

    def parse_evaluation_report(self, report_text: str) -> StructuredEvaluationReport:
        try:
            # 전체 텍스트를 '종합 평가' 부분과 '질문별 상세 평가' 부분으로 나눕니다.
            report_parts = re.split(r'\n## 질문별 상세 평가\n', report_text, 1)
            overall_text = report_parts[0]
            turns_text = report_parts[1] if len(report_parts) > 1 else ""

            # 정규표현식을 사용하여 각 항목을 추출합니다.
            score_match = re.search(r"\*\*- 종합 점수:\*\*\s*(\d+)", overall_text)
            # [수정] 종합 피드백이 다음 항목을 침범하지 않도록 비탐욕적(non-greedy) 패턴 `(.*?)` 사용
            feedback_match = re.search(r"\*\*- 종합 (?:평가|피드백):\*\*\s*(.*?)(?=\n\s*\*\*-|\Z)", overall_text, re.DOTALL)
            keywords_match = re.search(r"\*\*- 개선 키워드:\*\*(.*?)(?=\n\n---|\Z)", overall_text, re.DOTALL)
            
            overall_score = int(score_match.group(1)) if score_match else 0
            overall_feedback = feedback_match.group(1).strip() if feedback_match else "종합 피드백을 찾을 수 없습니다."
            
            keywords_text = keywords_match.group(1) if keywords_match else ""
            # [수정] improvement_keywords가 비어있는 라인을 포함하지 않도록 필터링 강화
            improvement_keywords = [
                self._strip_markdown(line.strip('- ').strip()) 
                for line in keywords_text.strip().split('\n') if line.strip() and line.strip() != '-'
            ]

            turn_evaluations = []
            if turns_text:
                # '질문별 상세 평가' 부분을 각 턴별로 나눕니다.
                turn_sections = re.split(r"### 턴 \d+:", turns_text)[1:]
                for i, section in enumerate(turn_sections, 1):
                    question_match = re.search(r"(.*?)\n\s*\*\*- 점수:", section, re.DOTALL)
                    turn_score_match = re.search(r"\*\*- 점수:\*\*\s*(\d+)", section)
                    # [수정] 각 턴의 피드백이 다음 턴을 침범하지 않도록 비탐욕적(non-greedy) 패턴 `(.*?)`과 경계(`\n### 턴|\Z`) 추가
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
            # 파싱 실패 시, 프론트엔드 에러 방지를 위해 오류 메시지를 포함한 기본 객체 반환
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

# FastAPI 앱 전체에서 공유할 싱글톤 인스턴스 생성
interview_model = InterviewModel()