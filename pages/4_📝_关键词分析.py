import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go

# 设置 Streamlit 标题
st.title("视觉类评论关键词关联分析")

# 上传 CSV 文件
uploaded_file = st.file_uploader("上传数据表", type=["csv", "xlsx"])

# 初始化 session_state，防止每次刷新时重置用户的选择
if 'classification_column' not in st.session_state:
    st.session_state.classification_column = None
if 'comment_column' not in st.session_state:
    st.session_state.comment_column = None
if 'likes_column' not in st.session_state:
    st.session_state.likes_column = None
if 'data' not in st.session_state:
    st.session_state.data = None

# 缓存文件读取函数
@st.cache_data
def read_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    else:
        return pd.read_excel(uploaded_file)

# 添加条形图生成函数
def generate_bar_chart(x_values, y_values, title, x_label, y_label):
    fig = px.bar(x=x_values, y=y_values, labels={'x': x_label, 'y': y_label}, title=title)
    fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
    fig.update_layout(showlegend=False)
    return fig

# 添加饼状图生成函数
def generate_pie_chart(labels, values, title):
    fig = px.pie(names=labels, values=values, title=title)
    fig.update_traces(textinfo='percent+label', hoverinfo='label+value')
    return fig

# 如果用户上传了文件，读取文件并显示列选择器
if uploaded_file:
    try:
        # 读取上传的文件并保存到 session_state
        st.session_state.data = read_file(uploaded_file)
        st.write("CSV 文件读取完毕")
    except Exception as e:
        st.error(f"文件读取失败：{e}")
        st.stop()

    # 动态选择用户上传文件中的列
    columns = list(st.session_state.data.columns)

    # 让用户选择"分类"列、"评论内容"列、"点赞数"列
    st.session_state.classification_column = st.selectbox(
        "选择分类列", columns, index=columns.index(st.session_state.classification_column) if st.session_state.classification_column in columns else 0)
    st.session_state.comment_column = st.selectbox(
        "选择评论内容列", columns, index=columns.index(st.session_state.comment_column) if st.session_state.comment_column in columns else 0)
    st.session_state.likes_column = st.selectbox(
        "选择点赞数列", columns, index=columns.index(st.session_state.likes_column) if st.session_state.likes_column in columns else 0)

    # 确认用户选择了正确的列，并提示用户可以启动分析
    if st.session_state.classification_column and st.session_state.comment_column and st.session_state.likes_column:
        st.success("列选择完毕，现在可以输入关键词并启动分析")

        # 输入关键词
        keywords = st.text_input("输入关键词（多个关键词用空格分隔）", "数据 可视化")

        # 输入保存文件名
        file_name = st.text_input("输入要保存的文件名（不包括扩展名）", "分析结果")

        # 只有在用户输入了关键词并完成列选择后，才显示“启动分析”按钮
        if keywords and st.button("启动分析"):
            # 获取视觉类评论
            visual_comments = st.session_state.data[st.session_state.data[st.session_state.classification_column] == '是']

            # 如果没有视觉类评论，提示用户
            if visual_comments.empty:
                st.error("没有找到分类为 '是' 的视觉类评论")
                st.stop()

            total_likes = visual_comments[st.session_state.likes_column].sum()  # 总点赞数
            keywords_list = keywords.split()  # 分割关键词

            # 初始化关键词关联统计
            match_count = 0
            keyword_counts = {keyword: 0 for keyword in keywords_list}
            keyword_likes = {keyword: 0 for keyword in keywords_list}
            matched_comments = []
            output_data = []

            # 查找包含关键词的评论
            for _, row in visual_comments.iterrows():
                comment = row[st.session_state.comment_column]
                likes = row[st.session_state.likes_column]
                matched_keywords = [keyword for keyword in keywords_list if keyword in comment]
                if matched_keywords:
                    match_count += 1
                    matched_comments.append(comment)
                    output_data.append({"评论内容": comment, "包含的关键词": ", ".join(matched_keywords), "点赞数": likes})
                    for keyword in matched_keywords:
                        keyword_counts[keyword] += 1
                        keyword_likes[keyword] += likes

            # 关键词统计和占比计算
            keyword_percentages = {keyword: count / len(visual_comments) * 100 for keyword, count in keyword_counts.items()}
            keyword_weighted_percentages = {keyword: likes / total_likes * 100 if total_likes > 0 else 0 for keyword, likes in keyword_likes.items()}
            total_keyword_likes = sum(keyword_likes.values())
            total_weighted_percentage = total_keyword_likes / total_likes * 100 if total_likes > 0 else 0

            # 显示统计结果
            st.write(f"总视觉类评论数: {len(visual_comments)}")
            st.write(f"总点赞数: {total_likes}")
            st.write(f"包含关键词的视觉类评论数: {match_count}")
            st.write(f"关键词关联占比: {match_count / len(visual_comments) * 100:.2f}%")
            st.write(f"总关键词点赞数: {total_keyword_likes}")
            st.write(f"总的关键词加权占比: {total_weighted_percentage:.2f}%")

            # 生成关键词分析表格
            table_data = pd.DataFrame({
                "关键词": list(keyword_percentages.keys()),
                "个数": list(keyword_counts.values()),
                "占比 (%)": [f"{percentage:.2f}" for percentage in keyword_percentages.values()],
                "总点赞数": list(keyword_likes.values()),
                "加权占比 (%)": [f"{weighted_percentage:.2f}" for weighted_percentage in keyword_weighted_percentages.values()]
            })

            fig_table = go.Figure(data=[go.Table(
                header=dict(values=list(table_data.columns), fill_color='darkblue', font=dict(color='white', size=12), align='left'),
                cells=dict(values=[table_data[col] for col in table_data.columns], align='left',
                           fill_color=[['lightcyan'] * len(table_data), ['lavender'] * len(table_data),
                                       ['lightgreen'] * len(table_data), ['lightyellow'] * len(table_data),
                                       ['lightpink'] * len(table_data)], font=dict(color='black', size=11))
            )])

            st.write("关键词占比、总点赞数和加权占比表格:")
            st.plotly_chart(fig_table)

            # 生成条形图、饼图和加权条形图
            st.write("关键词占比条形图:")
            st.plotly_chart(generate_bar_chart(list(keyword_percentages.keys()), list(keyword_percentages.values()), '关键词在视觉类评论中的占比', '关键词', '占比 (%)'))

            st.write("关键词占比饼状图:")
            st.plotly_chart(generate_pie_chart(list(keyword_counts.keys()), list(keyword_counts.values()), '关键词在视觉类评论中的占比'))

            st.write("关键词加权占比条形图:")
            st.plotly_chart(generate_bar_chart(list(keyword_weighted_percentages.keys()), list(keyword_weighted_percentages.values()), '关键词评论的加权占比', '关键词', '加权占比 (%)'))

            # 评论预览
            st.write("包含关键词的视觉类评论预览:")
            st.write(matched_comments[:10])

            # 提供下载链接
            if matched_comments:
                output_df = pd.DataFrame(output_data)
                csv = BytesIO()
                output_df.to_csv(csv, index=False, encoding='utf-8-sig')
                csv.seek(0)
                st.download_button(label="下载分析结果", data=csv, file_name=f'{file_name}.csv', mime='text/csv')
else:
    st.info("请先上传数据表")