import requests
import pandas as pd
from bs4 import BeautifulSoup
from pprint import pprint as pp
from collections import OrderedDict
import os


class Parser:
    def __init__(self, output):
        if os.path.exists(output):
            output = ''.join(output.split('.')[:-1]) + '_1' + '.xlsx'
        self.output = pd.ExcelWriter(output, engine='openpyxl')
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
            data.to_excel(self.output, sheet_name='Sheet1', index=False)
            self.output.save()
        else:
            data.to_excel(self.output, startrow= self.urls_parsed + 1, sheet_name= 'Sheet1', header=None, index=False)
            self.output.save()

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
                        self.output.close()
                        quit()
                    else:
                        user_answer = input('Parsing paused. Continue? (Y/N) ')
            except Exception as e:
                print('An Error occurred with url: {} {}'.format(url, e))
                self.output.save()
                self.output.close()
        self.output.save()
        self.output.close()

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

if __name__ == '__main__':
    # url = 'https://www.macrumors.com/2003/05/09/ibm-gobi-mojave-powerpc-970-and-beyond/'

    test = MacrumorsParser('macrumors3.xlsx')
    # data = test.get_data(url)
    # pp(test.article_parser(data))
    test.parse()