from flask import Flask, request, jsonify, abort, Response
import requests
import datetime as dt
from datetime import datetime
import urllib.request
from urllib.request import urlopen
import json
from bs4 import BeautifulSoup
import secrets

app = Flask(__name__)
yahoo_url = "https://finance.yahoo.com/quote/{}?p={}"
finviz_url = "https://finviz.com/chart.ashx?t={}&ty=c&ta=0&p=d&s=l.png"

class Error(Exception):
    pass

class TickerError(Error):
    pass

class RateError(Error):
    pass

@app.route('/', methods=["GET"])
def hello():
    return "<h1>Het is allemaal de schuld van de sossen</h1>"

@app.route('/stockforme', methods=["POST"])
def get_private_stock_info():
    token = request.form.get('token', None)
    command = request.form.get('command', None)
    text = request.form.get('text', None)
    symbol = str(text).upper()

    return get_stock_info(symbol)

@app.route('/stock', methods=["POST"])
def get_public_stock_info():
    token = request.form.get('token', None)
    command = request.form.get('command', None)
    text = request.form.get('text', None)
    response_url = request.form.get('response_url', None)
    symbol = str(text).upper()

    stock_text = get_stock_info(symbol)
    data = {"response_type": "in_channel", "text": stock_text}
    return Response(json.dumps(data), mimetype='application/json')

def get_stock_info(symbol):
    try:
        html = urlopen(yahoo_url.format(symbol, symbol))
        soup = BeautifulSoup(html, "lxml")
        current_stock_info = get_current_data(soup)
        change_emoji = ":chart_with_downwards_trend:" if current_stock_info[1] < 0 else ":chart_with_upwards_trend:"
        if symbol == "SNAP":
            change_emoji += ":xd:"
        pre_market_info = get_pre_market_info(soup)

        graph_url = finviz_url.format(symbol)
        return "*{}* {}\nCURRENT: {}\nCHANGE: {}%\n52W LOW: {}\n52W HIGH: {}\n".format(symbol.upper(), change_emoji, current_stock_info[0], round(current_stock_info[1], 2), current_stock_info[2], current_stock_info[3]) + pre_market_info + graph_url
    except TickerError:
        return "*{}* could not be found!".format(symbol.upper())
    except RateError:
        return "Rate limit reached, please try again later!"

def get_pre_market_info(soup):
    pre_market_info = get_pre_market_data(soup)
    if pre_market_info is not None:
        change_emoji = ":chart_with_downwards_trend:" if pre_market_info[1] < 0 else ":chart_with_upwards_trend:"
        return "*PRE-MARKET* {}\nCURRENT: {}\nCHANGE: {}%\n".format(change_emoji, pre_market_info[0], round(pre_market_info[1], 2))
    else:
        return ""

def get_pre_market_data(soup):
    if len(list(soup.findAll(text="Pre-Market:"))) > 0:
        values = list(soup.findAll(text="Pre-Market:")[0].parent.parent.parent.children)
        pre_market_price = float(values[0].text.replace(",", ""))
        pre_market_change = float(values[4].text.split(" (")[1][:-2])
        return (pre_market_price, pre_market_change)
    else:
        return None

def get_current_data(soup):
    if len(soup.findAll(id="quote-market-notice")) > 0:
        values = list(list(soup.findAll(id="quote-market-notice"))[0].parent.children)
        current_value = float(list(list(soup.findAll(id="quote-market-notice"))[0].parent.parent.children)[0].text.replace(",", ""))
        current_change = float(list(list(soup.findAll(id="quote-market-notice"))[0].parent.children)[0].text.split(" (")[1][:-2])
        year_range = [round(float(el), 2) for el in list(soup.findAll(attrs={"data-test":"FIFTY_TWO_WK_RANGE-value"}))[0].text.split() if el != "-"]
        return (current_value, current_change, year_range[0], year_range[1])
    else:
        raise TickerError

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
