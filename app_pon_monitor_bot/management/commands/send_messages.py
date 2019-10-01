from django.core.management.base import BaseCommand, CommandError
#from django.conf import settings
import calendar
from datetime import date, datetime
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist

from app_pon_monitor_bot.models import Message
from app_pon_monitor_bot.action_bdcom import PonSNMP

from easysnmp.exceptions import EasySNMPTimeoutError



class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):

        pon_snmp = PonSNMP('192.168.200.101', 'public', 'public')

        try:
            pon_snmp.get_all_onu_signal()
        except EasySNMPTimeoutError:
            print('ERROR')

        #for message in Message.objects.filter(sent=False):
        #    if message.client:
        #        print(message.client)
        #    else:
        #        print(message.client.employees_org)
            #settings.BOT.send_message(reminder_work.client.telegram_id, message)
