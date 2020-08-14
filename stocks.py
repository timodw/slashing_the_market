from flask import Flask, request, jsonify, abort, Response
from flask_caching import Cache
import requests
import datetime as dt
from datetime import datetime
import urllib.request
from urllib.request import urlopen
import json
from bs4 import BeautifulSoup
import secrets
import re


CACHE_TIME = 60 * 5 # Five minutes of caching

app = Flask(__name__)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

yahoo_url = "https://finance.yahoo.com/quote/{}?p={}"
finviz_url = "https://finviz.com/chart.ashx?t={}&ty=c&ta=1&p=d&s=l.png"
earnings_url = "https://whenisearnings.com/{}"

class Error(Exception):
    pass

class TickerError(Error):
    pass

class RateError(Error):
    pass

@app.route('/', methods=["GET"])
def hello():
    return "<h1>slashing the market is running</h1>"

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

@app.route('/graph', methods=["POST"])
def get_graph():
    text = request.form.get('text', None)
    symbol = str(text).upper()
    data = {"response_type": "in_channel", "text": finviz_url.format(symbol)}
    return Response(json.dumps(data), mimetype='application/json')

@app.route('/graphforme', methods=["POST"])
def get_private_graph():
    text = request.form.get('text', None)
    symbol = str(text).upper()
    return finviz_url.format(symbol)

@cache.memoize(CACHE_TIME)
def get_stock_info(symbol):
    try:
        html = urlopen(yahoo_url.format(symbol, symbol))
        soup = BeautifulSoup(html, "lxml")
        current_stock_info = get_current_data(soup)
        change_emoji = ":chart_with_downwards_trend:" if current_stock_info[1] < 0 else ":chart_with_upwards_trend:"
        if symbol == "SNAP":
            change_emoji += ":xd:"
        pre_market_info = get_pre_market_info(soup)
        ah_info = get_after_hours_info(soup)

        return "*{}* {}\nCURRENT: {} *{}%*\n52W RANGE: {}-{}\n".format( \
                                                                                        symbol.upper(), \
                                                                                        change_emoji, \
                                                                                        current_stock_info[0], \
                                                                                        format_percentage(current_stock_info[1]), \
                                                                                        current_stock_info[2], \
                                                                                        current_stock_info[3]) + pre_market_info + ah_info
    except TickerError:
        return "*{}* could not be found!".format(symbol.upper())
    except RateError:
        return "Rate limit reached, please try again later!"

def get_pre_market_info(soup):
    pre_market_info = get_pre_market_data(soup)
    if pre_market_info is not None:
        change_emoji = ":chart_with_downwards_trend:" if pre_market_info[1] < 0 else ":chart_with_upwards_trend:"
        return "*PRE-MARKET* {}\nCURRENT: {} *{}%*\n".format(change_emoji, pre_market_info[0], format_percentage(pre_market_info[1]))
    else:
        return ""

def get_after_hours_info(soup):
    ah_info = get_after_hours_data(soup)
    if ah_info is not None:
        change_emoji = ":chart_with_downwards_trend:" if ah_info[1] < 0 else ":chart_with_upwards_trend:"
        return "*AFTER HOURS* {}\nCURRENT: {} *{}%*\n".format(change_emoji, ah_info[0], format_percentage(ah_info[1]))
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

def get_after_hours_data(soup):
    if len(list(soup.findAll(text="After hours:"))) > 0:
        values = list(soup.findAll(text="After hours:")[0].parent.parent.parent.children)
        ah_price = float(values[0].text.replace(",", ""))
        ah_change = float(values[4].text.split(" (")[1][:-2])
        return (ah_price, ah_change)
    else:
        return None

def get_current_data(soup):
    if len(soup.findAll(id="quote-market-notice")) > 0:
        values = re.findall('([0-9,.]+)+', soup.findAll(id="quote-market-notice")[0].parent.text)
        current_value = float(values[0].replace(",", ""))
        current_change = float(values[2])

        year_range = [round(float(el.replace(",", "")), 2) for el in list(soup.findAll(attrs={"data-test":"FIFTY_TWO_WK_RANGE-value"}))[0].text.split() if el != "-"]
        return (current_value, current_change, year_range[0], year_range[1])
    else:
        raise TickerError

def format_percentage(percentage):
    return ("+" if percentage >= 0 else "") + str(round(percentage, 2))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
