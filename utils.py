import os

from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage, \
                           ImageSendMessage, ButtonsTemplate, TemplateSendMessage, \
                           PostbackAction, MessageAction, URIAction, DatetimePickerAction
from datetime import datetime, timedelta

channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)


def send_text_message(reply_token, text):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

    return "OK"

def send_format_text_message(reply_token, sport, gender, date:dict, day):
    line_bot_api = LineBotApi(channel_access_token)

    if gender == 'boy':
        field = '男網'
    elif gender == 'girl':
        field = '女網'
    else:
        field = '男女網都查'

    # message = f'運動: {sport}\n場地類型: {field}\n時間: {date["start"]} ~ {date["end"]}\n星期: {day}'
    message = f'運動: {sport}\n場地類型: {field}\n時間: {date["start"]} ~ {date["end"]}'
    confirming = '\n\n若以上訊息皆正確，請輸入「正確」來開始爬蟲\n若有錯誤，請輸入「重新查詢」來重新輸入相關資訊'

    line_bot_api.reply_message(reply_token, TextSendMessage(text=message+confirming))

def send_image_message(reply_token, url):
    line_bot_api = LineBotApi(channel_access_token)
    message = ImageSendMessage(
        type = 'image',
        original_content_url = url,
        preview_image_url = url
    )
    line_bot_api.reply_message(reply_token, message)

    return "OK"

def send_button_message_template(reply_token, button):
    line_bot_api = LineBotApi(channel_access_token)
    buttons_template_message = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url='https://example.com/image.jpg',
            title='Menu',
            text='Please select',
            actions=[
                PostbackAction(
                    label='postback',
                    display_text='postback text',
                    data='type=sport&ball=volley'
                ),
                MessageAction(
                    label='message',
                    text='message text'
                ),
                URIAction(
                    label='uri',
                    uri='http://example.com/'
                )
            ]
        )
    )


    line_bot_api.reply_message(reply_token, buttons_template_message)
    return "OK"

