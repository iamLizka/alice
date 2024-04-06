from flask import Flask, request, jsonify
import logging
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}
city = None
cities = {
    'лондон': '1030494/cd1247583c03d85a704e',
    'пенза': '213044/e9d0d557178adc5c8b91'
}


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
    global city, cities
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

    if req['request']['command'].lower() == 'да':
        city = random.choice(list(cities.keys()))
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['text'] = ''
        res['response']['card']['title'] = 'Угадай город'
        res['response']['card']['image_id'] = cities[city]
        res['response']['buttons'] = [{'title': 'помощь',
                                       'hide': True}]
        del cities[city]
        return

    if req['request']['command'].lower() == 'нет':
        res['response']['text'] = 'Прощай, друг'
        return

    if req['request']['command'].lower() == 'покажи город на карте':
        res['response']['text'] = 'Сыграем ещё?'
        res['response']['buttons'] = [{'title': 'Да',
                                       'hide': True},
                                      {'title': 'Нет',
                                       'hide': True}
                                      ]
        return

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
            city = random.choice(list(cities.keys()))
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['text'] = 'Угадай город'
            res['response']['card']['image_id'] = cities[city]
            res['response']['buttons'] = [{'title': 'помощь',
                                           'hide': True}]
            del cities[city]


    else:
        if req["request"]["command"] == city:
            if len(cities) < 1:
                res['response']['text'] = 'Верно! Ты превзошел меня, я больше не знаю городов.'
            else:
                res['response']['text'] = 'Верно! Сыграем ещё?'
                res['response']['buttons'] = [{'title': 'Да',
                                               'hide': True},
                                              {'title': 'Нет',
                                               'hide': True},
                                              {'title': 'Покажи город на карте',
                                               'hide': True,
                                               "url": f"https://yandex.ru/maps/?mode=search&text={city.title()}"}
                                              ]
        else:
            res['response']['text'] = 'Неверно! Попробуй еще раз.'


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