from flask import Flask, redirect, render_template, request, url_for
from analyzer import Analyzer
import helpers
import os
import sys

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search")
def search():

    # validate screen_name
    screen_name = request.args.get("screen_name", "").lstrip("@")
    if not screen_name:
        return redirect(url_for("index"))

    # get screen_name's tweets
    tweets = helpers.get_user_timeline(screen_name, 100)
    if tweets == None:
        return redirect(url_for("index"))
    
    # caculate sentiment ratios
    positives = os.path.join(sys.path[0], "positive-words.txt")
    negatives = os.path.join(sys.path[0], "negative-words.txt")
    analyzer = Analyzer(positives, negatives)

    n_positive, n_negative, n_neutral = 0, 0, 0
    for tweet in tweets:
        score = analyzer.analyze(tweet)
        if score > 0.0:
            n_positive += 1
        elif score < 0.0:
            n_negative += 1
        else:
            n_neutral += 1
            
    n_total = n_positive + n_negative + n_neutral
    positive, negative, neutral = n_positive/n_total, n_negative/n_total, n_neutral/n_total

    # generate chart
    chart = helpers.chart(positive, negative, neutral)

    # render results
    return render_template("search.html", chart=chart, screen_name=screen_name)
