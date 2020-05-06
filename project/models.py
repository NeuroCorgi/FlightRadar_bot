import math

import numpy


class KNNClassifier:
    """Классиикатор методом ближайших соседей """

    def __init__(self, neighbors):
        self.neigbours = neighbors
        self.M = None
        self.objects = self.classes = None
    
    def _distance(self, a, b):
        """Вычисление Евклидового расстояние между объектами"""
        return math.sqrt(sum((x1 - x2) ** 2 for x1, x2 in zip(a, b)))

    def fit(self, X, y):
        """Запоминание объектов обучающей выборки"""
        self.M = numpy.concatenate((X, y.T), axis=1)
        self.objects = X
        self.classes = y.T
    
    def predict(self, X):
        """Нахождение self.neigbours ближайших соседей и вычисление всзешенного расстояния для их классов"""

        nearest_objects = sorted(self.M, key=lambda obj: self._distance(obj[:-1], X))
        classes = {cls: 0 for cls in nearest_objects[:, -1]}

        for obj in nearest_objects:
            classes[nearest_objects[-1]] += 1 / self._distance(obj[:-1], X)
        
        return max(classes.keys(), key=lambda x: classes[x])


class TextGenerator:

    @staticmethod
    def __call__(pattern: str, data):
        return "working"
