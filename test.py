from PIL import Image as II
import pytesseract
import requests
import shutil
from lxml import html
from bs4 import BeautifulSoup as bs
from IPython.display import Image, display

session = requests.session()
headers = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36' }

def get_vcode():
    global session
    # session = requests.session()
    print(session)
    verify_url = 'https://cet.acad.ncku.edu.tw/ste/index.php?c=verifycode'
    response = session.get(url=verify_url, stream=True, verify=False)
    f = open('check1.png', 'wb')
    shutil.copyfileobj(response.raw, f)
    f.close()

    display(Image('./check.png'))

def login(user_id, passwd, vcode):
    # vcode = input('輸入驗證碼：')
    global session, headers
    url = 'https://cet.acad.ncku.edu.tw/ste/index.php?c=auth&m=login'
    print(vcode)

    payload = {
        'user_id': user_id,
        'passwd': passwd,
        'code': '',
        'x': '22',
        'y': '16'
    }
    payload['code'] = vcode

    print(session)
    a = session.post(url=url, headers=headers, data=payload)
    print(a)
    return a

if __name__ == '__main__':
    userID = input('USER ID')
    passwd = input('PASSWD')
    get_vcode()

    img = II.open('check1.png')
    text = pytesseract.image_to_string(img, lang='eng')
    print(text)

    # v = input('VCODE')

    a = login(userID, passwd, text[0:4])
    print(a.text)

    cookie_dict = session.cookies.get_dict()
    headers['Cookie'] = cookie_dict['PHPSESSID']
    print(headers)

    # # stay here
    url = 'https://cet.acad.ncku.edu.tw/ste/index.php?c=ste1121'
    t = session.get(url=url, headers=headers)
    print(t.text)