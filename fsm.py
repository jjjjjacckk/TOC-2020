from transitions.extensions import GraphMachine

from utils import send_text_message


class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

    # not_login
    def is_going_to_not_login(self, event):
        text = event.message.text
        return text.lower() == "登入"

    def on_enter_not_login(self, event=None):
        print("I'm entering \"not_login\"")

        if event != None:
            reply_token = event.reply_token
            send_text_message(reply_token, "請輸入你的學號")

    def on_exit_not_login(self, event=None):
        print("Leaving not_login")

    # get_ID
    def is_going_to_get_ID(self, event):
        text = event.message.text
        return (text.lower().find('f') != -1 and len(text) == 9)

    def on_enter_get_ID(self, event):
        print("I'm entering \"get_ID\"")

        reply_token = event.reply_token
        send_text_message(reply_token, "請輸入你的密碼\n- 輸入 +++ 能讓你重新輸入學號")

    def on_exit_get_ID(self, event=None):
        print("Leaving get_ID")

    # get_PWD
    def is_going_to_get_PWD(self, event):
        text = event.message.text
        return text.lower() != "+++"

    def on_enter_get_PWD(self, event):
        print("I'm entering \"get_PWD\"")

    def on_exit_get_PWD(self, event=None):
        print("Leaving get_PWD")

    # logged_in
    def on_enter_logged_in(self, event=None):
        print("I'm entering logged_in")

        if event != None:
            reply_token = event.reply_token
            send_text_message(reply_token, "Trigger logged_in")

    def on_exit_logged_in(self, event=None):
        if event != None:
            print(event)
        print("Leaving logged_in")

    # ch_sport
    def is_going_to_ch_sport(self, event=None):
        if event != None:
            text = event.message.text
            return text == "開始查詢"

    def on_enter_ch_sport(self, event=None):
        print("I'm entering ch_sport")

    def on_exit_ch_sport(self, event=None):
        if event != None:
            print(f'\n\nevent: \n{event}\n\n')
        print("Leaving ch_sport")

    # ch_gender
    def on_enter_ch_gender(self, event=None):
        print("I'm entering ch_gender")

    def on_exit_ch_gender(self, event=None):
        if event != None:
            print(f'\n\nevent: \n{event}\n\n')
        print("Leaving ch_gender")
    
    # ch_dates_start
    def on_enter_ch_dates_start(self, event=None):
        print("I'm entering ch_date_tart")
        # self.go_back()

    def on_exit_ch_dates_start(self, event=None):
        if event != None:
            print(f'\n\nevent: \n{event}\n\n')
        print("Leaving ch_date_tart")

    # ch_dates_end
    def on_enter_ch_dates_end(self, event=None):
        print("I'm entering ch_date_end")
        # self.go_back()

    def on_exit_ch_dates_end(self, event=None):
        if event != None:
            print(f'\n\nevent: \n{event}\n\n')
        print("Leaving ch_date_end")
    
    # ch_day
    def on_enter_ch_day(self, event=None):
        print("I'm entering ch_day")

    def on_exit_ch_day(self, event=None):
        if event != None:
            print(f'\n\nevent: \n{event}\n\n')
        print("Leaving ch_day")
    
    # confirm
    def on_enter_confirm(self, event=None):
        print("I'm entering confirm")

    def on_exit_confirm(self, event=None):
        if event != None:
            print(f'\n\nevent: \n{event}\n\n')
        print("Leaving confirm")

    # rent
    def on_enter_rent(self, event=None):
        print("I'm entering rent")

    def on_exit_rent(self, event=None):
        if event != None:
            print(f'\n\nevent: \n{event}\n\n')
        print("Leaving rent")
