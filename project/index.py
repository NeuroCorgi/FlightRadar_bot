import json
import logging

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
logging.basicConfig(filename='response.log',
                    level=logging.DEBUG)

vectorizer = Vectorizer(r"\b\w+\b")
with open('project/data/corpus') as study_data:
    lines = [line.split('--$--') for line in study_data.readlines()]
    X, y = [line[0] for line in lines], [int(line[1]) for line in lines]

y = np.array([y])

X = vectorizer.fit_transform(X).toarray()

logging.info(vectorizer.get_feature_names())

classifier = KNNClassifier(neighbors=7)
classifier.fit(X, y)


@app.route('/')
def home():
    return {"result": "ok"}


@app.route('/alice/', methods=["POST"])
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

    req_text_vector = vectorizer.transform(req['request']['original_utterance'])[0]

    themes = classifier.predict(req_text_vector)
    logging.debug(themes)

    theme = max(themes.keys(), key=lambda x: themes[x])

    if theme == -2:
        res['response']['end_session'] = True

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

    return
