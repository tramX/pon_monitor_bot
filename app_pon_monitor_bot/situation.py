import telebot
from django.conf import settings
from django.utils.crypto import get_random_string

from app_pon_monitor_bot.reply_keyboards import keyboard_entities
from app_pon_monitor_bot.models import User, Client, Organization, MikroTik, BDCOM
from django.contrib.auth.models import Permission
import time
import re
import asyncio
from threading import Thread

from app_pon_monitor_bot.action_mikrotik import ActionMikroTik
from app_pon_monitor_bot.action_bdcom import PonSNMP

messages = {
    'new_registration_client': 'Вы тут впервые. Какое действие желаете выполнить?',
    'new_registration_client_add_to_org': 'Введите идентификатор организации, к которой вы желаете присоедениться, '
                                          'а также имя и фамилию через двоеточие например: '
                                          'c6c489eb-473c-4ff1-bbb6-94f5918cf060:Иван:Иванов ',
    'new_registration_client_add_to_org_no_org': 'Вы ввели не действительный ID',
    'new_registration_client_reg_org': 'Укажите название новой организации',
    'what_info_show': 'Какую информацию отображать?',
    'mikrotik_action': 'ВЫберете одно из действий',
    'bdcom_action': 'Выберете одно из действий',
    'mikrotik_list': 'Выберете одно устройство из списка',
    'bdcom_list': 'Выберете одно устройство из списка',
    'mikrotik_ppp_active_find': 'Введите данные для поиска',
    'mikrotik_client_info': 'Введите логин клиента',
    'mikrotik_client_ping': 'Введите ip, например 172.16.4.27',
    'bdcom_find_mac': 'Введите МАС для поиска'
}


async def send_after_message(bot, chat_id, message):
    await
    asyncio.sleep(2)
    msg = bot.send_message(chat_id, message)


def get_message(situation):
    return messages.get(situation)


class SituationWorker:
    def __init__(self, situation, bot, chat_id, bot_message):
        self.situation = situation
        self.bot = bot
        self.chat_id = chat_id
        self.bot_message = bot_message
        settings.REDIS_SERVER.set(chat_id, situation)

    def create_button(self, button):
        return telebot.types.InlineKeyboardButton(text=button.get('title'),
                                                  callback_data='{}:{}'.format(button.get('slug'),
                                                                               button.get('return_value')))

    def current_situation_update(self, situation):
        settings.REDIS_SERVER.set(self.chat_id, situation)

    def get_keyboard(self):
        if keyboard_entities.get(self.situation):
            bot_keyboard = telebot.types.InlineKeyboardMarkup()

            keyboard_list = keyboard_entities.get(self.situation)

            for button_row in keyboard_list:
                bot_keyboard.add(
                    *[self.create_button(button) for button in button_row])
            return bot_keyboard

    def start_handler(self):

        if self.get_keyboard():
            msg = self.bot.send_message(self.chat_id, get_message(self.situation), reply_markup=self.get_keyboard())
        else:
            msg = self.bot.send_message(self.chat_id, get_message(self.situation))

    def callback(self, value):
        if self.get_keyboard():
            msg = self.bot.send_message(self.chat_id, get_message(self.situation), reply_markup=self.get_keyboard())
        else:
            msg = self.bot.send_message(self.chat_id, get_message(self.situation))

    def text_answer(self, value):
        print(value)


class SituationNewClient(SituationWorker):

    def callback(self, value):
        if value == 'new_org':
            msg = self.bot.send_message(self.chat_id, get_message('new_registration_client_reg_org'))
            self.current_situation_update('new_registration_client_reg_org')

        if value == 'add_to_org':
            msg = self.bot.send_message(self.chat_id, get_message('new_registration_client_add_to_org'))
            self.current_situation_update('new_registration_client_add_to_org')


