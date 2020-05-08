import re
import math
import logging
from random import choice
from datetime import datetime
from datetime import timedelta

import numpy


class KNNClassifier:
    """Классиикатор методом ближайших соседей """

    def __init__(self, neighbors):
        self.neigbours = neighbors
        self.M = None
        self.objects = self.classes = None
    
    def _distance(self, a, b):
        """Вычисление Евклидового расстояние между объектами"""
        return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))

    def fit(self, X, y):
        """Запоминание объектов обучающей выборки"""
        self.M = numpy.concatenate((X, y.T), axis=1)
        self.objects = X
        self.classes = y.T
    
    def predict(self, X):
        """Нахождение self.neigbours ближайших соседей и вычисление всзешенного расстояния для их классов"""
        X = X.T

        nearest_objects = numpy.array(sorted(self.M, key=lambda obj: self._distance(obj[:-1], X)))
        classes = {cls: 0 for cls in nearest_objects[:, -1]}

        for obj in nearest_objects:
            try:
                classes[obj[-1]] += 1 / self._distance(obj[:-1], X)
            except ZeroDivisionError:
                classes[obj[-1]] += 100
        
        return classes


class TextGenerator:

    def __init__(self, pattern: str, data):
        with open(pattern) as pattern:
            pattern = choice(pattern.read().split('\n\n'))
        self.text = pattern
        self.data = data
    
    def replace_with_data(self):
        get_datetime_obj = lambda x: (datetime.utcfromtimestamp(x) + timedelta(seconds=self.data['airport']['origin']['timezone']['offset']))
        get_date_time = lambda x: str(get_datetime_obj(x).day) + " " + str(get_datetime_obj(x).month) + " " + str(get_datetime_obj(x).time())
        get_time = lambda x: str((datetime.utcfromtimestamp(x) + timedelta(seconds=self.data['airport']['destination']['timezone']['offset'])).time())

        regex = r"{{ ([^\{\}]*) }}"
        command = re.search(regex, self.text)
        while command:
            data = eval(command[1], {}, {'flight': self.data, 'get_date_time': get_date_time, 'get_time': get_time})
            start, end = command.span()
            self.text = self.text[:start] + str(data) + self.text[end:]
            command = re.search(regex, self.text)
        
    def replace_statements(self):
        regex = r"{% if ([^{}]*)%}\n([^{}]*)\n{% else %}\n([^{}]*)\n{% endif %}"
        command = re.search(regex, self.text)
        while command:
            data = command[2] if eval(command[1], {}, {'flight': self.data}) else command[3]
            start, end = command.span()
            self.text = self.text[:start] + data + self.text[end:]
            command = re.search(regex, self.text)
    
    def replace_choices(self):
        regex = r"\[([^\[\]]+)\]"
        command = re.search(regex, self.text)
        while command:
            inner_text = command.group(1)
            start, end = command.span()
            self.text = self.text[:start] + choice(inner_text.split('|')) + self.text[end:]
            command = re.search(regex, self.text)
    
    def to_str(self):
        self.replace_with_data()
        self.replace_statements()
        self.replace_choices()
        return self.text
