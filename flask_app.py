from flask import Flask, request, jsonify
import logging
import json
import requests
from geopy.distance import geodesic

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# создаем словарь, в котором ключ — название города,
# а.json значение — массив, где перечислены id картинок,
# которые мы записали в прошлом пункте.


# создаем словарь, где для каждого пользователя
# мы будем хранить его имя
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    # если пользователь новый, то просим его представиться.
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем словарь в который в будущем положим имя пользователя
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    if req['request']['command'] == 'помощь':
        res['response']['buttons'] = [{'title': 'продожить',
                                       'hide': True}]

        res['response']['text'] = 'помощи не будет'
        return

    if req['request']['command'] == 'продожить':
        res['response']['text'] = 'Напиши мне город, а я тебе страну, в котором этот город находится.' \
                                  + ' Еще можещь отправить мне 2 города и я посчитаю расстояние между ними.'
        res['response']['buttons'] = [{'title': 'помощь',
                                       'hide': True}]
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, то это говорит о том,
    # что пользователь еще не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' \
                          + first_name.title() \
                          + '. Я - Алиса. Напиши мне город, а я тебе страну, в котором этот город находится.' \
                          + ' Еще можещь отправить мне 2 города и я посчитаю расстояние между ними.'

            res['response']['buttons'] = [{'title': 'помощь',
                                           'hide': True}]

    # если мы знакомы с пользователем и он нам что-то написал,
    # то это говорит о том, что он уже говорит о городе,
    # что хочет увидеть.
    else:
        if len(req["request"]["command"].split()) == 1:
            city = req["request"]["command"]
            country = get_country(city)
            if country:
                res['response']['text'] = f"{city.title()} находится в {country}"
            else:
                res['response']['text'] = 'Не знаю такой город.'

        elif len(req["request"]["command"].split()) == 2:
            city1, city2 = req["request"]["command"].split()
            distance = get_distance(req["request"]["command"].split())
            if distance:
                res['response']['text'] = f"Расстояние между городами {city1.title()} и {city2.title()} - {distance} км"
            else:
                res['response']['text'] = 'Не знаю такие города.'

        else:
            res['response']['text'] = 'Слишком много городов. Я запуталась.'

        res['response']['buttons'] = [{'title': 'помощь',
                                       'hide': True}]


def get_distance(cities):

    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params1 = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": cities[0],
        "format": "json"}

    geocoder_params2 = geocoder_params1.copy()
    geocoder_params2['geocode'] = cities[1]

    response1 = requests.get(geocoder_api_server, params=geocoder_params1)
    response2 = requests.get(geocoder_api_server, params=geocoder_params2)

    if not response1 or not response2:
        return False

    json_response1 = response1.json()
    json_response2 = response2.json()

    try:
        toponym_longitude1, toponym_lattitude1 = json_response1["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]["Point"]["pos"].split(" ")
        toponym_longitude2, toponym_lattitude2 = json_response2["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]["Point"]["pos"].split(" ")
    except:
        return False

    # Создайте кортежи с координатами
    coord_city1 = (toponym_lattitude1, toponym_longitude1)
    coord_city2 = (toponym_lattitude2, toponym_longitude2)

    # Вычислите расстояние между городами
    distance = geodesic(coord_city1, coord_city2).kilometers
    return round(distance, 2)


def get_country(city):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": city,
        "format": "json"}

    response = requests.get(geocoder_api_server, params=geocoder_params)

    if not response:
        return False

    json_response = response.json()
    try:
        country = json_response["response"]["GeoObjectCollection"]["featureMember"][0][
            "GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["Address"]["Components"][0]["name"]
    except:
        return False

    return country


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()