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

#############################
# TODO                      #
# 1. 加上state transform     #
# 2. 解決登入問題             #
#############################

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

login_state = 0 # 0:not logged-in, 1: get vcode, 2: logged in
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
    # # print(sport, gender, date, day, machine, session, headers_new)
    seq = scrawler.gen_dates(date['start'], date['end'])
    # # print('\nSEQ!\n')
    total = scrawler.get_mapped_form(time_seq=seq, session=session, header=headers_new, sport=sport)
    # # print(total)
    # # print('\nTOTAL\n')
    outcome_list = scrawler.format_free_time(scrawler.find_free_time(seq, total, gender))

    # # print('Done searching...')
    
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
        
        # # print('\n', text, sep='')

        instruction = '\n> 請輸入「借場」來開啟借場系統的網頁 <'
        send_text_message(event.reply_token, text+instruction)
        return 'RENT'

def swap(a, b):
    return (b, a)

# @app.route("/callback", methods=["POST"])
# def callback():
#     signature = request.headers["X-Line-Signature"]
#     # get request body as text
#     body = request.get_data(as_text=True)
#     app.logger.info("Request body: " + body)

#     # parse webhook body
#     try:
#         events = parser.parse(body, signature)
#     except InvalidSignatureError:
#         abort(400)

#     # if event is MessageEvent and message is TextMessage, then echo text
#     for event in events:
#         if not isinstance(event, MessageEvent):
#             continue
#         if not isinstance(event.message, TextMessage):
#             continue

#         line_bot_api.reply_message(
#             event.reply_token, TextSendMessage(text=event.message.text+" if i see this, then I succeed")
#         )

#     return "OK"

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
    
    # # print(f'events: {events}')

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        # # print(f'EVENT: {event}\n{isinstance(event, PostbackEvent), not isinstance(event, MessageEvent)}')
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

        # # print(f'\nlogin state: {login_state} {len(event.message.text)}')
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

        if machine.state == 'confirm':
            if event.message.text == '正確':
                response = machine.confirm2Rent()
                # # print(f'\nresponse: {response}')
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
        
        print(f"\nFSM AFTER STATE: {machine.state}")
        print(f'response: \n{response}')

        if response == False:
            if machine.state == 'init':
                login_state = 0
                # send_image_message(event.reply_token, 'https://402c6f9347ae.ngrok.io/show-verify-code')

                # send_button_message(event.reply_token, 'select_sport')
                send_text_message(event.reply_token, "請先輸入「登入」來繼續！(response = False, init)")
            elif machine.state == 'not_login':
                send_text_message(event.reply_token, "請輸入你的學號(response = False, not_login)")
            elif machine.state == 'get_ID':
                if event.message.text.lower() == "+++": # on enter PWD,
                    machine.back2NotLogin()
                    send_text_message(event.reply_token, "請輸入你的學號(response = False, getID)")
            # elif machine.state == 'get_PWD':
            #     if event.message.text.lower() == "+++":
            #         machine.back2NotLogin()
            #         send_text_message(event.reply_token, "請輸入你的學號(response = False, getPWD)")
            elif machine.state == 'logged_in':
                date['start'] = date['end'] = ''
                sport = gender = day = ''
                send_text_message(event.reply_token, "請輸入「開始查詢」！")
            elif machine.state == 'confirm':
                # if event.message.text == '正確':
                #     machine.confirm2rent()
                #     scrawler(event)
                # elif event.message.text == '重新查詢':
                #     date['start'] = date['end'] = ''
                #     sport = gender = day = ''
                #     machine.back2ChooseSport()
                #     send_button_message(event.reply_token, 'select_sport')
                # else:
                send_text_message(event.reply_token, '請輸入「正確」來開始爬蟲\n或輸入「重新查詢」來重新輸入相關資訊')
            elif machine.state == u'rent':
                send_text_message(event.reply_token, '請輸入「借場」來開啟借場系統的網頁')
            
            # elif login_state == 1 and len(event.message.text) == 9:
            #     if event.message.text.lower().find('f') == -1:
            #         send_text_message(event.reply_token, "請輸入你的學號")
            #     else:
            #         login_state = 2
            #         user_id = event.message.text
            #         send_text_message(event.reply_token, "請輸入你的密碼\n- 輸入 +++ 能讓你重新輸入學號")
            # elif login_state == 2:
            #     if event.message.text.lower() == '+++':
            #         login_state = 1
            #         send_text_message(event.reply_token, "請輸入你的學號")
            #     else:
            #         login_state = 3
            #         password = event.message.text

            #         # session = requests.session()
            #         verify_url = 'https://cet.acad.ncku.edu.tw/ste/index.php?c=verifycode'
            #         response = session.get(url=verify_url, stream=True, verify=False)
            #         f = open('check.png', 'wb')
            #         shutil.copyfileobj(response.raw, f)
            #         f.close()
            #         # display(Image('check.png'))

            #         img = II.open('check.png')
            #         vcode = pytesseract.image_to_string(img, lang='eng')
            #         vcode = vcode[0:4]
            #         # print(vcode)

            #         html = login(user_id, password, vcode)
            #         # # print(html)
            #         if html.text.find('排球') == -1:
            #             login_state = 1
            #             send_text_message(event.reply_token, "學號、密碼或驗證碼有輸入錯誤，請重新登入")
            #         else:
            #             login_state = 4
            #             # cookie_dict = session.cookies.get_dict()
            #             # headers_new['Cookie'] = cookie_dict['PHPSESSID']
            #             send_text_message(event.reply_token, "登入成功！\n請輸入「開始查詢」來輸入查詢資料")
            #         # send_image_message(event.reply_token, 'https://402c6f9347ae.ngrok.io/show-verify-code')
            # elif login_state == 3:
            #     vcode = event.message.text
            #     html = login(user_id, password, vcode)
            #     # print(html)
            #     if html.text.find('排球') == -1:
            #         login_state = 1
            #         send_text_message(event.reply_token, "學號、密碼或驗證碼有輸入錯誤，請重新登入")
            #     else:
            #         login_state = 4
            #         cookie_dict = session.cookies.get_dict()
            #         headers_new['Cookie'] = cookie_dict['PHPSESSID']
            #         send_text_message(event.reply_token, "登入成功！\n請輸入「開始查詢」來輸入查詢資料")
            # elif login_state == 4:
            #     if event.message.text.lower() == 'fsm':
            #         send_image_message(event.reply_token, 'https://402c6f9347ae.ngrok.io/show-fsm')
            #         # send_text_message(event.reply_token, text=TextMessage("Not Entering any State"))
            #     if event.message.text.lower() == 'vcode':
            #         send_image_message(event.reply_token, 'https://402c6f9347ae.ngrok.io/show-verify-code')
            #         # send_text_message(event.reply_token, text=TextMessage("Not Entering any State"))
            #     elif event.message.text.lower() == 'go_back':
            #         if (machine.state == 'user'):
            #             send_text_message(event.reply_token, 'Already in User state!\n')
            #             # print(f'Already in User state!\n')
            #         else:
            #             machine.go_back()
            #             # print(f'\nGoing back\n')
            #     elif event.message.text.lower() == 'scrawler':
            #         seq = scrawler.gen_dates('20201225', '20201231')
            #         # print('\nSEQ!\n')
            #         total = scrawler.get_mapped_form(time_seq=seq, session=session, header=headers_new, sport='排球')
            #         # print(total)
            #         # print('\nTOTAL\n')
            #         outcome_list = scrawler.format_free_time(scrawler.find_free_time(seq, total, 'b'))

            #         # print('Done searching...')
                    
            #         text = ''
            #         for content in outcome_list:
            #             text += content
            #             text += '\n'
                    
            #         # print('\n', text, sep='')
            #         t = 'FINISH\nAbout to end...\n'
            #         send_text_message(event.reply_token, text)
            #     elif event.message.text.lower() == 'button':
            #         send_button_message(event.reply_token, 'select_sport')
            #     elif event.message.text == '輸入日期':
            #         if machine.state() != 'user': # TODO: Change here to forbid input
            #             send_text_message(event.reply_token, "請輸入「球類選擇」再執行此指令")
            #         else:
            #             # print("YEAH")
            #     elif event.message.text == 'Test':
            #         send_button_message(event.reply_token, 'final')
            
            else:
                send_text_message(event.reply_token, "請先輸入「登入」來繼續！")
        else:
            # if machine.state == 'not_login':
            #     # print('In not login\n')
            if machine.state == 'get_ID':
                user_id = event.message.text
                # print('userID = get_ID\n')
            elif machine.state == 'get_PWD':
                password = event.message.text
                # print('password = get_PWD\n')
                # user_id = event.message.text

                # # print("IDK...\n")
                # password = event.message.text

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
                # print(vcode)

                # login
                html = login(user_id, password, vcode)
                # # print(html)
                if html.text.find('排球') == -1:
                    machine.back2NotLogin()
                    send_text_message(event.reply_token, "學號、密碼或驗證碼有輸入錯誤，請輸入「登入」重新登入")
                else:
                    machine.suc_LOGIN()
                    # cookie_dict = session.cookies.get_dict()
                    # headers_new['Cookie'] = cookie_dict['PHPSESSID']
                    send_text_message(event.reply_token, "登入成功！\n請輸入「開始查詢」來輸入查詢資料")
                # send_image_message(event.reply_token, 'https://402c6f9347ae.ngrok.io/show-verify-code')
            elif machine.state == 'ch_sport':
                send_button_message(event.reply_token, 'select_sport')

    return "OK"

