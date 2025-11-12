# services/gemini_service.py

import google.generativeai as genai
from core.config import GEMINI_API_KEY, TAIL_QUESTION_MODEL, EVALUATION_MODEL
from models.interview_models import Message, StructuredEvaluationReport, TurnEvaluation
from typing import List, Dict, Any
import json
import re
import time
from markdown_it import MarkdownIt

# --- 초기 설정 ---
genai.configure(api_key=GEMINI_API_KEY)
generation_config = {"temperature": 0.7}
tail_question_model = genai.GenerativeModel(model_name=TAIL_QUESTION_MODEL, generation_config=generation_config)
evaluation_model = genai.GenerativeModel(model_name=EVALUATION_MODEL, generation_config=generation_config)
md_parser = MarkdownIt()

# --- 비동기 성능 측정 헬퍼 함수 ---
async def _generate_content_with_performance_metrics(model, prompt: str) -> (str, Dict[str, Any]):
    """
    비동기 스트리밍 API 호출을 통해 응답을 생성하고, TTFT와 TPS와 같은 성능 지표를 측정합니다.
    """
    start_time = time.time()
    
    stream = await model.generate_content_async(prompt, stream=True)
    
    first_chunk_time = None
    full_response_text = ""
    
    async for chunk in stream:
        if chunk.text:
            if first_chunk_time is None:
                first_chunk_time = time.time()
            full_response_text += chunk.text

    end_time = time.time()

    try:
        token_count_result = await model.count_tokens_async(full_response_text)
        total_tokens = token_count_result.total_tokens
    except Exception:
        total_tokens = len(full_response_text) // 2 

    ttft = (first_chunk_time - start_time) * 1000 if first_chunk_time else 0
    total_time = end_time - start_time
    
    pure_generation_time = end_time - first_chunk_time if first_chunk_time else total_time
    if pure_generation_time <= 0:
        pure_generation_time = total_time
        
    tps = total_tokens / pure_generation_time if pure_generation_time > 0 else 0

    performance = {
        "time_to_first_token_ms": round(ttft, 2),
        "total_generation_time_s": round(total_time, 2),
        "tokens_per_second": round(tps, 2),
        "total_tokens": total_tokens
    }
    
    return full_response_text, performance

# --- 마크다운 제거 헬퍼 함수 ---
def _strip_markdown(text: str) -> str:
    """
    Markdown 텍스트를 렌더링한 후 HTML 태그를 제거하여 순수 텍스트만 반환합니다.
    """
    html = md_parser.render(text)
    plain_text = re.sub('<[^<]+?>', '', html)
    return re.sub(r'\n{2,}', '\n', plain_text).strip()

# --- 꼬리질문 생성 함수 ---
async def generate_tail_question(conversation: List[Message]) -> Dict[str, Any]:
    """
    이전 대화 내용을 바탕으로 다음 꼬리 질문을 비동기로 생성하고 성능을 측정합니다.
    """
    prompt = """
    당신은 IT 기업의 숙련된 기술 면접관입니다.
    아래 대화는 지원자와의 CS 기술 면접 내용입니다.
    지원자의 마지막 답변을 바탕으로, 그의 지식을 더 깊게 파고들 수 있는 날카로운 꼬리 질문을 '한글로' 그리고 '하나만' 생성해 주세요.
    질문은 간결하고 명확해야 합니다. 다른 부가적인 설명 없이 질문 내용만 반환해주세요.

    [대화 내용]
    {chat_history}
    """.format(chat_history="\n".join([f"{msg.role}: {msg.content}" for msg in conversation]))

    response_text, performance = await _generate_content_with_performance_metrics(tail_question_model, prompt)
    cleaned_response = _strip_markdown(response_text)
    return {"response": cleaned_response, "performance": performance}

