import sys
import os
import re
import concurrent.futures
from bs4 import BeautifulSoup
import requests
import urllib
from string import ascii_lowercase
import json
import time

def get_link_content(url):
    response = requests.get(url)
    html_string = response.text
    return BeautifulSoup(html_string, 'html.parser')


staffletters =  'абвгдежзийклмнопрстфхцшюя'
departments = ["algebra","veroyatnosti-operacionni-izsledvaniya-i-statistika","geometriya","diferencialni-uravneniya","informacionni-tehnologii","kompleksen-analiz-i-topologiya","kompyutrna-informatika","matematicheska-logika-i-prilozheniyata-y","matematicheski-analiz","mehatronika-robotika-i-mehanika","obuchenie-po-matematika-i-informatika","softuerni-tehnologii","chisleni-metodi-i-algoritmi","izsledovateli-km-fmi-dekanat"]
#scraped with the following code from https://www.fmi.uni-sofia.bg/bg/departments:
#const links = Array.from(document.querySelectorAll('#main .content .item-list .field-content a'))
#console.log(JSON.stringify(links.map(({href}) => href.split('/')[5])));

def scrape_pagenum_by_letter(letter):
    soup = get_link_content(f'https://www.fmi.uni-sofia.bg/bg/faculty-staff/{letter}')
    return len(soup.select('.pager .pager-item')) + 1

def scrape_staff_by_letter_and_pagenum(letter, pagenum):
    soup = get_link_content(f'https://www.fmi.uni-sofia.bg/bg/faculty-staff/{letter}?page={pagenum}')
    names = map(lambda el: el.text, soup.select('.view-content .views-row .views-field-title .field-content'))
    titles = map(lambda el: el.text, soup.select('.view-content .views-row .views-field-field-mt-academic-title-ref .field-content'))
    return [{ 'names': name, 'titles': title } for name, title in zip(names, titles)]

def scrape_department(department):
    departmentFromStaffMember = dict()
    soup = get_link_content(f'https://www.fmi.uni-sofia.bg/bg/departments/{department}')
    names = map(lambda el: el.text.strip(), soup.select('.view-header .view-content .views-field-title'))
    for name in names:
        name = name.strip()
        if name in departmentFromStaffMember:
            print(f'WARNING: overwriting department {department} on top of {departmentFromStaffMember[name]} for staff member {name}', file=sys.stderr)
        departmentFromStaffMember[name] = department

    return departmentFromStaffMember

def download_pdf(link, directory, index):
    def get_filename_from_cd(cd):
        """
        Get filename from content-disposition
        """
        if not cd:
            return None
        fname = re.findall('filename=(.+)', cd)
        if len(fname) == 0:
            return None
        return fname[0]

    r = requests.get(link, allow_redirects=True)
    r.raise_for_status()
    filename = get_filename_from_cd(r.headers.get('content-disposition'))
    if filename is None:
        filename = f'optional-course-{index}.pdf'
    else:
        filename = urllib.parse.unquote(filename.strip('"'))

    with open(os.path.join(directory, filename), mode='wb') as file:
        file.write(r.content)

    print('wrote', filename, file=sys.stderr)

def scrape_pdf_link(link):
    soup = get_link_content(link)
    anchor = soup.select('#header-primary-action a')[0]
    return anchor.attrs.get('href')

def getStaff():
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(staffletters)) as executor:
            pagenumbers = executor.map(scrape_pagenum_by_letter, staffletters)

    pagenumbers = list(pagenumbers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=sum(pagenumbers)) as executor:
            unfolded_staffletters = [ letter for letter, pagenum in zip(staffletters, pagenumbers) for _ in range(pagenum) ]
            unfolded_pagenumbers = [ page for pagenum in pagenumbers for page in range(pagenum) ]
            results = executor.map(scrape_staff_by_letter_and_pagenum, unfolded_staffletters, unfolded_pagenumbers)

    staff = []
    for result in results:
        staff.extend(result)

    return staff

def getDepartments():
    departmentFromStaffMember = dict()

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(departments)) as executor:
            results = executor.map(scrape_department, departments)

    for result in results:
        departmentFromStaffMember.update(result)

    return departmentFromStaffMember



def savePDFS(directory):
    with open('optionalcourses-links.json') as file:
        links = json.loads(file.read())

    print(len(links), file=sys.stderr)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            links = list(executor.map(scrape_pdf_link, links))

    print(len(links), file=sys.stderr)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(download_pdf, links, [directory] * len(links), range(len(links))))

    print(results)

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print('Not specified what to scrape')
        sys.exit(1)
    if sys.argv[1] == 'staff':
        print(json.dumps(getStaff()))
    elif sys.argv[1] == 'departments':
        print(json.dumps(getDepartments()))
    elif sys.argv[1] == 'pdfs':
        if len(sys.argv) < 3:
            print('Did not specify directory', file=sys.stderr)
            sys.exit(1)

        directory = sys.argv[2]

        savePDFS(directory)
        print('Saved pdfs')
    else:
        print('invalid thing to scrape')
        sys.exit(1)
