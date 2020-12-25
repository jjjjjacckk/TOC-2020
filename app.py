from collections import UserDict
from logging import Handler, LogRecord
import os
import sys
from numpy.core.records import get_remaining_size
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
from utils import send_button_message, send_format_text_message, send_text_message, send_image_message
import scrawler 

load_dotenv()

machine = TocMachine(
    states=[ 
        "init", "not_login", "get_ID", "get_PWD", "logged_in",
        "ch_sport", "ch_gender", "ch_date_start", "ch_date_end", "ch_day", "confirm", "rent"
    ],
    transitions=[
        {"trigger": "advance", "source": "init", "dest": "not_login", "conditions": "is_going_to_not_login"},
        {"trigger": "advance", "source": "not_login", "dest": "get_ID", "conditions": "is_going_to_get_ID"},
        {"trigger": "advance", "source": "get_ID", "dest": "get_PWD", "conditions": "is_going_to_get_PWD"},
        {"trigger": "advance", "source": "logged_in", "dest": "ch_sport", "conditions": "is_going_to_ch_sport"},
        
        {"trigger": "sport2Gender", "source": "ch_sport", "dest": "ch_gender"},
        {"trigger": "gender2DateStart", "source": "ch_gender", "dest": "ch_date_start"},

        {"trigger": "DateStart2DateEnd", "source": "ch_date_start", "dest": "ch_date_end"},
        {"trigger": "DateStart2Gender", "source": "ch_date_start", "dest": "ch_gender"},

        {"trigger": "DateEnd2Day", "source": "ch_date_end", "dest": "ch_day"},
        {"trigger": "DateEnd2Confirm", "source": "ch_date_end", "dest": "confirm"},
        {"trigger": "DateEnd2DateStart", "source": "ch_date_end", "dest": "ch_date_start"},

        {"trigger": "day2Confirm", "source": "ch_day", "dest": "confirm"},
        {"trigger": "day2DateStart", "source": "ch_day", "dest": "ch_date_start"},

        {"trigger": "confirm2Rent", "source": "confirm", "dest": "rent"},
        
        {"trigger": "suc_LOGIN", "source": "get_PWD", "dest": "logged_in"},
        {
            "trigger": "back2LoggedIn",
            "source": ["ch_sport", "ch_date_start", "ch_date_end", "ch_day", "rent"], 
            "dest": "logged_in"
        },
        {
            "trigger": "back2ChooseSport",
            "source": ["ch_gender", "ch_date_start", "ch_date_end", "ch_day", "confirm", "rent"],
            "dest": "ch_sport"
        },
        {
            "trigger": "back2NotLogin",
            "source": ["get_ID", "get_PWD"],
            "dest": "not_login"
        }
    ],
    initial="init",
    auto_transitions=False,
    show_conditions=True,
)

app = Flask(__name__, static_url_path="")

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    # print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    # print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)
handler = WebhookHandler(channel_secret)

greeting = '請輸入「開始查詢」來查詢球場資訊！'

# login_state = 0 # 0:not logged-in, 1: get vcode, 2: logged in
sport = ''
gender = ''
date = {
    'start':'',
    'end':''
}
day = ''
session = requests.session()
# # print(f'global: ', session)
headers_ori = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36' }
headers_new = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36' }
user_id = ''
password = ''
vcode = ''


def login(user_id, passwd, vcode):
    global session
    url = 'https://cet.acad.ncku.edu.tw/ste/index.php?c=auth&m=login'
    # print(vcode)

    payload = {
        'user_id': user_id,
        'passwd': passwd,
        'code': '',
        'x': '22',
        'y': '16'
    }
    payload['code'] = vcode
    # print('payload:', payload)
    # print('headers:', headers_new)

    # print('In login: ', session)
    a = session.post(url=url, headers=headers_new, data=payload, verify=False)
    # # print(a.text)
    return a

