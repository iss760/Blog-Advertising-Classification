import time
from db_connect import DB
from category_classification import classification_nb

start = time.time()     # 전체 작업 시작 시간

db = DB()
bbc_nb = classification_nb.BCC_NB()

t_test_load_s = time.time()     # 테스트 데이터 로드 시작 시간

# 테스트 데이터 로드
sql = 'SELECT posting_url, posting_contents From blog order by rand() limit 10'
pre_doc_ls = db.data_load(sql)

t_test_load = time.time() - t_test_load_s       # 테스트 데이터 로드 끝 시간

# 테스트 데이터 전처리
doc_ls = []
for i, doc in enumerate(pre_doc_ls):
    print(i, ')   ', doc[0])
    temp = str(doc[1])
    temp = temp.replace('(', '')
    temp = temp.replace(')', '')
    doc_ls.append(temp)

# 테스트 데이터 카테고리 분류
bbc_nb.classifier(doc_ls, use_mecab=True, use_save_model=True)

# bbc_nb.model_evaluation()
# bbc_nb.model_train()
# bbc_nb.model_test()

# 시간 출력
print('test data load time : ', round(t_test_load, 2))
print('total time : ', round(time.time() - start, 2))
