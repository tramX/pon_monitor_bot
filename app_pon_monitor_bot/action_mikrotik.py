import socket

from app_pon_monitor_bot.RosAPI import ApiRos


class ActionMikroTik:
    def __init__(self, device):
        self.device = device
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((device.network_address, device.api_port))
        self.apiros = ApiRos(s)
        self.apiros.login(device.login, device.password)

    # Поиск в ARP таблице
    def get_arp(self):
        arp_list = []
        for record in self.apiros.talk(["/ip/arp/print", "=.proplist=" + ".id,address,mac-address", ]):
            if record[1] == {}:
                pass
            else:
                arp_list.append([record[1]['=address'], record[1]['=mac-address']])
        return arp_list

    # Поиск в PPP active
    def get_ppp(self, login):
        for record in self.apiros.talk(["/ppp/active/print", "=.proplist=" + ".id,name,uptime", ]):
            if record[1] == {}:
                pass
            else:
                if record[1]['=name'] == login:
                    return record[1]['=uptime']
        return False

    # Получить список PPP Active
    def get_ppp_active(self):
        ppp_active = []
        for record in self.apiros.talk(["/ppp/active/print", "=.proplist=" + ".id,name,uptime", ]):
            if record[1] == {}:
                pass
            else:
                ppp_active.append([record[1]['=name'], record[1]['=uptime']])
        return ppp_active

    def get_address_list(self):
        addresses = []
        for record in self.apiros.talk(["/ip/firewall/address-list/print", "=.proplist=" + ".id,list,address", ]):
            if record[1] == {}:
                pass
            else:
                addresses.append([record[1]['=list'], record[1]['=address']])
        return addresses

    def ping(self, host, count='15'):
        pings = []

        for record in self.apiros.talk(["/ping", "=address=" + host, "=count=" + count]):
            if record[1].get('=status'):
                pings.append(record[1].get('=status'))

            if type(record[1].get('=time')) == str:
                pings.append(record[1].get('=time'))
            # pings.append(record[1])
        return pings

    # Клиент инфо
    def get_client_info(self, login):
        client_info = {'arp': False, 'uptime': False, 'address_list': []}
        for record in self.apiros.talk(["/ppp/secret/print", "=.proplist=" + ".id,name,password,remote-address", ]):
            if record[1] == {}:
                pass
            else:
                if login == record[1]['=name']:
                    client_info.update({'login': record[1]['=name'], 'password': record[1]['=password'],
                                        'ip': record[1]['=remote-address']})
                    for ip, mac in self.get_arp():
                        if ip == client_info.get('ip'):
                            client_info['arp'] = True

                    for login_active, uptime in self.get_ppp_active():
                        if login == login_active:
                            client_info['uptime'] = uptime

                    for list, address in self.get_address_list():
                        if address == client_info.get('ip'):
                            client_info['address_list'].append([list, address])

        return client_info


class Device:
    def __init__(self):
        self.network_address = '80.93.126.30'
        self.api_port = 28728
        self.login = 'vps'
        self.password = ''

# device = Device()

# action_mikroTik = ActionMikroTik(device)
# print(action_mikroTik.get_client_info('akbx26'))