# --- 평가 프롬프트 생성 헬퍼 함수 ---
def _format_for_evaluation(conversation: List[Message]) -> str:
    """
    대화 기록을 기반으로 Gemini 모델에 전달할 최종 평가 지시 프롬프트를 생성합니다.
    """
    interview_record = ""
    dialogue = [msg for msg in conversation if msg.role in ["assistant", "user"]]
    turn = 1
    for i in range(0, len(dialogue), 2):
        if i + 1 < len(dialogue):
            question, answer = dialogue[i].content, dialogue[i+1].content
            interview_record += f"### 턴 {turn}\n**[질문]**\n{question}\n\n**[답변]**\n{answer}\n---\n\n"
            turn += 1

    return f"""
    당신은 지원자의 기술적 깊이를 평가하는 IT 전문 면접관입니다.
    다음은 한 지원자와의 전체 CS 기술 면접 대화록입니다.
    이 대화 내용을 바탕으로 지원자의 CS 지식을 평가하고, 아래 [출력 형식]을 '반드시' 준수하여 '한글로' 응답해 주세요.

    # [면접 기록]
    {interview_record}
    ---
    # [지시사항]
    위 [면접 기록]을 바탕으로, 지원자에 대한 최종 종합 평가를 아래 [출력 형식]에 맞춰 마크다운으로 생성하십시오.

    # [출력 형식]
    # 최종 종합 평가
    **- 종합 점수:** (1-100 사이의 정수 점수)
    **- 종합 피드백:** (종합적인 강점과 약점을 2-3문장으로 요약)
    **- 개선 키워드:**
        - (핵심 개선 키워드 1)
        - (핵심 개선 키워드 2)
    ---
    ## 질문별 상세 평가
    ### 턴 1: (첫 번째 질문 내용 요약)
    **- 점수:** (1-100 사이의 정수 점수)
    **- 피드백:** (첫 번째 답변에 대한 구체적인 피드백)

    ### 턴 2: (두 번째 질문 내용 요약)
    **- 점수:** (1-100 사이의 정수 점수)
    **- 피드백:** (두 번째 답변에 대한 구체적인 피드백)

    ### 턴 3: (세 번째 질문 내용 요약)
    **- 점수:** (1-100 사이의 정수 점수)
    **- 피드백:** (세 번째 답변에 대한 구체적인 피드백)
    """

# --- 평가 결과 파싱 헬퍼 함수 ---
def _parse_structured_evaluation_report(report_text: str) -> StructuredEvaluationReport:
    """
    Gemini가 생성한 마크다운 형식의 평가 텍스트를 파싱하여 StructuredEvaluationReport 객체로 변환합니다.
    """
    try:
        overall_text, turns_text = re.split(r'\n## 질문별 상세 평가\n', report_text, 1)

        score_match = re.search(r"\*\*- 종합 점수:\*\*\s*(\d+)", overall_text)
        feedback_match = re.search(r"\*\*- 종합 피드백:\*\*\s*(.*?)(?=\n\s*\*\*-|\Z)", overall_text, re.DOTALL)
        keywords_match = re.search(r"\*\*- 개선 키워드:\*\*(.*?)(?=\n\n---|\Z)", overall_text, re.DOTALL)
        
        overall_score = int(score_match.group(1)) if score_match else 0
        overall_feedback = feedback_match.group(1).strip() if feedback_match else "종합 피드백을 찾을 수 없습니다."
        
        keywords_text = keywords_match.group(1) if keywords_match else ""
        improvement_keywords = [_strip_markdown(line.strip('- ').strip()) for line in keywords_text.strip().split('\n') if line.strip()]

        turn_evaluations = []
        turn_sections = re.split(r"### 턴 \d+:", turns_text)[1:]
        for i, section in enumerate(turn_sections, 1):
            question_match = re.search(r"(.*?)\n\s*\*\*- 점수:", section, re.DOTALL)
            turn_score_match = re.search(r"\*\*- 점수:\*\*\s*(\d+)", section)
            turn_feedback_match = re.search(r"\*\*- 피드백:\*\*\s*(.*)", section, re.DOTALL)

            turn_evaluations.append(TurnEvaluation(
                turn=i,
                question=_strip_markdown(question_match.group(1).strip() if question_match else "질문 없음"),
                score=int(turn_score_match.group(1)) if turn_score_match else 0,
                feedback=turn_feedback_match.group(1).strip() if turn_feedback_match else "피드백 없음"
            ))

        return StructuredEvaluationReport(
            overall_score=overall_score,
            overall_feedback=overall_feedback,
            improvement_keywords=improvement_keywords,
            turn_evaluations=turn_evaluations
        )
    except Exception as e:
        print(f"평가 보고서 파싱 실패: {e}\n원본 텍스트:\n{report_text}")
        return StructuredEvaluationReport(
            overall_score=0,
            overall_feedback=f"리포트 파싱 중 오류가 발생했습니다. 모델이 생성한 원본 텍스트를 확인해주세요:\n\n{report_text}",
            improvement_keywords=[],
            turn_evaluations=[]
        )

# --- 종합 평가 함수 ---
async def evaluate_conversation(conversation: List[Message]) -> Dict[str, Any]:
    """
    전체 대화 내용을 바탕으로 면접을 비동기로 평가하고, 성능을 측정한 뒤 구조화된 딕셔너리로 반환합니다.
    """
    prompt = _format_for_evaluation(conversation)
    markdown_response, performance = await _generate_content_with_performance_metrics(evaluation_model, prompt)
    structured_report = _parse_structured_evaluation_report(markdown_response.strip())
    
    # --- 👇 사용자님께서 제안하신 수정 사항 ---
    # performance는 계산되지만, 최종 반환 딕셔너리에서는 제외됩니다.
    return {
        "evaluation_report": structured_report,
        # "performance": performance 
    }