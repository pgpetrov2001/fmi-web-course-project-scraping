import json

def percentageValue(val):
    if val is None:
        return 0
    if type(val) == int:
        return val
    if type(val) == str:
        val = val.rstrip('%')
        val = val.strip()
        val = ''.join(val.split())
        if val == '':
            return 0
        return int(val)
    raise Exception(f'Invalid percentage value {val} encountered with type {type(val)}')

with open('courses.json') as file:
    courses = json.loads(file.read())

minor_abbreviations = {
    'Анализ на данни': 'И',
    'Математика': 'M',
    'Приложна математика': 'ПМ',
    'Статистика': 'Стат',
    'Информатика': 'И',
    'Информационни системи': 'ИС',
    'Компютърни науки': 'КН',
    'Софтуерно инженерство': 'СИ',
    'Математика и информатика': 'МИ',
}

def isAcademicTitlePart(s):
    s = s.lower().rstrip('.')
    if s in ['д-р', 'доц', 'гл', 'ас', 'инж', 'изсл', 'проф']:
        return True
    return '.' in s and not s.endswith('.')

for d in courses:
    d['bibliography'] = list(filter(lambda item: len(item), d['bibliography']))
    if 'exam_synopsis' in d:
        d['exam_synopsis'] = list(filter(lambda item: len(item), d['exam_synopsis']))

    new_grading = dict()

    for key, value in d['grading'].items():
        sanitized_key = key.replace('\n', '')

        if sanitized_key == 'Workshops (информационно търсене и колективно обсъждане':
            sanitized_key = 'Workshops (информационно търсене и колективно обсъждане на доклади и реферати)'

        new_grading[sanitized_key] = percentageValue(value)

    d['grading'] = new_grading

    for key in d:
        if type(d[key]) == str:
            d[key] = ' '.join(d[key].strip().split())
        if key.endswith('engagement'):
            d[key] = percentageValue(d[key])

    for s in d['synopsis']:
        s['horarium'] = list(filter(lambda h: type(h) == int or len(h), s['horarium']))

        if len(s['horarium']) == 1 and s['horarium'][0] == 0:
            s['horarium'] = [0,0,0]

        if len(s['horarium']) != 3:
            s['horarium'] = s['horarium'][:3]
            s['horarium'] += (3-len(s['horarium'])) * [0]

    d['credits'] = float(d['credits'].replace(',', '.'))

    d['minors'] = [ minor for minor in d['minor'].split(',') ]
    del d['minor']

    new_minors = []
    for minor in d['minors']:
        minor = minor.split(';')[0].strip().rstrip('.')

        found = False

        for key in minor_abbreviations.keys():
            if minor.startswith(key):
                minor = minor_abbreviations[key]
                found = True
                break

        for token in minor.split():
            token = token.rstrip('.')
            if token in minor_abbreviations.values():
                minor = token
                found = True
                break

        if minor.lower().find('всички'):
            new_minors = list(minor_abbreviations.values())
            break

        if not found:
            continue

        new_minors.append(minor)

    d['minors'] = new_minors

    d['lecturers'] = [ lecturer for lecturer in d['lecturer'].split(' и ') ]
    d['lecturers'] = [ lecturer for token in d['lecturers'] for lecturer in token.split(', ') if len(lecturer.split()) > 1 ]
    d['lecturers'] = [ ' '.join([ l for l in lecturer.split() if not isAcademicTitlePart(l) and l[0].isupper() ]) for lecturer in d['lecturers'] ]
    d['lecturers'] = list(filter(lambda l: len(l), d['lecturers']))
    del d['lecturer']

    for s in d['synopsis']:
        s['description'] = s['description'].strip().replace('\n', ' ')
    if 'exam_synopsis' in d:
        d['exam_synopsis'] = list(map(lambda s: s.strip().replace('\n', ' '), d['exam_synopsis']))
    d['bibliography'] = list(map(lambda s: s.strip().replace('\n', ' '), d['bibliography']))

print('******************')
print('minors:')
print(set([minor for d in courses for minor in d['minors']]))
print('******************')
print('grading:')
print(set([key for keys in map(lambda c: c['grading'].keys(), courses) for key in keys]))
print('******************')
print('credits:')
print(set([d['credits'] for d in courses]))
print('******************')
print('syllabus horariums:')
print(set(l for d in courses for l in map(lambda item: len(item['horarium']), d['synopsis'])))
print('******************')
print('lecturers:')
print(set([lecturer for d in courses for lecturer in d['lecturers'] if d['lecturers'] is not None]))
print('******************')

with open('cleaned_courses.json', mode='wt') as file:
    file.write(json.dumps(courses))
