from django.db import models
from django.contrib.auth.models import User
import uuid


class Client(models.Model):
    user = models.ForeignKey(User, related_name='client_profile')
    approved = models.BooleanField(default=False, verbose_name='Одобрен')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        db_table = 'clients'

    def __str__(self):
        return '{} {}'.format(self.user.username, self.approved)


class Organization(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название организация')
    org_id = models.UUIDField(auto_created=True, default=uuid.uuid4, max_length=10, verbose_name='ID организации')
    own = models.OneToOneField(Client, verbose_name='Владелец', related_name='client_org')
    employees = models.ManyToManyField(Client, verbose_name='Сотрудники', related_name='employees_org')

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'
        db_table = 'organizations'

    def __str__(self):
        return '{} {} {} {}'.format(self.title, self.org_id, self.own, self.employees)


class BDCOM(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название')
    ip_address = models.GenericIPAddressField(verbose_name='ip адрес')
    snmp_public = models.CharField(max_length=255, verbose_name='Публичное комюнити')
    snmp_private = models.CharField(max_length=255, verbose_name='Приватное комюнити')
    port_count = models.PositiveIntegerField(verbose_name='Количество портов')
    org = models.ForeignKey(Organization, verbose_name='Организация', related_name='org_bdcoms')

    class Meta:
        verbose_name = 'BDCOM'
        verbose_name_plural = 'BDCOM-s'
        db_table = 'bdcoms'

    def __str__(self):
        return '{} {} {} {} {} {}'.format(self.title, self.ip_address, self.snmp_public, self.snmp_private,
                                          self.port_count, self.org)


class MikroTik(models.Model):
    title = models.CharField(max_length=150, verbose_name='Название MikroTik')
    network_address = models.GenericIPAddressField(verbose_name='Сетевой адрес устройства')
    login = models.CharField(max_length=50, verbose_name='Логин для доступа к устройству')
    password = models.CharField(max_length=50, verbose_name='Пароль для доступа к устройству')
    api_port = models.IntegerField(verbose_name='API порт', default=8728)
    org = models.ForeignKey(Organization, verbose_name='Организация', related_name='org_mikrotiks')

    class Meta:
        verbose_name = 'MikroTik'
        verbose_name_plural = 'MikroTik-s'
        db_table = 'mikrotiks'

    def __str__(self):
        return '{} {} {} {} {} {}'.format(self.title, self.network_address, self.login, self.password, self.api_port,
                                          self.org)


class Message(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название сообщения')
    text = models.TextField(verbose_name='Текст сообщения')
    client = models.ForeignKey(Client, blank=True, null=True, verbose_name='Выбрать конкретного сотрудника')
    sent = models.BooleanField(default=False, verbose_name='Статус отправки')
    org = models.ForeignKey(Organization)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        db_table = 'messages'

    def __str__(self):
        return '{} {} {} {}'.format(self.title, self.text, self.client, self.sent)
