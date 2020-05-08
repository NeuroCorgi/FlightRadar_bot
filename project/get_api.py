from typing import List
from datetime import datetime

from requests import Session

session = Session()
session.headers.update({'User-agent': 'mkorkmaz/FR24/2.0'})


def get_flight_by_dep_arr_city(dep_city, arr_city) -> dict:
    """Получает рейсы по городам валета и посадки"""
    now = datetime.now().timestamp()

    arr_city = arr_city.upper()
    URL = f"http://api.flightradar24.com/common/v1/airport.json?code={dep_city}"
    dep_airport_data = session.get(URL).json()['result']['response']['airport']['pluginData']['schedule']['departures']['data']
    check_destination = lambda flight: flight['flight']['airport']['destination']['code']['iata'] == arr_city
    flights = [flight['flight'] for flight in dep_airport_data if check_destination(flight)]

    for i in range(len(flights)):
        if flights[i]['status']['live']:
            return flights[i]

    abs_ = lambda x: 2 * abs(x) if x < 0 else x
    try:
        return min(flights, key=lambda flight: abs_(flight['time']['scheduled']['departure'] - now))
    except ValueError:
        return {}


def get_flight_by_number(flight_number) -> dict:
    """Получает рейс по его номеру"""
    URL = f"http://api.flightradar24.com/common/v1/flight/list.json?&fetchBy=flight&page=1&limit=25&query={flight_number}"
    flights = session.get(URL).json()['result']['response']['data']
    for i in range(25):
        if flights[i]['status']['live']:
            return flights[i]
        elif flights[i]['status']['text'] != "Scheduled":
            return flights[i - 1]


def get_departures(city) -> list:
    """Получает все вылеты из аэропорта"""
    URL = f"http://api.flightradar24.com/common/v1/airport.json?code={city}"
    dep_airport_data = session.get(URL).json()['result']['response']['airport']['pluginData']['schedule']['departures']
    return dep_airport_data


def get_arrivals(city) -> list:
    """Получает все прибывающие в аэропорт рейсы"""
    URL = f"http://api.flightradar24.com/common/v1/airport.json?code={city}"
    arr_airport_data = session.get(URL).json()['result']['response']['airport']['pluginData']['schedule']['arrivals']
    return arr_airport_data


def translate(text) -> str:
    api_key = "trnsl.1.1.20200508T101107Z.b482f8350bed9bb7.c9f545e58c6b697c6d1c46e5a6ce11c1630ca765"
    tr_text = session.get(f"https://translate.yandex.net/api/v1.5/tr.json/translate?key={api_key}&lang=ru-en&text={text}").json()
    return tr_text['text'][0]


if __name__ == "__main__":
    print(get_flights_by_dep_arr_city("svo", 'mcx'))