class SituationClientAddToOrg(SituationWorker):
    def text_answer(self, value):
        try:
            org_id, first_name, last_name = value.split(':')
            organization = Organization.objects.get(org_id=org_id)
            password = get_random_string()
            user = User.objects.create_user(self.chat_id, email='{}@telegram.ru'.format(self.chat_id),
                                            password=password)
            user.is_active = True
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            client = Client.objects.create(user=user)
            organization.employees.add(client)
            organization.save()

            msg = self.bot.send_message(self.chat_id, 'Вы добавленны как сотрудник данной организации, '
                                                      'ожидайте одобрения администратором')
            msg = self.bot.send_message(organization.own.user.username, 'К организации присоеденился новый сотрудник.')
            situation_worker = situation_worker_classes.get('what_info_show')('what_info_show', self.bot, self.chat_id,
                                                                              self.bot_message)
            situation_worker.start_handler()
        except:
            msg = self.bot.send_message(self.chat_id, 'Организации не существует, попробуйте еще раз')


class SituationClientRegOrg(SituationWorker):

    def text_answer(self, value):
        permission_list = ['add_bdcom', 'change_bdcom', 'delete_bdcom', 'change_client', 'add_message',
                           'change_message', 'delete_message', 'add_mikrotik', 'change_mikrotik', 'delete_mikrotik',
                           'add_organization', 'change_organization', 'delete_organization']

        password = get_random_string()
        user = User.objects.create_user(self.chat_id, email='{}@telegram.ru'.format(self.chat_id), password=password)
        user.is_staff = True
        user.is_active = True
        user.first_name = 'Admin'
        user.last_name = 'Admin'
        for permission in Permission.objects.all():
            if permission.codename in permission_list:
                user.user_permissions.add(permission)
        user.save()
        client = Client.objects.create(user=user, approved=True)
        organization = Organization.objects.create(title=value, own=client)
        organization.employees.add(client)
        organization.save()
        msg = self.bot.send_message(self.chat_id, 'Организация создана. Перейдите в панель администрирования '
                                                  'http://monitor.bridge.biz.ua/admin/ ваш логин: {} ваш пароль: '
                                                  '{}'.format(self.chat_id, password))


class SituationWhatInfoShow(SituationWorker):

    def callback(self, value):
        if value == 'mikrotik':
            situation_worker = situation_worker_classes.get('mikrotik_list')('mikrotik_list', self.bot, self.chat_id,
                                                                             self.bot_message)
            situation_worker.start_handler()

        if value == 'bdcom':
            situation_worker = situation_worker_classes.get('bdcom_list')('bdcom_list', self.bot, self.chat_id,
                                                                          self.bot_message)
            situation_worker.start_handler()

        if value == 'find_mac':
            situation_worker = situation_worker_classes.get('bdcom_find_mac')('bdcom_find_mac',
                                                                              self.bot, self.chat_id,
                                                                              self.bot_message)
            situation_worker.start_handler()


