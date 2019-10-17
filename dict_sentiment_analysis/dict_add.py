import json
import pandas as pd

# json 파일 업데이트 함수
def update_file(file_path, data_list):
    """
    :param file_path: (str) 저장 경로
    :param data: (list) 추가 할 딕셔너리 데이터의 리스트
    :return: None
    """
    # 파일 읽기
    with open(file_path, mode='r', encoding='utf-8') as f:
        load_file = json.load(f)

    # 삽입 데이터 정리
    for data in data_list:
        # 사전 중복 단어 검사
        is_duplication = False
        for i in range(len(load_file)):
            if load_file[i]['word'] == data['word']:
                is_duplication = True

        # 중복이 아닐시 삽입 데이터에 추가
        if is_duplication is False:
            load_file.append(data)

    # 파일 업데이트
    json.dump(load_file, open(file_path, 'w', encoding='utf-8'), ensure_ascii=False, indent='\t')

# json 파일 업데이트를 위한 데이터 로드
def load_data(file_path):
    """
    :param file_path: (str) 추가 할 데이터가 있는 엑셀 파일의 경로
    :return: (list) 추가 할 딕셔너리 데이터의 리스트
    """
    # 파일 읽기
    load_data = pd.read_excel(file_path, sheet_name='Sheet1')

    # 데이터 정리
    word_list = load_data[load_data.columns[0]].values
    polarity_list = load_data[load_data.columns[1]].values
    result = []
    for word, polarity in zip(word_list, polarity_list):
        temp = {}
        temp['word'] = word
        temp['polarity'] = str(polarity)
        result.append(temp)

    return result


data = load_data('./sentiword_list2.xlsx')
update_file('./sentiword_dict2.json', data)
