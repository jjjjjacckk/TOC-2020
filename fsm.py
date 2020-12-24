from transitions.extensions import GraphMachine

from utils import send_text_message


class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

    # state1
    def is_going_to_state1(self, event):
        text = event.message.text
        return text.lower() == "go to state1"

    def on_enter_state1(self, event):
        print("I'm entering state1")

        reply_token = event.reply_token
        send_text_message(reply_token, "Trigger state1")
        self.go_back()

    def on_exit_state1(self):
        print("Leaving state1")

    # state2
    def is_going_to_state2(self, event):
        text = event.message.text
        return text.lower() == "go to state2"

    def on_enter_state2(self, event):
        print("I'm entering state2")

        reply_token = event.reply_token
        send_text_message(reply_token, "Trigger state2")
        self.go_back()

    def on_exit_state2(self):
        print("Leaving state2")

    # state3
    def is_going_to_state3(self, event):
        text = event.message.text
        return text.lower() == "go to state3"

    def on_enter_state3(self, event):
        print("I'm entering state3")

        reply_token = event.reply_token
        send_text_message(reply_token, "Trigger state3")
        self.go_back()

    def on_exit_state3(self):
        print("Leaving state3")

    # input_dates_start
    def is_going_to_DateStart(self, event):
        text = event.message.text
        return text.lower() == "go to datestart"

    def on_enter_input_dates_start(self, event):
        print("I'm entering DateStart")

        reply_token = event.reply_token
        send_text_message(reply_token, "Trigger DateStart")
        # self.go_back()

    def on_exit_input_dates_start(self, event):
        print(f'\n\nevent: \n{event}\n\n')
        print("Leaving DateStart")

    # input_dates_end
    def is_going_to_DateEnd(self, event):
        text = event.message.text
        return text.lower() == "go to dateend"

    def on_enter_input_dates_end(self, event):
        print("I'm entering DateEnd")

        reply_token = event.reply_token
        send_text_message(reply_token, "Trigger DateEnd")
        # self.go_back()

    def on_exit_input_dates_end(self, event):
        print(type(event))
        print("Leaving DateEnd")
    
    # input_dates_finish
    def is_going_to_DateFinish(self, event):
        text = event.message.text
        return text.lower() == "go to datefinish"

    def on_enter_input_dates_finish(self, event):
        print("I'm entering DateFinish")

        reply_token = event.reply_token
        send_text_message(reply_token, "Trigger DateFinish")
        self.go_back()

    def on_exit_input_dates_finish(self):
        print("Leaving DateFinish")
    