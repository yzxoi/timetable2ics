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
5. 仅在 `location` 与 `classroom` 不同或需更精准定位时填 `location`，否则可以省略（让前端用 `.get("location", classroom)`）。
6. 输出示例（请勿直接使用）：
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

