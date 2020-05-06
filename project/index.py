import json
import logging

import schedule

from project.errors import *
from project.models import KNNClassifier
from project.parser import (
    Vectorizer,
    Answer
)


from flask import (
    Flask,
    request
)
import numpy as np

app = Flask(__name__)

vectorizer = Vectorizer(r"\b\w+\b")
with open('project/data/corpus') as study_data:
    lines = [line.split('--$--') for line in study_data.readlines()]
    X, y = [line[0] for line in lines], [int(line[1]) for line in lines]

y = np.array([y])

X = vectorizer.fit_transform(X).toarray()
print(X, y)
print(X.shape)
print(y.shape)

classifier = KNNClassifier(neighbors=3)
classifier.fit(X, y)


@app.route('/alice/')
def alice():
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_alice_dialog(request.json, response)

    logging.info(f'Response:  {response!r}')

    return json.dumps(response)


def handle_alice_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = Answer(theme=0)
        return

    req_text_vector = vectorizer.git(req['request']['original_utterance'])

    theme = classifier.predict(req_text_vector)
    print(theme)

    try:
        res['response']['text'] = Answer(theme, text=req['request']['original_utterance'], **req)
    except DepartureCityError:
        res['response']['text'] = Answer("dep_city_error")
    except ArivalCityError:
        res['response']['text'] = Answer("arr_city_error")
    except CityNotFound as e:
        res['response']['text'] = Answer('not_found_error', text=e)
    except FlightNumberError:
        res['response']['text'] = Answer("fl_n_error")
    

    if req['request']['original_utterance'].lower() in ['ладно', 'куплю', 'покупаю', 'хорошо']:
        res['response']['text'] = 'Слона можно найти на Яндекс.Маркете!'
        res['response']['end_session'] = True
        return



if __name__ == '__main__':
    app.run()
