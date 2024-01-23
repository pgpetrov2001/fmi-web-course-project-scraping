import json

def staff_with_abbreviations(staff):
    #titles = [ title for member in staff for title in member['titles'].split(', ') ]
    #print(list(set(titles)))

    abbreviations = {
        "Старши преподавател": "Ст. пр.",
        "Изследовател (R4)": "Изсл. (R4)",
        "Изследовател (R2)": "Изсл. (R2)",
        "Изследовател (R1)": "Изсл. (R1)",
        "Доктор": "Д-р",
        "Професор": "Проф.",
        "Доцент": "Доц.",
        "Главен асистент": "Гл. ас.",
        "Асистент": "Ас.",
        "Доктор на науките": "ДН",
        "Преподавател": "Пр.",
        "Математик": "Мат.",
        "Изследовател (R3)": "Изсл. (R3)"
    }

    staff = [ { 'names': member['names'], 'titles': ' '.join(map(lambda title: abbreviations[title].lower(), member['titles'].split(', '))) } for member in staff ]

    return staff

if __name__ == '__main__':
    with open('staff.json') as file:
        staff = json.loads(file.read())

    print(json.dumps(staff_with_abbreviations(staff)))