def to_scrawler(event):
    global sport, gender, date, day, machine, session, headers_new
    seq = scrawler.gen_dates(date['start'], date['end'])
    total = scrawler.get_mapped_form(time_seq=seq, session=session, header=headers_new, sport=sport)
    outcome_list = scrawler.format_free_time(scrawler.find_free_time(seq, total, gender))

    if len(outcome_list) == 0:
        text = '！所選的時段已經沒有空場了！\n！換一個時間重新查詢看看吧！\n\n'
        instruction = '> 請輸入「開始查詢」，來重新輸入查詢內容 <'
        machine.back2LoggedIn()
        send_text_message(event.reply_token, text+instruction)
        return 'NO_FREE_TIME'
    else:
        text = ''
        for content in outcome_list:
            text += content
            text += '\n'
        
        instruction = '\n> 請輸入「借場」來開啟借場系統的網頁 <'
        send_text_message(event.reply_token, text+instruction)
        return 'RENT'

def swap(a, b):
    return (b, a)

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
    
    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            if isinstance(event, PostbackEvent):    # handle POSTBACK event
                handle_postback(event)
            continue
        if not isinstance(event.message, TextMessage):
            continue
        if not isinstance(event.message.text, str):
            continue
        # if isinstance(event, PostbackEvent):
        #     send_text_message(event.reply_token, "IN HANDLER\n")

        print(f"\nFSM BEFORE STATE: {machine.state}")
        # print(f"REQUEST BODY: \n{body}")
        print(f'EVENT: \n{event}')
        print(f'text: {event.message.text} {event.message.text == "借場"}')  
        print(f'{machine.state == u"rent"} {repr(machine.state)} {type(machine.state)}')

        if event.message.text == 'fsm':
            send_image_message(event.reply_token, 'https://4d03acaaf663.ngrok.io/show-fsm')
            return "OK"
        # elif event.message.text == '說明' or event.message.text.lower() == 'help' or event.message.text.lower() == 'h':
        #     send_text_message(event.reply_token, '- 請輸入')
        #     return "OK"

        # special handling
        if machine.state == 'confirm':
            if event.message.text == '正確':
                response = machine.confirm2Rent()
                if to_scrawler(event) == 'NO_FREE_TIME':
                    return "OK"
            elif event.message.text == '重新查詢':
                date['start'] = date['end'] = ''
                sport = gender = day = ''
                response = machine.back2ChooseSport()
            else:
                response = False
        elif machine.state == u'rent':
            if event.message.text == '借場':
                response = machine.back2LoggedIn()
                send_button_message(event.reply_token, 'rent')
            else:
                response = False
        else:
            response = machine.advance(event)
        

        if response == False:
            if machine.state == 'init':
                login_state = 0
                send_text_message(event.reply_token, "請先輸入「登入」來繼續！")
            elif machine.state == 'not_login':
                send_text_message(event.reply_token, "請輸入你的學號！")
            elif machine.state == 'get_ID':
                if event.message.text.lower() == "+++": # on enter PWD,
                    machine.back2NotLogin()
                    send_text_message(event.reply_token, "請輸入你的學號！")
            elif machine.state == 'logged_in':
                date['start'] = date['end'] = ''
                sport = gender = day = ''
                send_text_message(event.reply_token, "請輸入「開始查詢」！")
            elif machine.state == 'confirm':
                send_text_message(event.reply_token, '1. 請輸入「正確」來開始爬蟲\n2. 輸入「重新查詢」來重新輸入相關資訊')
            elif machine.state == u'rent':
                send_text_message(event.reply_token, '請輸入「借場」來開啟借場系統的網頁！')
            else:
                send_text_message(event.reply_token, "請先輸入「登入」來繼續！")
        else:
            if machine.state == 'get_ID':
                user_id = event.message.text
            elif machine.state == 'get_PWD':
                password = event.message.text

                # get verify code
                verify_url = 'https://cet.acad.ncku.edu.tw/ste/index.php?c=verifycode'
                response = session.get(url=verify_url, stream=True, verify=False)
                f = open('check.png', 'wb')
                shutil.copyfileobj(response.raw, f)
                f.close()
                # display(Image('check.png'))

                # extract numbers from verify code
                img = II.open('check.png')
                vcode = pytesseract.image_to_string(img, lang='eng')
                vcode = vcode[0:4]

                # login
                html = login(user_id, password, vcode)

                # check if logged in succesfully                
                if html.text.find('排球') == -1:
                    machine.back2NotLogin()
                    send_text_message(event.reply_token, "！學號、密碼或驗證碼有輸入錯誤！\n請輸入「登入」重新登入")
                else:
                    machine.suc_LOGIN()
                    send_text_message(event.reply_token, "！登入成功！\n請輸入「開始查詢」來輸入查詢資料")
            elif machine.state == 'ch_sport':
                send_button_message(event.reply_token, 'select_sport')

    return "OK"

