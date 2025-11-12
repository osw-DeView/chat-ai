import csv
import random
import os
import logging

logger = logging.getLogger("uvicorn")

_questions = []

def load_questions_from_csv():
    """
    프로젝트의 data/cs_questions.csv 파일에서 질문을 읽어와 _questions 리스트에 저장합니다.
    서버 시작 시 이 모듈이 임포트되면서 단 한 번만 호출됩니다.
    """
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cs_questions.csv')

    try:
        with open(file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
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
        return "선택할 수 있는 질문이 없습니다."
    return random.choice(_questions)

load_questions_from_csv()