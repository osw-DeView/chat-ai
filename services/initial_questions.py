import csv
import random
import os

_questions = []

def load_questions_from_csv():
    """
    프로젝트의 data/cs_questions.csv 파일에서 질문을 읽어와 _questions 리스트에 저장합니다.
    서버 시작 시 자동으로 한 번만 호출됩니다.
    """
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cs_questions.csv')

    try:
        with open(file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                if 'question' in row:
                    _questions.append(row['question'])
        if not _questions:
            print(f"Warning: '{file_path}' 파일이 비어있거나 'question' 컬럼을 포함하고 있지 않습니다.")
            _questions.append("등록된 질문이 없습니다. data/cs_questions.csv 파일을 확인해주세요.")

    except FileNotFoundError:
        print(f"Error: '{file_path}' 파일을 찾을 수 없습니다. 질문 기능을 사용할 수 없습니다.")
        _questions.append("질문 파일을 찾을 수 없습니다. 관리자에게 문의하세요.")
    except Exception as e:
        print(f"Error loading questions from CSV: {e}")
        _questions.append("질문을 불러오는 중 오류가 발생했습니다.")


def get_random_question() -> str:
    """
    메모리에 로드된 질문 목록(_questions)에서 무작위로 하나를 선택하여 반환합니다.
    """ 
    if _questions:
        return random.choice(_questions)
    return "선택할 수 있는 질문이 없습니다."
load_questions_from_csv()