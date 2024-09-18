import streamlit as st
import pandas as pd
import jieba
from io import BytesIO
from jieba import analyse

# 加载自定义词典
jieba.load_userdict("LDA/SogouLabDic.txt")
jieba.load_userdict("LDA/dict_baidu_utf8.txt")
jieba.load_userdict("LDA/dict_pangu.txt")
jieba.load_userdict("LDA/dict_sougou_utf8.txt")
jieba.load_userdict("LDA/dict_tencent_utf8.txt")
jieba.load_userdict("LDA/my_dict.txt")

# 加载停用词
stopwords = {}.fromkeys(
    [line.rstrip() for line in open('LDA/Stopword.txt')])


# 分词和停用词过滤
def preprocess_text(text):
    seg = jieba.cut(text)
    return [i for i in seg if i not in stopwords]


# 设置 Streamlit 标题
st.title("视觉类评论关键词密度分析")

# 上传 CSV 文件
uploaded_file = st.file_uploader("上传分类结果数据表", type="csv")

# 输入关键词
keywords = st.text_input("输入关键词（多个关键词用空格分隔）", "数据 可视化")

# 文件名输入框
file_name = st.text_input("输入要保存的文件名（不包括扩展名）", "分析结果")

# 分析按钮
if st.button("启动分析"):
    if uploaded_file is not None:
        # 读取上传的 CSV 文件
        st.write("正在读取上传的 CSV 文件...")
        data = pd.read_csv(uploaded_file)
        st.write("CSV 文件读取完毕")

        # 获取视觉类评论
        visual_comments = data[data['classification'] == '是']

        # 分割关键词
        keywords_list = keywords.split()

        # 初始化计数
        keyword_density = {keyword: 0 for keyword in keywords_list}
        total_words = 0

        # 计算关键词密度
        for _, row in visual_comments.iterrows():
            comment = row['评论内容']
            words = preprocess_text(comment)
            total_words += len(words)
            for keyword in keywords_list:
                keyword_density[keyword] += words.count(keyword)

        # 计算并显示每个关键词的密度
        keyword_density_percentage = {keyword: (count / total_words) * 100 for keyword, count in
                                      keyword_density.items()}

        st.write(f"总视觉类评论数: {len(visual_comments)}")
        st.write(f"总词数: {total_words}")

        st.write("关键词密度分析结果:")
        density_data = pd.DataFrame({
            "关键词": list(keyword_density.keys()),
            "出现次数": list(keyword_density.values()),
            "关键词密度 (%)": [f"{density:.2f}" for density in keyword_density_percentage.values()]
        })

        st.write(density_data)

        # 提供下载链接
        csv = BytesIO()
        density_data.to_csv(csv, index=False, encoding='utf-8-sig')
        csv.seek(0)
        st.download_button(label="下载关键词密度分析结果", data=csv, file_name=f'{file_name}.csv', mime='text/csv')

    else:
        st.error("请先上传数据表")
