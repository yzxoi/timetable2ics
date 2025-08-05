from data import Course


def json_to_courses(json_data):
    courses = []
    for item in json_data:
        courses.append(
            Course(
                name=item["name"],
                teacher=item["teacher"],
                classroom=item["classroom"],
                location=item.get("location", item["classroom"]),
                weekday=item["weekday"],
                weeks=item["weeks"],
                indexes=sorted(item["indexes"]),
            )
        )
    return courses
