import os
import re
import sys
import json
from yahoo_finance import Share

import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    message_to_send = "Error! Type HELP to get a list of commands"
                    try:
                        if re.search(r"(?i)market|cap|capitilazation", message_text) != None:
                            stock_symb = re.sub(r"(?i)market|cap|capitilazation","", message_text)
                            try:
                                stock = Share(stock_symb.strip())
                                log(stock_symb.strip())
                                stock_price = stock.get_market_cap()
                                log(stock_price)
                                if (stock_price == None):
                                    message_to_send = "error"
                                else:
                                    message_to_send = "The Market Capitilization for {} is {}".format(message_text, stock_price)
                            except:
                                message_to_send = "Could not recognize the symbol"
                        elif re.search(r"(?i)open|start", message_text) != None:
                            stock_symb = re.sub(r"(?i)open|start","", message_text)
                            try:
                                stock = Share(stock_symb.strip())
                                log(stock_symb.strip())
                                stock_price = stock.get_open()
                                log(stock_price)
                                if (stock_price == None):
                                    message_to_send = "error"
                                else:
                                    message_to_send = "The opening price for {} is {}".format(message_text, stock_price)
                            except:
                                message_to_send = "Could not recognize the symbol"
                        elif re.search(r"(?i)high", message_text) != None:
                            if re.search(r"(?i)year|52|52 wk|52 week", message_text) != None:
                                stock_symb = re.sub(r"(?i)high|year|52|52 wk|52 week","", message_text)
                                try:
                                    stock = Share(stock_symb.strip())
                                    log(stock_symb.strip())
                                    stock_price = stock.get_year_high()
                                    log(stock_price)
                                    if (stock_price == None):
                                        message_to_send = "error"
                                    else:
                                        message_to_send = "The 52 wk high for {} is {}".format(message_text, stock_price)
                                except:
                                    message_to_send = "Could not recognize the symbol"
                        elif re.search(r"(?i)close", message_text) != None:
                            stock_symb = re.sub(r"(?i)previous|close|for", "", message_text)
                            try:
                                stock_symb = stock_symb.upper()
                                stock = Share(stock_symb)
                                stock_price = stock.get_prev_close()
                                if (stock_price == None):
                                    message_to_send = "error"
                                else:
                                    message_to_send = "The previous close for {} is {}".format(message_text.strip(), stock_price)
                            except:
                                message_to_send = "Could not recognize the symbol"
                        elif message_text == "HELP":
                            message_to_send = "Here is a list of commands"
                        else:
                            stock = Share(message_text)
                            stock_price = stock.get_price()
                            if (stock_price == None):
                                message_to_send = "Please enter a stock symbol, not a company name"
                            else:
                                message_to_send = "The stock price for {} is {}".format(message_text.strip().upper(), stock_price)
                    except:
                        message_to_send = "There was some error in your request, type HELP to get a list of commands"
                    send_message(sender_id, message_to_send)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

if __name__ == '__main__':
    app.run(debug=True)