# handle PostBack event from 'button'
@handler.add(PostbackEvent)
def handle_postback(event):
    global sport, gender, date, day, machine, greeting

    init = event.postback.data

    # regular button event
    data = init.split('&')
    data[0] = data[0].split('=')
    data[1] = data[1].split('=')


    if data[0][1] == 'sport':
        if data[1][1] == 'volley':
            sport = '排球'
            machine.sport2Gender()
            send_button_message(event.reply_token, 'select_gender')
        elif data[1][1] == 'basket':
            sport = '籃球'
            send_button_message(event.reply_token, 'select_gender')
    elif data[0][1] == 'gender':
        if data[1][1] == 'go_back':
            gender = ''
            machine.back2ChooseSport()
            send_button_message(event.reply_token, 'select_sport')
        else:
            gender = data[1][1]
            machine.gender2DateStart()
            send_button_message(event.reply_token, 'select_date_start')
    elif data[0][1] == 'date_start':
        if data[1][1] == 'start':
            time = event.postback.params['datetime']
            date['start'] = time[0:4] + time[5:7] + time[8:10]
            machine.DateStart2DateEnd()
            send_button_message(event.reply_token, 'select_date_end')
        elif data[1][1] == 'go_back':
            date['start'] = date['end'] = ''
            machine.DateStart2Gender()
            send_button_message(event.reply_token, 'select_gender')
    elif data[0][1] == 'date_end':
        if data[1][1] == 'end':
            time = event.postback.params['datetime']
            date['end'] = time[0:4] + time[5:7] + time[8:10]

            if int(date['end']) - int(date['start']) < 0:
                date['start'], date['end'] = date['end'], date['start']
            # I got no time for this :(
            # machine.DateEnd2Day()
            # send_button_message(event.reply_token, 'select_day')
            machine.DateEnd2Confirm()
            send_format_text_message(event.reply_token, sport=sport, gender=gender, date=date, day=day)
        elif data[1][1] == 'go_back':
            date['start'] = date['end'] = ''
            machine.DateEnd2DateStart()
            send_button_message(event.reply_token, 'select_date_start')
    elif data[0][1] == 'day':
        if data[1][1] == 'go_back':
            day = ''
            date['start'] = date['end'] = ''
            machine.day2DateStart()
            send_button_message(event.reply_token, 'select_date_start')
        elif data[1][1] == 'weekdays':
            day = 'weekdays'
            machine.day2Confirm()
            send_format_text_message(event.reply_token, sport=sport, gender=gender, date=date, day=day)
        elif data[1][1] == 'weekend':
            day = 'weekend'
            machine.day2Confirm()
            send_format_text_message(event.reply_token, sport=sport, gender=gender, date=date, day=day)
    elif data[0][1] == 'reset':
        date['start'] = date['end'] = ''
        sport = gender = day = ''
        machine.back2ChooseSport()
        send_text_message(event.reply_token, greeting)

    return "OK"

@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("fsm.png", prog="dot", format="png")
    return send_file("fsm.png", mimetype="image/png")

# @app.route('/show-verify-code', methods=['GET'])
# def show_verify_code():
#     global session
#     session = requests.session()
#     verify_url = 'https://cet.acad.ncku.edu.tw/ste/index.php?c=verifycode'
#     response = session.get(url=verify_url, stream=True, verify=False)
#     f = open('check.png', 'wb')
#     shutil.copyfileobj(response.raw, f)
#     f.close()
#     return send_file('check.png', mimetype='image/png')

if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
