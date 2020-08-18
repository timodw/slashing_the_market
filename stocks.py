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


# map things people might try to the correct symbol
symbolmap = {
    'EUR': 'EURUSD=X',
    'USD': 'USDEUR=X',
    'EUR/USD': 'EURUSD=X',
    'USD/EUR': 'USDEUR=X',
    'TESLA': 'TSLA',
    'BTC': 'BTC-USD',
}

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
    symbol = str(text)

    return get_stock_info(symbol)

@app.route('/stock', methods=["POST"])
def get_public_stock_info():
    token = request.form.get('token', None)
    command = request.form.get('command', None)
    text = request.form.get('text', None)
    response_url = request.form.get('response_url', None)
    symbol = str(text)

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
    symbol = symbol.upper()
    if symbol in symbolmap:
        symbol = symbolmap[symbol]
    try:
        html = urlopen(yahoo_url.format(symbol, symbol))
        soup = BeautifulSoup(html, "lxml")
        current_stock_info = get_current_data(soup)
        change_emoji = ":chart_with_downwards_trend:" if current_stock_info[1] < 0 else ":chart_with_upwards_trend:"
        if symbol == "SNAP":
            change_emoji += ":xd:"
        try:
            pre_market_info = get_pre_market_info(soup)
        except:
            print('error getting pre market info')

        return "*{}* {}\nCURRENT: {} *{}%*\n52W RANGE: {}-{}\n".format(
            symbol,
            change_emoji,
            current_stock_info[0],
            format_percentage(current_stock_info[1]),
            current_stock_info[2],
            current_stock_info[3]) + pre_market_info

    except TickerError:
        return "*{}* could not be found!".format(symbol)
    except RateError:
        return "Rate limit reached, please try again later!"

def get_pre_market_info(soup):
    if 'Before hours:' in soup.text:
        pre = 'Before hours'
    elif 'After hours:' in soup.text:
        pre = 'After hours'
    else:
        return ""

    values = list(soup.findAll(text="%s:" % pre)[0].parent.parent.parent.children)
    print(values)
    pre_market_price = float(values[0].text.replace(",", ""))
    pre_market_change = float(values[4].text.split(" (")[1][:-2])
    change_emoji = ":chart_with_downwards_trend:" if pre_market_change < 0 else ":chart_with_upwards_trend:"
    return "*{}* {}\nCURRENT: {} *{}%*\n".format(pre, change_emoji, pre_market_price,
                                                 format_percentage(pre_market_change))

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
