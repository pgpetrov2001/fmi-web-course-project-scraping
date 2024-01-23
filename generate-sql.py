import json
from utils import staff_with_abbreviations
from scrape import departments

with open('staff.json') as file:
    staff = json.loads(file.read())
with open('departments-map.json') as file:
    department_from_member = json.loads(file.read())

staff = staff_with_abbreviations(staff)

for member in staff:
    member['names'] = member['names'].strip()
    department = department_from_member.get(member['names'])
    member['department_id'] = departments.index(department)+1 if department is not None else None

def SQL_NULL_IF_NONE(val):
    return 'NULL' if val is None else val

values = ',\n'.join(f'({SQL_NULL_IF_NONE(member["department_id"])}, \'{member["titles"]}\', \'{member["names"]}\')' for member in staff)

sql = f'''
INSERT INTO lecturers (department_id, titles, names)
VALUES
{values};
'''

print(sql)
