import streamlit as st
import json
from parserics.llm_parser import parse_timetable, parse_adjustments
from parserics.json_to_courses import json_to_courses
from data import School
import datetime

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

# iPhone 导入受阻时的快捷指令公告
st.info(
    """
    iPhone 上无法直接导入 ICS？可使用快捷指令一键添加到苹果日历。

    打开 ICS 文件后，点击「共享」图标 或「用其他应用打开」，选择「ICS To Calendar」即可。
    - 快捷指令： [导入 ICS 到苹果日历](https://www.icloud.com/shortcuts/76e984f27b194fbf9c81044bf8bd0109)
    - 作者（下载失败请点这里）： [8isnothing](https://routinehub.co/shortcut/7005/)
    """
)

st.divider()

st.header("1️⃣ 课表原始数据输入")
api_key = st.text_input("Alibaba LLM API Key（调用 qwen3.8-flash model，可留空使用公用Key）", type="password").strip()
if not api_key:
    st.info("如未填写API Key，将会调用公共API。")
raw = st.text_area("粘贴你的课表文本（必填）", height=200, help="请直接粘贴从教务系统复制的课表内容")

adjust_text = st.text_area(
    "放假/调休公告（可选）",
    value="中秋节：9月25日（周五）至27日（周日）放假，共3天。国庆节：10月1日（周四）至7日（周三）放假调休，共7天。9月20日（周日）、10月10日（周六）上课、上班，9月20日（周日）安排10月6日（周二）的教学工作，10月10日（周六）安排10月7日（周三）的教学工作。",
    height=120,
    help="例如：中秋节：9月25日（周五）至27日（周日）放假，共3天；国庆节：10月1日（周四）至7日（周三）放假调休，共7天；9月20日（周日）安排10月6日（周二）的教学工作。"
)

apply_adjustments = st.checkbox("启用调休规则", value=True, help="关闭后将忽略放假/调休规则")

st.divider()

st.header("2️⃣ 学期与课程时间设置")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("开学第一周周一日期", value=datetime.date(2026, 9, 14), help="用于计算每周的具体日期")
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

    # 若提供了调休公告，尝试解析
    if adjust_text.strip():
        with st.spinner("正在解析放假/调休公告..."):
            adj_str = parse_adjustments(adjust_text, api_key_to_use, start_date.year)
            try:
                adj_data = json.loads(adj_str) if adj_str.strip() else {}
            except Exception as e:
                st.warning(f"调休公告解析失败（将不应用调休）：{e}\n\n原始输出：\n{adj_str}")
                adj_data = {}
            st.session_state["adjustments"] = adj_data

if st.session_state["show_qr"]:
    with st.expander("感谢支持！如觉得本工具有用欢迎扫码赞赏（可关闭继续使用）", expanded=True):
        st.image("reward_wx.jpg", caption="赞赏码")
        if st.button("关闭赞赏码"):
            st.session_state["show_qr"] = False

if "course_list" in st.session_state:
    st.subheader("课表预览（可在此处修改）")

    # Create a deep copy for editing to avoid altering the original data
    import copy
    editable_course_list = copy.deepcopy(st.session_state["course_list"])

    # Convert list-like columns to comma-separated strings for st.data_editor
    for course in editable_course_list:
        if 'weeks' in course and isinstance(course['weeks'], list):
            course['weeks'] = ", ".join(map(str, course['weeks']))
        if 'indexes' in course and isinstance(course['indexes'], list):
            course['indexes'] = ", ".join(map(str, course['indexes']))

    edited_records = st.data_editor(
        editable_course_list,
        use_container_width=True,
        num_rows="dynamic",
        key="course_editor",
    )

    if edited_records is None:
        edited_records = editable_course_list

    # st.data_editor returns list-like data when provided list[dict]; ensure consistent format
    if hasattr(edited_records, "to_dict"):
        edited_records = edited_records.to_dict("records")
    elif isinstance(edited_records, dict):
        edited_records = [edited_records]
    for record in edited_records:
        if 'weeks' in record and isinstance(record['weeks'], str):
            try:
                record['weeks'] = [int(x.strip()) for x in record['weeks'].split(',') if x.strip()]
            except ValueError:
                st.error(f"课程 '{record.get('name', '')}' 的周次（weeks）格式不正确，请使用逗号分隔的数字。")
                st.stop()
        if 'indexes' in record and isinstance(record['indexes'], str):
            try:
                record['indexes'] = [int(x.strip()) for x in record['indexes'].split(',') if x.strip()]
            except ValueError:
                st.error(f"课程 '{record.get('name', '')}' 的节次（indexes）格式不正确，请使用逗号分隔的数字。")
                st.stop()

    st.session_state["course_list"] = edited_records

    # 预览调休解析结果 + 高级手动覆盖
    if st.session_state.get("adjustments") or apply_adjustments:
        with st.expander("调休规则预览 / 高级编辑", expanded=False):
            st.json(st.session_state.get("adjustments", {}))
            manual_json = st.text_area(
                "高级：手动覆盖调休JSON（可选）",
                value="",
                height=140,
                help="如需手动修正，粘贴形如 {\"off_dates\":[\"2024-10-01\"],\"remap\":[{\"date\":\"2024-09-28\",\"from\":\"2024-10-07\"}]} 的JSON"
            )
            if manual_json.strip():
                try:
                    override = json.loads(manual_json)
                    st.session_state["adjustments"] = override
                    st.success("已应用手动覆盖的调休JSON")
                except Exception as e:
                    st.error(f"手动覆盖JSON解析失败：{e}")

    if st.button("确认无误，生成ICS文件"):
        courses = json_to_courses(st.session_state["course_list"])
        try:
            school = School(
                duration=duration,
                timetable=timetable,
                start=(start_date.year, start_date.month, start_date.day),
                courses=courses,
                adjustments=st.session_state.get("adjustments", {}) if apply_adjustments else {},
            )
            ics_content = school.generate()
        except ValueError as e:
            st.error(str(e))
        else:
            st.success("ICS文件已生成！")
            st.download_button("下载ICS文件", ics_content, file_name="timetable.ics")