class SituationMikroTikActions(SituationWorker):

    def callback(self, value):

        mikrotik_id = settings.REDIS_SERVER.get('mikrotik_{}'.format(self.chat_id)).decode("utf-8")
        mikrotik = MikroTik.objects.get(id=mikrotik_id)
        try:
            action_mikrotik = ActionMikroTik(mikrotik)
        except:
            msg = self.bot.send_message(self.chat_id, 'Устройство в данный момент не доступна')

        if value == 'ppp_active':
            message = ''
            active_ppps = action_mikrotik.get_ppp_active()
            msg = self.bot.send_message(self.chat_id, 'Всего подключено {}'.format(len(active_ppps)))

            for ppp in active_ppps:
                message += ' {}={}'.format(ppp[0], ppp[1])

                if len(message) > 900:
                    # msg = self.bot.send_message(self.chat_id, message)
                    ioloop = asyncio.new_event_loop()
                    asyncio.set_event_loop(ioloop)
                    tasks = [
                        ioloop.create_task(send_after_message(self.bot, self.chat_id, message))]
                    wait_tasks = asyncio.wait(tasks)
                    ioloop.run_until_complete(wait_tasks)
                    ioloop.close()
                    message = ''

            if message != '':
                ioloop = asyncio.new_event_loop()
                asyncio.set_event_loop(ioloop)
                tasks = [
                    ioloop.create_task(send_after_message(self.bot, self.chat_id, message))]
                wait_tasks = asyncio.wait(tasks)
                ioloop.run_until_complete(wait_tasks)
                ioloop.close()

            situation_worker = situation_worker_classes.get('what_info_show')('what_info_show', self.bot, self.chat_id,
                                                                              self.bot_message)
            situation_worker.start_handler()

        if value == 'ppp_active_find':
            situation_worker = situation_worker_classes.get('mikrotik_ppp_active_find')('mikrotik_ppp_active_find',
                                                                                        self.bot, self.chat_id,
                                                                                        self.bot_message)
            situation_worker.start_handler()

        if value == 'mikrotik_client_ping':
            situation_worker = situation_worker_classes.get('mikrotik_client_ping')('mikrotik_client_ping',
                                                                                    self.bot, self.chat_id,
                                                                                    self.bot_message)
            situation_worker.start_handler()

        if value == 'arp':
            message = ''
            arp_records = action_mikrotik.get_arp()
            msg = self.bot.send_message(self.chat_id, 'Всего записей {}'.format(len(arp_records)))
            for arp_record in arp_records:
                message += ' {}={}'.format(arp_record[0], arp_record[1])

                if len(message) > 900:
                    # msg = self.bot.send_message(self.chat_id, message)
                    ioloop = asyncio.new_event_loop()
                    asyncio.set_event_loop(ioloop)
                    tasks = [
                        ioloop.create_task(send_after_message(self.bot, self.chat_id, message))]
                    wait_tasks = asyncio.wait(tasks)
                    ioloop.run_until_complete(wait_tasks)
                    ioloop.close()
                    message = ''

            if message != '':
                ioloop = asyncio.new_event_loop()
                asyncio.set_event_loop(ioloop)
                tasks = [
                    ioloop.create_task(send_after_message(self.bot, self.chat_id, message))]
                wait_tasks = asyncio.wait(tasks)
                ioloop.run_until_complete(wait_tasks)
                ioloop.close()

            situation_worker = situation_worker_classes.get('what_info_show')('what_info_show', self.bot, self.chat_id,
                                                                              self.bot_message)
            situation_worker.start_handler()

        if value == 'mikrotik_client_info':
            situation_worker = situation_worker_classes.get('mikrotik_client_info')('mikrotik_client_info',
                                                                                    self.bot, self.chat_id,
                                                                                    self.bot_message)
            situation_worker.start_handler()


class SituationBDCOMActions(SituationWorker):

    def callback(self, value):
        bdcom_id = settings.REDIS_SERVER.get('bdcom_{}'.format(self.chat_id)).decode("utf-8")
        bdcom_obj = BDCOM.objects.get(id=bdcom_id)
        pon_snmp = PonSNMP(bdcom_obj.ip_address, bdcom_obj.snmp_public, bdcom_obj.snmp_private)

        if value == 'active_onu':

            message = ''

            onu_list = pon_snmp.onu_in_interfaces_online(bdcom_obj.port_count)

            for k in onu_list.keys():
                message += ' {}={}'.format(k, len(onu_list.get(k)))

            msg = self.bot.send_message(self.chat_id, message)
            situation_worker = situation_worker_classes.get('what_info_show')('what_info_show', self.bot, self.chat_id,
                                                                              self.bot_message)
            situation_worker.start_handler()

        if value == 'all_onu':
            message = ''

            all_onu = pon_snmp.get_all_onu_mac_address()

            if all_onu:

                msg = self.bot.send_message(self.chat_id, 'Всего ONU {}'.format(len(all_onu)))

                for onu_id, onu_mac in all_onu:
                    message += ' {}->{}'.format(onu_id, onu_mac)

                    if len(message) > 900:
                        # msg = self.bot.send_message(self.chat_id, message)
                        ioloop = asyncio.new_event_loop()
                        asyncio.set_event_loop(ioloop)
                        tasks = [
                            ioloop.create_task(send_after_message(self.bot, self.chat_id, message))]
                        wait_tasks = asyncio.wait(tasks)
                        ioloop.run_until_complete(wait_tasks)
                        ioloop.close()
                        message = ''

                if message != '':
                    ioloop = asyncio.new_event_loop()
                    asyncio.set_event_loop(ioloop)
                    tasks = [
                        ioloop.create_task(send_after_message(self.bot, self.chat_id, message))]
                    wait_tasks = asyncio.wait(tasks)
                    ioloop.run_until_complete(wait_tasks)
                    ioloop.close()

                situation_worker = situation_worker_classes.get('what_info_show')('what_info_show', self.bot,
                                                                                  self.chat_id,
                                                                                  self.bot_message)
                situation_worker.start_handler()
            else:
                msg = self.bot.send_message(self.chat_id, 'Нет связи')


