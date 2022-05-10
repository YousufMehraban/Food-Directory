from flask import Flask, request, session, render_template, redirect, g, flash
from flask_bcrypt import Bcrypt
from models import db, User, FavList
from forms import LoginForm, SignupForm, CurrencyForm
from forex_python.converter import CurrencyRates, CurrencyCodes
import requests

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


@app.route('/', methods=['GET', 'POST'])
def root():
    """display the root page"""
    form = CurrencyForm()
    fav_list = FavList.query.filter(FavList.user_id==g.user).all()
    return render_template('index.html', form=form, fav_list=fav_list)


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

    city = request.args['search']
    cuisine = request.args['cuisine']
    url = 'http://www.mapquestapi.com/geocoding/v1/address'
    params = {'key': 'p5TuSJkVmN7GGIqEuXubL09QIOUYgAft', 'city': city}
    res = requests.get(url, params)
    g = res.json()
    lat = g['results'][0]['locations'][0]['latLng']['lat']
    lng = g['results'][0]['locations'][0]['latLng']['lng']

    url2 = 'https://api.documenu.com/v2/restaurants/search/geo'
    params2 = {'key': '840ec3546d315c15e5f3a06e52c54c3c',
                'lat': lat,
                'lon': lng,
                'distance': 5,
                'cuisine': cuisine}
    res2 = requests.get(url2, params2)
    res2 = res2.json()
    datas = res2['data']

    weather_url = 'http://api.weatherapi.com/v1/current.json'
    weather_params = {'key': '891a3de7056f418485051151220903','q': city }

    w_res = requests.get(weather_url, weather_params)
    w_json = w_res.json()
    name = w_json['location']['name']
    temp = w_json['current']['temp_f']
    cond = w_json['current']['condition']['text']
    icon = w_json['current']['condition']['icon']

    form = CurrencyForm()
    fav_list = FavList.query.filter(FavList.user_id==session[user_key]).all()

    return render_template('index.html', datas = datas, name=name, temp=temp, cond=cond, 
                            icon=icon, form=form, fav_list=fav_list)


@app.route('/users/restaurant/<int:r_id>')
def show_restaurant(r_id):

    url = f'https://api.documenu.com/v2/restaurant/{r_id}'
    header = {'key': '840ec3546d315c15e5f3a06e52c54c3c'}
    res = requests.get(url, header)
    r = res.json()
    res_data = r['result']
    data = r['result']['menus'][0]['menu_sections']
    return render_template('restaurant.html', data = data, res_data=res_data)


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
        
        if from_currency not in currencies or to_currency not in currencies:
            flash('One of the Currency not Supported!')
            return redirect('/')
        else:
            converter = CurrencyRates()
            conversion = round(converter.convert(from_currency, to_currency, amount), 2)

        return render_template('currency.html', form = form, conversion=conversion, 
                                x = from_currency, y = to_currency, a=amount)

    return redirect('/')



@app.route("/users/restaurant/add/<int:r_id>")
def add_restaurant_favorite(r_id):

    url = f'https://api.documenu.com/v2/restaurant/{r_id}'
    header = {'key': '840ec3546d315c15e5f3a06e52c54c3c'}
    res = requests.get(url, header)
    r = res.json()
    restaurant_name = r['result']['restaurant_name']
    city = r['result']['address']['city'] 
    state = r['result']['address']['state']
    cuisine = r['result']['cuisines']
    restaurant_id = r['result']['restaurant_id']

    fav_restaurant = FavList(name=restaurant_name, city=city, state=state, cuisine=cuisine, restaurant_id=restaurant_id, user_id = g.user)
    db.session.add(fav_restaurant)
    db.session.commit()
    return redirect('/')















# ++++++++++++++++++++++++++++++++++++++++++



from flask_wtf import FlaskForm
from wtforms import StringField, SearchField, PasswordField, IntegerField
from wtforms.validators import InputRequired, Email

class LoginForm(FlaskForm):

    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


class SignupForm(FlaskForm):

    username = StringField('Username', validators=[InputRequired()])
    first_name = StringField('First_name')
    last_name = StringField('Last_name')
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


class CurrencyForm(FlaskForm):

    from_currency = StringField('From_Currency', validators=[InputRequired()])
    to_currency = StringField('To_Currency', validators=[InputRequired()])
    amount = IntegerField('Amount', validators=[InputRequired()])
    






    # +++++++++++++++++++++++++++++÷

from unicodedata import name
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False, unique=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)


    @classmethod
    def signup(cls, username, first_name, last_name, email, password):

        hashed_password = bcrypt.generate_password_hash(password)
        decoded_hashed_password = hashed_password.decode('utf-8')

        user = User(username = username, 
                    first_name = first_name, 
                    last_name = last_name, 
                    email = email, 
                    password = decoded_hashed_password)

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        users = [user.username for user in User.query.all()]
        if username in users:
            user = User.query.filter(User.username == username).first()
            if bcrypt.check_password_hash(user.password, password):
                return True
        return False


