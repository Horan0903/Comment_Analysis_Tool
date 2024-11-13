import streamlit as st
import pandas as pd

# 设置 Streamlit 标题
st.title("评论数据统计工具")

# 上传文件，支持 CSV 和 Excel 格式
uploaded_file = st.file_uploader("上传评论数据表", type=["csv", "xlsx"])

if uploaded_file is not None:
    # 读取上传的文件并处理不同格式
    st.write("正在读取上传的文件...")
    if uploaded_file.name.endswith('.csv'):
        data = pd.read_csv(uploaded_file)
    else:
        data = pd.read_excel(uploaded_file)

    # 显示文件中的列名，供用户选择评论内容和点赞数所在的列
    st.write("请选择评论内容和点赞数所在的列：")
    comment_column = st.selectbox("选择评论内容所在的列", data.columns)
    likes_column = st.selectbox("选择点赞数所在的列", data.columns)

    # 清洗评论内容列，填充缺失值并转换为字符串类型
    data[comment_column] = data[comment_column].fillna('')  # 用空字符串填充缺失值
    data[comment_column] = data[comment_column].astype(str)  # 转换为字符串

    st.write("文件读取完毕，预览数据：")
    st.dataframe(data.head())  # 显示前五行数据

    # 筛选视觉类评论
    st.write("正在计算视觉类评论的加权占比...")
    if 'classification' not in data.columns:
        st.error("文件中没有找到 'classification' 列，无法继续分析。")
    else:
        # 只保留 classification 为“是”的视觉类评论
        visual_comments = data[
            (data['classification'] == '是') & (data[comment_column].str.strip() != '') & (data[comment_column] != ',,,,')]

        # 计算视觉类评论的总点赞数
        visual_likes = visual_comments[likes_column].sum()

        # 计算所有有效评论的总点赞数
        filtered_data = data[(data[comment_column].str.strip() != '') & (data[comment_column] != ',,,,')]
        total_likes = filtered_data[likes_column].sum()

        # 计算视觉类评论加权占比
        weighted_visual_ratio = visual_likes / total_likes if total_likes != 0 else 0

        # 计算详细数据
        total_comments = len(filtered_data)
        visual_comments_count = len(visual_comments)

        # 显示详细数据
        st.write(f"总评论数: {total_comments}")
        st.write(f"视觉类评论数: {visual_comments_count}")
        st.write(f"总点赞数: {total_likes}")
        st.write(f"视觉类评论点赞数: {visual_likes}")
        st.write(f"视觉类评论加权占比: {weighted_visual_ratio:.2%}")

        # 获取点赞数前十的视觉类评论
        st.write("点赞数前十的视觉类评论：")
        top_10_visual_comments = visual_comments.nlargest(10, likes_column)[[comment_column, likes_column]]
        st.dataframe(top_10_visual_comments)

        # 提供下载按钮，允许用户下载筛选后的数据
        st.download_button(
            label="下载筛选后的结果",
            data=visual_comments.to_csv(index=False).encode('utf-8'),
            file_name="filtered_visual_comments.csv",
            mime='text/csv'
        )