def send_button_message(reply_token, type, param:dict={'start':'', 'end':''}):
    line_bot_api = LineBotApi(channel_access_token)

    select_sport = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url='https://example.com/image.jpg',
            title='球類運動',
            text='選擇要查詢哪一種球類場地',
            actions=[
                PostbackAction(
                    label='排球',
                    display_text='你選擇了「排球」',
                    data='type=sport&ball=volley'
                ),
                # PostbackAction(
                #     label='籃球',
                #     display_text='你選擇了「籃球」',
                #     data='type=sport&ball=basket'
                # ),
                PostbackAction(
                    label='回到初始狀態',
                    display_text='你選擇了「回到初始狀態」',
                    data='type=reset&ball=None'
                ),
            ]
        )
    )

    select_gender = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url='https://example.com/image.jpg',
            title='排球場地類型',
            text='選擇要查男網、女網、或是都查',
            actions=[
                PostbackAction(
                    label='我要查男網',
                    display_text='你選擇了「我要查男網」',
                    data='type=gender&gender=boy'
                ),
                PostbackAction(
                    label='我要查女網',
                    display_text='你選擇了「我要查女網」',
                    data='type=gender&gender=girl'
                ),
                PostbackAction(
                    label='男女網都查',
                    display_text='你選擇了「男女網都查」',
                    data='type=gender&gender=both'
                ),
                PostbackAction(
                    label='重新選擇球類',
                    display_text='你選擇了「重新選擇球類」',
                    data='type=gender&gender=go_back'
                ),
            ]
        )
    )

    today = datetime.today()
    today = today.strftime("%Y-%m-%dt00:00")

    select_date_start = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url='https://example.com/image.jpg',
            title='輸入要查詢的「開始」時間區段',
            text='選擇要查詢的第一天：',
            actions=[
                DatetimePickerAction(
                    type="datetimepicker",
                    label="選擇開始的日期",
                    data="type=date_start&date=start",
                    mode="datetime",
                    initial=today,
                    max="2030-02-28t23:59",
                    min="2020-12-10t00:00"
                ),
                PostbackAction(
                    label='重新選擇場地類型',
                    display_text='你選擇了「重新選擇場地類型」',
                    data='type=date_start&date=go_back'
                ),
                PostbackAction(
                    label='取消查詢',
                    display_text='你選擇了「取消查詢」',
                    data='type=reset&date=None'
                )
            ]
        )
    )

    select_date_end = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url='https://example.com/image.jpg',
            title='輸入要查詢的「結束」時間區段',
            text='選擇要查詢的最後一天，若僅要查詢一天，請選擇和開始時間相同的日期',
            actions=[
                DatetimePickerAction(
                    type="datetimepicker",
                    label="選擇結束的日期",
                    data="type=date_end&date=end",
                    mode="datetime",
                    initial=today,
                    max="2030-02-28t23:59",
                    min="2020-12-10t00:00"
                ),
                PostbackAction(
                    label='重新選擇開始時間',
                    display_text='你選擇了「重新選擇開始時間」',
                    data='type=date_end&date=go_back'
                ),
                PostbackAction(
                    label='取消查詢',
                    display_text='你選擇了「取消查詢」',
                    data='type=reset&day=None'
                )
            ]
        )
    )

    # this is redundant
    select_date_confirm = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url='https://example.com/image.jpg',
            title='確認選定的日期：',
            text=str('你選的是：\n- 開始：{0}\n- 結束：{1}？'.format(param['start'], param['end'])),
            actions=[
                PostbackAction(
                    label='是',
                    display_text='你選擇了「是」',
                    data='type=confirm&answer=yes'
                ),
                PostbackAction(
                    label='否',
                    display_text='你選擇了「否」\n請重新選擇日期！',
                    data='type=confirm&answer=no'
                )
            ]
        )
    )

    select_day = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url='https://example.com/image.jpg',
            title='選擇要查詢的星期',
            text='例：選擇星期一、四，則只會公布選擇時間區間中，星期一、四的空場時間',
            actions=[
                PostbackAction(
                    label='全部平日',
                    display_text='你選擇了「全部平日」',
                    data='type=day&day=weekdays'
                ),
                PostbackAction(
                    # label='自訂時間',   
                    # display_text='你選擇了「自訂時間」',
                    # data='type=day&day=manual'
                    label='週末',   
                    display_text='你選擇了「週末」',
                    data='type=day&day=weekend'
                ),
                PostbackAction(
                    label='重新選擇排球場地類型',
                    display_text='你選擇了「重新選擇時間」',
                    data='type=day&day=go_back'
                ),
                PostbackAction(
                    label='取消查詢',
                    display_text='你選擇了「取消查詢」',
                    data='type=reset&day=None'
                )
            ]
        )
    )

    final_message = f'sport: {123}'

    confirm  = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url='https://example.com/image.jpg',
            title='以下是你輸入的資料，請問都正確嗎？',
            text=final_message,
            actions=[
               PostbackAction(
                    label='正確',
                    display_text='你選擇了「正確」\n將開始爬取資料...',
                    data='type=rent&data=correct'
                ),
                PostbackAction(
                    label='錯誤',
                    display_text='你選擇了「錯誤」\n重新選擇球類運動',
                    data='type=reset&data=None'
                )
            ]
        )
    )

    rent = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url='https://example.com/image.jpg',
            title='要帶你去借場的網站嗎？',
            text='是：會開啟借場網站；否：重新回到初始狀態',
            actions=[
                URIAction(
                    label='是',
                    uri='https://cet.acad.ncku.edu.tw/ste/index.php?c=ste11211'
                ),
                PostbackAction(
                    label='否',
                    display_text='你選擇了「否」',
                    data='type=reset&data=None'
                )
            ]
        )
    )

    if type == 'select_sport':
        line_bot_api.reply_message(reply_token, select_sport)
    elif type == 'select_gender':
        line_bot_api.reply_message(reply_token, select_gender)
    elif type == 'select_day':
        line_bot_api.reply_message(reply_token, select_day)
    elif type == 'select_date_start':
        line_bot_api.reply_message(reply_token, select_date_start)
    elif type == 'select_date_end':
        line_bot_api.reply_message(reply_token, select_date_end)
    elif type == 'confirm':
        line_bot_api.reply_message(reply_token, confirm)
    elif type == 'rent':
        line_bot_api.reply_message(reply_token, rent)
    else:
        line_bot_api.reply_message(reply_token, TextMessage(text="No matching button template TT"))

    return "OK"



"""
def send_image_url(id, img_url):
    pass

def send_button_message(id, text, buttons):
    pass
"""
