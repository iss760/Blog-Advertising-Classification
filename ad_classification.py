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
        if posting_path in 'blog.me':
            blogger = str(posting_path).split('.blog.me')[0]
            posting_real_number = str(posting_path).split('.blog.me/')[1]
        else:
            blogger = str(posting_path).split('blog.naver.com/')[1].split('/')[0]
            posting_real_number = str(posting_path).split(blogger + '/')[1]

        posting_real_link = self.bc.real_link_build(blogger, posting_real_number)
        length, pictures, videos, maps = self.bc.get_posting_feature(posting_real_link)

        f_class = self.pc.classification(length, pictures, videos, maps)

        blog_url = 'https://blog.naver.com/' + blogger
        posting_real_number_ls, posting_date_ls = self.bc.get_posting_info(blog_url)

        ex_posting_body_ls = []
        category_classification_result = []
        for posting_real_number, posing_date in zip(posting_real_number_ls, posting_date_ls):
            posting_real_link = self.bc.real_link_build(blogger, posting_real_number)
            ex_posting_body = self.bc.get_posting_body(posting_real_link)
            ex_posting_body_ls.append(ex_posting_body)

            c1_result = self.c1.classifier(ex_posting_body)
            category_classification_result.append(self.c2.classifier(c1_result))

        restaurant_posting_count = 0
        sentiment_analysis_result = []
        for i, _category_classification_result in enumerate(category_classification_result):
            if _category_classification_result == 100:
                restaurant_posting_count += 1
                sentiment_analysis_result.append(ex_posting_body_ls[i])

        diversity_category = len(set(category_classification_result))

        negative_posting_count = 0
        for _sentiment_analysis_result in sentiment_analysis_result:
            if _sentiment_analysis_result == 0:
                negative_posting_count += 1
        negative_posting_rate = negative_posting_count / restaurant_posting_count

        alpha = 0.3
        beta = 0.35
        gamma = 0.35

        result = alpha * f_class - beta * (diversity_category - 3) + gamma * (negative_posting_rate * 10)

        if result > 0.45:
            print('Non Advertisement')
        else:
            print('Advertisement')
