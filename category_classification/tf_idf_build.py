import json
import math

from nltk import FreqDist
from collections import OrderedDict

from tokenizer import KrTokenizer
from db_connect import DB


krt = KrTokenizer()
dl = DB()


# standard DTM 생성 함수
def standard_dtm_build():
    # 데이터 로드
    load_size = 1000
    sql = 'SELECT posting_contents FROM blog.blog_restaurant order by rand() LIMIT ' + str(load_size) + ';'
    temp = dl.data_load(sql)

    # str 형식으로 변환
    source = []
    for _temp in temp:
        _temp = str(_temp)
        _temp = _temp.replace('(', '')
        _temp = _temp.replace(')', '')
        source.append(_temp)

    # 토크나이징
    token_data = krt.extract_morphs_for_all_document(source, False)
    combined_token_data = []
    for _token_data in token_data:
        combined_token_data = combined_token_data + _token_data

    fdist = FreqDist(combined_token_data)
    temp_list = fdist.most_common(100)

    token_list = []
    dtm_list = []
    for i in range(len(temp_list)):
        token_list.append(temp_list[i][0])
        temp_n = int(temp_list[i][1] // (load_size / 2))
        if temp_n < 1:
            temp_n = 1
        dtm_list.append(temp_n)

    print(token_list)
    print(dtm_list)

    save_data = OrderedDict()
    save_data['token'] = token_list
    save_data['dtm'] = dtm_list
    json.dump(save_data, open('./standard_dtm.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent='\t')


# custom DTM 생성 함수
def custom_dtm_build():
    # 맛집
    # 화장품/패션
    # IT/인터넷
    # 금융/제테크
    # 미디어/문화
    # 여행/숙박
    # 육아/출산

    # 각 카테고리 별 핵심 토큰들
    token_list = [
        ['먹다', '맛있다', '나오다', '메뉴', '주문', '고기', '맛집', '음식', '느낌', '소스', '방문',
         '식사', '테이블', '손님', '가격', '요리', '많다', '사진', '먹기', '느끼다'],
        ['사용', '피부', '제품', '먹다', '느낌', '받다', '바르다', '컬러', '예쁘다', '편하다', '크림',
         '기능', '관리', '추천', '케어', '이용', '얼굴', '쓰다', '성분', '느끼다'],
        ['사용', '중국', '제품', '기능', '서비스', '기업', '이용', '투자', '가격', '시장', '기기',
         '기술', '갤럭시', '시기', '구매', '브랜드', '미국', '점검', '애플', '지원'],
        ['시장', '전망', '중국', '성장', '투자', '증가', '기업', '업체', '미국', '가격', '상승',
         '확대', '하락', '산업', '사업', '예상', '국내', '수요', '매출', '주가'],
        ['영화', '이야기', '현재', '작품', '감독', '보이다', '읽다', '내용', '개봉', '배우', '모습',
         '확인', '새롭다'],
        ['여행', '먹다', '호텔', '사진', '사용', '할인', '일본', '예약', '카페', '방문', '찍다',
         '참고', '느낌', '다녀오다', '편하다', '영상', '한국', '다니다', '겨울', '여름'],
        ['아이', '먹다', '사용', '자다', '마음', '기능', '제품', '편하다', '좋아하다', '크다', '광고',
         '엄마']
    ]
    # 각 카테고리 별 핵심 토큰들의 한 문서 당 평균 빈도수
    frequency_list = [
        [9, 4, 1, 3, 3, 2, 3, 3, 1, 2, 2, 1, 1, 2, 2, 2, 1, 1, 1, 1],
        [5, 5, 5, 3, 2, 2, 3, 2, 2, 2, 2, 1, 1, 1, 1, 2, 2, 1, 1, 1],
        [5, 4, 3, 3, 2, 2, 2, 2, 2, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1],
        [7, 6, 6, 5, 5, 4, 4, 4, 4, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2],
        [7, 4, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1],
        [6, 4, 3, 3, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [5, 2, 3, 3, 3, 2, 2, 2, 2, 1, 1, 2]
    ]
    '''
    token_list = [
        ['먹다', '맛있다', '나오다', '메뉴', '주문', '고기', '맛집', '음식', '느낌', '소스', '방문', '식사', '테이블', '손님', '가격', '요리', '많다', '사진', '먹기'],
        ['사용', '피부', '제품', '느낌', '바르다', '컬러', '예쁘다', '편하다', '크림', '기능', '관리', '추천', '케어', '이용', '얼굴', '쓰다', '성분', '느끼다'],
        ['시장', '전망', '중국', '성장', '투자', '증가', '기업', '업체', '미국', '가격', '상승', '확대', '하락', '산업', '사업', '예상', '국내', '수요', '매출', '주가'],
        ['영화', '이야기', '현재', '작품', '감독', '보이다', '읽다', '내용', '개봉', '배우', '모습', '확인', '새롭다'],
        ['아이', '사용', '마음', '기능', '제품', '편하다', '광고', '엄마']
    ]
    # 각 카테고리 별 핵심 토큰들의 한 문서 당 평균 빈도수
    frequency_list = [
        [9, 4, 1, 3, 3, 2, 3, 3, 1, 2, 2, 1, 1, 2, 2, 2, 1, 1, 1],
        [5, 5, 5, 2, 3, 2, 2, 2, 2, 1, 1, 1, 1, 2, 2, 1, 1, 1],
        [7, 6, 6, 5, 5, 4, 4, 4, 4, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2],
        [7, 4, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1],
        [5, 3, 3, 2, 2, 2, 1, 2]
    ]
    '''
    category_size = len(token_list)

    # 각 카테고리 별 토큰 리스트를 하나의 리스트로 정리
    temp_list = []
    for _token_list in token_list:
        temp_list = temp_list + _token_list
    unique_token_list = list(set(temp_list))

    '''
    for i in range(len(token_list)):
        print(len(token_list[i]))
        print(len(frequency_list[i]))
    '''

    # DTM 초기화
    dtm_list = [[0 for _ in range(len(unique_token_list))] for _ in range(category_size)]

    # DTM 값 할당
    for i in range(category_size):
        for j, token in enumerate(unique_token_list):
            for k in range(len(token_list[i])):
                if token == token_list[i][k]:
                    dtm_list[i][j] = frequency_list[i][k]

    # 생성 된 DTM 저장
    save_data = OrderedDict()
    save_data['token'] = unique_token_list
    save_data['dtm'] = dtm_list
    json.dump(save_data, open('./custom_dtm.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent='\t')


# standard TF-IDF 생성 함수
def standard_tf_idf_build():
    with open('./standard_dtm.json', 'r', encoding='UTF-8') as f:
        load_data = json.load(f)
    token_list = load_data['token']
    dtm_list = load_data['dtm']

    # TF-IDF 생성
    tf_idf_list = dtm_to_tf_idf(dtm_list)

    # TF-IDF 저장
    save_data2 = OrderedDict()
    save_data2['token'] = token_list
    save_data2['tf_idf'] = tf_idf_list
    json.dump(save_data2, open('./standard_tf_idf.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent='\t')


# custom TF-IDF 생성 함수
def custom_tf_idf_build():
    # DTM 로드
    with open('./custom_dtm.json', 'r', encoding='UTF-8') as f:
        load_data = json.load(f)
    unique_token_list = load_data['token']
    dtm_list = load_data['dtm']

    # TF-IDF 생성
    tf_idf_list = dtm_to_tf_idf(dtm_list)

    # TF-IDF 저장
    save_data2 = OrderedDict()
    save_data2['token'] = unique_token_list
    save_data2['tf_idf'] = tf_idf_list
    json.dump(save_data2, open('./custom_tf_idf.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent='\t')


# DTM 을 TF-IDF 로 변환 하는 함수
def dtm_to_tf_idf(dtm_matrix):
    """
    :param dtm_matrix: (list) DTM 배열
    :return: (list) TF-IDF 배열
    """
    col_size = len(dtm_matrix[0])
    row_size = len(dtm_matrix)
    tf_idf_matrix = [[0 for _ in range(col_size)] for _ in range(row_size)]

    for i in range(row_size):
        for j in range(col_size):
            count = 0
            for k in range(row_size):
                if (dtm_matrix[i][j] > 0) and (dtm_matrix[k][j] > 0):
                    count = count + 1
            tf_idf_matrix[i][j] = math.log(row_size / (count + 1)) * dtm_matrix[i][j]

    return tf_idf_matrix


custom_dtm_build()
custom_tf_idf_build()
