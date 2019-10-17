import re
import json

from konlpy.tag import Okt
try:
    from konlpy.tag import Mecab
    from eunjeon import Mecab
except:
    try:
        import MeCab
    except:
        pass

from threading import Thread
import jpype
import queue


# 한글(kr) 전용 전처리 토크나이징 클래스 (Stemming, Stop_word)
class KrTokenizer(object):
    def __init__(self):
        self.twit = Okt()
        self.mecab = Mecab()

        # 정규 표현식 리스트
        self.regex_ls = [
            '[\t\n\r\f\v]',
            '\(.+?\)', '\[.+?\]', '\<.+?\>', '◀.+?▶',
            '(?<=▶).+', '(?<=▷).+', '(?<=※).+',
            '(?<=Copyrights).+',
            '[\w]+@[a-zA-Z]+\.[a-zA-Z]+[\.]?[a-z]*',
            '[가-힣]+기자', '[가-힣]+ 기자', '[가-힣]+ 선임기자', '[가-힣]+ 동아닷컴 기자',
            '[\{\}\[\]\/?,;·:“‘|\)*~`!^\-_+<>@○▲▶■◆\#$┌─┐&\\\=\(\'\"├┼┤│┬└┴┘|ⓒ]',
            '[0-9]+[년월분일시]*',
            '사진=[가-힣]*', '사진제공=[가-힣]*'
        ]

        # 제거대상 리스트, 불용어 리스트
        with open('../preprocessing_data/stopword_list.json', 'r', encoding='UTF-8') as f:
            load_file = json.load(f)
            self.word_to_be_cleaned_ls = load_file['clean']
            self.stopword_ls = load_file['stopword']

    # text에 정규표현식을 적용하는 함수입니다.
    def clean_text(self, text):
        """
        :param text: (str) 정규표현식이 적용 될 문자열
        :return: (str) 정규표현식이 적용 된 문자열
        """
        try:
            for regex in self.regex_ls:
                text = re.sub(regex, '', text)
        except:
            text = ' '
        return text

    # 복수 개의 문서를 클렌징하는 함수입니다.
    def clean_doc(self, doc_ls):
        """
        :param doc_ls: (list) 정규표현식이 적용 될 문자열로 이루어진 리스트
        :return: (list) 정규표현식이 적용 된 문자열로 이루어진 리스트
        """
        return [self.clean_text(doc) for doc in doc_ls]

    # 불용어를 제거하는 함수입니다.
    def remove_stopwords(self, token_doc_ls):
        """
        :param token_doc_ls: (list) 토큰 형태에 문서가 담긴 리스트
        :return: (list) 불용어 처리가 완료 된 토큰 문서 리스트
        """
        total_stopword_set = set(self.stopword_ls + self.word_to_be_cleaned_ls)

        # input이 복수 개의 문서가 담긴 list라면, 개별 문서에 따라 단어를 구분하여 불용어 처리
        return_ls = []

        if token_doc_ls:
            if type(token_doc_ls[0]) == list:
                for doc in token_doc_ls:
                    return_ls += [[token for token in doc if not token in total_stopword_set]]

            elif type(token_doc_ls[0]) == str:
                return_ls = [token for token in token_doc_ls if not token in total_stopword_set]
        return return_ls

    # 한 개의 문서에서 명사(nouns)만 추출하는 함수
    def extract_nouns_for_single_doc(self, doc, use_mecab=True):
        """
        :param doc: (str) 문서
        :param use_mecab: (bool) 메캅 사용 유무
        :return: (list) 명사에 대해 토크나이징 한 리스트
        """
        # 클렌징
        clean_doc = self.clean_text(doc)

        # 명사 추출
        if use_mecab:
            token_ls = [x for x in self.mecab.nouns(clean_doc) if len(x) > 1]
        else:
            token_ls = [x for x in self.twit.nouns(clean_doc) if len(x) > 1]

        # 불용어 제거 후 반환
        return self.remove_stopwords(token_ls)

    # 한 개의 문서에서 형태소(morphs)만 추출하는 함수
    def extract_morphs_for_single_doc(self, doc, use_mecab=True):
        """
        :param doc: (str) 문서
        :param use_mecab: (bool) 메캅 사용 유무
        :return: (list) 형태소에 대해 토크나이징 한 리스트
        """
        # 클렌징
        clean_doc = self.clean_text(doc)

        # 형태소 추출
        try:
            if use_mecab:
                token_ls = [x for x in self.mecab.morphs(clean_doc) if len(x) > 1]
            else:
                token_ls = []
                temp = self.twit.pos(clean_doc, norm=True, stem=True)
                for i in range(len(temp)):
                    # 불필요 형태소 제거
                    if (temp[i][1] not in (
                            'Josa', 'Punctuation', 'Number', 'Eomi', 'Foreign', 'Suffix', 'URL', 'PreEomi',
                            'Determiner', 'Exclamation', 'Modifier', 'ScreenName', 'Hashtag'))\
                            and (len(temp[i][0]) > 1):
                        token_ls.append(temp[i][0])
                # token_ls = [x for x in self.twit.morphs(clean_doc) if len(x) > 1]
        except:
            token_ls = []

        # 불용어 제거 후 반환
        return self.remove_stopwords(token_ls)

    # 모든 문서에서 명사(nouns)를 추출하는 함수
    def extract_nouns_for_all_document(self, doc_ls, use_mecab=True):
        """
        :param doc_ls: (list) 문서들의 리스트
        :param use_mecab: (bool) 메캅 사용 유무
        :return: (list) 명사에 대해 토크나이징 한 문서들의 토큰 리스트
        """
        jpype.attachThreadToJVM()

        # 클렌징
        clean_doc_ls = self.clean_doc(doc_ls)
        # 명사 추출
        token_doc_ls = [self.extract_nouns_for_single_doc(doc, use_mecab=use_mecab) for doc in clean_doc_ls]
        # 불용어 제거 후 반환
        return self.remove_stopwords(token_doc_ls)

    # 모든 문서에서 형태소(morph)를 추출하는 함수.
    def extract_morphs_for_all_document(self, doc_ls, use_mecab=True):
        """
        :param doc_ls: (list) 문서들의 리스트
        :param use_mecab: (bool) 메캅 사용 유무
        :return: (list) 형태소에 대해 토크나이징 한 문서들의 토큰 리스트
        """
        jpype.attachThreadToJVM()

        # 전처리
        clean_doc_ls = self.clean_doc(doc_ls)
        # 형태소 추출
        token_doc_ls = [self.extract_morphs_for_single_doc(doc, use_mecab=use_mecab) for doc in clean_doc_ls]
        # 불용어 제거 후 반환
        return self.remove_stopwords(token_doc_ls)

    # 토크나이징(명사)을 병렬처리 하는데 사용되는 함수
    def _extract_nouns_for_multiprocessing(self, tuple_ls, use_mecab=True):
        """
        :param tuple_ls: [(idx, doc)] 형태의 tuple. 인덱싱과 문서
         (멀티프로세싱의 경우, 병렬처리시 순서가 뒤섞이는 것을 방지 목적)
        :param use_mecab:  (bool) 메캅 사용 유무
        :return: (list) 명사에 대해 토크나이징 된 인덱싱과 토큰의 리스트
        """
        jpype.attachThreadToJVM()
        return [(idx, self.extract_nouns_for_single_doc(doc, use_mecab=use_mecab)) for idx, doc in tuple_ls]

    # 토크나이징(형태소)을 병렬처리 하는데 사용되는 함수
    def _extract_morphs_for_multiprocessing(self, tuple_ls, use_mecab=True):
        """
        :param tuple_ls: [(idx, doc)] 형태의 tuple. 인덱싱과 문서
         (멀티프로세싱의 경우, 병렬처리시 순서가 뒤섞이는 것을 방지 목적)
        :param use_mecab:  (bool) 메캅 사용 유무
        :return: (list) 형태소에 대해 토크나이징 된 인덱싱과 토큰의 리스트
        """
        jpype.attachThreadToJVM()
        return [(idx, self.extract_morphs_for_single_doc(doc, use_mecab=use_mecab)) for idx, doc in tuple_ls]

    # 병렬 처리를 위해 리스트를 분할 하는 함수
    def split_list(self, ls, n_batch):
        """
        :param ls: (list) 작업 대상 리스트
        :param n_batch: (int) 분할 하는 배치의 수
        :return: (list) 분할 결과 값
        """
        n = len(ls)
        batch_size = n // n_batch + 1

        return_ls = []
        for idx in range(0, n, batch_size):
            return_ls.append(ls[idx: min(idx + batch_size, n)])
        return return_ls

    # 멀티쓰레딩을 적용하여 토크나이징(형태소)하는 함수
    def extract_morphs_for_all_document_with_okt_FAST_VERSION(self, doc_ls, n_thread=4):
        """
        :param doc_ls: (list) 문서들의 리스트
        :param n_thread: (int) 사용 할 쓰레드의 갯수, default=4
        :return: (list) 형태소에 대해 토크나이징 한 문서들의 토큰 리스트
        """
        jpype.attachThreadToJVM()

        # 텍스트 클렌징 작업 수행, [(idx, clean_doc)] 형태로 저장
        clean_tuple_ls = [(idx, clean_doc) for idx, clean_doc in zip(range(len(doc_ls)), self.clean_doc(doc_ls))]

        # 멀티쓰레딩을 위한 작업(리스트)분할
        split_clean_tuple_ls = self.split_list(clean_tuple_ls, n_thread)

        que = queue.Queue()
        thread_ls = []

        for tuple_ls in split_clean_tuple_ls:
            temp_thread = Thread(
                target=lambda q, arg1, arg2: q.put(self._extract_morphs_for_multiprocessing(arg1, arg2)),
                args=(que, tuple_ls))

            temp_thread.start()
            thread_ls.append(temp_thread)

        for thread in thread_ls:
            thread.join()

        # 정렬을 위한 index_ls와 token_ls를 사용
        index_ls = []
        token_ls = []

        # thread의 return 값을 결합
        while not que.empty():
            result = que.get()  # [(idx, token), (idx, token)...] 형태를 반환
            index_ls += [idx for idx, _ in result]
            token_ls += [token for _, token in result]

        token_ls = [token for idx, token in sorted(zip(index_ls, token_ls))]

        return token_ls
