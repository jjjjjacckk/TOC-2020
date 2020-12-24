from collections import UserDict
from logging import Handler, LogRecord
import os
import sys
import requests, shutil
import pytesseract
from PIL import Image as II
from IPython.core.display import Image, display
from future.utils import _get_caller_globals_and_locals

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.models.events import PostbackEvent

from fsm import TocMachine
from utils import send_button_message, send_text_message, send_image_message
import scrawler 

load_dotenv()

#############################
# TODO                      #
# 1. 加上state transform     #
# 2. 解決登入問題             #
#############################

machine = TocMachine(
    states=[
        "state1", "state2", "state3",
        "input_dates_start", "input_dates_end",
        "input_dates_finish", 
        "not_login", "get_ID", "get_PWD", "get_VCODE", "logged_in"],
    transitions=[
        {"trigger": "advance", "source": "not_login", "dest": "state1", "conditions": "is_going_to_state1"},
        {"trigger": "advance", "source": "not_login", "dest": "state2", "conditions": "is_going_to_state2"},
        {"trigger": "advance", "source": "not_login", "dest": "state3", "conditions": "is_going_to_state3"},
        {"trigger": "advance", "source": "not_login", "dest": "input_dates_start", "conditions": "is_going_to_DateStart"},
        {"trigger": "advance", "source": "input_dates_start", "dest": "input_dates_end", "conditions": "is_going_to_DateEnd"},
        {"trigger": "advance", "source": "input_dates_end", "dest": "input_dates_finish", "conditions": "is_going_to_DateFinish"},
        {
            "trigger": "go_back",
            "source": ["state1", "state2", "state3", "input_dates_start", "input_dates_end", "input_dates_finish"], 
            "dest": "not_login"
        },
    ],
    initial="not_login",
    auto_transitions=False,
    show_conditions=True,
)

app = Flask(__name__, static_url_path="")

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)
handler = WebhookHandler(channel_secret)

login_state = 0 # 0:not logged-in, 1: get vcode, 2: logged in
sport = ''
gender = ''
date = {
    'start':'',
    'end':''
}
day = ''
session = requests.session()
print(f'global: ', session)
headers_ori = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36' }
headers_new = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36' }
user_id = ''
password = ''
vcode = ''


