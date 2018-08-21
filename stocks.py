from flask import Flask, request, jsonify, abort, Response
import datetime as dt
import urllib.request
import json
import secrets

app = Flask(__name__)

@app.route('/stockforme', methods=["POST"])
def get_private_stock_info():
    token = request.form.get('token', None)
    command = request.form.get('command', None)
    text = request.form.get('text', None)

    return get_stock_info(text)

@app.route('/stock', methods=["POST"])
def get_public_stock_info():
    token = request.form.get('token', None)
    command = request.form.get('command', None)
    text = request.form.get('text', None)
    
    stock_text = get_stock_info(text)
    data = {"response_type": "in_channel", "text": stock_text}
    return Response(json.dumps(data), mimetype='application/json')

def get_stock_info(symbol):
    function = "TIME_SERIES_INTRADAY"
    interval = "1min"
    key = secrets.API_KEY
    response = urllib.request.urlopen("https://www.alphavantage.co/query?function={}&symbol={}&interval={}&apikey={}".format(function, symbol, interval, key)).read().decode('utf-8')
    data = json.loads(response)
    time_series = data["Time Series (1min)"]
    timestamps = list(time_series.keys())
    formated_times = [dt.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamps]
    formated_times.sort(reverse=True)
    str_times = [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in formated_times]
    last_entry = time_series[str_times[0]]
    current_stock_value = float(last_entry["4. close"])

    function = "TIME_SERIES_DAILY"
    response = urllib.request.urlopen("https://www.alphavantage.co/query?function={}&symbol={}&apikey={}".format(function, symbol, key)).read().decode('utf-8')
    data = json.loads(response)
    time_series = data["Time Series (Daily)"]
    timestamps = list(time_series.keys())
    formated_times = [dt.datetime.strptime(ts, "%Y-%m-%d") for ts in timestamps]
    formated_times.sort(reverse=True)
    str_times = [ts.strftime("%Y-%m-%d") for ts in formated_times]
    yesterday = time_series[str_times[1]]
    yesterday_close = float(yesterday["4. close"])

    change = current_stock_value/yesterday_close * 100 - 100

    return "*{}*\nCURRENT: {}\nCHANGE: {}%".format(symbol.upper(), current_stock_value, round(change, 2))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
