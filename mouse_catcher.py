import random
from datetime import datetime
import pytz
from telebot import TeleBot
import settings
import time
from random import randint, choice
from menu_games import mouse_appear
import json

bot_token = settings.BOT_TOKEN
bot = TeleBot(bot_token)
my_id = settings.MY_ID
delay_min = 20 * 60
delay_max = 60 * 60
ratio = 7
time_sleep = 10

with open('params.json', 'r') as file:
    bot_params = json.loads(file.read())
    chats = bot_params["mouse_hunt"]["groups"]
    test_chats = bot_params["mouse_hunt_test"]["groups"]

if settings.TEST_MODE:
    chats = test_chats
    delay_min = 3
    delay_max = 5
    ratio = 5
    time_sleep = 1


def score_counter(chat_id, user_id, score, reaction=None):
    chat_id, user_id = str(chat_id), str(user_id)
    with open('mouse_scores.json') as file:
        scores = json.loads(file.read())
        current_chat = scores["mice_caught"].setdefault(chat_id, {})
        current_user_scores = current_chat.setdefault(user_id, 0)[0]
        scores["mice_caught"][chat_id][user_id][0] += score
        cur_reaction = scores["mice_caught"][chat_id][user_id][1]
        if cur_reaction is None:
            scores["mice_caught"][chat_id][user_id][1] = reaction
        else:
            if reaction is not None:
                scores["mice_caught"][chat_id][user_id][1] = min(cur_reaction, reaction)
    with open('mouse_scores.json', 'w') as file:
        file.write(json.dumps(scores))
    return current_user_scores + score


def save_user(user_id, username):
    with open('users.json', 'r') as file:
        user_list = json.loads(file.read())
    if str(user_id) not in user_list:
        user_list[str(user_id)] = username
        with open('users.json', 'w') as file:
            file.write(json.dumps(user_list))


def get_score(chat_id, user_id):
    with open('mouse_scores.json') as file:
        scores_list = json.loads(file.read())["mice_caught"]
        if str(chat_id) not in scores_list:
            score_counter(chat_id, user_id, 0)
            return 0
        if str(user_id) in scores_list[str(chat_id)]:
            return scores_list[str(chat_id)][str(user_id)][0]
        else:
            return 0


def show_scores(chat_id):
    chat_id = str(chat_id)
    with open('params.json', 'r') as file:
        bot_params = json.loads(file.read())
    if not settings.TEST_MODE:
        chats = bot_params["mouse_hunt"]["groups"]
    else:
        chats = bot_params["mouse_hunt_test"]["groups"]
    mouse_name = chats[chat_id]["names"][0]
    rats_name = chats[chat_id]["names"][1]
    with open('mouse_scores.json') as file:
        scores = json.loads(file.read())["mice_caught"]
    with open('users.json') as file:
        user_list = json.loads(file.read())
    if str(chat_id) not in scores:
        return "В этом чате мышей не ловят"
    scores = scores[chat_id]
    rating = f'<code>Рейтинг охотников на {mouse_name} в чате:\n'
    sorted_scores = sorted(scores, key=scores.get, reverse=True)
    total = sum([int(i[0]) for i in scores.values() if int(i[0]) > 0])
    # total_rats = abs(sum([int(i) for i in scores.values() if int(i) < 0]))

    for id in sorted_scores:
        name = user_list[id]
        points = scores[id][0]
        if points == 0:
            continue
        if points % 100 == 0 or points % 111 == 0:
            points = 0
        if len(name) > 15:
            rating += name.split()[0] + '\n'
            name = ' '.join(name.split()[1:])
        if points > 0:
            rating += f'{name:<15} {points:>4} {points/total:>6.2%}\n'
        else:
            rating += f'{name:<15} {points:>4}\n'
    rating += f'{"—"*30}\nИТОГО: {total} {mouse_name}</code>'
    return rating


def set_raschlenenka(raschlenenka):
    with open('params.json', 'r') as file:
        bot_params = json.loads(file.read())
        if not settings.TEST_MODE:
            bot_params["mouse_hunt"]["raschlenenka"][0] = raschlenenka
            bot_params["mouse_hunt"]["raschlenenka"][1] = time.time() + 24 * 3600.0 - 300
        else:
            bot_params["mouse_hunt_test"]["raschlenenka"][0] = raschlenenka
            bot_params["mouse_hunt_test"]["raschlenenka"][1] = time.time() + 60
    with open('params.json', 'w') as file:
        file.write(json.dumps(bot_params))


def set_shower(state):
    with open('params.json', 'r') as file:
        bot_params = json.loads(file.read())
        if not settings.TEST_MODE:
            bot_params["mouse_hunt"]["liven"][0] = state
        else:
            bot_params["mouse_hunt_test"]["liven"][0] = state
    with open('params.json', 'w') as file:
        file.write(json.dumps(bot_params))

def get_hunt_params():
    with open('params.json', 'r') as file:
        bot_params = json.loads(file.read())
    if not settings.TEST_MODE:
        chats = bot_params["mouse_hunt"]["groups"]
        raschlenenka = bot_params["mouse_hunt"]["raschlenenka"][0]
        raschlenenka_till = bot_params["mouse_hunt"]["raschlenenka"][1]
        liven = bot_params["mouse_hunt"]["liven"][0]

    else:
        chats = bot_params["mouse_hunt_test"]["groups"]
        raschlenenka = bot_params["mouse_hunt_test"]["raschlenenka"][0]
        raschlenenka_till = bot_params["mouse_hunt_test"]["raschlenenka"][1]
        liven = bot_params["mouse_hunt_test"]["liven"][0]
    return chats, raschlenenka, raschlenenka_till, liven


def start_mouse_shower(bot, username, shower_chats):
    N = 20
    for chat in shower_chats:
        chat_mouse_name = chats[chat]["names"][0]
        bot.send_message(chat, f'Спасибо, {username}! '
                               f'В этом чате включен дождик, ловите больше {chat_mouse_name}!')
    while N > 0:
        for chat in shower_chats:
            rnd_mouse = choice(['mouse'] * ratio + ['rat'] * (10 - ratio))
            mouse_appear(bot, chat, rnd_mouse, fast=True)
        N -= 1
    set_shower(False)

    for chat in shower_chats:
        chat_mouse_name = chats[chat]["names"][0]
        bot.send_message(chat, f'Дождик из {chat_mouse_name} закончился! Можно порадоваться радуге и подумать о '
                               f'покупке еще одного.')


if __name__ == '__main__':
    while True:
        msk_zone = pytz.timezone('Europe/Moscow')
        now = datetime.now(tz=msk_zone)

        time.sleep(randint(delay_min, delay_max))
        if 7 <= now.hour < 23:
            _, _, _, shower = get_hunt_params()
            if shower:
                set_shower(False)
            for chat in chats.keys():
                rnd_mouse = choice(['mouse'] * ratio + ['rat'] * (10 - ratio))
                mouse_appear(bot, chat, rnd_mouse)
                time.sleep(time_sleep)

    # with open('params.json', 'r') as file:
    #     bot_params = json.loads(file.read())
    #     # chats = bot_params["mouse_hunt_test"]["groups"]
    # for chat in chats:
    #     # print(chat)
    #     print(show_scores(chat))
    # score_counter(settings.MY_ID, settings.MY_ID, 2)
    # print(get_score(my_id, my_id))
    # save_user(123, 'name')
