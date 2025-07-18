# 大学生课表转 ICS 日历工具

## 项目简介
本项目旨在帮助大学生将教务系统导出的课表文本，快速转换为可导入 Apple/Google/Outlook 等日历应用的 `.ics` 文件。支持 LLM 智能解析、课表预览、节次时间自定义等功能。

## 主要功能
- 粘贴原始课表文本，一键解析为结构化课程数据
- 支持自定义每节课的开始时间、学期起始日、课时长度
- 解析结果可表格预览，确认无误后生成 `.ics` 文件
- 支持自带 LLM API Key 或使用平台公用 Key
- 赞赏码弹窗鼓励支持开发者

## 目录结构
```
timetable2ics/
├── web.py                # Streamlit 网页主入口
├── data.py               # 课表数据结构与生成逻辑
├── main.py               # 示例/命令行入口
├── requirements.txt      # 依赖列表
├── reward_wx.jpg         # 赞赏码图片
├── parserics/            # 解析相关模块
│   ├── llm_parser.py     # LLM 解析接口
│   ├── json_to_courses.py# JSON转Course工具
│   └── ...
├── image/                # 项目配图
│   ├── render.jpg        # 效果图
│   └── apple.jpg         # Apple Maps 说明图
├── usage.md              # 导入/订阅日历说明
├── UESTC.ics             # Apple Maps 示例
└── ...
```

## 安装依赖
建议使用 Python 3.8+，推荐虚拟环境：

```bash
pip install -r requirements.txt
```

## 快速使用
1. 启动网页：
   ```bash
   streamlit run web.py
   ```
2. 在网页中：
   - 粘贴你的课表文本
   - （可选）填写 LLM API Key（如阿里云 DashScope Key），否则自动使用公用 Key
   - 设置学期起始日、每节课时长、每节课开始时间
   - 点击“解析课表”，预览无误后生成并下载 `.ics` 文件

## LLM 公用 Key 与赞赏
- 未填写 API Key 时，系统会自动弹出赞赏码，欢迎支持开发者！
- 公用 Key 仅供体验，建议长期使用时申请自己的 Key。

## 常见问题
- **课表格式不标准/解析失败？**
  - 请尽量粘贴原始教务系统表格文本，或适当调整格式。
- **时间格式错误？**
  - 每节课时间请用 `8:00` 这种格式填写。
- **ics 文件导入失败？**
  - 请参考 `usage.md` 或各大日历应用官方说明。

## 致谢
- [阿里云通义千问](https://dashscope.aliyun.com/) LLM 支持
- 参考自 [UESTC-ics](https://github.com/lyc8503/UESTC-ics) 等开源项目

---
如有建议或问题，欢迎 Issue 或 PR！ 