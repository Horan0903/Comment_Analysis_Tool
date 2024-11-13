import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from wordcloud import WordCloud
import jieba
from jieba import analyse
import io

# 缓存加载自定义词典
@st.cache_resource
def load_custom_dict():
    user_dicts = [
        "/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/SogouLabDic.txt",
        "/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/dict_baidu_utf8.txt",
        "/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/dict_pangu.txt",
        "/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/dict_sougou_utf8.txt",
        "/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/dict_tencent_utf8.txt",
        "/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/my_dict.txt"
    ]
    for dict_path in user_dicts:
        jieba.load_userdict(dict_path)

# 加载自定义词典
load_custom_dict()

# 缓存加载停用词
@st.cache_resource
def load_stopwords():
    with open('/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/Stopword.txt') as f:
        return set(line.strip() for line in f)

stopwords = load_stopwords()

# 缓存加载字体
@st.cache_resource
def load_font():
    return font_manager.FontProperties(fname='/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/Songti.ttc')

my_font = load_font()

# 分词和停用词过滤
def preprocess_text(text):
    seg = jieba.cut(text)
    return ' '.join([i for i in seg if i not in stopwords])

# 关键词提取
def extract_keywords(text):
    keywords = analyse.extract_tags(text)
    return keywords

# 生成词云
def display_word_cloud(keywords):
    wordcloud = WordCloud(width=800, height=400, font_path='/Users/liuhaoran/LHR/PycharmProjects/Comment analysis/LDA/Songti.ttc').generate_from_frequencies(keywords)
    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    st.image(buf, use_column_width=True)
    plt.close()

# Streamlit应用
st.title("关键词占比分析工具")

uploaded_file = st.file_uploader("上传数据表", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.write("数据预览：", df.head())
    except Exception as e:
        st.error(f"文件读取失败：{e}")
        st.stop()

    # 检查文件是否有必要的列
    if df.empty:
        st.error("数据表为空，请上传有效的数据表。")
        st.stop()

    # 选择分析的列
    selected_column = st.selectbox("选择用于分析的列", df.columns)

    if selected_column:
        # 提取关键词
        df['关键词'] = df[selected_column].apply(lambda x: ' '.join(extract_keywords(str(x))))
        st.write("关键词提取结果：", df[[selected_column, '关键词']].head())

        # 统计关键词出现频率
        keyword_list = df['关键词'].str.split().explode()
        keyword_count = keyword_list.value_counts()
        keyword_count_df = keyword_count.reset_index()
        keyword_count_df.columns = ['关键词', '出现次数']

        st.write("关键词出现次数：", keyword_count_df)

        # 生成词云
        st.write("关键词词云：")
        display_word_cloud(keyword_count.to_dict())

        # 关键词占比可视化（条形图）
        st.write("关键词占比：")

        # 限制关键词数量（例如只显示前30个关键词）
        top_n = st.slider("选择要显示的关键词数量", 5, 50, 30)
        keyword_count_df = keyword_count_df.head(top_n)

        fig, ax = plt.subplots(figsize=(12, 8))  # 增大图形尺寸

        # 绘制条形图
        ax.barh(keyword_count_df['关键词'], keyword_count_df['出现次数'], color='skyblue')

        # 设置中文字体
        ax.set_yticklabels(keyword_count_df['关键词'], fontproperties=my_font)

        # 设置标题和标签
        ax.set_xlabel('出现次数', fontproperties=my_font)
        ax.set_ylabel('关键词', fontproperties=my_font)
        plt.xticks(rotation=45)  # 旋转 x 轴的标签

        # 在条形图顶部显示数值
        for i in ax.patches:
            ax.text(i.get_width() + 0.2, i.get_y() + i.get_height() / 2, f'{int(i.get_width())}', va='center')

        plt.tight_layout()
        st.pyplot(fig)

    else:
        st.error("请选择一个用于分析的列。")