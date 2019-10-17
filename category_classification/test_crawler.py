import crawler

bc = crawler.Blog_Crawler('c://chromedriver.exe')

category_list = [100, 101, 102, 103, 104, 105, 106, 107, 108]
search_number = 100

for category in category_list:
    bc.crawler_ver_category(category, search_number)
