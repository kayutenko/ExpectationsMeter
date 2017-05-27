import re
import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
from pprint import pprint as pp
from collections import OrderedDict
from time import sleep
import os
from selenium import webdriver


class Parser:
    def __init__(self, output):
        if os.path.exists(output):
            output = ''.join(output.split('.')[:-1]) + '_1' + '.xlsx'
        # self.output = pd.ExcelWriter(output, engine='openpyxl')
        self.output = output
        self.urls_parsed = 0
        pass

    def get_element(self, source, path):
        element = source.select(path)
        if element:
            return element[0].get_text()
        else:
            return ''

    @staticmethod
    def get_data(url):
        web_page = requests.get(url).text
        html = BeautifulSoup(web_page, 'html.parser').html
        return html

    def article_parser(self, data):
        yield data

    def urls_collector(self):
        return []

    def write_data(self, data):
        data = pd.DataFrame([list(data.values())], columns=list(data.keys()))
        if self.urls_parsed == 0:
            try:
                data.to_csv(self.output, index=False)
                # self.output.save()
            except Exception as e:
                print('csv saving error', e)
        else:
            try:
                data.to_csv(self.output, mode='a', header=False, index=False)
                # self.output.save()
            except Exception as e:
                print('csv saving error', e)

    def parse(self):
        urls = self.urls_collector()
        for url in urls:
            try:
                data = self.article_parser(self.get_data(url))
                self.write_data(data)
                self.urls_parsed += 1
                print(self.urls_parsed, url)
            except KeyboardInterrupt:
                user_answer = input('Parsing paused. Continue? (Y/N) ')
                while True:
                    if user_answer == 'Y':
                        break
                    elif user_answer == 'N':
                        # self.output.close()
                        quit()
                    else:
                        user_answer = input('Parsing paused. Continue? (Y/N) ')
            except Exception as e:
                print('An Error occurred with url: {} {}'.format(url, e))
                # self.output.save()
                # self.output.close()
        # self.output.save()
        # self.output.close()


class MacrumorsParser(Parser):
    def urls_collector(self):
        urls = []
        for year in range(2009, 2018):
            for month in range(1, 13):
                if month < 10:
                    month = '0' + str(month)
                url = 'https://www.macrumors.com/archive/{year}/{month}/'.format(year=year, month=month)
                html = self.get_data(url)
                content = html.select('#contentContainer #content .wrapper')[0]
                urls_found = ['http:' + a.get('href') for a in content.find_all('a')]
                print(year, month, 'URL: ', url, "URLS found:", len(urls_found))
                urls.extend(urls_found)
        return urls

    def article_parser(self, data):
        output = OrderedDict()
        article = data.select('.article')[0]
        output['title'] = self.get_element(article, 'h1.title')
        if output['title'] == '':
            output['title'] = self.get_element(article, 'h1.header-title')
        output['body'] = self.get_element(article, '.content')
        if output['body'] == '':
            output['body'] = self.get_element(article, '#content .body')
        output['author'] = self.get_element(article, '.byline > a.author-url')
        byline = self.get_element(article, '.byline')
        output['datetime'] = byline[:byline.find('by')-1]
        if '' in list(output.values()):
            raise Exception('Something went wrong and one var is empty')
        return output


class AppleInsiderParser(Parser):
    def urls_collector(self):
        urls = []
        for year in range(9, 18):
            if year < 10: year = '0' + str(year)
            for month in range(1, 13):
                if month < 10: month = '0' + str(month)
                for day in range(1, 32):
                    if day < 10: day = '0' + str(day)
                    url = "http://appleinsider.com/archives/{year}/{month}/{day}/page/1".format(year=year, month=month, day=day)
                    html = self.get_data(url)
                    content = html.select('#content')[0]
                    urls_found = ['http:' + a.get('href') for a in content.select('.post a')]
                    print(year, month, 'URL: ', url, "URLS found:", len(urls_found))
                    urls.extend(urls_found)
        with open('AppleInsiderUrls', 'w', encoding='utf-8') as f:
            [f.write(i + '\n') for i in urls]
        return urls

    def article_parser(self, data):
        output = OrderedDict()
        article_data = json.loads(self.get_element(data, "script[type='application/ld+json']"))
        output['title'] = article_data['headline']
        body = BeautifulSoup(str(BeautifulSoup(article_data['articleBody'], 'html.parser').get_text()), 'lxml').get_text()
        output['body'] = re.sub('\n{2,}|\r\n','\n', body)
        output['author'] = article_data['author']['name']
        output['datetime'] = article_data['datePublished']
        return output


