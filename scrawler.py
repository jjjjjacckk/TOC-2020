import requests
from lxml import html
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta

sport_dict = {
        '田徑'   : 'A',
        '足球'   : 'B',
        '籃球'   : 'C',
        '排球'   : 'D',
        '網球'   : 'E',
        '棒球'   : 'F',
        '壘球'   : 'G',
        '橄欖球' : 'H',
        '羽球'   : 'S',
        '桌球'   : 'T'
}

volley_court_dict = {
    '00':'光低1',
    '01':'光低1',
    '02':'光低1',
    '10':'光低2',
    '11':'光低2',
    '12':'光低2',
    '20':'光低3',
    '21':'光低3',
    '22':'光低3',
    '30':'光低4',
    '31':'光低4',
    '32':'光低4',
    '40':'光低5',
    '41':'光低5',
    '42':'光低5',
    '50':'高場東',
    '51':'高場東',
    '52':'高場東',
    '60':'高場西',
    '61':'高場西',
    '62':'高場西',
}

time_dict = {
    '0':'0600~1200',
    '1':'1200~1800',
    '2':'1800~2100'
}

def gen_dates(start:str, end:str):
    start_date = datetime.strptime(start, '%Y%m%d')
    end_date = datetime.strptime(end, '%Y%m%d')
    serial = []
    if (end_date - start_date).days >= 0:
        for i in range((end_date - start_date).days+1):
            tmp = start_date + timedelta(days=i)
            serial.append('{0:>{3}4}{1:>{3}2}{2:>{3}2}'.format(tmp.year, tmp.month, tmp.day, 0))
            
    return serial

def get_sport_raw(date:str, session, header, sport_in:str):
    url = 'https://cet.acad.ncku.edu.tw/ste/index.php?c=ste11211'
    payload = {
        'sport': sport_dict[sport_in],
        'sdate': date,
        'c': 'ste11211',
        'm': 'read'
    }


    volleyball = session.post(url=url, headers=header, data=payload)
    # print(session.cookies.get)
    # print(login.cookies, login.cookies.get_dict())
    # print(headers['Cookie'])

    # if login.cookies.get_dict():        #保持cookie有效
        # login.cookies.update(login.cookies)
    # volleyball = session.post(url=url_get, headers=headers, data=payload)
    # print(login.cookies, bool(login.cookies.get_dict()))
    # print(login.text)
    # print(volleyball.text)
    # with open('test.html', 'w', encoding='utf-8') as fp:
    #     fp.write(volleyball.text)

    # replace is for '體育室 <br/>(數學系)' (in raw)
    # but in '體育室 <br>(數學系)' (in html)
    return bs(volleyball.text.replace('<br>', ''), 'html.parser')

def retreive_form(soup):
    if not isinstance(soup, type(bs())):
        raise TypeError("soup must be a " + repr(type(bs())))
    else:
        form =[]
        row = []
        counter = 0
        for content in soup.find_all('td'):
            # print(content, '\t\t', repr(content.string))
            if content.string not in ('\xa0\xa0', '可借用', '不可借用', '已借用'):
                if counter == 3:
                    counter = 0
                    form.append(row)
                    row = []
                row.append(content.string)
                counter += 1
    
    return form

def get_mapped_form(time_seq:list, session, header, sport:str='排球'):
    situation = {}
    for dates in time_seq:
        m = get_sport_raw(dates, sport_in=sport, header=header, session=session)
        situation[dates] = retreive_form(m)

    return situation

def find_free_time(seq:list, situation:dict, gender:str='both'):
    # gender = 'a' -> both gender
    free = []
    for dates in seq:
        for row in range(7):
            for column in range(3):
                # print(situation[dates][row][column])
                if isinstance(situation[dates][row][column], type(None)):
                    element = '{0} | {1} | {2}'.format(dates[4:6]+'/'+dates[6:], time_dict[str(column)], volley_court_dict[str(row*10+column).zfill(2)])
                    if gender.lower() == 'boy': # boy
                        if row in [3, 4, 5]:
                            continue
                    elif gender.lower() == 'girl': # girl
                        if row not in [3, 4, 5]:
                            continue
                    free.append(element)
    return free

def format_free_time(free:list):
    new_free = []
    if len(free) != 1:
        old = -1
        for lines in free:
            if old == -1:
                old = int(lines[0:2] + lines[3:5])
            elif old != int(lines[0:2] + lines[3:5]):
                old = int(lines[0:2] + lines[3:5])
                new_free.append('-' * (len(lines)))
            new_free.append(lines)
    
    return new_free


if __name__ == '__main__':
    seq = gen_dates('20201224', '20201231')
    get_sport_raw('20201223', '排球')
    # total = get_mapped_form(seq)
    # outcome_list = format_free_time(find_free_time(seq, total, 'b'))

    # for content in outcome_list:
    #     print(content)
