# -*-coding:utf-8-*-

import json


# 사전 기반 감정 분석
class DSA:
    def __init__(self):
        print("\n[한국어 감성사전]")
        print("-1:부정, 0:중립 or Unknown, 1:긍정,")
        print("\n")
        with open('./sentiword_dict.json', encoding='utf-8', mode='r') as f:
            self.data = json.load(f)
        with open('./sentiword_dict2.json', encoding='utf-8', mode='r') as f:
            self.data2 = json.load(f)

    # 단어에 대한 감정분석 함수
    def word_sentiment_analysis(self, word):
        """
        :param word: (str) 토크나이징 된 단어
        :return: (list) 단어와 단어의 점수
        """

        data = self.data
        data2 = self.data2

        sentiword_dict = data + data2

        result = ['UNK', 'UNK']
        for i in range(0, len(sentiword_dict)):
            if sentiword_dict[i]['word'] == word:
                result.pop()
                result.pop()
                result.append(sentiword_dict[i]['word'])
                result.append(sentiword_dict[i]['polarity'])

        r_word = result[0]
        s_word = result[1]

        return r_word, s_word

    # 토크나이징 된 문서에 대한 감정분석 함수
    def doc_sentiment_analysis(self, doc):
        """
        :param doc: (list) 하나의 문서를 토크나이징 한 토큰의 모음
        :return: (list) 토큰과 토큰의 감정 점수로 이루어진 리스트
        """

        result = []
        for word in doc:
            word_sentiment = self.word_sentiment_analysis(word)

            # 사전에 없는 단어 제외
            if word_sentiment[0] is 'UNK':
                continue
            result.append(self.word_sentiment_analysis(word))

        return result

    # 토크나이징 된 문서에 대한 긍부정 분류 함수
    def sentiment_analysis_classifier(self, doc, threshold=0.05):
        """
        :param doc: (list) 하나의 문서를 토크나이징 한 토큰의 모음
        :param threshold: (float) 긍부정 분류를 위한 threshold, [default=0.05]
        :return: (list) 긍정점수의 총합, 부정점수의 총합, 문서의 긍정부정 여부로 이루어진 리스트
        """

        result = []

        word_list = self.doc_sentiment_analyisis(doc)

        # 긍정/부정 점수 계산
        positive_score = 0
        negative_score = 0
        for word in word_list:
            if int(word[1]) > 0:
                positive_score = positive_score + int(word[1])
            elif int(word[1]) < 0:
                negative_score = negative_score + int(word[1])

        result.append(positive_score)
        result.append(negative_score)

        # 부정점수 비교를 위한 절댓값 처리
        negative_score = abs(negative_score)

        # 긍정/부정 점수가 같을 경우
        if positive_score == negative_score:
            result.append('중립')

        # 긍정 점수가 더 높을 경우
        elif positive_score > negative_score:
            try:
                positive_rate = (positive_score/negative_score) - 1
                if positive_rate > threshold:
                    result.append('긍정')
                else:
                    result.append('중립')
            except ZeroDivisionError:
                result.append('긍정')

        # 부정 점수가 더 높을 경우
        else:
            try:
                negative_rate = (negative_score/positive_score) - 1
                if negative_rate > threshold:
                    result.append('부정')
                else:
                    result.append('중립')
            except ZeroDivisionError:
                result.append('부정')

        return result

    # 토크나이징 된 문서 리스트에 대한 긍부정 분류 함수
    def all_sentiment_analysis_classifier(self, doc_list, threshold=0.05):
        """
        :param doc_list: (list) 토크나이징된 문서로 이루어진 문서 모음
        :param threshold: (float) 긍부정 분류를 위한 threshold, [default=0.05]
        :return: (list) 문서들의 긍정점수, 부정점수, 긍정부정 여부
        """

        result = []
        for doc in doc_list:
            doc_result = self.sentiment_analysis_classifier(doc, threshold)
            result.append(doc_result)

        return result


