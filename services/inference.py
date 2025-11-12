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
        self.load_gguf_model()

    def load_gguf_model(self):
        logger.info(f"'{config.GGUF_MODEL_PATH}' GGUF 모델 로드를 시작합니다...")
        try:
            # --------------------------------------------------------------------------
            # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ GPU 사양에 맞춰 이 값을 조절하세요 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
            # --------------------------------------------------------------------------
            # n_gpu_layers: GPU VRAM으로 얼마나 많은 모델 레이어를 올릴지 결정하는 핵심 값.
            # -1: VRAM이 허용하는 만큼 모든 레이어를 GPU로 올립니다. (고사양 GPU 권장)
            # 0: GPU를 전혀 사용하지 않고 CPU로만 실행합니다. (매우 느림)
            # 1 이상의 정수: 지정된 숫자만큼의 레이어를 GPU로 올립니다.
            
            # --- GPU VRAM별 n_gpu_layers 설정 가이드 ---
            # ∙  8GB VRAM (RTX 2060S, 3060): 20 ~ 28 사이에서 조절 (시작 추천값: 25)
            # ∙ 12GB VRAM (RTX 3060 12GB, 4070): 30 ~ 35 사이에서 조절 (시작 추천값: 33)
            # ∙ 24GB VRAM (RTX 3090, 4090): -1 로 설정하여 모두 GPU에 올리는 것을 추천
            
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
        cleaned_content = re.sub(r"^\s*<think>.*?</think>\s*", "", raw_content, flags=re.DOTALL).strip()
        
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
            improvement_keywords = [
                self._strip_markdown(line.strip('- ').strip()) 
                for line in keywords_text.strip().split('\n') if line.strip()
            ]

            turn_evaluations = []
            if turns_text:
                turn_sections = re.split(r"### 턴 \d+:", turns_text)[1:]
                for i, section in enumerate(turn_sections, 1):
                    question_match = re.search(r"(.*?)\n\s*\*\*- 점수:", section, re.DOTALL)
                    turn_score_match = re.search(r"\*\*- 점수:\*\*\s*(\d+)", section)
                    turn_feedback_match = re.search(r"\*\*- (?:평가|피드백):\*\*\s*(.*)", section, re.DOTALL)

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
                overall_feedback=f"리포트 파싱 중 오류 발생. 원본: {report_text}",
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
            {"role": "system", "content": config.EVALUATION_SYSTEM_PROMPT},
            {"role": "user", "content": final_instruction}
        ]

interview_model = InterviewModel()