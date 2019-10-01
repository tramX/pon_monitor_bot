from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import telebot
import json
import redis

from app_pon_monitor_bot import models
from app_pon_monitor_bot.situation import situation_worker_classes

settings.BOT.set_webhook(url=settings.WEBHOOK_URL_BASE + settings.WEBHOOK_URL_PATH,
                         certificate=open(settings.WEBHOOK_SSL_CERT, 'r'))


@csrf_exempt
def action(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    update = telebot.types.Update.de_json(body)
    settings.BOT.process_new_updates([update])

    @settings.BOT.message_handler(commands=['start', ])
    def send_welcome(message):
        chat_id = message.chat.id

        if models.User.objects.filter(username=chat_id).count() == 0:
            situation_worker = situation_worker_classes.get('new_registration_client')('new_registration_client',
                                                                                       settings.BOT, message.chat.id,
                                                                                       message)
            situation_worker.start_handler()
        else:
            situation_worker = situation_worker_classes.get('what_info_show')('what_info_show',
                                                                              settings.BOT, message.chat.id,
                                                                              message)
            situation_worker.start_handler()

    @settings.BOT.callback_query_handler(func=lambda message: True)
    def process_step(message):

        action, return_value = message.data.split(':')

        situation = settings.REDIS_SERVER.get(message.from_user.id).decode("utf-8")

        situation_worker = situation_worker_classes.get(situation)(situation, settings.BOT, message.from_user.id,
                                                                   message)
        situation_worker.callback(return_value)

    @settings.BOT.message_handler(func=lambda message: True, content_types=['text'])
    def add_answer(message):
        situation = settings.REDIS_SERVER.get(message.from_user.id).decode("utf-8")

        situation_worker = situation_worker_classes.get(situation)(situation, settings.BOT, message.from_user.id,
                                                                   message)
        situation_worker.text_answer(message.text)

    return JsonResponse({})