class FavList(db.Model):

    __tablename__ = 'fav_list'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    state = db.Column(db.String, nullable=False)
    cuisine = db.Column(db.String, default='NA')
    restaurant_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))



# ++++++++++++++++++++++++++++++++++++++++++ base

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>   Food Directory  </title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
    <link rel="stylesheet" href="https://unpkg.com/jasmine-core/lib/jasmine-core/jasmine.css" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.12.0/css/all.min.css">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>

    {% if not g.user %}
    <nav class="navbar navbar-expand-lg navbar-light" style="background-color: #392c01;">
        <img src="/static/Food_directory.jpg" alt="">
        <div class="container-fluid d-flex flex-row-reverse">
            <div class="navbar-nav me-10">
              <a class="btn btn-outline-primary me-2" aria-current="page" href="/users/signup"><strong> Sign Up</strong> </a>
              <a class="btn btn-outline-primary" href="/users/login"> <strong> Log In</strong> </a>
            </div>
        </div>
      </nav>
      <h3 class="position-absolute top-50 start-50 translate-middle text-center">Please log in or sign up to use Food Directory!</h3>

    {% else %}
    <nav class="navbar navbar-expand-lg navbar-light" style="background-color: #392c01;">
        <div class="container-fluid">
          <div class="navbar-nav me-10">
            <img src="/static/Food_directory.jpg" class="me-2" alt="">
            <a href="/users/{{g.user}}" class="me-2"><img src="/static/user.png" alt=""></a>
            <a class="btn btn-outline-primary" href="/users/logout">Log Out</a>
          </div>
            <div class="container-fluid d-flex flex-row-reverse">
              <form action="/users/search" class="d-flex">
                <input class="form-control col-md-6 me-2" type="search" placeholder="Enter a city" name="search">
                <input class="form-control col-md-4 me-2" type="search" placeholder="Enter a cuisine" name="cuisine">
                <button class="btn btn-outline-success" type="submit">Search</button>
              </form>
            </div>
        </div>
    </nav>

    {% endif %}

    
    

    {% block content %}     {% endblock %}


</body>
</html>





# ++++++++++++++++++++++++++++++++++ index

{% extends 'base.html' %}




{% block content %}



    {% for message in get_flashed_messages() %}
        <h3 class="alert alert-danger">{{message}}</h3>
    {% endfor %}


    <div class="grid" id="container">
        <div class="row">
            <div class="col text-center"> 
                <div class="container" id="weather">
                    <b>{{name}}</b> Forecast <br>
                    <b> {{cond}} <img src="{{icon}}" alt=""> {{temp}} <span>&#8457;</span> </b>
                    
                </div>

                <div class="container" id="weather">
                    <h3>Favorite_List</h3>
                    <table class="table">
                        <tr>
                            <th>Name</th>
                            <th>City</th>
                            <th>State</th>
                        </tr>
                        {% for fav in fav_list %}
                        <tr class="w-25">
                            <td><a href="/users/restaurant/{{fav['restaurant_id']}}">{{fav.name}}</a></td>
                            <td>{{fav.city}}</td>
                            <td>{{fav.state}}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>

            </div>
            
            
            <div class="col-7">
                <ul>
                {% for data in datas %}
                
                <li class="gap-3">
                    <a href="/users/restaurant/add/{{data['restaurant_id']}}" class="btn btn-outline-primary btn-sm">Add Fav</a> Restaurant Name: <a href="/users/restaurant/{{data['restaurant_id']}}"><b>{{data['restaurant_name']}} </b></a> | 
                        {% for cuisine in data['cuisines'] %}
                            <i>{{ cuisine }}</i> |
                        {% endfor %}
                        <i>{{data['address']['city']}}</i>

                </li>

                {% endfor %}
                </ul>
            </div>
            
            <div class="col">
                <form action="/users/convert" class="container" method="post"> 
                    {{form.hidden_tag()}}

                    <p><b> Currency Converter </b></p> 
                    {% for field in form if field.widget.input_type != 'hidden' %}
                        {{field.label (class_="form-lable")}}
                        {{field (class_="form-control")}}

                        {% for error in field.errors %}
                            <p>{{error}}</p>
                        {% endfor %}

                    {% endfor %}
                    <button class="btn btn-primary">Convert</button>
                </form>

            </div>
        </div>
    </div>





{% endblock %}





# ++++++++++++++++++++++++++++++++++++++ currency 

{% extends 'base.html' %}




