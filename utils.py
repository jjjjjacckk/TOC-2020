import os

from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage, \
                           ImageSendMessage, ButtonsTemplate, TemplateSendMessage, \
                           PostbackAction, MessageAction, URIAction


channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)


def send_text_message(reply_token, text):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

    return "OK"

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

def send_button_message(reply_token, type):
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
                PostbackAction(
                    label='籃球',
                    display_text='你選擇了「籃球」',
                    data='type=sport&ball=basket'
                ),
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
                    label='自訂時間',
                    display_text='你選擇了「自訂時間」',
                    data='type=day&day=manual'
                ),
                PostbackAction(
                    label='重新選擇排球場地類型',
                    display_text='你選擇了「重新選擇排球場地類型」',
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

    final = TemplateSendMessage(
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
                ),
            ]
        )
    )

    if type == 'select_sport':
        line_bot_api.reply_message(reply_token, select_sport)
    elif type == 'select_gender':
        line_bot_api.reply_message(reply_token, select_gender)
    elif type == 'select_day':
        line_bot_api.reply_message(reply_token, select_day)
    elif type == 'final':
        line_bot_api.reply_message(reply_token, final)

    return "OK"



"""
def send_image_url(id, img_url):
    pass

def send_button_message(id, text, buttons):
    pass
"""
