from unittest import result
from flask import Flask, request, session, render_template, redirect, g, flash
from flask_bcrypt import Bcrypt
from models import db, User, FavList
from forms import LoginForm, SignupForm, CurrencyForm
from forex_python.converter import CurrencyRates, CurrencyCodes
import requests
from keys.keys import Yelp_API_key, Weather_API_key

app = Flask(__name__)

app.config['SECRET_KEY'] = 'nothing'
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
    """display the root page"""
    
    form = CurrencyForm()
    fav_list = FavList.query.filter(FavList.user_id==g.user).all()
    return render_template('index.html', form=form, fav_list=fav_list)


@app.route('/users/signup', methods=['GET', 'POST'])
def signup():

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


def get_weather(url, params):
    res = requests.get(url, params)
    res = res.json()
    name = res['location']['name']
    temp = res['current']['temp_f']
    cond = res['current']['condition']['text']
    icon = res['current']['condition']['icon']
    return [name, temp, cond, icon]

@app.route('/users/search')
def search():

    city = request.args['search']
    cuisine = request.args['cuisine']

    url = 'https://api.yelp.com/v3/businesses/search'
    headers = {'Authorization': Yelp_API_key}
    params = {'term': 'restaurants', 'location': city, 'categories': cuisine}

    res_raw = requests.get(url, params, headers=headers)
    res = res_raw.json()
    datas = res['businesses']

    weather_url = 'http://api.weatherapi.com/v1/current.json'
    weather_params = {'key': Weather_API_key,'q': city }

    weather_result = get_weather(weather_url, weather_params)
    name, temp, cond, icon = weather_result

    form = CurrencyForm()
    fav_list = FavList.query.filter(FavList.user_id==session[user_key]).all()

    return render_template('index.html', datas = datas, name=name, temp=temp, cond=cond, 
                            icon=icon, form=form, fav_list=fav_list)


@app.route('/users/restaurant/<id>')
def show_restaurant(id):

    url = f'https://api.yelp.com/v3/businesses/{id}'
    headers = {'Authorization': Yelp_API_key}
    res_raw = requests.get(url, headers=headers)
    result = res_raw.json()
    
    form = CurrencyForm()
    fav_list = FavList.query.filter(FavList.user_id==session[user_key]).all()

    return render_template('restaurant.html', result = result, form = form, fav_list=fav_list)


@app.route('/users/convert', methods=['GET', 'POST'])
def convert():

    form = CurrencyForm()
    currencies = ['EUR', 'JPY', 'BGN', 'CZK', 'DKK', 'GBP', 'HUF', 'PLN', 'RON', 'SEK', 
                    'CHF', 'ISK', 'NOK', 'HRK', 'TRY', 'AUD', 'BRL', 'CAD', 'CNY', 'HKD', 
                    'IDR', 'INR', 'KRW', 'MXN', 'MYR', 'NZD', 'PHP', 'SGD', 'THB', 'ZAR', 'USD']

    if form.validate_on_submit():
        
        from_currency = form.from_currency.data.upper()
        to_currency = form.to_currency.data.upper()
        amount = form.amount.data
        fav_list = FavList.query.filter(FavList.user_id==session[user_key]).all()


        if from_currency not in currencies or to_currency not in currencies:
            flash('One of the Currency not Supported!')
            return redirect('/')
        else:
            converter = CurrencyRates()
            conversion = round(converter.convert(from_currency, to_currency, amount), 2)

        return render_template('currency.html', form = form, conversion=conversion, 
                                x = from_currency, y = to_currency, a=amount, fav_list=fav_list)

    return redirect('/')



@app.route("/users/restaurant/add/<id>")
def add_restaurant_favorite(id):

    url = f'https://api.yelp.com/v3/businesses/{id}'
    headers = {'Authorization': Yelp_API_key}
    res_raw = requests.get(url, headers=headers)
    result = res_raw.json()
    restaurant_name = result['name']
    city = result['location']['city'] 
    state = result['location']['state']
    restaurant_id = result['id']

    fav_restaurant = FavList(name=restaurant_name, city=city, state=state, restaurant_id=restaurant_id, user_id = g.user)
    db.session.add(fav_restaurant)
    db.session.commit()
    return redirect('/')