{% block content %}



    {% for message in get_flashed_messages() %}
        <h3 class="alert alert-danger">{{message}}</h3>
    {% endfor %}


    <div class="grid" id="container">
        <div class="row">
            <div class="col text-center"> 
                <div class="container" id="weather">
                <b>{{name}}</b> Forecast <br>
                <b> {{cond}} <img src="{{icon}}" alt=""> {{temp}} <span>&#8457;</span> </b>
                </div>
            </div>
            
            <div class="col-7">
                <ul>
                <!-- {% for data in datas %}
                
                <li>
                    Restaurant Name: <a href="/users/restaurant/{{data['restaurant_id']}}"><b>{{data['restaurant_name']}} </b></a> | 
                        {% for cuisine in data['cuisines'] %}
                            <i>{{ cuisine }}</i> |
                        {% endfor %}
                        <i>{{data['address']['city']}}</i>

                </li>

                {% endfor %} -->
                </ul>
            </div>
            
            <div class="col">
                <form action="/users/convert" class="container" method="post"> 
                    {{form.hidden_tag()}}

                    <p><b> Currency Converter </b></p> 
                    {% for field in form if field.widget.input_type != 'hidden' %}
                        {{field.label (class_="form-lable")}}
                        {{field (class_="form-control")}}

                        {% for error in field.errors %}
                            {{error}}
                        {% endfor %}

                    {% endfor %}
                    <button class="btn btn-primary">Convert</button>
                </form>
                <br>
                <br>
                <h3 class="text-center"> {{a}} {{x}} equals:</h3>
                <h2 class="text-center"><b>{{conversion}}</b> {{y}}</h2>

            </div>
        </div>
    </div>





{% endblock %}


# +++++++++++++++++++++++++++++++++++++ login

{% extends 'base.html' %}


{% block content %}
        {% for message in get_flashed_messages()%}
            <h3 >{{message}}</h3>
        {% endfor %}

    <div class="row justify-content-md-center">
        <div class="col-md-7 col-lg-5">
            <fieldset class="form container">
             
            <form action="/users/login" method="post" class="form">
                {{form.hidden_tag()}}

                {% for field in form if field.widget.input_type != 'hidden' %}
                <p>
                    {{field.label (class_="form-lable")}}
                    {{field (class_="form-control")}}
                    {% for error in field.errors %}
                    {{error}}
                    {% endfor %}
                </p>
                {% endfor %}
                <button class="btn btn-primary">Log In</button>
            </form>
            </fieldset>
        </div>
    </div>
{% endblock %}







# +++++++++++++++++++++++++++++++++++++ singup 
{% extends 'base.html' %}


{% block content %}
        {% for message in get_flashed_messages()%}
            <h3 >{{message}}</h3>
        {% endfor %}

    <div class="row justify-content-md-center">
        <div class="col-md-7 col-lg-5">
            <fieldset class="form container">
             
            <form action="/users/signup" method="post" class="form">
                {{form.hidden_tag()}}

                {% for field in form if field.widget.input_type != 'hidden' %}
                <p>
                    {{field.label (class_="form-lable")}}
                    {{field (class_="form-control")}}
                    {% for error in field.errors %}
                    {{error}}
                    {% endfor %}
                </p>
                {% endfor %}
                <button class="btn btn-primary">Sign Up</button>
            </form>
            </fieldset>
        </div>
    </div>
{% endblock %}








# +++++++++++++++++++++++++++++++++++++ restaurant 
{% extends 'base.html' %}


{% block content %}


<div class="grid" id="container">
    <div class="row">
        <div class="col"></div>
        
        <div class="col-7">
            <h1> Restaurant: <b>{{res_data['restaurant_name']}}</b> </h1>
            <h5> Phone: {{res_data['restaurant_phone']}} </h5>
            <h5> Address: {{res_data['address']['formatted']}} </h5>
            <br>
            <h1>Menu Items</h1>
            <ul>
                {% for n in data %}
                    <h3>{{n['section_name']}}</h3>
                    {% for x in n['menu_items'] %}
                        <li>{{x['name']}}</li>
                    {% endfor %}

                {% endfor %}

            </ul>

        </div>
            
        <div class="col"></div>
    </div>
</div>


{% endblock %}




# +++++++++++++++++++++++++++++++++++++ user 

{% extends 'base.html' %}


{% block content %}

    {% if not g.user %}    
        {% for msg in get_flashed_messages() %}
        <h3 class="alert alert-danger">
            {{msg}}
        </h3> 
        {% endfor %}

    {% else %}
        <div class="row justify-content-md-center">
            <div class="col-md-7 col-lg-5">             
                <h3><ul>
                    <li>
                        First_Name: {{user.first_name.title()}} 
                    </li>
                    <li>
                        Last_Name: {{user.last_name.title()}}   
                    </li>
                </ul>
                </h3>
            </div>
        </div>

    {% endif %}
{% endblock %}