class SituationMikroTikList(SituationWorker):
    def get_keyboard(self):
        bot_keyboard = telebot.types.InlineKeyboardMarkup()

        li = []
        keyboard_list = []

        user = User.objects.get(username=self.chat_id)

        for c in user.client_profile.filter(approved=True):
            for org in c.employees_org.all():
                for mikrotik in org.org_mikrotiks.all():
                    li.append(
                        {'slug': 'mikrotik_list', 'title': mikrotik.title, 'return_value': mikrotik.id})

        keyboard_list.append(li)

        for button_row in keyboard_list:
            bot_keyboard.add(
                *[self.create_button(button) for button in button_row])

        return bot_keyboard

    def callback(self, value):
        settings.REDIS_SERVER.set('mikrotik_{}'.format(self.chat_id), value)
        situation_worker = situation_worker_classes.get('mikrotik_action')('mikrotik_action', self.bot, self.chat_id,
                                                                           self.bot_message)
        situation_worker.start_handler()


class SituationBdcomikList(SituationWorker):
    def get_keyboard(self):
        bot_keyboard = telebot.types.InlineKeyboardMarkup()

        li = []
        keyboard_list = []

        user = User.objects.get(username=self.chat_id)

        for c in user.client_profile.filter(approved=True):
            for org in c.employees_org.all():
                for bdcom in org.org_bdcoms.all():
                    li.append(
                        {'slug': 'bdcom_list', 'title': bdcom.title, 'return_value': bdcom.id})

        keyboard_list.append(li)

        for button_row in keyboard_list:
            bot_keyboard.add(
                *[self.create_button(button) for button in button_row])

        return bot_keyboard

    def callback(self, value):
        settings.REDIS_SERVER.set('bdcom_{}'.format(self.chat_id), value)
        situation_worker = situation_worker_classes.get('bdcom_action')('bdcom_action', self.bot, self.chat_id,
                                                                        self.bot_message)
        situation_worker.start_handler()


class SituationPPPActiveFind(SituationWorker):
    def text_answer(self, value):
        mikrotik_id = settings.REDIS_SERVER.get('mikrotik_{}'.format(self.chat_id)).decode("utf-8")
        mikrotik = MikroTik.objects.get(id=mikrotik_id)
        try:
            action_mikrotik = ActionMikroTik(mikrotik)
        except:
            msg = self.bot.send_message(self.chat_id, 'Устройство в данный момент не доступна')

        message = ''

        for ppp_name, ppp_time in action_mikrotik.get_ppp_active():
            if re.search(r'{}'.format(value), ppp_name) != None:
                message += ' {}'.format(ppp_name)
                if len(message) > 100:
                    # msg = self.bot.send_message(self.chat_id, message)
                    ioloop = asyncio.new_event_loop()
                    asyncio.set_event_loop(ioloop)
                    tasks = [
                        ioloop.create_task(send_after_message(self.bot, self.chat_id, message))]
                    wait_tasks = asyncio.wait(tasks)
                    ioloop.run_until_complete(wait_tasks)
                    ioloop.close()
                    message = ''
                    # time.sleep(2)

        if message != '':
            msg = self.bot.send_message(self.chat_id, message)

        situation_worker = situation_worker_classes.get('what_info_show')('what_info_show', self.bot, self.chat_id,
                                                                          self.bot_message)
        situation_worker.start_handler()


