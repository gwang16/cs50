from cs50 import SQL # easier to execute SQL commands
from flask import Flask, flash, redirect, render_template, request, session, url_for # web-based application, jinja
from flask_session import Session # track log in status
from passlib.apps import custom_app_context as pwd_context 
from tempfile import gettempdir 

from helpers import *

from passlib.context import CryptContext # password hashing

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# configure hash algorithm
pwd_context = CryptContext(
                schemes=["pbkdf2_sha256", "des_crypt"],
                deprecated="auto",
            )
            
            
@app.route("/")
@login_required
def index():
    portfolio = db.execute("SELECT symbol, SUM(shares) AS shares FROM history WHERE user_id = :id GROUP BY 1 ORDER BY 1", 
            id=session["user_id"])
    cash = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])[0].get("cash")
    
    for stock in portfolio:
        symbol = stock.get("symbol").upper()
        stock["name"] = lookup(symbol).get("name")
        stock["price"] = lookup(symbol).get("price")
        stock["total"] = float(stock["shares"]) * stock["price"]
    
    running_total = float(cash) + sum(stock["total"] for stock in portfolio)
    
    return render_template("index.html", portfolio = portfolio, cash = cash, total = running_total)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # Check for symbol
        if request.form.get("symbol") == None:
            return apology("must provide symbol")
        elif lookup(request.form.get("symbol")) == None:
            return apology("symbol does not exist")
            
        # Check for shares
        if request.form.get("shares") == None:
            return apology("must provide number of shares")
        
        # Current stock price
        price = lookup(request.form.get("symbol")).get("price")
            
        # Amount in bank account
        cash = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])[0].get("cash")
            
        # Check affordability
        if float(price) * float(request.form.get("shares")) > float(cash):
            return apology("we require more minerals")
        
        # Store who, what, how many, how much, when
        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES(:user_id, :symbol, :shares, :price)", 
                    user_id = session["user_id"], symbol = request.form.get("symbol").upper(), 
                    shares = request.form.get("shares"), price = price)
        
        # Reduce cash
        db.execute("UPDATE 'users' SET cash = :cash where id = :id", 
                cash = float(cash) - float(price) * float(request.form.get("shares")), id = session["user_id"])
        
        # redirect to transaction history page
        return redirect(url_for("index"))
        
        
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    
    hist = db.execute("SELECT * FROM history where user_id = :user_id", user_id=session["user_id"])
    return render_template("history.html", history = hist)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # input stock symbol
        if not request.form.get("symbol"):
            return apology("symbol cannot be blank")
        else:
            result = lookup(request.form.get("symbol"))
            return render_template("quoted.html", name= result.get("name"), symbol= result.get("symbol"), price= result.get("price"))
    
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")
    
    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # check for username input
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if not request.form.get("username"):
            return apology("username cannot be blank")
        elif len(rows) == 1:
            return apology("username already exists")
        
        # check for password input
        if not request.form.get("password"):
            return apology("password cannot be blank")
        elif request.form.get("password") != request.form.get("password_r"):
            return apology("passwords do not match")
        
        # insert username and hashed password into database
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hashed)", 
            username=request.form.get("username"), hashed=pwd_context.hash(request.form.get("password")))
        return redirect(url_for("index"))
            
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    
    # implementation is similar to buy
    if request.method == "POST":
        
        # Check for symbol
        if request.form.get("symbol") == None:
            return apology("must provide symbol")
        elif lookup(request.form.get("symbol")) == None:
            return apology("symbol does not exist")
        
            
        # Check for shares
        if request.form.get("shares") == None:
            return apology("must provide number of shares")
            
        # Check for shares in portfolio
        portfolio = db.execute("SELECT symbol, SUM(shares) AS shares FROM history WHERE user_id = :id GROUP BY 1 HAVING symbol = :symbol", 
            id=session["user_id"], symbol = request.form.get("symbol").upper())
        if len(portfolio) < 1:
            return apology("You don't own that stock")
        if float(request.form.get("shares")) > portfolio[0].get("shares"):
            return apology("You don't own that many shares")
        
        # Current stock price
        price = lookup(request.form.get("symbol")).get("price")
            
        # Amount in bank account
        cash = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])[0].get("cash")
            
        # Store who, what, how many, how much, when
        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES(:user_id, :symbol, :shares, :price)", 
                    user_id = session["user_id"], symbol = request.form.get("symbol").upper(), 
                    shares = -1 * float(request.form.get("shares")), price = price)
        
        # Add cash to account
        db.execute("UPDATE 'users' SET cash = :cash where id = :id", 
                cash = float(cash) + float(price) * float(request.form.get("shares")), id = session["user_id"])
        
        # redirect to transaction history page
        return redirect(url_for("index"))
        
        
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("sell.html")


@app.route("/scoreboard", methods=["GET"])
#@login_required
def scoreboard():
    """Create a scoreboard for all registered accounts"""
    
    # get all accounts
    accounts = db.execute("SELECT DISTINCT id FROM users")
        
    # for each account, calculate the sum of its portfolio value and cash        
    for account in accounts:
        
        # portfolio value
        portfolio = db.execute("SELECT symbol, SUM(shares) AS shares FROM history WHERE user_id = :id GROUP BY 1 ORDER BY 1", 
                id= account.get("id"))
        for stock in portfolio:
            symbol = stock.get("symbol").upper()
            stock["price"] = lookup(symbol).get("price")
            stock["total"] = float(stock["shares"]) * stock["price"]
        
        # cash
        users = db.execute("SELECT * FROM users WHERE id = :id", id= account.get("id"))[0]
        cash = users.get("cash")
        
        # total AUM
        account["name"] = users.get("username")
        account["aum"] = float(cash) + sum(stock["total"] for stock in portfolio)
    
    accounts_sorted = sorted(accounts, key=lambda k: k['aum'], reverse = True) 
    return render_template("scoreboard.html", aum = accounts_sorted)
