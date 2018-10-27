#!/usr/bin/env python3
"""
Daemon to watch over Zabbix
"""

from pyzabbix import ZabbixAPI
from aiohttp import web
from os import getenv
import logging


zabbix_srv = 'https://zabbix.company.ru'
zabbix_user = getenv('secret_zabbix_user')
zabbix_pass = getenv('secret_zabbix_pass')
zabbix_groups = ['Production']


def get_all_versions():
    zapi = ZabbixAPI(zabbix_srv)
    zapi.login(zabbix_user, zabbix_pass)
    logging.info('Connected to Zabbix API Version %s' % zapi.api_version())

    listed = list()
    'Get groups IDs'
    groups = zapi.hostgroup.get(output=['itemid', 'name'])
    for group in groups:
        if group['name'] in zabbix_groups:
            listed.append(group['groupid'])

    'Search query'
    query = {'key_': 'service_ping[*,service,version]'}

    'Get all items'
    items = zapi.item.get(
        groupids=listed,
        search=query,
        searchWildcardsEnabled=True,
        output=['name', 'lastvalue'])

    output = dict()
    for item in items:
        'Skip zero values'
        if item['lastvalue'] != '0':
            app = item['name'].split('"')[1]
            ver = item['lastvalue']

            'Create app dict for the first time'
            if app not in output:
                output[app] = dict()

            'Create ver dict for the first time'
            if ver not in output[app]:
                output[app][ver] = int()

            output[app][ver] += 1

    return output


def get_current_versions(data):
    output = dict()
    output['multi'] = dict()
    output['most'] = dict()

    for app in data:
        'Make it simple if there is only one version'
        if len(data[app]) == 1:
            output['most'][app] = next(iter(data[app]))
        else:
            multi = sorted(data[app], key=data[app].get, reverse=True)
            output['most'][app] = next(iter(multi))
            'Multi-version list'
            output['multi'][app] = multi

    return output


async def get_it(request):
    """
    Get data from Zabbix

    :param request: parameters
    :type request: aiohttp.web_request.Request
    :return: information about versions in json
    :rtype: aiohttp.json_response.Response
    """
    app = request.match_info.get('data', None)
    logging.info('incoming: %s' % app)

    data = get_all_versions()

    output = get_current_versions(data)

    if app:
        if app in output['most']:
            version = output['most'][app]
        else:
            version = 'N/A'
            logging.error('app not found: %s' % app)

        output = {'version': version}

    logging.info('output: %s' % output)
    return web.json_response(output)


if __name__ == "__main__":
    'Setup logging'
    logging.basicConfig(format='xerxes_overwatch - %(levelname)s - %(message)s', level=logging.WARNING)

    app = web.Application()
    app.add_routes([
        web.get('/{data}', get_it),
        web.get('/', get_it)])

    web.run_app(app, port=8080)