class SituationMikroTikClientInfo(SituationWorker):
    def text_answer(self, value):
        mikrotik_id = settings.REDIS_SERVER.get('mikrotik_{}'.format(self.chat_id)).decode("utf-8")
        mikrotik = MikroTik.objects.get(id=mikrotik_id)

        try:
            action_mikrotik = ActionMikroTik(mikrotik)
        except:
            msg = self.bot.send_message(self.chat_id, 'Устройство в данный момент не доступна')

        message = ''

        client_info = action_mikrotik.get_client_info(value)

        if client_info.get('login'):
            message += ' Логин - {} '.format(client_info.get('login'))
            message += ' Пароль - {}'.format(client_info.get('password'))
            message += ' IP - {}'.format(client_info.get('ip'))
            message += ' ARP - {}'.format(client_info.get('arp'))
            message += ' Время работы - {}'.format(client_info.get('uptime'))
            message += ' Разрешен в '

            for list, ip in client_info.get('address_list'):
                message += ',{}'.format(list)

            msg = self.bot.send_message(self.chat_id, message)
        else:
            msg = self.bot.send_message(self.chat_id, 'Клиент не найден')

        situation_worker = situation_worker_classes.get('what_info_show')('what_info_show', self.bot, self.chat_id,
                                                                          self.bot_message)
        situation_worker.start_handler()


class SituationPing(SituationWorker):
    def text_answer(self, value):
        mikrotik_id = settings.REDIS_SERVER.get('mikrotik_{}'.format(self.chat_id)).decode("utf-8")
        mikrotik = MikroTik.objects.get(id=mikrotik_id)
        try:
            action_mikrotik = ActionMikroTik(mikrotik)
        except:
            msg = self.bot.send_message(self.chat_id, 'Устройство в данный момент не доступна')

        message = ''

        for ping_responae in action_mikrotik.ping(value):

            message += '{}\n'.format(ping_responae)
            if len(message) > 100:
                ioloop = asyncio.new_event_loop()
                asyncio.set_event_loop(ioloop)
                tasks = [
                    ioloop.create_task(send_after_message(self.bot, self.chat_id, message))]
                wait_tasks = asyncio.wait(tasks)
                ioloop.run_until_complete(wait_tasks)
                ioloop.close()
                message = ''

        if message != '':
            msg = self.bot.send_message(self.chat_id, message)

        situation_worker = situation_worker_classes.get('what_info_show')('what_info_show', self.bot, self.chat_id,
                                                                          self.bot_message)
        situation_worker.start_handler()


class SituationBDCOMFindMACThread(Thread):

    def __init__(self, value, chat_id, bot):
        Thread.__init__(self)
        self.value = value
        self.chat_id = chat_id
        self.bot = bot

    def run(self):
        for bdcom_obj in BDCOM.objects.all():
            pon_snmp = PonSNMP(bdcom_obj.ip_address, bdcom_obj.snmp_public, bdcom_obj.snmp_private)

            info = pon_snmp.get_all_onu_mac_address()

            if info:

                for id, mac in pon_snmp.get_all_onu_mac_address():
                    if mac == self.value:
                        self.bot.send_message(self.chat_id,
                                              'MAC {} находится на устройстве {}'.format(self.value, bdcom_obj.title))


class SituationBDCOMFindMAC(SituationWorker):
    def text_answer(self, value):
        my_thread = SituationBDCOMFindMACThread(value, self.chat_id, self.bot)
        my_thread.start()

        self.bot.send_message(self.chat_id, 'Данные обробатываются. Ожидайте сообщение')

        situation_worker = situation_worker_classes.get('what_info_show')('what_info_show', self.bot, self.chat_id,
                                                                          self.bot_message)
        situation_worker.start_handler()


situation_worker_classes = {
    'new_registration_client': SituationNewClient,
    'new_registration_client_add_to_org': SituationClientAddToOrg,
    'new_registration_client_reg_org': SituationClientRegOrg,
    'what_info_show': SituationWhatInfoShow,
    'mikrotik_action': SituationMikroTikActions,
    'bdcom_action': SituationBDCOMActions,
    'mikrotik_list': SituationMikroTikList,
    'mikrotik_ppp_active_find': SituationPPPActiveFind,
    'bdcom_list': SituationBdcomikList,
    'mikrotik_client_info': SituationMikroTikClientInfo,
    'mikrotik_client_ping': SituationPing,
    'bdcom_find_mac': SituationBDCOMFindMAC
}
