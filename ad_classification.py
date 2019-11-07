from crawler import Blog_Crawler
from db_connect import DB
from category_classification.classification_nb import BCC_NB
from category_classification.classification_nb_02 import BCC_NB_02
from posting_feture_classification.posting_classification import Posting_Classification
from rs_sentiment_analysis.sentiment_analysis import Sentiment_Analysis


class AD_Classificaion:
    def __init__(self):
        self.db = DB()
        self.bc = Blog_Crawler('c://chromedriver.exe')
        self.c1 = BCC_NB()
        self.c2 = BCC_NB_02()
        self.pc = Posting_Classification()
        self.sa = Sentiment_Analysis()

    def classifier(self, posting_path):
        # 블로거, 포스팅의 고유 번호 추출
        if posting_path in 'blog.me':
            blogger = str(posting_path).split('.blog.me')[0]
            posting_real_number = str(posting_path).split('.blog.me/')[1]
        else:
            blogger = str(posting_path).split('blog.naver.com/')[1].split('/')[0]
            posting_real_number = str(posting_path).split(blogger + '/')[1]

        # 포스팅의 특징 추출
        posting_real_link = self.bc.real_link_build(blogger, posting_real_number)
        length, pictures, videos, maps = self.bc.get_posting_feature(posting_real_link)

        # 특징 분석을 통한 광고 유무 판별
        f_class = self.pc.classification(length, pictures, videos, maps)

        # 포스팅을 작성한 블로거 추출
        blog_url = 'https://blog.naver.com/' + blogger

        # 블로거의 기존 포스팅 고유 번호들과 작성 날짜 수집
        posting_real_number_ls, posting_date_ls = self.bc.get_posting_info(blog_url)

        # 기존 포스팅들의 본문 수집과 카테고리 분류 결과
        ex_posting_body_ls = []
        category_classification_result = []
        for posting_real_number, posing_date in zip(posting_real_number_ls, posting_date_ls):
            # 기존 포스팅 본문 수집
            posting_real_link = self.bc.real_link_build(blogger, posting_real_number)
            ex_posting_body = self.bc.get_posting_body(posting_real_link)
            ex_posting_body_ls.append(ex_posting_body)

            # 1차 카테고리 분류
            c1_result = self.c1.classifier(ex_posting_body)

            # 1차 카테고리 분류에서 맛집으로 분류 된 경우
            if c1_result == 103:
                # 2차 카테고리 분류
                category_classification_result.append(self.c2.classifier(ex_posting_body))
            # 1차 카테고리 분류에서 맛집으로 분류 되지 않은 경우
            else:
                category_classification_result.append(c1_result)

        # 기존 포스팅들의 감성분석 결과
        restaurant_posting_count = 0
        sentiment_analysis_result = []
        for i, _category_classification_result in enumerate(category_classification_result):
            # 맛집 포스팅에 대해서만 카운팅과 감성분석
            if _category_classification_result == 100:
                restaurant_posting_count += 1
                sentiment_analysis_result.append(self.sa.sentiment_analysis(ex_posting_body_ls[i]))

        # 기존 포스팅들의 카테고리 다양성 수치화
        diversity_category = len(set(category_classification_result))

        # 기존 포스팅들의 부정적 포스팅 비율 수치화
        negative_posting_count = 0
        for _sentiment_analysis_result in sentiment_analysis_result:
            # 기존 포스팅들 중 부정적 포스팅만을 카운팅
            if _sentiment_analysis_result == 0:
                negative_posting_count += 1

        # 기존 포스팅들 중 부정적 포스팅의 비율 도출
        negative_posting_rate = negative_posting_count / restaurant_posting_count

        # 계수 설정
        alpha = 0.3
        beta = 0.35
        gamma = 0.35

        # 결과 값 도출
        result = alpha * f_class - beta * (diversity_category - 3) + gamma * (negative_posting_rate * 10)

        # 결과 출력
        threshold = 0.45
        if result > threshold:
            print('Non Advertisement')
        else:
            print('Advertisement')