class NineToFiveMacParser(Parser):
    def urls_collector(self):
        urls = []
        for year in range(2009, 2018):
            for month in range(1, 13):
                if month < 10: month = '0' + str(month)
                for day in range(1, 31):
                    if day < 10: day = '0' + str(day)
                    url = "https://9to5mac.com/{year}/{month}/{day}/".format(year=year, month=month, day=day)
                    html = self.get_data(url)
                    content = html.select('#content')[0]
                    urls_found = [a.get('href') for a in content.select('.post-title a')]
                    print(year, month, 'URL: ', url, "URLS found:", len(urls_found))
                    urls.extend(urls_found)
                    # sleep(2)
        with open('NineToFiveMacUrls', 'w', encoding='utf-8') as f:
            [f.write(i + '\n') for i in urls]
        return urls

    def article_parser(self, data):
        output = OrderedDict()
        article = data.select('.post-content')[0]
        output['title'] = self.get_element(article, 'h1.post-title a')
        output['body'] = self.get_element(article, '.post-body').strip()
        output['author'] = self.get_element(article, 'p[itemprop=author]').strip()
        output['datetime'] = article.select('meta[itemprop=datePublished]')[0]['content']
        if '' in list(output.values()):
            raise Exception('Something went wrong and one var is empty')
        # sleep(2)
        return output


class AmazonParser(Parser):
    def __init__(self, output):
        super().__init__(output)
        self.driver = webdriver.Chrome()

    def get_data(self, url):
        print(url)
        for n in range(1, 1000):
            current_url = url.format(n)
            print(current_url)
            self.driver.get(current_url)
            reviews = self.driver.find_element_by_id('cm_cr-review_list').get_attribute('innerHTML')
            if 'Sorry, no reviews match your current selections.' not in reviews:
                yield BeautifulSoup(reviews, 'html.parser')
            else:
                break

    def get_reviews(self, bs_data):
        reviews = bs_data.select('.a-section.review > .celwidget')
        return reviews

    def review_parser(self, bs_review):
        output = OrderedDict()
        output['stars'] = self.get_element(bs_review, 'i[data-hook=review-star-rating] > span.a-icon-alt')
        output['title'] = self.get_element(bs_review, 'a.review-title')
        output['body'] = self.get_element(bs_review, 'span.review-text').strip()
        output['author'] = self.get_element(bs_review, 'a.author').strip()
        output['date'] = self.get_element(bs_review, 'span.review-date').strip()
        # if '' in list(output.values()):
        #     raise Exception('Something went wrong and one var is empty')
        # # sleep(2)
        return output

    def parse(self, start_urls):
        for url in start_urls:
            for page in self.get_data(url):
                for review in self.get_reviews(page):
                    try:
                        review_data = self.review_parser(review)
                        self.write_data(review_data)
                        self.urls_parsed += 1
                    except KeyboardInterrupt:
                        user_answer = input('Parsing paused. Continue? (Y/N) ')
                        while True:
                            if user_answer == 'Y':
                                break
                            elif user_answer == 'N':
                                quit()
                            else:
                                user_answer = input('Parsing paused. Continue? (Y/N) ')
                    except Exception as e:
                        print('An Error occurred with url: {} {}'.format(url, e))


if __name__ == '__main__':
    # test = AppleInsiderParser('AppleInsider_6.xlsx')
    # test.parse()

    # test = NineToFiveMacParser('NineToFiveMac.xlsx')
    # test.parse()

    # test = MacrumorsParser('MacRummors5.csv')
    # test.parse()
    with open('..\\sentiment_analysis\\seed_urls_ipads', 'r', encoding='utf-8') as f:
        start_urls = [url.strip('\n') for url in f.readlines()]
    test = AmazonParser('AmazonAppleiPads.csv')
    test.parse(start_urls)
    del(test)

    with open('..\\sentiment_analysis\\seed_urls_macs', 'r', encoding='utf-8') as f:
        start_urls = [url.strip('\n') for url in f.readlines()]
    test2 = AmazonParser('AmazonAppleMacs.csv')
    test2.parse(start_urls)