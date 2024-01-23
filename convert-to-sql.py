import sys
import glob
import json
import camelot
import pandas as pd

def get_tables(file):
    tables = camelot.read_pdf(file, pages='all', line_scale=80, split_text=True)

    if len(tables) < 12:
        raise Exception(f'Something wrong with PDF, too few tables extracted: {len(tables)}')

    tables = tables[1:-1] # logo gets interpreted as a table, last table we don't need (it is always on a separate page, so it won't get split into 2 parts)
    avg_accuracy = 0
    for table in tables:
        avg_accuracy += table.parsing_report['accuracy']

    avg_accuracy /= len(tables)

    if avg_accuracy < 91:
        raise Exception(f'PDF probably had some formatting differences or is in the old format. Accuracy was {avg_accuracy:.1f}%')

    return list(map(lambda t: t.df, tables)), list(map(lambda t: { 'page': t.page }, tables))


def identify_and_merge_tables(tables, metadata):
    identifying_headers = [
        'редовна форма на обучение',
        'Дисциплина:',
        'Учебната програма е разработена и предложена за утвърждаване от катедра:',
        'Заетост и кредити',
        'Предвидена форма на оценяване:',
        'Формиране на оценката по дисциплината',
        'Анотация на учебната дисциплина',
        'Предварителни изисквания',
        'Очаквани резултати',
        'Учебно съдържание',
        'Конспект за изпит',
        'Библиография',
        '$$$$$$$$$$$$$$$$$'
    ]

    def get_table_header(table):
        return table.iloc[0, 0].strip()

    result = {}

    i = 0
    prev_page = 1

    for table, meta in zip(tables, metadata):
        header = get_table_header(table)
        edge_case = identifying_headers[i] == 'Конспект за изпит' and header == 'Библиография' # exam syllabus is optional

        if header != identifying_headers[i] and not edge_case:
            assert(meta['page'] == prev_page + 1) # a table was split because of a page break
            assert(i > 0)
            assert(identifying_headers[i-1] in result)

            result[identifying_headers[i-1]] = pd.concat([result[identifying_headers[i-1]], table])
        else:
            if edge_case:
                i += 1
            result[header] = table
            i += 1

        prev_page = meta['page']

    assert(i == len(identifying_headers) - 1)

    #Additional checks:
    # first 5 tables should be on the first page (no free text in them)
    assert(len(set(map(lambda m: m['page'], metadata[:5]))) == 1)
    # 6-th table should be on the second page
    assert(metadata[5]['page'] == 2)

    return result


def convert_to_json(tables_from_header):
    result = {}
    #major
    result['minor'] = tables_from_header['редовна форма на обучение'].iloc[2, 0]
    result['title'] = tables_from_header['Дисциплина:'].iloc[1, 0]
    #tutor?
    result['lecturer'] = tables_from_header['Учебната програма е разработена и предложена за утвърждаване от катедра:'].iloc[2,1]
    result['credits'] = tables_from_header['Заетост и кредити'].iloc[2,2]
    # work instead of engagement
    result['lecture_engagement'] = tables_from_header['Заетост и кредити'].iloc[4,2]
    result['seminar_engagement'] = tables_from_header['Заетост и кредити'].iloc[5,2]
    result['practice_engagement'] = tables_from_header['Заетост и кредити'].iloc[6,2]
    result['homework_engagement'] = tables_from_header['Заетост и кредити'].iloc[9,2]
    result['test_prep_engagement'] = tables_from_header['Заетост и кредити'].iloc[10,2]
    result['course_project_engagement'] = tables_from_header['Заетост и кредити'].iloc[11,2]
    result['self_study_engagement'] = tables_from_header['Заетост и кредити'].iloc[12,2]
    result['study_report_engagement'] = tables_from_header['Заетост и кредити'].iloc[13,2]
    result['other_extracurricular_engagement'] = tables_from_header['Заетост и кредити'].iloc[14,2]
    result['exam_prep_engagement'] = tables_from_header['Заетост и кредити'].iloc[15,2]
    result['grading'] = { indicator: percentage for indicator, percentage in tables_from_header['Формиране на оценката по дисциплината'].iloc[2:,1:].to_numpy() }
    result['headnote'] = tables_from_header['Анотация на учебната дисциплина'].iloc[1,0]
    result['prerequisites'] = tables_from_header['Предварителни изисквания'].iloc[1,0]
    result['expected_results'] = tables_from_header['Очаквани резултати'].iloc[1,0]
    #syllabus
    result['synopsis'] = [ (description, list(map(int, horarium.strip().split())) if len(horarium) == 1 else list(horarium)) for description, *horarium in tables_from_header['Учебно съдържание'].iloc[2:, 1:].to_numpy() ]
    result['synopsis'] = [ { 'description': description, 'horarium': horarium } for description, horarium in result['synopsis'] ]
    if 'Конспект за изпит' in tables_from_header:
        result['exam_synopsis'] = [ description for description in tables_from_header['Конспект за изпит'].iloc[2:, 1].to_numpy() ]
    seq = tables_from_header['Библиография'].iloc[1:, 0]
    seq = seq[(seq != 'Основна') * (seq !=  'Допълнителна')]
    result['bibliography'] = [ content for content in seq ]

    return result


if len(sys.argv) < 2:
    print('Specify directory with pdf files')

directory = sys.argv[1]

courses_json = []

for file in glob.glob(f'{directory}/*.pdf'):
    print(f'Parsing file {file.strip(f"{directory}/")}')

    try:
        tables, metadata = get_tables(file)
    except Exception as e:
        print(f'An error occurred while parsing {file}: {e}', file=sys.stderr)
        continue

    tables_from_header = identify_and_merge_tables(tables, metadata)

    course = convert_to_json(tables_from_header)
    courses_json.append(course)

with open('courses.json', mode='wt') as file:
    file.write(json.dumps(courses_json))
