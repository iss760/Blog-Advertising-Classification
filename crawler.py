from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
from random import randint
from datetime import datetime, timedelta

from db_connect import DB


class Blog_Crawler:
    def __init__(self, web_path):
        self.driver = webdriver.Chrome(web_path)
        self.db = DB()
        
        # 100 영화, 문화
        # 101 육아, 결혼
        # 102 상품리뷰
        # 103 여행
        # 104 맛집, 음식
        # 105 IT, 인터넷
        # 106 사회, 정치
        # 107 비즈니스, 경제
        # 108 패션, 미용
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

                self.db.data_save_blog(url, posting_body, category_number)

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

class Restaurant_Review_Crawler:
    def __init__(self, web_path):
        """
        :param web_path: (str) 크롬 브라우저 경로
        """
        self.driver = webdriver.Chrome(web_path)
        self.db = DB()

        # 사람처럼 보이기 위한 옵션들
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("disable-gpu")
        self.options.add_argument("lang=ko_KR")

        # 검색 키워드 리스트
        self.keyword_ls = [# '강남역',
                           #'홍대', '건대',
                           # '혜화',
                           # '광화문', '이태원',
                           # '명동', '종로',
                           '신촌', '압구정',
                           '동대문', '신림',                 # di-re
                           '영등포', '신사', '노원', '잠실'
                           ]
        # 검색 키워드 당 맛집 수집 개수
        self.n_restaurant = 200

        # DB primary key
        self.number = 38390

    # 다이닝 코드 리뷰 수집 함수
    def get_dining_code_review(self):
        # 키워드 별 순환
        for keyword in self.keyword_ls:
            # 키워드 검색 페이지 접근
            page_link = 'https://www.diningcode.com/isearch.php?query=' + str(keyword)
            self.driver.get(page_link)

            # 맛집 링크 리스트 불러오기
            self.driver.find_element_by_xpath('//*[@id="btn_normal_list"]/a/span').click()
            n_click = 0
            for i in range(self.n_restaurant//10 - 1):
                sleep(5)
                try:
                    self.driver.find_element_by_xpath('//*[@id="div_list_more"]/a/span').click()
                # n_restaurant 보다 맛집이 더 적을 경우 불러올 수 있을만큼 불러오기...
                except:
                    break
                n_click = i

            # 맛집 링크 리스트 추출
            rs_link_ls = []
            for i in range(1, self.n_restaurant + n_click + 1):
                try:
                    x_path = '// *[ @ id = "div_list"] / li[' + str(i) + '] / a / span[2]'
                    rs_link_ls.append(self.driver.find_element_by_xpath(x_path))
                # 중간 광고 pass
                except:
                    pass
            sleep(3)

            # 맛집 소개 순환하며 데이터 추출
            for rs_link in rs_link_ls:
                # 링크로 접근
                rs_link.click()
                sleep(randint(5, 9))
                self.driver.switch_to.window(window_name=self.driver.window_handles[-1])

                # 맛집 기본 정보 (이름, 평점) 수집
                rs_name = self.driver.find_element_by_xpath('//*[@id="div_profile"]/div[1]/div[2]/p').text
                rs_score = self.driver.find_element_by_xpath('//*[@id="div_profile"]/div[1]/div[4]/p/strong').text

                # 리뷰 리스트 불러오기
                while True:
                    try:
                        sleep(1)
                        self.driver.find_element_by_xpath('//*[@id="div_more_review"]/a/span').click()
                    # 더 이상 없을 때까지...
                    except:
                        break

                # 리뷰들의 고유 id 추출
                try:
                    info_page = BeautifulSoup(self.driver.page_source, 'html.parser')
                # 로그인 요구 팝업 창 처리
                except Exception as e:
                    print(e)
                    sleep(30)
                    self.driver.close()
                    self.driver.switch_to.window(window_name=self.driver.window_handles[0])
                    continue

                review_blocks1 = info_page.findAll('div', {'class': 'latter-graph'})
                review_blocks2 = info_page.findAll('div', {'class': 'latter-graph short'})
                review_blocks = review_blocks1 + review_blocks2
                review_id_ls = [review_block.attrs['id'] for review_block in review_blocks if 'id' in review_block.attrs]
                review_id_ls = set(review_id_ls)

                # print(rs_name, rs_score, 'reviews count : ', len(review_id_ls))

                # 리뷰 데이터 수집
                for review_id in review_id_ls:
                    # 리뷰 남긴 사람 ID 수집 및 정제
                    reviewer = self.driver.find_element_by_xpath('//*[@id="' + review_id + '"]/p[1]/span[1]/strong').text

                    # 리뷰 평점 수집 및 정제
                    review_score = self.driver.find_element_by_xpath('//*[@id="' + review_id + '"]/p[1]/span[3]/i[1]/i')
                    review_score = str(review_score.get_attribute('style'))
                    review_score = review_score.replace('width: ', '')
                    review_score = review_score.replace('%;', '')
                    review_score = int(review_score)//20

                    # 리뷰 날짜 수집 및 정제
                    review_date = self.driver.find_element_by_xpath('//*[@id="' + review_id + '"]/p[1]/span[3]/i[2]').text
                    review_date = str(review_date)
                    try:
                        try:
                            # 올해 이전에 작성된 리뷰
                            temp_date = datetime.strptime(review_date, '%Y년 %m월 %d일')
                        except:
                            # 올해 작성된 리뷰 처리
                            temp_date = '2019년 ' + str(review_date)
                            temp_date = datetime.strptime(temp_date, '%Y년 %m월 %d일')
                        review_date = datetime.strftime(temp_date, '%Y-%m-%d')
                    except:
                        try:
                            # 며칠 전에 작성된 리뷰
                            temp_date = review_date.replace('일 전', '')
                            temp_date = int(temp_date)
                            temp_date = datetime.now() + timedelta(days=(temp_date * (-1)))
                            review_date = datetime.strftime(temp_date, '%Y-%m-%d')
                        except:
                            # 몇분전, 몇시간전 작성된 리뷰 (그냥 버려...)
                            continue

                    # 리뷰 내용 수집 및 정제
                    try:
                        review_contents = self.driver.find_element_by_xpath('//*[@id="' + review_id + '"]/p[3]').text
                        review_contents = str(review_contents).replace("'", "")
                    except:
                        review_contents = ''

                    # 데이터 저장
                    self.db.data_save_restaurant(self.number, rs_name, reviewer, review_score, review_date,
                                                 review_contents, 'dining_code')
                    self.number = self.number + 1

                # 수집 한 페이지 닫기
                self.driver.close()
                self.driver.switch_to.window(window_name=self.driver.window_handles[0])

    # 망고 플레이트 리뷰 수집 함수
    def get_mango_plate_review(self):
        # 키워드 별 순환
        for keyword in self.keyword_ls:
            review_id_ls = []
            # 페이지 별 순환하며 맛집 소개 페이지 링크 추출
            for page_num in range(1, self.n_restaurant//20 + 1):
                page_link = 'https://www.mangoplate.com/search/' + str(keyword) + '?keyword=' + str(keyword) +\
                            '&page=' + str(page_num)
                self.driver.get(page_link)
                sleep(2)
                try:
                    info_page = BeautifulSoup(self.driver.page_source, 'html.parser')
                    sleep(2)
                    info_boxes = info_page.findAll('div', {'class': 'info'})
                    # 한 페이지 당 20개의 맛집 소개
                    for i in range(20):
                        temp = str(info_boxes[i]).split('a href="')
                        temp = temp[1].split('">')
                        review_id_ls.append(temp[0])
                # n_restaurant 보다 맛집이 더 적을 경우 불러올 수 있을만큼 불러오기...
                except:
                    break

            # 맛집 소개 페이지 순환
            for review_id in review_id_ls:
                # 맛집 소개 페이지 접근
                review_link = 'https://www.mangoplate.com' + str(review_id)
                self.driver.get(review_link)
                sleep(3)

                try:
                    # 맛집 기본 정보 (이름, 평점) 수집
                    rs_name = self.driver.find_element_by_xpath(
                        '/html/body/main/article/div[1]/div[1]/div/section[1]/header/div[1]/span/h1').text
                    rs_score = self.driver.find_element_by_xpath(
                        '/html/body/main/article/div[1]/div[1]/div/section[1]/header/div[1]/span/strong').text

                    # 맛집 리뷰 개수 추출
                    review_count = self.driver.find_element_by_xpath(
                        '/html/body/main/article/div[1]/div[1]/div/section[3]/header/ul/li[1]/button/span').text
                    review_count = int(review_count)
                except:
                    sleep(10)
                    continue

                # 리뷰 리스트 불러오기 (원인을 알수없는 불러오기 문제로 인해 15번으로 제한)
                for _ in range(15):
                    try:
                        sleep(3)
                        more_list_button = self.driver.find_element_by_xpath(
                            '/html/body/main/article/div[1]/div[1]/div/section[3]/div[2]')
                        more_list_button.click()
                    # 더 이상 없을 때까지...
                    except:
                        break

                # 리뷰 데이터 수집
                for i in range(review_count):
                    try:
                        # 각 수집 데이터들의 x_path
                        reviewer_xPath = '/html/body/main/article/div[1]/div[1]/div/section[3]/ul/li['\
                                         + str(i + 1) + ']/a/div[1]/span'
                        review_score_xPath = '/html/body/main/article/div[1]/div[1]/div/section[3]/ul/li[' \
                                             + str(i + 1) + ']/a/div[3]/span'
                        review_date_xPath = '/html/body/main/article/div[1]/div[1]/div/section[3]/ul/li[' \
                                            + str(i + 1) + ']/a/div[2]/div/span'
                        review_contents_xPath = '/html/body/main/article/div[1]/div[1]/div/section[3]/ul/li[' \
                                                + str(i + 1) + ']/a/div[2]/div/p'

                        # 리뷰 남긴 사람 ID 수집 및 정제
                        reviewer = self.driver.find_element_by_xpath(reviewer_xPath).text

                        # 리뷰 평점 수집 및 정제 (맛있다 : 5점, 괜찮다 : 3점, 별로다 : 1점)
                        review_score = self.driver.find_element_by_xpath(review_score_xPath).text
                        if review_score == '맛있다':
                            review_score = 5
                        elif review_score == '별로':
                            review_score = 1
                        else:
                            review_score = 3

                        # 리뷰 날짜 수집 및 정제
                        review_date = self.driver.find_element_by_xpath(review_date_xPath).text

                        # 리뷰 내용 수집 및 정제
                        review_contents = self.driver.find_element_by_xpath(review_contents_xPath).text
                        review_contents = str(review_contents).replace("'", "")

                        # 데이터 저장
                        self.db.data_save_restaurant(self.number, rs_name, reviewer, review_score, review_date,
                                                     review_contents, 'mango_plate')
                        self.number = self.number + 1
                    # 수집 에러 데이터는 그냥 버리기...
                    except:
                        pass


