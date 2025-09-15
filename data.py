import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import md5
from typing import Any


@dataclass
class Course:
    name: str
    teacher: str
    classroom: str
    weekday: int
    weeks: list[int]
    indexes: list[int]

    def title(self) -> str:
        """
        每一次课程日历项的标题：
        如希望传递「当前是第几周」这样的参数，可在这里预留格式化变量，并在 School.generate() 函数中修改
        """
        return f"{self.name} - {self.classroom}"

    def description(self) -> str:
        """
        每一次课程日历项目的介绍信息：
        如希望传递「当前是第几周」这样的参数，可在这里预留格式化变量，并在 School.generate() 函数中修改
        """
        return f"任课教师：{self.teacher}。"

    @staticmethod
    def week(start: int, end: int) -> list[int]:
        """
        返回周数列表：
        如 week(1, 3) -> [1, 2, 3]
        """
        return list(range(start, end + 1))

    @staticmethod
    def odd_week(start: int, end: int) -> list[int]:
        """
        返回奇数周列表：
        如 odd_week(1, 4) -> [1, 3]
        """
        return [i for i in range(start, end + 1) if i % 2]

    @staticmethod
    def even_week(start: int, end: int) -> list[int]:
        """
        返回偶数周列表
        如 even_week(1, 4) -> [2, 4]
        """
        return [i for i in range(start, end + 1) if not i % 2]


@dataclass
class School:
    duration: int = 45
    timetable: list[tuple[int, int]] = field(default_factory=list)
    start: tuple[int, int, int] = (2023, 9, 1)
    courses: list[Course] = field(default_factory=list)
    adjustments: dict = field(default_factory=dict)

    HEADERS = [
        "BEGIN:VCALENDAR",
        "METHOD:PUBLISH",
        "VERSION:2.0",
        "X-WR-CALNAME:课表",
        "X-WR-TIMEZONE:Asia/Shanghai",
        "CALSCALE:GREGORIAN",
        "BEGIN:VTIMEZONE",
        "TZID:Asia/Shanghai",
        "END:VTIMEZONE"]
    FOOTERS = ["END:VCALENDAR"]

    def __post_init__(self) -> None:
        assert self.timetable, "请设置每节课的上课时间，以 24 小时制两元素元组方式输入小时、分钟"
        assert len(self.start) >= 3, "请设置为开学第一周的日期，以元素元组方式输入年、月、日"
        assert self.courses, "请设置你的课表数组，每节课是一个 Course 实例"
        self.timetable.insert(0, (0, 0))
        for c in self.courses:
            if not c.indexes:
                raise ValueError(f"{c.name} 未设置节次")
            c.indexes.sort()
        # Ensure timetable covers all course indexes to avoid IndexError in time()
        max_index = max(i for c in self.courses for i in c.indexes)
        if max_index >= len(self.timetable):
            raise ValueError(
                f"课程节次 {max_index} 超过设定的总节数 {len(self.timetable) - 1}, 请检查课表设置"
            )
        self.start_dt = datetime(*self.start[:3])
        self.start_dt -= timedelta(days=self.start_dt.weekday())

    def time(self, week: int, weekday: int, index: int, plus: bool = False) -> datetime:
        """
        生成详细的日期和时间：
        week: 第几周，weekday: 周几，index: 第几节课，plus: 是否增加课程时间
        """
        date = self.start_dt + timedelta(weeks=week - 1, days=weekday - 1)
        return date.replace(
            hour=self.timetable[index][0], minute=self.timetable[index][1]
        ) + timedelta(minutes=self.duration if plus else 0)

    def generate(self) -> str:
        runtime = datetime.now()
        texts = []
        
        # 1) 生成全部原始事件（不考虑调休）
        all_events = []  # list of dict for easier post-process
        for course in self.courses:
            for week in course.weeks:
                start_dt = self.time(week, course.weekday, course.indexes[0])
                end_dt = self.time(week, course.weekday, course.indexes[-1], True)
                if end_dt <= start_dt:
                    raise ValueError(f"{course.name} 的结束时间不晚于开始时间，请检查节次设置")
                all_events.append({
                    "course": course,
                    "week": week,
                    "weekday": course.weekday,
                    "indexes": tuple(course.indexes),
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                })

        # 2) 解析调休数据
        off_dates = set()
        remap_pairs = []  # list of (to_date, from_date)
        if self.adjustments:
            try:
                for d in self.adjustments.get("off_dates", []) or []:
                    off_dates.add(datetime.fromisoformat(d).date())
                for m in self.adjustments.get("remap", []) or []:
                    to_d = datetime.fromisoformat(m.get("date")).date()
                    from_d = datetime.fromisoformat(m.get("from")).date()
                    remap_pairs.append((to_d, from_d))
            except Exception:
                # 忽略无效的调休输入，按无调休处理
                off_dates = set()
                remap_pairs = []

        # 3) 先基于 off_dates 过滤原始事件
        filtered_events = [e for e in all_events if e["start_dt"].date() not in off_dates]

        # 4) 基于 remap 复制事件：将 from_date 的事件复制到 to_date（时间点不变，仅日期替换）
        remapped_events = []
        if remap_pairs:
            # 建立 from_date -> 事件列表 的索引（从全部事件中取，确保假期被移除但仍可作为来源）
            from_index = {}
            for e in all_events:
                d = e["start_dt"].date()
                from_index.setdefault(d, []).append(e)
            for to_date, from_date in remap_pairs:
                for src in from_index.get(from_date, []):
                    # 复制并替换日期
                    start_dt = src["start_dt"].replace(year=to_date.year, month=to_date.month, day=to_date.day)
                    end_dt = src["end_dt"].replace(year=to_date.year, month=to_date.month, day=to_date.day)
                    remapped_events.append({
                        "course": src["course"],
                        "week": src["week"],
                        "weekday": src["weekday"],
                        "indexes": src["indexes"],
                        "start_dt": start_dt,
                        "end_dt": end_dt,
                        "remapped_from": from_date.isoformat(),
                        "remapped_to": to_date.isoformat(),
                    })

        final_events = filtered_events + remapped_events

        # 5) 渲染到 ICS 文本
        events = []
        for e in final_events:
            course = e["course"]
            start_dt = e["start_dt"]
            end_dt = e["end_dt"]
            uid_src = (
                course.title(),
                start_dt.date().isoformat(),
                tuple(e["indexes"]),
                e.get("remapped_from", "orig"),
            )
            events.append([
                "BEGIN:VEVENT",
                f"UID:{md5(str(uid_src).encode()).hexdigest()}",
                f"DTSTAMP:{runtime:%Y%m%dT%H%M%SZ}",
                f"DTSTART;TZID=Asia/Shanghai:{start_dt:%Y%m%dT%H%M%S}",
                f"DTEND;TZID=Asia/Shanghai:{end_dt:%Y%m%dT%H%M%S}",
                f"SUMMARY:{course.title()}",
                f"DESCRIPTION:{course.description()}",
                "URL;VALUE=URI:",
                "END:VEVENT",
            ])
        items = [line for event in events for line in event]
        for line in self.HEADERS + items + self.FOOTERS:
            first = True
            while line:
                texts.append((" " if not first else "") + line[:72])
                line = line[72:]
                first = False
        return "\n".join(texts)



