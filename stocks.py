from flask import Flask, request, jsonify, abort, Response
import datetime as dt
from datetime import datetime
import urllib.request
import json
import secrets

app = Flask(__name__)

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
    symbol = str(text).upper()

    stock_text = get_stock_info(symbol)
    data = {"response_type": "in_channel", "text": stock_text}
    return Response(json.dumps(data), mimetype='application/json')


def get_stock_info(symbol):
    current_stock_value = get_current_value(symbol)
    yesterday_close = get_yesterday_close(symbol)
    change = current_stock_value/yesterday_close * 100 - 100

    return "*{}*\nCURRENT: {}\nCHANGE: {}%".format(symbol.upper(), current_stock_value, round(change, 2))


intraday_cache = dict()
def get_current_value(symbol):
    global intraday_cache
    if symbol in intraday_cache and datetime.now() - dt.timedelta(seconds=60) < intraday_cache[symbol][0]:
        return intraday_cache[symbol][1]
    else:
        function = "TIME_SERIES_INTRADAY"
        interval = "1min"
        response = urllib.request.urlopen("https://www.alphavantage.co/query?function={}&symbol={}&interval={}&apikey={}".format(function, symbol, interval, secrets.API_KEY)).read().decode('utf-8')
        data = json.loads(response)
        time_series = data["Time Series (1min)"]
        timestamps = list(time_series.keys())
        formated_times = [dt.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamps]
        formated_times.sort(reverse=True)
        str_times = [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in formated_times]
        last_entry = time_series[str_times[0]]
        current_stock_value = float(last_entry["4. close"])
        intraday_cache[symbol] = (datetime.now(), current_stock_value)
        return current_stock_value


daily_cache = dict()
def get_yesterday_close(symbol):
    global daily_cache
    if symbol in daily_cache and datetime.today().date() == daily_cache[symbol][0]:
        return daily_cache[symbol][1]
    else:
        function = "TIME_SERIES_DAILY"
        response = urllib.request.urlopen("https://www.alphavantage.co/query?function={}&symbol={}&apikey={}".format(function, symbol, secrets.API_KEY)).read().decode('utf-8')
        data = json.loads(response)
        time_series = data["Time Series (Daily)"]
        timestamps = list(time_series.keys())
        formated_times = [dt.datetime.strptime(ts, "%Y-%m-%d") for ts in timestamps]
        formated_times.sort(reverse=True)
        str_times = [ts.strftime("%Y-%m-%d") for ts in formated_times]
        yesterday = time_series[str_times[1]]
        yesterday_close = float(yesterday["4. close"])
        daily_cache[symbol] = (datetime.today().date(), yesterday_close)
        return yesterday_close




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
