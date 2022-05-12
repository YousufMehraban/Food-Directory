import requests
from flask import flash, redirect
from forex_python.converter import CurrencyRates, CurrencyCodes
from keys.keys import Yelp_API_key, Weather_API_key, AppSecret



def get_weather(city):
    url = 'http://api.weatherapi.com/v1/current.json'
    params = {'key': Weather_API_key,'q': city }
    res = requests.get(url, params)
    res = res.json()
    name = res['location']['name']
    temp = res['current']['temp_f']
    cond = res['current']['condition']['text']
    icon = res['current']['condition']['icon']
    return [name, temp, cond, icon]


def all_businesses_search(city, cuisine):
    url = 'https://api.yelp.com/v3/businesses/search'
    headers = {'Authorization': Yelp_API_key}
    params = {'term': 'restaurants', 'location': city, 'categories': cuisine}

    res_raw = requests.get(url, params, headers=headers)
    result = res_raw.json()
    data = result['businesses']
    return data


def business_search(url, headers):
    res_raw = requests.get(url, headers=headers)
    result = res_raw.json()
    return result



def currency_change(x, y, amount):
    currencies = ['EUR', 'JPY', 'BGN', 'CZK', 'DKK', 'GBP', 'HUF', 'PLN', 'RON', 'SEK', 
                    'CHF', 'ISK', 'NOK', 'HRK', 'TRY', 'AUD', 'BRL', 'CAD', 'CNY', 'HKD', 
                    'IDR', 'INR', 'KRW', 'MXN', 'MYR', 'NZD', 'PHP', 'SGD', 'THB', 'ZAR', 'USD']

    
    if x not in currencies or y not in currencies:
        flash('One of the Currency not Supported!')
        return redirect('/')
    else:
        converter = CurrencyRates()
        conversion = round(converter.convert(x, y, amount), 2)
        return conversion

