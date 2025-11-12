# 모델 경로
GGUF_MODEL_PATH = "./qwen3-8b-cs-interviewer-merge-v1-150-Q4_K_M.gguf"
SYSTEM_PROMPT = "당신은 최고의 IT 기술 면접 전문가입니다. 당신은 지원자와 심층적인 기술 대화를 나눌 수 있으며, 면접이 끝난 후 '# [지시]' 태그를 포함한 명확한 '평가' 지시를 받으면, 전체 대화 기록을 분석하여 상세한 최종 평가를 생성할 수 있습니다."
# 추론 파라미터
GENERATION_CONFIG = {
    "max_new_tokens": 1024,
    "do_sample": True,
    "temperature": 0.1,
    "top_p": 0.95,
}