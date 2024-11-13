import streamlit as st
import pandas as pd
import pkuseg
from io import BytesIO

# 初始化 pkuseg 分词器，使用细领域模型（如 'web'）
@st.cache_resource
def get_segmenter(model='web'):
    return pkuseg.pkuseg(model_name=model)

seg = get_segmenter()

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
        try:
            data = pd.read_csv(uploaded_file)
            st.write("CSV 文件读取完毕")
        except Exception as e:
            st.error(f"文件读取失败：{e}")
            st.stop()

        # 检查文件是否有必要的列
        if 'classification' not in data.columns or '评论内容' not in data.columns:
            st.error("数据表缺少 'classification' 或 '评论内容' 列")
            st.stop()

        # 获取视觉类评论
        visual_comments = data[data['classification'] == '是']

        if visual_comments.empty:
            st.error("没有找到分类为 '是' 的视觉类评论")
            st.stop()

        # 分割关键词
        keywords_list = keywords.strip().split()

        if not keywords_list:
            st.error("请输入至少一个关键词")
            st.stop()

        # 初始化计数
        keyword_density = {keyword: 0 for keyword in keywords_list}
        total_words = 0
        extracted_keywords_list = []  # 用于保存提取的关键词

        # 计算关键词密度
        st.write("正在分析关键词密度，请稍候...")
        for _, row in visual_comments.iterrows():
            comment = row['评论内容']
            words = seg.cut(comment)  # 使用 pkuseg 分词器进行分词
            extracted_keywords_list.append(' '.join(words))  # 保存分词结果
            total_words += len(words)
            for word in words:
                for keyword in keywords_list:
                    if keyword in word:
                        keyword_density[keyword] += 1

        # 如果没有找到关键词，给出提示
        if total_words == 0:
            st.error("没有在视觉类评论中找到任何有效的关键词")
            st.stop()

        # 计算并显示每个关键词的密度
        keyword_density_percentage = {keyword: (count / total_words) * 100 for keyword, count in keyword_density.items()}

        st.write(f"总视觉类评论数: {len(visual_comments)}")
        st.write(f"总词数: {total_words}")

        st.write("关键词密度分析结果:")
        density_data = pd.DataFrame({
            "关键词": list(keyword_density.keys()),
            "出现次数": list(keyword_density.values()),
            "关键词密度 (%)": [f"{density:.2f}" for density in keyword_density_percentage.values()]
        })

        st.write(density_data)

        # 显示提取的关键词结果
        st.write("分词结果预览（前10条）:")
        for i, keywords in enumerate(extracted_keywords_list[:10], 1):
            st.write(f"评论 {i}: {keywords}")

        # 提供下载链接
        csv = BytesIO()
        density_data.to_csv(csv, index=False, encoding='utf-8-sig')
        csv.seek(0)
        st.download_button(label="下载关键词密度分析结果", data=csv, file_name=f'{file_name}.csv', mime='text/csv')

    else:
        st.error("请先上传数据表")