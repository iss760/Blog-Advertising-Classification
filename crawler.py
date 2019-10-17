from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
from db_connect import DB

# 100 영화, 문화
# 101 육아, 결혼
# 102 상품리뷰
# 103 여행
# 104 맛집, 음식
# 105 IT, 인터넷
# 106 사회, 정치
# 107 비즈니스, 경제
# 108 패션, 미용


class Blog_Crawler:
    def __init__(self, web_path):
        self.driver = webdriver.Chrome(web_path)
        self.db = DB()
        self.category_list = {
            '100': 6, '101': 15, '102': 21, '103': 27, '104': 29, '105': 30, '106': 31, '107': 33, '108': 18
        }

    # 포스팅의 크롤링 가능한 실제 링크를 반환 하는 함수 (네이버 블로그는 크롤링 가능 링크와 읽기용 링크 따로 존재)
    def real_link_build(self, blogger, posting_index):
        """
        :param blogger: (str) 블로거의 아이디
        :param posting_index: (str) 해당 포스팅의 고유 번호
        :return: (str) 크롤링이 가능한 포스팅 실제 주소
        """
        posting_real_link = 'http://blog.naver.com/PostView.nhn?blogId=' + str(blogger) + \
                            '&logNo=' + str(posting_index) + \
                            '&from=search&redirect=Log&widgetTypeCall=true&directAccess=false'
        return posting_real_link

    # 카테고리 버전의 블로그 크롤링 함수
    def crawler_ver_category(self, category_number, search_number):
        """
        :param category_number: (int) 수집할 카테고리 고유 번호
        :param search_number: (int) 수집할 포스팅의 갯수
        :return: None
        """
        count = 0
        page_number = 1
        posting_body_list = []
        while True:
            page_link = 'https://section.blog.naver.com/ThemePost.nhn?directoryNo=' \
                        + str(self.category_list[str(category_number)]) + \
                        '&activeDirectorySeq=4&currentPage=' + str(page_number)
            self.driver.get(page_link)

            sleep(3)

            posting_page = BeautifulSoup(self.driver.page_source, 'html.parser')
            temp_list = posting_page.findAll('a', {'class': 'desc_inner'})

            url_list = []
            for temp in temp_list:
                temp = str(temp)
                temp = temp.split('" href="')
                temp = temp[1]
                temp = temp.split('" ng')
                url_list.append(temp[0])

            for url in url_list:
                url = str(url)
                temp = url.split('.com/')
                temp = temp[1]
                temp = temp.split('/')
                blogger = temp[0]
                posting_index = temp[1]

                posting_real_link = self.real_link_build(blogger, posting_index)
                posting_body = self.body_crawler(posting_real_link)
                posting_body_list.append(posting_body)

                count = count + 1

                self.db.data_save(url, posting_body, category_number)

                if count >= search_number:
                    return

            page_number = page_number + 1

    # 포스팅의 본문 수집 함수
    def body_crawler(self, url):
        """
        :param url: (str) 포스팅 실제 링크 (real_link)
        :return: (str) 포스팅 본문
        """
        posting_full_contents = ''
        try:
            # 포스팅 본문으로 접근
            self.driver.get(url)
            posting_page = BeautifulSoup(self.driver.page_source, 'html.parser')

            try:
                # 본문 "se-main-container" HTML_TAG 사용
                temp = posting_page.find('div', {'class': 'se-main-container'}).text
                temp = str(temp).replace('\n', '')
                posting_full_contents = temp.strip()
                posting_full_contents = posting_full_contents.replace("'", "")
                posting_full_contents = posting_full_contents.replace("\\", "")
            except:
                try:
                    # 본문 "postViewArea" HTML_TAG 사용
                    temp = posting_page.find('div', {'id': 'postViewArea'}).text
                    temp = str(temp).replace('\n', '')
                    posting_full_contents = temp.strip()
                    posting_full_contents = posting_full_contents.replace("'", "")
                    posting_full_contents = posting_full_contents.replace("\\", "")
                except:
                    try:
                        # 본문 "se_component_wrap sect_dsc __se_component_area" HTML_TAG 사용
                        temp = posting_page.find('div', {'class': 'se_component_wrap sect_dsc __se_component_area'}).text
                        temp = str(temp).replace('\n', '')
                        posting_full_contents = temp.strip()
                        posting_full_contents = posting_full_contents.replace("'", "")
                        posting_full_contents = posting_full_contents.replace("\\", "")
                    except:
                        # 분문이 다른 HTML_TAG 사용
                        print("posting error (maybe new html_tag) url : ", url)
                        pass
        except Exception as e:
            print(e)
            print("posting error (maybe deleted posts) url : ", url)
            pass

        return posting_full_contents




