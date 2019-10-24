# -*- coding: utf-8 -*-

from rs_sentiment_analysis.sentiment_analysis import Sentiment_Analysis
from db_connect import DB

if __name__ == '__main__':
    sa = Sentiment_Analysis()
    db = DB()

    sql = "select contents from restaurant.review where not contents = '' order by rand() limit 10;"
    source = db.data_load(sql)

    data = []
    for _source in source:
        temp = str(_source).replace('(', '')
        temp = temp.replace(')', '')
        temp = temp.replace("'", "")
        data.append(temp)
    for i, j in enumerate(data):
        print(i + 1, ' ) ', j)

    print('\n**********************************')
    sa.sentiment_analysis(data)
