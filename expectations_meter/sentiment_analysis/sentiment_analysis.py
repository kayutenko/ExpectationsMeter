from pprint import pprint as pp
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import  TfidfVectorizer
from sklearn.tree import DecisionTreeClassifier
from nltk.corpus import stopwords as sp
from nltk.stem import SnowballStemmer
from string import punctuation

with open('../english_stopwords.txt', 'r', encoding='utf-8') as f:
    stopwords = [word.strip('\n') for word in f.readlines()]

stemmer = SnowballStemmer('english')

def preprocess(text):
    tokens = [word.strip(punctuation) for word in text.lower().split() if not word in stopwords]
    stems = [stemmer.stem(token) for token in tokens]
    return stems
print('Reading df...')
df = pd.read_csv('Amazon.csv')
# bodies = list(df.body)
# pp(bodies)
# print('Preprocessing...')
texts = [preprocess(text) for text in list(df.body)[:10] if not pd.isnull(text)]
vectorizer = TfidfVectorizer(lowercase=False, max_df=0.4, min_df = 20)
X = vectorizer.fit_transform([' '.join(text) for text in texts])
print(X)

#
#
#
#
# y = pd.DataFrame([1 if int(star[0]) >= 4 else 0 for star in df.stars])
#
#
