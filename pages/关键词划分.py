import streamlit as st
from openai import OpenAI
import pandas as pd
import re
import time

# 设置 Streamlit 标题
st.title("视觉评论关键词分析工具")

# 输入 API 密钥和 URL
api_key = st.text_input("API 密钥", type="password")
base_url = st.text_input("Base URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 上传 CSV 文件
uploaded_file = st.file_uploader("上传评论数据表", type="csv")

# 输入模型名称
model_name = st.text_input("模型名称", "qwen-turbo")

# 输入系统提示语
system_prompt = st.text_area("系统提示语", "You are a helpful assistant.")

# 输入用户提示语的模板
keyword_prompt_template = st.text_area("关键词分析提示语",
                                       "以下内容出自网络视频评论区。请你根据以下提示语对评论进行逐条关键词分析。\n\n评论：{comment}\n分析结果：")

# 输入其他参数
temperature = st.slider("Temperature", 0.0, 1.0, 0.8)
top_p = st.slider("Top P", 0.0, 1.0, 0.8)
max_comment_length = st.number_input("最大评论长度", value=1000, step=1)

# 输入输出文件名
output_filename = st.text_input("输出文件名", "keyword_analysis_results.csv")


def preprocess_comment(comment):
    if not isinstance(comment, str):
        comment = str(comment)
    comment = re.sub(r'[^\w\s,.:?!]', '', comment)  # 移除除了字母、数字、空格和基本标点符号外的所有字符
    comment = comment.strip()  # 去除前后空格
    return comment[:max_comment_length]


def analyze_keywords(client, comment, retries=3):
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': keyword_prompt_template.format(comment=comment)}
    ]

    for attempt in range(retries):
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                top_p=top_p
            )
            analysis_result = completion.choices[0].message.content.strip()
            return analysis_result
        except Exception as e:
            if "data_inspection_failed" in str(e):
                st.warning(f"分析关键词时内容审查失败，重试中... ({attempt + 1}/{retries})")
                time.sleep(5)  # 等待5秒后重试
            else:
                st.error(f"分析关键词时出错: {e}")
                return "无法分析"
    return "无法分析"


@st.cache_resource
def init_client(api_key, base_url):
    return OpenAI(api_key=api_key, base_url=base_url)


if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    data['评论内容'] = data['评论内容'].fillna('')  # 用空字符串填充缺失值
    data['评论内容'] = data['评论内容'].astype(str)  # 转换为字符串
    comments = data['评论内容'].tolist()  # 假设评论列名为'评论内容'
    classifications = data.get('classification', [])  # 获取分类结果列，如果没有则为空列表

    st.write("CSV 文件读取完毕，预览数据：")
    st.dataframe(data.head())  # 显示前五行数据

    client = init_client(api_key, base_url)

    if st.button("运行关键词分析"):
        if api_key and base_url:
            st.write("初始化 OpenAI 客户端...")

            # 处理视觉评论并显示进度条
            keyword_analysis_results = []
            log_window = st.empty()  # 创建一个占位符窗口
            st.write("开始处理视觉评论...")
            progress_bar = st.progress(0)

            # 筛选视觉类评论
            visual_comments = data[data['classification'] == '是']

            for i, comment in enumerate(visual_comments['评论内容']):
                if not comment.strip() or comment == ',,,,':  # 如果评论为空或仅包含逗号，则跳过
                    keyword_analysis_results.append("未处理")
                    continue

                log_window.text(f"正在预处理评论 {i + 1}/{len(visual_comments)}: {comment[:50]}...")
                clean_comment = preprocess_comment(comment)
                log_window.text(f"正在分析评论 {i + 1}/{len(visual_comments)}: {clean_comment[:50]}...")
                analysis_result = analyze_keywords(client, clean_comment)
                keyword_analysis_results.append(analysis_result)
                log_window.text(f"评论 {i + 1}/{len(visual_comments)} 的关键词分析结果: {analysis_result}")
                progress_bar.progress((i + 1) / len(visual_comments))

            st.write("关键词分析完成，正在保存分析结果...")

            # 将关键词分析结果添加到数据表中
            visual_comments['keyword_analysis'] = keyword_analysis_results

            # 保存分析结果到新的数据表
            visual_comments.to_csv(output_filename, index=False)
            st.success(f"关键词分析结果已保存到: {output_filename}")

            st.write("关键词分析结果预览：")
            st.dataframe(visual_comments.head())  # 显示前五行分析结果数据

        else:
            st.error("请提供 API 密钥和 Base URL")
