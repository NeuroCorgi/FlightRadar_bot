import re
import typing
import math
import json

from project.get_api import *
from project.errors import *
from project.models import TextGenerator

from pymorphy2 import MorphAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer


PATH = "project/data/patterns/"


def _match_flight_number(text) -> re.Match:
    regex = r"[a-zа-я0-9]( )?[a-zа-я0-9]( )?[a-zа-я0-9]( )?[a-zа-я0-9]( )?[a-zа-я0-9](( )?[a-zа-я0-9](( )?[a-zа-я0-9])?)?"
    number = re.match(regex, text, re.IGNORECASE)
    return number


def _replace_flight_number(text) -> str:
    number = _match_flight_number(text)
    if number:
        start = number.start()
        stop = number.end()
        text = text[:start] + "flight_number" + text[stop:]
    return text


class Vectorizer(TfidfVectorizer):
    """Веторизатор мешком слов с tf-idf коэффицентом"""

    def __init__(self, pattern):
        super().__init__(token_pattern=pattern)
        self.regex = re.compile(pattern)
        self.morpher = MorphAnalyzer()
        self.lemmatize = lambda token: self.morpher.parse(token)[0].normal_form
    
    def tokenize(self, sent: str) -> typing.List[str]:
        """Удаление стоп слов и лемматизация"""
        sent = _replace_flight_number(sent)
        tokens = self.regex.findall(sent)
        tokens = list(map(lambda token: self.lemmatize(token) if "Geox" not in self.morpher.parse(token)[0].tag and token else "city", tokens))
        return tokens
    
    def fit_transform(self, raw_documents: List[str], y=None):
        """Формирование мешка слов"""
        document = map(lambda sent: ' '.join(self.tokenize(sent)), raw_documents) # Лемматизация
        return super().fit_transform(document, y=y)
    
    def fit(self, raw_sent, y=None):
        """Сопостовление мешка слов вектору"""
        sent = ' '.join(self.tokenize(sent)) # Лемматизация
        return super().fit(sent)


class SideDataParser:
    """Парсер сторонних данных"""

    @staticmethod
    def parse_dep_city(sent):
        try:
            return re.search(r"из \w+", sent)[0][3:]
        except IndexError:
            return "local"
    
    @staticmethod
    def parse_arr_city(sent):
        try:
            return re.search(r"в \w+", sent)[0][2:]
        except IndexError:
            return "local"
    
    @staticmethod
    def parse_flight_number(sent):
        _trans_table = {
            ord('а'): ord('a'), ord('б'): ord('b'), ord('в'): ord('v'),
            ord('г'): ord('g'), ord('д'): ord('d'), ord('е'): ord('e'),
            ord('з'): ord('z'), ord('и'): ord('i'), ord('к'): ord('k'),
            ord('л'): ord('l'), ord('м'): ord('m'), ord('н'): ord('n'),
            ord('о'): ord('o'), ord('п'): ord('p'), ord('с'): ord('s'),
            ord('р'): ord('r'), ord('т'): ord('t'), ord('у'): ord('u'),
            ord('ф'): ord('f'), ord('ю'): ord('y'), ord('э'): ord('e')
        }
        flight_number = _match_flight_number(sent)

        if not flight_number:
            raise FlightNumberError

        flight_number = ''.join(sent[flight_number.start():flight_number.end()].split()).translate(_trans_table)
    

    @staticmethod
    def parse_city_to_airport(city):
        with open("project/data/airports" "w") as json_airports:
            airports = json.load(json_airports)
        
        city_airports = filter(lambda airport: city in airport['name'], airports)

        return [airport['iata'] for airport in city_airports]


class Answer:
    """Генератор ответов"""

    def __init__(self):
        pass

    @staticmethod
    def __call__(theme, text, **req):
        """Возвращает строку с ответом исходя из определённой темы и фразы"""

        if theme == 0:
            return """Просто спросите любую интересующую вас информацию о вылетающих и прибывающих рейсах почти из всех аэропортов мира"""

        elif theme == 1:
            dep_city = SideDataParser.parse_dep_city(text)

            if dep_city == "local":
                dep_city = req['meta']['timezone']
                if dep_city == "UTC":
                    raise DepartureCityError
                else:
                    dep_city = dep_city.split('/')[1]
                
            dep_city = SideDataParser.parse_city_to_airport(dep_city)

            arr_city = SideDataParser.parse_arr_city(text)

            if arr_city == "local":
                arr_city = req['meta']['timezone']
                if arr_city == "UTC":
                    raise ArivalCityError
                else:
                    arr_city = arr_city.split('/')[1]
                
                arr_city = SideDataParser.parse_city_to_airport(arr_city)

            flights = [get_flights_by_dep_arr_city(dep_airport, arr_airport) for dep_airport in dep_city for arr_airport in arr_city]

            return TextGenerator(pattern=PATH + "dep_arr_city_pattern", data=flights)

        elif theme == 2:
            flight_number = SideDataParser.parse_flight_number(text)

            flight = get_flight_by_number(flight_number)

            return TextGenerator(pattern=PATH + "flight_num_pattern", data=flight)
        
        elif theme == 3:
            dep_city = SideDataParser.parse_dep_city(text)

            if dep_city == "local":
                dep_city = req['meta']['timezone']
                if dep_city == "UTC":
                    raise DepartureCityError
                dep_city = dep_city.split('/')[1]
            
            dep_airports = SideDataParser.parse_city_to_airport(dep_city)

            if not dep_airports:
                raise CityNotFound(dep_city)

            flights = [get_departures(dep_airport) for dep_airport in dep_airports]
            
            return TextGenerator(pattern=PATH + "dep_city_pattern", data=flights)

        elif theme == 4:
            arr_city = SideDataParser.parse_arr_city(text)

            if arr_city == "local":
                arr_city = req['meta']['timezone']
                if arr_city == "UTC":
                    raise ArivalCityError
                arr_city = arr_city.split('/')[1]
            
            arr_airports = SideDataParser.parse_city_to_airport(arr_city)

            if not arr_airports:
                raise CityNotFound(arr_city)

            flights = [get_arrivals(arr_airport) for arr_airport in arr_airports]

            return TextGenerator(pattern=PATH + "arr_city_pattern", data=flights)
        
        elif theme == "dep_city_error":
            return TextGenerator(pattern=PATH + "dep_city_error", data=text)
        elif theme == "arr_city_error":
            return TextGenerator(pattern=PATH + "arr_city_error", data=text)
        elif theme == "fl_n_error":
            return TextGenerator(pattern=PATH + "flight_num_error", data=text)
        elif theme == "not_found_error":
            return TextGenerator(pattern=PATH + "not_found_error", data=text)
