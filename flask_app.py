from flask import Flask, request, jsonify
import logging


app = Flask(__name__)

# Устанавливаем уровень логирования
logging.basicConfig(level=logging.INFO)

# Создадим словарь, чтобы для каждой сессии общения
# с навыком хранились подсказки, которые видел пользователь.

sessionStorage = {}
# животные, которые мы хотим продать
animals = ['слона', 'кролика', 'таракана', 'крокодила', 'гиппопотама']


@app.route('/post', methods=['POST'])
# Функция получает тело запроса и возвращает ответ.
def main():
    logging.info(f'Request: {request.json!r}')

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    # Отправляем request.json и response в функцию handle_dialog.
    handle_dialog(request.json, response)

    logging.info(f'Response:  {response!r}')

    return jsonify(response)


def handle_dialog(req, res):
    global animals
    user_id = req['session']['user_id']

    if req['session']['new']:
        sessionStorage[user_id] = {
            'suggests': [
                "Не хочу.",
                "Не буду.",
                "Отстань!",
            ]
        }

        # Заполняем текст ответа
        res['response']['text'] = f'Привет! Купи {animals[0]}!'
        # Получим подсказки
        res['response']['buttons'] = get_suggests(user_id)
        return

    # Сюда дойдем только, если пользователь не новый,
    # и разговор с Алисой уже был начат
    # Обрабатываем ответ пользователя.
    if req['request']['original_utterance'].lower() in [
        'окей',
        'ладно',
        'куплю',
        'покупаю',
        'хорошо'
    ]:
        # Пользователь согласился, прощаемся.
        res['response']['text'] = f'{animals[0].title()} можно найти на Яндекс.Маркете!'

        # убираем первое животное, тк продали
        animals = animals[1::]
        # если всех жвотных продали, то завершаем сессию
        if not animals:
            res['response']['end_session'] = True
        else:
            sessionStorage[user_id] = {
                'suggests': [
                    "Не хочу.",
                    "Не буду.",
                    "Отстань!",
                ]
            }

            # добавляем текст к ответу
            res['response']['text'] += f'\nУ нас ещё есть {animals[0][0:-1]}! Купи {animals[0]}!'
            # Получим подсказки
            res['response']['buttons'] = get_suggests(user_id)
        return

    # Если нет, то убеждаем его купить животное!
    res['response']['text'] = \
        f"Все говорят '{req['request']['original_utterance']}', а ты купи {animals[0]}!"
    res['response']['buttons'] = get_suggests(user_id)


# Функция возвращает две подсказки для ответа.
def get_suggests(user_id):
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests'][:2]
    ]

    # Убираем первую подсказку, чтобы подсказки менялись каждый раз.
    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    # Если осталась только одна подсказка, предлагаем подсказку
    # со ссылкой на Яндекс.Маркет.
    if len(suggests) < 2:
        suggests.append({
            "title": "Ладно",
            "hide": True,
            "url": f"https://market.yandex.ru/search?text={animals[0][0:-1]}",
        })

    return suggests


if __name__ == '__main__':
    app.run()