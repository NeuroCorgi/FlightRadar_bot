import re
import typing
import math
import json
import logging

from project.get_api import *
from project.errors import *
from project.models import TextGenerator

from pymorphy2 import MorphAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer

PATH = "project/data/"


def _match_flight_number(text):
    regex = r"\b[a-zа-я0-9]( )?[a-zа-я0-9](( )?[0-9]){2,5}\b"
    number = re.search(regex, text, re.IGNORECASE)
    return number


def _replace_flight_number(text) -> str:
    """Заменяет номер рейса на заглушку flight_number"""
    number = _match_flight_number(text)
    if number:
        start = number.start()
        end = number.end()
        text = text[:start] + "flight_number" + text[end:]
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
    
    def transform(self, raw_sent, y=None):
        """Сопостовление мешка слов вектору"""
        sent = ' '.join(self.tokenize(raw_sent)) # Лемматизация
        return super().transform([sent]).toarray()


class SideDataParser:
    """Парсер сторонних данных"""

    @staticmethod
    def parse_dep_city(sent):
        try:
            return re.search(r"из \w+", sent)[0][3:]
        except TypeError:
            return "local"
    
    @staticmethod
    def parse_arr_city(sent):
        try:
            return re.search(r"в \w+", sent)[0][2:]
        except TypeError:
            return "local"
    
    @staticmethod
    def parse_flight_number(sent):
        _trans_table = {
            ord('а'): ord('a'), ord('б'): ord('b'), ord('в'): ord('v'),
            ord('г'): ord('g'), ord('д'): ord('d'), ord('е'): ord('e'),
            ord('з'): ord('z'), ord('и'): ord('i'), ord('к'): ord('k'),
            ord('л'): ord('l'), ord('м'): ord('m'), ord('н'): ord('n'),
            ord('о'): ord('o'), ord('п'): ord('p'), ord('с'): ord('s'),
            ord('р'): ord('r'), ord('т'): ord('t'), ord('у'): ord('y'),
            ord('ф'): ord('f'), ord('ю'): ord('u'), ord('э'): ord('e'),
            ord(' '): None
        }
        flight_number = _match_flight_number(sent)
        return flight_number[0].translate(_trans_table)
    

    @staticmethod
    def parse_city_to_airport(city):
        with open(PATH + "airports.json") as json_airports:
            airports = json.load(json_airports)

        city = translate(MorphAnalyzer().parse(city)[0].normal_form.lower())[0]
        print(city)
        
        city_airports = filter(lambda airport: city in airport['name'].lower(), airports)

        return [airport['iata'] for airport in city_airports]


def Answer(theme, text=None, **req):
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
        
        print(arr_city)

        flights = [get_flights_by_dep_arr_city(dep_airport, arr_airport) for dep_airport in dep_city for arr_airport in arr_city]
        print(flights)

        return TextGenerator(pattern=PATH + "patterns/flight_pattern", data=flights).to_str()

    elif theme == 2:
        flight_number = SideDataParser.parse_flight_number(text)

        if not flight_number:
            raise FlightNumberError
    
        logging.debug("Flight info: %s" % flight_number)

        flight = get_flight_by_number(flight_number)

        return TextGenerator(pattern=PATH + "patterns/flight_pattern", data=flight).to_str()
    
    elif theme == "dep_city_error":
        return TextGenerator(pattern=PATH + "patterns/dep_city_error", data=text).to_str()
    elif theme == "arr_city_error":
        return TextGenerator(pattern=PATH + "patterns/arr_city_error", data=text).to_str()
    elif theme == "fl_n_error":
        return TextGenerator(pattern=PATH + "patterns/flight_num_error", data=text).to_str()
    elif theme == "not_found_error":
        return TextGenerator(pattern=PATH + "patterns/not_found_error", data=text).to_str()
