from data import AppleMaps, Course, Geo, School

school = School(
    duration=45,   # 每节课时间为 45 分钟
    timetable=[
        (8, 00),   # 上午第一节课时间为 8:30 至 9:15
        (8, 50),
        (10, 00),
        (10, 50),
        (13, 30),  # 下午第一节课时间为下午 2:30 至 3:15
        (14, 20),
        (15, 30),
        (16, 20),
        (17, 50),
        (19, 00),
        (19, 50),
        (20, 40),
    ],
    start=(2025, 2, 24),  # 开学第一周当周周一至周日以内的任意日期
    courses = [
		Course(
			name="工程管理",
			teacher="王",
			classroom="北205",
			location="北205",
			weekday=4,
			weeks=Course.week(1, 17),
			indexes=[10, 11],
		),
	],
)

with open("课表.ics", "w") as w:
    w.write(school.generate())
