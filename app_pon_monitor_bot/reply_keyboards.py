# Регистрация нового клиента
NEW_CLIENT = {'slug': 'new_registration_client', 'title': 'Первый раз'}
NEW_CLIENT_NEW_ORG = {'slug': 'new_registration_client', 'title': 'Создать новую организацию',
                      'return_value': 'new_org'}
NEW_CLIENT_ADD_TO_ORG = {'slug': 'new_registration_client', 'title': 'Вступить в организацию',
                         'return_value': 'add_to_org'}

# Какую информацию отображать
WHAT_INFO_SHOW = {'slug': 'what_info_show', 'title': 'Какую информацию отображать?'}
WHAT_INFO_SHOW_MIKROTIK = {'slug': 'what_info_show', 'title': 'MikroTik', 'return_value': 'mikrotik'}
WHAT_INFO_SHOW_BDCOM = {'slug': 'what_info_show', 'title': 'BDCOM', 'return_value': 'bdcom'}
WHAT_INFO_FIND_MAC = {'slug': 'what_info_show', 'title': 'Найти по MAC', 'return_value': 'find_mac'}

# MikroTik
MIKROTIK_ACTION = {'slug': 'mikrotik_action', 'title': 'Mikrotik'}
MIKROTIK_ACTION_PPP_ACTIVE = {'slug': 'mikrotik_action', 'title': 'Активные PPP', 'return_value': 'ppp_active'}
MIKROTIK_ACTION_ARP = {'slug': 'mikrotik_action', 'title': 'ARP записи', 'return_value': 'arp'}
MIKROTIK_ACTION_PPP_ACTIVE_FIND = {'slug': 'mikrotik_action', 'title': 'Активные PPP поиск',
                                   'return_value': 'ppp_active_find'}
MIKROTIK_CLIENT_INFO = {'slug': 'mikrotik_action', 'title': 'Клиент инфо', 'return_value': 'mikrotik_client_info'}
MIKROTIK_CLIENT_PING = {'slug': 'mikrotik_action', 'title': 'Клиент ping', 'return_value': 'mikrotik_client_ping'}

# BDCOM
BDCOM_ACTION = {'slug': 'bdcom_action', 'title': 'BDCOM'}
BDCOM_ACTION_ALL_ONU = {'slug': 'bdcom_action', 'title': 'Все ONU', 'return_value': 'all_onu'}
BDCOM_ACTION_ACTIVE_ONU = {'slug': 'bdcom_action', 'title': 'Активные ONU', 'return_value': 'active_onu'}

keyboard_entities = {
    NEW_CLIENT.get('slug'): [
        [NEW_CLIENT_NEW_ORG, NEW_CLIENT_ADD_TO_ORG]
    ],
    WHAT_INFO_SHOW.get('slug'): [
        [WHAT_INFO_SHOW_MIKROTIK, WHAT_INFO_SHOW_BDCOM],
        [WHAT_INFO_FIND_MAC]
    ],
    MIKROTIK_ACTION.get('slug'): [
        [MIKROTIK_ACTION_PPP_ACTIVE, ],
        [MIKROTIK_ACTION_PPP_ACTIVE_FIND, MIKROTIK_CLIENT_INFO],
        [MIKROTIK_CLIENT_PING, ]
    ],
    BDCOM_ACTION.get('slug'): [
        [BDCOM_ACTION_ALL_ONU, BDCOM_ACTION_ACTIVE_ONU]
    ]
}
