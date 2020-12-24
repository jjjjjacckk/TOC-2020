from logging import Handler, LogRecord
import os
import sys

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
    states=["user", "state1", "state2", "state3"],
    transitions=[
        {
            "trigger": "advance",
            "source": "user",
            "dest": "state1",
            "conditions": "is_going_to_state1",
        },
        {
            "trigger": "advance",
            "source": "user",
            "dest": "state2",
            "conditions": "is_going_to_state2",
        },
        {
            "trigger": "advance",
            "source": "user",
            "dest": "state3",
            "conditions": "is_going_to_state3",
        },
        {   
            "trigger": "go_back", 
            "source": ["state1", "state2", "state3"], 
            "dest": "user"
        },
    ],
    initial="user",
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

sport = ''
gender = ''
date = {
    'start':'',
    'end':''
}
day = ''


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
    global sport, gender, date, day

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

        print(f'HERE')
        print(f"\nFSM STATE: {machine.state}")
        print(f"REQUEST BODY: \n{body}")
        print(f'EVENT: \n{event}')
        response = machine.advance(event)
        print(f'response: \n{response}')
        if response == False:
            if event.message.text.lower() == 'fsm':
                send_image_message(event.reply_token, 'https://6557c9ca56dc.ngrok.io/show-fsm')
                send_text_message(event.reply_token, "Not Entering any State")
            elif event.message.text.lower() == 'go_back':
                if (machine.state == 'user'):
                    send_text_message(event.reply_token, 'Already in User state!\n')
                    print(f'Already in User state!\n')
                else:
                    machine.go_back()
                    print(f'\nGoing back\n')
            elif event.message.text.lower() == 'scrawler':
                seq = scrawler.gen_dates('20201224', '20201231')
                total = scrawler.get_mapped_form(seq)
                outcome_list = scrawler.format_free_time(scrawler.find_free_time(seq, total, 'b'))

                print('Done searching...')
                # print(outcome_list)
                
                text = ''
                for content in outcome_list:
                    # print(content)
                    text += content
                    text += '\n'
                    # text.append(content)
                    # text.append('\n')
                
                print('\n', text, sep='')
                t = 'FINISH\nAbout to end...\n'
                send_text_message(event.reply_token, text)


                # text = ''
                # for index in range(len(outcome_list)-1):
                #     text.append(outcome_list[index])
                #     text.append('\n')
                # text.append(outcome_list[:-1])
                # print(text)
            elif event.message.text.lower() == 'button':
                send_button_message(event.reply_token, 'select_sport')
            else:
                send_text_message(event.reply_token, "Not Entering any State")


    return "OK"

# handle PostBack event from 'button'
@handler.add(PostbackEvent)
def handle_postback(event):
    global sport, gender, date, day
    
    data = event.postback.data.split('&')
    data[0] = data[0].split('=')
    data[1] = data[1].split('=')

    print(f'\nHERE\n {data}')


    if data[0][1] == 'sport':
        if data[1][1] != 'reset':
            send_button_message(event.reply_token, 'select_gender')
        else:
            send_text_message(event.reply_token, '已經回到初始狀態')
    elif data[0][1] == 'gender':
        if data[1][1] != 'go_back':
            send_button_message(event.reply_token, 'select_day')
        else:
            send_button_message(event.reply_token, 'select_sport')
    elif data[0][1] == 'day':
        if data[1][1] != 'go_back':
            send_button_message(event.reply_token, 'final')
        else:
            send_button_message(event.reply_token, 'select_gender')
    elif data[0][1] == 'reset':
        send_text_message(event.reply_token, '已經回到初始狀態')

    return "OK"

    

@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("fsm.png", prog="dot", format="png")
    return send_file("fsm.png", mimetype="image/png")


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