def login(user_id, passwd, vcode):
    global session
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
    print('payload:', payload)
    print('headers:', headers_new)

    print('In login: ', session)
    a = session.post(url=url, headers=headers_new, data=payload, verify=False)
    # print(a.text)
    return a

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text+" if i see this, then I succeed")
        )

    return "OK"

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    global sport, gender, date, day, \
           login_state, user_id, password, vcode, session

    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    print(f'events: {events}')

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        # print(f'EVENT: {event}\n{isinstance(event, PostbackEvent), not isinstance(event, MessageEvent)}')
        if not isinstance(event, MessageEvent):
            if isinstance(event, PostbackEvent):    # handle POSTBACK event
                handle_postback(event)
            continue
        if not isinstance(event.message, TextMessage):
            continue
        if not isinstance(event.message.text, str):
            continue
        if isinstance(event, PostbackEvent):
            send_text_message(event.reply_token, "IN HANDLER\n")

        print(f'\nlogin state: {login_state} {len(event.message.text)}')
        print(f"\nFSM STATE: {machine.state}")
        print(f"REQUEST BODY: \n{body}")
        print(f'EVENT: \n{event}')
        response = machine.advance(event)
        print(f'response: \n{response}')

        if response == False:
            if login_state == 0 and event.message.text.lower() == 'login':
                login_state = 1
                # send_image_message(event.reply_token, 'https://402c6f9347ae.ngrok.io/show-verify-code')
                send_text_message(event.reply_token, "請輸入你的學號")
            elif login_state == 1 and len(event.message.text) == 9:
                if event.message.text.lower().find('f') == -1:
                    send_text_message(event.reply_token, "請輸入你的學號")
                else:
                    login_state = 2
                    user_id = event.message.text
                    send_text_message(event.reply_token, "請輸入你的密碼\n- 輸入 +++ 能讓你重新輸入學號\n- 輸入密碼後，請輸入圖片中的數字")
            elif login_state == 2:
                if event.message.text.lower() == '+++':
                    login_state = 1
                    send_text_message(event.reply_token, "請輸入你的學號")
                else:
                    login_state = 3
                    password = event.message.text

                    # session = requests.session()
                    verify_url = 'https://cet.acad.ncku.edu.tw/ste/index.php?c=verifycode'
                    response = session.get(url=verify_url, stream=True, verify=False)
                    f = open('check.png', 'wb')
                    shutil.copyfileobj(response.raw, f)
                    f.close()
                    # display(Image('check.png'))

                    img = II.open('check.png')
                    vcode = pytesseract.image_to_string(img, lang='eng')
                    vcode = vcode[0:4]
                    print(vcode)

                    html = login(user_id, password, vcode)
                    # print(html)
                    if html.text.find('排球') == -1:
                        login_state = 1
                        send_text_message(event.reply_token, "學號、密碼或驗證碼有輸入錯誤，請重新登入")
                    else:
                        login_state = 4
                        # cookie_dict = session.cookies.get_dict()
                        # headers_new['Cookie'] = cookie_dict['PHPSESSID']
                        send_text_message(event.reply_token, "登入成功！\n請輸入「開始查詢」來輸入查詢資料")
                    # send_image_message(event.reply_token, 'https://402c6f9347ae.ngrok.io/show-verify-code')
            elif login_state == 3:
                vcode = event.message.text
                html = login(user_id, password, vcode)
                print(html)
                if html.text.find('排球') == -1:
                    login_state = 1
                    send_text_message(event.reply_token, "學號、密碼或驗證碼有輸入錯誤，請重新登入")
                else:
                    login_state = 4
                    cookie_dict = session.cookies.get_dict()
                    headers_new['Cookie'] = cookie_dict['PHPSESSID']
                    send_text_message(event.reply_token, "登入成功！\n請輸入「開始查詢」來輸入查詢資料")
            elif login_state == 4:
                if event.message.text.lower() == 'fsm':
                    send_image_message(event.reply_token, 'https://402c6f9347ae.ngrok.io/show-fsm')
                    # send_text_message(event.reply_token, text=TextMessage("Not Entering any State"))
                if event.message.text.lower() == 'vcode':
                    send_image_message(event.reply_token, 'https://402c6f9347ae.ngrok.io/show-verify-code')
                    # send_text_message(event.reply_token, text=TextMessage("Not Entering any State"))
                elif event.message.text.lower() == 'go_back':
                    if (machine.state == 'user'):
                        send_text_message(event.reply_token, 'Already in User state!\n')
                        print(f'Already in User state!\n')
                    else:
                        machine.go_back()
                        print(f'\nGoing back\n')
                elif event.message.text.lower() == 'scrawler':
                    seq = scrawler.gen_dates('20201225', '20201226')
                    print('\nSEQ!\n')
                    total = scrawler.get_mapped_form(time_seq=seq, session=session, header=headers_new, sport='排球')
                    print(total)
                    print('\nTOTAL\n')
                    outcome_list = scrawler.format_free_time(scrawler.find_free_time(seq, total, 'b'))

                    print('Done searching...')
                    
                    text = ''
                    for content in outcome_list:
                        text += content
                        text += '\n'
                    
                    print('\n', text, sep='')
                    t = 'FINISH\nAbout to end...\n'
                    send_text_message(event.reply_token, text)
                elif event.message.text.lower() == 'button':
                    send_button_message(event.reply_token, 'select_sport')
                elif event.message.text == '輸入日期':
                    if machine.state() != 'user': # TODO: Change here to forbid input
                        send_text_message(event.reply_token, "請輸入「球類選擇」再執行此指令")
                    else:
                        print("YEAH")
                elif event.message.text == 'Test':
                    send_button_message(event.reply_token, 'final')
            else:
                send_text_message(event.reply_token, "請先輸入「login」來登入！")


    return "OK"

