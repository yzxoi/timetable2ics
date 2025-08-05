import streamlit as st
import json
from parserics.llm_parser import parse_timetable
from parserics.json_to_courses import json_to_courses
from data import School
import datetime
import pandas as pd

st.set_page_config(page_title="大学生课表转ICS日历", page_icon="📅", layout="centered")

# 顶部导航栏/链接
st.markdown("""
<div style='display: flex; justify-content: flex-end; align-items: center; margin-bottom: 0.5em;'>
  <a href="https://github.com/yzxoi/timetable2ics" target="_blank" style="text-decoration: none; color: #0366d6; font-weight: bold; font-size: 1.1em;">
    🚀 项目源码（GitHub）
  </a>
</div>
""", unsafe_allow_html=True)

st.title("📅 大学生课表转ICS日历工具")
st.markdown("""
本工具可将教务系统导出的课表文本，快速转换为可导入 Apple/Google/Outlook 等日历的 .ics 文件。

- 支持自定义节次时间、学期起始日
- 支持 LLM 智能解析（可自带 API Key 或使用平台公用 Key）
- 解析结果可预览、确认后再生成日历
""")

st.divider()

st.header("1️⃣ 课表原始数据输入")
api_key = st.text_input("Alibaba LLM API Key（调用 qwen-turbo model，可留空使用公用Key）", type="password").strip()
if not api_key:
    st.info("如未填写API Key，将会调用公共API。")
raw = st.text_area("粘贴你的课表文本（必填）", height=200, help="请直接粘贴从教务系统复制的课表内容")

st.divider()

st.header("2️⃣ 学期与课程时间设置")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("开学第一周周一日期", value=datetime.date.today(), help="用于计算每周的具体日期")
with col2:
    duration = st.number_input("每节课时长（分钟）", value=45, help="不含课间休息时间")

st.markdown("#### 每节课开始时间设置")
num_periods = st.number_input("总节数", min_value=1, max_value=20, value=11, help="本学期单日最多上几节课")

default_times = [
    "8:00", "8:50", "10:00", "10:50",
    "13:30", "14:20", "15:30", "16:20",
    "18:30", "19:20", "20:10"
]
while len(default_times) < num_periods:
    default_times.append("8:00")

timetable = []
cols = st.columns(4)
for i in range(num_periods):
    with cols[i % 4]:
        time_str = st.text_input(
            f"第{i+1}节时间", 
            value=default_times[i], 
            key=f"time_{i}", 
            help="格式如 8:00"
        )
        try:
            h, m = map(int, time_str.strip().split(":"))
            timetable.append((h, m))
        except Exception:
            st.error(f"第{i+1}节时间格式错误：{time_str}，请用 8:00 这种格式")
            st.stop()

st.divider()

st.header("3️⃣ 课表解析与日历生成")

# 赞赏二维码弹窗控制
if "show_qr" not in st.session_state:
    st.session_state["show_qr"] = False

if st.button("解析课表") and raw:
    if not api_key:
        st.session_state["show_qr"] = True
        api_key_to_use = st.secrets.get("PUBLIC_API_KEY", "")
    else:
        api_key_to_use = api_key
    with st.spinner("正在调用 LLM 解析课表..."):
        json_str = parse_timetable(raw, api_key_to_use)
        try:
            json_data = json.loads(json_str)
            if isinstance(json_data, dict) and "courses" in json_data:
                course_list = json_data["courses"]
            else:
                course_list = json_data
            st.session_state["course_list"] = course_list
            st.success("解析成功！请在下方预览课表，确认无误后生成ICS文件。")
        except Exception as e:
            st.error(f"解析 LLM 返回内容失败: {e}\n\nLLM原始输出：\n{json_str}")
            st.stop()

if st.session_state["show_qr"]:
    with st.expander("感谢支持！如觉得本工具有用欢迎扫码赞赏（可关闭继续使用）", expanded=True):
        st.image("reward_wx.jpg", caption="赞赏码")
        if st.button("关闭赞赏码"):
            st.session_state["show_qr"] = False

if "course_list" in st.session_state:
    st.subheader("课表预览")
    df = pd.DataFrame(st.session_state["course_list"])
    st.dataframe(df, use_container_width=True)
    if st.button("确认无误，生成ICS文件"):
        courses = json_to_courses(st.session_state["course_list"])
        try:
            school = School(
                duration=duration,
                timetable=timetable,
                start=(start_date.year, start_date.month, start_date.day),
                courses=courses,
            )
            ics_content = school.generate()
        except ValueError as e:
            st.error(str(e))
        else:
            st.success("ICS文件已生成！")
            st.download_button("下载ICS文件", ics_content, file_name="timetable.ics")
