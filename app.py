from unittest import result
from flask import Flask, request, session, render_template, redirect, g, flash
from flask_bcrypt import Bcrypt
from models import db, User, FavList
from forms import LoginForm, SignupForm, CurrencyForm
from forex_python.converter import CurrencyRates, CurrencyCodes
import requests
from keys.keys import Yelp_API_key, Weather_API_key, AppSecret
from helper import get_weather, business_search, currency_change, all_businesses_search


app = Flask(__name__)

app.config['SECRET_KEY'] = AppSecret
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///capstone1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

db.app = app
db.init_app(app)

db.create_all()


user_key = 'current_user'

@app.before_request
def add_user_to_g():

    if user_key in session:
        user = User.query.get(session[user_key])
        g.user = user.id
    else:
        g.user = None


@app.route('/', methods=['GET', 'POST'])
def root():
    """displays the root page"""
    
    form = CurrencyForm()
    fav_list = FavList.query.filter(FavList.user_id==g.user).all()
    return render_template('index.html', form=form, fav_list=fav_list)


@app.route('/users/signup', methods=['GET', 'POST'])
def signup():
    """displays new user sign up form"""

    form = SignupForm()

    if form.validate_on_submit():
        username = form.username.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        new_user = User.signup(username=username, 
                                first_name=first_name, 
                                last_name=last_name, 
                                email=email, 
                                password=password)
        db.session.add(new_user)
        db.session.commit()
        session[user_key] = new_user.id
        return redirect('/')

    return render_template('signup.html', form = form)

@app.route('/users/login', methods=['GET', 'POST'])
def login():
    """displays user login form"""

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter(User.username == username).first()
        if user:
            if user.authenticate(username = username, password = password):
                session[user_key] = user.id
                return redirect('/')

    return render_template('login.html', form = form)


@app.route('/users/logout')
def logout():
    """logout user """

    if session[user_key]:
        del session[user_key]
        return redirect('/')

@app.route('/users/<int:user_id>')
def user(user_id):
    
    if not g.user:
        flash('Access Denied', 'danger')
        return redirect('/')

    user = User.query.get(user_id)
    return render_template('user.html', user = user)


@app.route('/users/search')
def search():
    """searches all business providing the specified cuisine in a particular city"""

    city = request.args['search']
    cuisine = request.args['cuisine']

    datas = all_businesses_search(city, cuisine)

    weather_result = get_weather(city)
    name, temp, cond, icon = weather_result

    form = CurrencyForm()
    fav_list = FavList.query.filter(FavList.user_id==session[user_key]).all()

    return render_template('index.html', datas = datas, name=name, temp=temp, cond=cond, 
                            icon=icon, form=form, fav_list=fav_list)


@app.route('/users/restaurant/<id>')
def show_restaurant(id):
    """displays all details of a restaurant"""


    url = f'https://api.yelp.com/v3/businesses/{id}'
    headers = {'Authorization': Yelp_API_key}
    
    result = business_search(url, headers)
    
    form = CurrencyForm()
    fav_list = FavList.query.filter(FavList.user_id==session[user_key]).all()

    return render_template('restaurant.html', result = result, form = form, fav_list=fav_list)


@app.route('/users/convert', methods=['GET', 'POST'])
def convert():
    """currency exchange or converter"""

    form = CurrencyForm()

    if form.validate_on_submit():
        
        from_currency = form.from_currency.data.upper()
        to_currency = form.to_currency.data.upper()
        amount = form.amount.data
        fav_list = FavList.query.filter(FavList.user_id==session[user_key]).all()

        conversion = currency_change(from_currency, to_currency, amount)
        

        return render_template('currency.html', form = form, conversion=conversion, 
                                from_currency = from_currency, to_currency = to_currency, 
                                amount=amount, fav_list=fav_list)

    return redirect('/')



@app.route("/users/restaurant/add/<id>")
def add_restaurant_favorite(id):
    """adding a favorite restaurant to the favorite list and save it into the database"""

    url = f'https://api.yelp.com/v3/businesses/{id}'
    headers = {'Authorization': Yelp_API_key}

    result = business_search(url, headers)
    restaurant_name = result['name']
    city = result['location']['city'] 
    state = result['location']['state']
    restaurant_id = result['id']

    fav_restaurant = FavList(name=restaurant_name, city=city, state=state, restaurant_id=restaurant_id, user_id = g.user)
    db.session.add(fav_restaurant)
    db.session.commit()
    return redirect('/')





