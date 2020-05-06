from typing import List

from requests import Session

session = Session()
session.headers.update({'User-agent': 'mkorkmaz/FR24/2.0'})


def get_flights_by_dep_arr_city(dep_city, arr_city) -> List[dict]:
    """Получает рейсы по городам валета и посадки"""
    arr_city = arr_city.upper()
    URL = f"http://api.flightradar24.com/common/v1/airport.json?code={dep_city}"
    dep_airport_data = session.get(URL).json()['result']['response']['airport']['pluginData']['schedule']['departures']
    check_destination = lambda flight: flight['flight']['airport']['destination']['code']['iata'] == arr_city
    flights = [flight for flight in dep_airport_data if check_destination(flight)]
    return flights


def get_flights_by_airline(air_line) -> List[dict]:
    """Получает рейсы авиокомпании"""
    pass


def get_flight_by_number(flight_number) -> dict:
    """Получает рейс по его номеру"""
    URL = f"http://api.flightradar24.com/common/v1/flight/list.json?&fetchBy=flight&page=1&limit=25&query={flight_number}"
    flights = session.get(URL).json()['response']['data'][0]
    return flights


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