# handle PostBack event from 'button'
@handler.add(PostbackEvent)
def handle_postback(event):
    global sport, gender, date, day, machine, greeting
    # print(f'\n\n\nevent: {event}\n\n\n')

    init = event.postback.data

    # regular button event
    data = init.split('&')
    data[0] = data[0].split('=')
    data[1] = data[1].split('=')

    # print(f'\nHERE\n {data}')
    # print('\nTEST:', (data[0][1] == 'date_start'))

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
        # # print("\n\n\n\n\nTTT\n\n\n\n")
        # # print(f'\n\nevent: {event}\n\n')
        if data[1][1] == 'start':
            time = event.postback.params['datetime']
            date['start'] = time[0:4] + time[5:7] + time[8:10]
            machine.DateStart2DateEnd()
            # # print(f'IN DATE_START\n')
            send_button_message(event.reply_token, 'select_date_end')
        elif data[1][1] == 'go_back':
            date['start'] = date['end'] = ''
            machine.DateStart2Gender()
            send_button_message(event.reply_token, 'select_gender')
        # send_button_message(event.reply_token, 'select_date_end')
    elif data[0][1] == 'date_end':
        if data[1][1] == 'end':
            time = event.postback.params['datetime']
            date['end'] = time[0:4] + time[5:7] + time[8:10]

            # print(int(date['end']), int(date['start']), int(date['end']) - int(date['start']) < 0)
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
    # elif data[0][1] == '借場':
    #     if data[1][1] == 'correct':
    #         machine.back2ChooseSport()
    #         # print("\n\n\n開始爬蟲啦！！！\n\n\n")
    elif data[0][1] == 'reset':
        date['start'] = date['end'] = ''
        sport = gender = day = ''
        machine.back2ChooseSport()
        send_text_message(event.reply_token, greeting)

    # print(f'sport: {sport}\ngender: {gender}\nday: {day}\ndate: {date}\n')

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