# handle PostBack event from 'button'
@handler.add(PostbackEvent)
def handle_postback(event):
    global sport, gender, date, day
    print(f'\n\n\nevent: {event}\n\n\n')

    init = event.postback.data

    # regular button event
    data = init.split('&')
    data[0] = data[0].split('=')
    data[1] = data[1].split('=')

    print(f'\nHERE\n {data}')
    print('\nTEST:', (data[0][1] == 'date_start'))

    if data[0][1] == 'sport':
        if data[1][1] == 'None':
            sport = ''
            send_text_message(event.reply_token, '已經回到初始狀態')
        elif data[1][1] == 'volley':
            sport = '排球'
            send_button_message(event.reply_token, 'select_gender')
        elif data[1][1] == 'basket':
            sport = '籃球'
            send_button_message(event.reply_token, 'select_gender')
    elif data[0][1] == 'gender':
        if data[1][1] == 'go_back':
            gender = ''
            send_button_message(event.reply_token, 'select_sport')
        else:
            gender = data[1][1]
            send_button_message(event.reply_token, 'select_date_start')
    elif data[0][1] == 'date_start':
        # print("\n\n\n\n\nTTT\n\n\n\n")
        print(f'\n\nevent: {event}\n\n')
        if data[1][1] == 'start':
            time = event.postback.params['datetime']
            date['start'] = time[0:4] + time[5:7] + time[8:10]
            print(f'IN DATE_START\n')
            send_button_message(event.reply_token, 'select_date_end')
        elif data[1][1] == 'go_back':
            date['start'] = date['end'] = ''
            send_button_message(event.reply_token, 'select_gender')
        # send_button_message(event.reply_token, 'select_date_end')
    elif data[0][1] == 'date_end':
        if data[1][1] == 'end':
            time = event.postback.params['datetime']
            date['end'] = time[0:4] + time[5:7] + time[8:10]
            send_button_message(event.reply_token, 'select_date_confirm', date)
        elif data[1][1] == 'go_back':
            date['start'] = date['end'] = ''
            send_button_message(event.reply_token, 'select_date_start')
    elif data[0][1] == 'confirm':
        if data[1][1] == 'yes':
            send_button_message(event.reply_token, 'select_day')
        elif data[1][1] == 'no':
            date['start'] = date['end'] = ''
            send_button_message(event.reply_token, 'select_date_start')
    elif data[0][1] == 'day':
        if data[1][1] == 'go_back':
            day = ''
            send_button_message(event.reply_token, 'select_date_start')
        elif data[1][1] == 'weekdays':
            day = 'weekdays'
            send_button_message(event.reply_token, 'final')
        elif data[1][1] == 'weekend':
            day = 'weekend'
            send_button_message(event.reply_token, 'final')
    elif data[0][1] == 'reset':
        date['start'] = date['end'] = ''
        sport = gender = day = ''
        send_text_message(event.reply_token, '已經回到初始狀態')

    print(f'sport: {sport}\ngender: {gender}\nday: {day}\ndate: {date}\n')

    return "OK"

@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("fsm.png", prog="dot", format="png")
    return send_file("fsm.png", mimetype="image/png")

@app.route('/show-verify-code', methods=['GET'])
def show_verify_code():
    global session
    session = requests.session()
    verify_url = 'https://cet.acad.ncku.edu.tw/ste/index.php?c=verifycode'
    response = session.get(url=verify_url, stream=True, verify=False)
    f = open('check.png', 'wb')
    shutil.copyfileobj(response.raw, f)
    f.close()
    return send_file('check.png', mimetype='image/png')

if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
