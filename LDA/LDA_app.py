import streamlit as st
import pandas as pd
import pyLDAvis
import pyLDAvis.gensim_models as gensimvis
import matplotlib.pyplot as plt
from gensim.corpora import Dictionary
from gensim.models import LdaModel
from gensim.matutils import Sparse2Corpus
from sklearn.feature_extraction.text import CountVectorizer
from wordcloud import WordCloud
import jieba
from jieba import analyse
import io
import re
import string

# 加载自定义词典
jieba.load_userdict("/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/SogouLabDic.txt")
jieba.load_userdict("/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/dict_baidu_utf8.txt")
jieba.load_userdict("/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/dict_pangu.txt")
jieba.load_userdict("/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/dict_sougou_utf8.txt")
jieba.load_userdict("/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/dict_tencent_utf8.txt")
jieba.load_userdict("/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/my_dict.txt")

# 加载停用词
stopwords = {}.fromkeys([line.rstrip() for line in open('/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/Stopword.txt')])


# 分词和停用词过滤
def preprocess_text(text):
    seg = jieba.cut(text)
    return ' '.join([i for i in seg if i not in stopwords])


# 关键词提取
def extract_keywords(text):
    keywords = analyse.extract_tags(text, allowPOS=(
    'ns', 'nr', 'nt', 'nz', 'nl', 'n', 'vn', 'vd', 'vg', 'v', 'vf', 'a', 'an', 'i'))
    return ' '.join(keywords)


# 主题建模
def perform_topic_modeling_gensim(data, n_topics=5):
    vectorizer = CountVectorizer(preprocessor=preprocess_text, max_df=0.95, min_df=2, stop_words='english')
    doc_term_matrix = vectorizer.fit_transform(data)

    # 转换为gensim可用的格式
    corpus = Sparse2Corpus(doc_term_matrix, documents_columns=False)
    id2word = Dictionary.from_corpus(corpus,
                                     id2word=dict((i, s) for i, s in enumerate(vectorizer.get_feature_names_out())))

    lda = LdaModel(corpus=corpus, num_topics=n_topics, id2word=id2word, random_state=0)

    return lda, id2word, corpus


# 显示主题词云
def display_word_cloud(lda, id2word):
    for idx, topic in enumerate(lda.get_topics()):
        plt.figure(figsize=(10, 6))
        word_freq = dict(zip(id2word.values(), topic))
        wordcloud = WordCloud(width=800, height=400, max_words=50, font_path='/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/Songti.ttc').generate_from_frequencies(word_freq)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Topic {idx + 1}')
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        st.image(buf, use_column_width=True)
        plt.close()

# 替换pyLDAvis中的文本为中文
def translate_html_to_chinese(html_content):
    translations = {
        "Topic": "主题",
        "Lambda": "λ 值",
        "Relevance": "关联度",
        "Overall term frequency": "整体词频",
        "Top 30 Most Salient Terms": "前30个最显著的词语",
        "Most relevant words for topic": "主题的相关词语",
    }
    for english, chinese in translations.items():
        html_content = html_content.replace(english, chinese)
    return html_content

# Streamlit应用
st.title("主题建模工具")

uploaded_file = st.file_uploader("上传数据表", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.write("数据预览：", df.head())

    if '评论内容' in df.columns:
        # 提取关键词
        df['关键词'] = df['评论内容'].apply(extract_keywords)

        st.write("关键词提取结果：", df[['评论内容', '关键词']].head())

        n_topics = st.slider("选择主题数目", 2, 20, 5)
        lda_model, id2word, corpus = perform_topic_modeling_gensim(df['评论内容'], n_topics=n_topics)

        # 显示LDA可视化
        st.write("LDA 模型可视化：")
        lda_vis_data = gensimvis.prepare(lda_model, corpus, id2word)
        pyLDAvis_html = pyLDAvis.prepared_data_to_html(lda_vis_data)
        st.components.v1.html(pyLDAvis_html, width=1300, height=800, scrolling=True)

        # 显示主题词云
        st.write("主题词云：")
        display_word_cloud(lda_model, id2word)
    else:
        st.error("数据表中未找到'评论内容'列，请确保上传的表格包含该列。")