import os
from openai import OpenAI


def parse_timetable(raw_text, api_key):
    api_key = (api_key or os.getenv("DASHSCOPE_API_KEY") or "").strip()
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    prompt = f"""请从下列文本中提取所有课程记录。
文本开始>>
{raw_text}
<<文本结束
    """
    completion = client.chat.completions.create(
        model="qwen-turbo",
        messages=[
            {"role": "system", "content": """你是一名严格输出 JSON 的机器人，只能输出json，不能输出其他内容。
请遵守以下规则：
1. 每条课程记录对应 **一次真实上课事件**（同一课程在不同星期或不同节次需拆成多条）。
2. `weekday` 用阿拉伯数字：星期一→1，…，星期日→7。
3. `indexes` 必须是升序整数数组；例：“3-4节”→[3,4]。
4. `weeks` 要 **全部展开** 成整数数组：
   • “[1-16]” → `[1,2,…,16]`
   • “[2-16双]” → `[2,4,6,…,16]`
   • “[1, 3, 5]” 原样提取 `[1,3,5]`
5. 输出示例（请勿直接使用）：
{
  "courses":[
    {
      "name":"离散数学",
      "teacher":"舒少龙",
      "classroom":"南216",
      "weekday":1,
      "indexes":[7,8],
      "weeks":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
    }
  ]
}
             """},
            {"role": "user", "content": prompt}
        ],
        extra_body={"enable_thinking": False},
    )
    # Qwen 返回格式与 OpenAI 兼容
    return completion.choices[0].message.content


def parse_adjustments(adjust_text: str, api_key: str, start_year: int) -> str:
    """
    使用 LLM 将中文放假/调休公告解析为结构化 JSON。
    返回形如：
    {
      "off_dates": ["2024-10-01", "2024-10-02"],
      "remap": [
        {"date": "2024-09-28", "from": "2024-10-07"},
        {"date": "2024-10-11", "from": "2024-10-08"}
      ]
    }
    规则：
    - off_dates：完全不安排课程/工作（放假）的公历日期。
    - remap：在指定 date 按照 from 那一天的教学安排上课/上班。
    - 所有日期均输出为 YYYY-MM-DD，年份优先使用 start_year；如公告明显跨年则据语义判断。
    - 只能输出 JSON，不得包含任何额外文字。
    """
    api_key = (api_key or os.getenv("DASHSCOPE_API_KEY") or "").strip()
    if not adjust_text.strip():
        return "{}"
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    prompt = f"""请将下面的中文放假/调休公告解析为 JSON：
公告文本开始>>
{adjust_text}
<<公告文本结束

请严格输出：
{{
  "off_dates": ["{start_year}-MM-DD", ...],
  "remap": [{{"date":"{start_year}-MM-DD","from":"{start_year}-MM-DD"}}]
}}
要求：
1) off_dates 为完全放假的日期；
2) remap 中的每条表示：在 date 这一天，按 from 那一天的教学安排执行；
3) 所有日期都必须是 YYYY-MM-DD；
4) 年份默认使用 {start_year}，如公告明确跨年则按实际年份输出；
5) 只输出 JSON，无解释，无多余文字。
"""
    completion = client.chat.completions.create(
        model="qwen-turbo",
        messages=[
            {"role": "system", "content": "你是严格 JSON 解析器，只能输出 JSON。"},
            {"role": "user", "content": prompt},
        ],
        extra_body={"enable_thinking": False},
    )
    return completion.choices[0].message.content

