from django.core.management.base import BaseCommand, CommandError
#from django.conf import settings
import calendar
from datetime import date, datetime
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist

from easysnmp import Session
from easysnmp.exceptions import EasySNMPTimeoutError

MIBS = {
    'onu_mac_addresses':'.1.3.6.1.4.1.3320.101.10.1.1.3',
    'onu_signal':'.1.3.6.1.4.1.3320.101.10.5.1.5.',
    'onu_distance':'1.3.6.1.4.1.3320.101.10.1.1.27',
    'all_onu_signal':'iso.3.6.1.4.1.3320.101.10.5.1.5',
    'interfaces_list': '1.3.6.1.2.1.2.2.1.2'
}

class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):

        session = Session(hostname='192.168.200.101', community='public', version=2, )

        try:
            for i in session.walk(MIBS.get('interfaces_list')):
                print(i)
            print('WWWWWWWWWWWWWWWWWWWWWWWWWW')
            print(session.walk(MIBS.get('all_onu_signal')))
        except EasySNMPTimeoutError:
            print('ERROR')

        #for message in Message.objects.filter(sent=False):
        #    if message.client:
        #        print(message.client)
        #    else:
        #        print(message.client.employees_org)
            #settings.BOT.send_message(reminder_work.client.telegram_id, message)
