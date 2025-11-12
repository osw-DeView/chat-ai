import csv
import random
import os
import logging

# uvicorn 로거를 사용하여 로그를 출력합니다.
logger = logging.getLogger("uvicorn")

# 메모리에 질문을 저장할 리스트 (모듈 전역 변수)
_questions = []

def load_questions_from_csv():
    """
    프로젝트의 data/cs_questions.csv 파일에서 질문을 읽어와 _questions 리스트에 저장합니다.
    서버 시작 시 이 모듈이 임포트되면서 단 한 번만 호출됩니다.
    """
    # 현재 파일의 위치를 기준으로 data 폴더의 절대 경로를 계산합니다.
    # 이렇게 하면 어떤 위치에서 서버를 실행해도 파일 경로가 항상 정확합니다.
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cs_questions.csv')

    try:
        with open(file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                # 'question' 컬럼이 존재하고, 내용이 비어있지 않은 경우에만 추가합니다.
                if 'question' in row and row['question'].strip():
                    _questions.append(row['question'].strip())
        
        if not _questions:
            logger.warning(f"'{file_path}' 파일이 비어있거나 'question' 컬럼을 포함하고 있지 않습니다.")
            _questions.append("등록된 질문이 없습니다. data/cs_questions.csv 파일을 확인해주세요.")
        else:
            logger.info(f"✅ 총 {_questions.__len__()}개의 초기 질문을 '{file_path}' 파일에서 성공적으로 로드했습니다.")

    except FileNotFoundError:
        logger.error(f"'{file_path}' 파일을 찾을 수 없습니다. 초기 질문 기능을 사용할 수 없습니다.")
        _questions.append("질문 파일을 찾을 수 없습니다. 관리자에게 문의하세요.")
    except Exception as e:
        logger.error(f"CSV 파일에서 질문을 불러오는 중 오류가 발생했습니다: {e}")
        _questions.append("질문을 불러오는 중 오류가 발생했습니다.")


def get_random_question() -> str:
    """
    메모리에 로드된 질문 목록(_questions)에서 무작위로 하나를 선택하여 반환합니다.
    """ 
    if not _questions:
        # 이 경우는 load_questions_from_csv 함수에서 문제가 발생했을 때 해당됩니다.
        return "선택할 수 있는 질문이 없습니다."
    return random.choice(_questions)

# --- 모듈 로딩 시점 실행 ---
# 이 파이썬 파일이 처음으로 import 될 때 (즉, FastAPI 서버가 시작될 때)
# load_questions_from_csv() 함수가 자동으로 실행되어 질문들을 메모리에 올려놓습니다.
load_questions_from_csv()