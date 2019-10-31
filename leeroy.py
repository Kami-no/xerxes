#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
import requests
import logging
import warnings
import config


def jenkins_get_crumb(cfg):
    """
    Получить заголовок с crumb - CSRF Protection

    :param cfg: настройки для подключения к Jenkins
    :type cfg: dict
    :return: crumb-заголовок
    :rtype: dict
    """
    f_uri = '%s/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)' % cfg['srv']
    jenkins_response = requests.get(
        f_uri,
        auth=(cfg['user'], cfg['pass']),
        verify=False)

    "Подготовить заголовок с crumb"
    crumb = jenkins_response.text
    h = crumb.split(':')

    output = {h[0]: h[1]}

    logging.info('jenkins crumb: %s' % output)

    return output


def jenkins_request(cfg, j_uri):
    """
    Сделать запрос в Jenkins

    :param cfg: настройки для подключения к Jenkins
    :type cfg: dict
    :param j_uri: url для jenkins
    :type j_uri: str
    :return: http-код ответа
    :rtype: requests.Response
    """
    jenkins_crumb = jenkins_get_crumb(cfg)
    f_uri = '%s/%s/%s' % (
        cfg['srv'],
        cfg['path'],
        j_uri)

    logging.info('fury: %s' % f_uri)

    jenkins_response = requests.post(
        f_uri,
        auth=(cfg['user'], cfg['pass']),
        verify=False,
        headers=jenkins_crumb)

    return jenkins_response


def jenkins_info_job(cfg, app_name):
    """
    Получить состояние последней задачи

    :param cfg: настройки для подключения к Jenkins
    :type cfg: dict
    :param app_name: параметры приложения
    :type app_name: str
    :return: информация о последней задаче
    :rtype: dict
    """
    jenkins_uri = 'app_%s/wfapi/runs' % app_name
    jenkins_response = jenkins_request(cfg, jenkins_uri)

    console_url = '%s/%s/app_%s/%s/console' % (
        cfg['srv'],
        cfg['path'],
        app_name,
        jenkins_response.json()[0]['id'])

    "Информация о последней задаче"
    output = {
        'id': jenkins_response.json()[0]['id'],
        'status': jenkins_response.json()[0]['status'],
        'name': jenkins_response.json()[0]['name'],
        'stage': len(jenkins_response.json()[0]['stages']),
        'console': console_url}

    logging.info('jenkins job info: %s' % output)

    return output


def jenkins_info_task(cfg, app_name, app_task):
    """
    Получить состояние послезнего запуска задачи

    :param cfg: настройки для подключения к Jenkins
    :type cfg: dict
    :param app_name: параметры приложения
    :type app_name: str
    :param app_task: jenkins task id
    :type app_task: int
    :return: информация о jenkins task
    :rtype: dict
    """
    jenkins_uri = 'app_%s/%s/api/json' % (
        app_name,
        app_task)
    jenkins_response = jenkins_request(cfg, jenkins_uri)

    first_host = str()
    for item in jenkins_response.json()['actions']:
        if 'parameters' in item:
            first_host = item['parameters'][1]['value']
            break

    output = {
        'user': jenkins_response.json()['actions'][1]['causes'][0]['userId'],
        'host': first_host,
        'result': jenkins_response.json()['result']}

    logging.info('jenkins task info: %s' % output)

    return output


def jenkins_info_pipe(cfg, app_name, app_task):
    """
    Проверить ожидает ли pipeline действий от пользователя

    :param cfg: настройки для подключения к Jenkins
    :type cfg: dict
    :param app_name: параметры приложения
    :type app_name: str
    :param app_task: jenkins task id
    :type app_task: int
    :return: jenkins task input id
    :rtype: int
    """
    jenkins_uri = 'app_%s/%s/wfapi/pendingInputActions' % (
        app_name,
        app_task)
    jenkins_response = jenkins_request(cfg, jenkins_uri)

    input_id = jenkins_response.json()[0]

    logging.info('jenkins task pipe input id: %s' % input_id)

    return input_id


def jenkins_run_job(cfg, app_name, app_ver):
    """
    Запустить билд

    :param cfg: настройки для подключения к Jenkins
    :type cfg: dict
    :param app_name: параметры приложения
    :type app_name: str
    :param app_ver: версия пакета для установки
    :type app_ver: str
    :return: http-код ответа
    :rtype: int
    """
    jenkins_uri = 'app_%s/buildWithParameters/api/json?app_version="%s"' % (
        app_name,
        app_ver)
    jenkins_response = jenkins_request(cfg, jenkins_uri)

    logging.warning('run job %s v%s' % (app_name, app_ver))
    logging.info('response code: %s' % jenkins_response.status_code)

    return jenkins_response.status_code


def jenkins_run_pipe(cfg, app_name, app_task, app_input):
    """
    Продолжить pipeline

    :param cfg: настройки для подключения к Jenkins
    :type cfg: dict
    :param app_name: имя приложения
    :type app_name: str
    :param app_task: jenkins task id
    :type app_task: int
    :param app_input: jenkins task input id
    :type app_input: int
    :return: http-код ответа
    :rtype: int
    """
    jenkins_uri = 'app_%s/%s/input/%s/proceedEmpty' % (
        app_name,
        app_task,
        app_input)
    jenkins_response = jenkins_request(cfg, jenkins_uri)

    logging.warning('run next step %s %s' % (app_name, app_task))
    logging.info('response code: %s' % jenkins_response.status_code)

    return jenkins_response.status_code


async def info(request):
    """
    Получить информацию из Jenkins

    :param request: настройки для подключения к Jenkins
    :type request: aiohttp.web_request.Request
    :return: ответ в формате json
    :rtype: aiohttp.json_response.Response
    """
    data = request.match_info.get('data', None)
    json = await request.json()

    logging.info('json %s: %s' % (data, json))

    output = dict()
    if 'perimeter' in json and data in ('job', 'task', 'pipe'):
        if json['perimeter'] == 'pcidss':
            cfg = config.jenkins_pcidss
        else:
            cfg = config.jenkins_base

        if data == 'job':
            if 'name' in json:
                output = jenkins_info_job(cfg, json['name'])
        elif data == 'task':
            if 'name' in json and 'task' in json:
                output = jenkins_info_task(cfg, json['name'], json['task'])
        elif data == 'pipe':
            if 'name' in json and 'task' in json:
                output = jenkins_info_pipe(cfg, json['name'], json['task'])

    logging.info('output: %s' % output)

    return web.json_response(output)


async def run(request):
    """
    Запустить задачу в Jenkins

    :param request: настройки для подключения к Jenkins
    :type request: aiohttp.web_request.Request
    :return: ответ в формате json
    :rtype: aiohttp.json_response.Response
    """
    data = request.match_info.get('data', None)
    json = await request.json()

    logging.info('json %s: %s' % (data, json))

    output = dict()
    if 'perimeter' in json and data in ('job', 'pipe'):
        if json['perimeter'] == 'pcidss':
            cfg = config.jenkins_pcidss
        else:
            cfg = config.jenkins_base

        if data == 'job':
            if 'name' in json and 'version' in json:
                output = jenkins_run_job(cfg, json['name'], json['version'])
        elif data == 'pipe':
            if 'name' in json and 'task' in json and 'input' in json:
                output = jenkins_run_pipe(cfg, json['name'], json['task'], json['input'])

    logging.info('output: %s' % output)

    return web.json_response(output)


if __name__ == "__main__":
    "Настраиваем логи"
    logging.basicConfig(format='xerxes_leeroy - %(levelname)s - %(message)s', level=logging.WARNING)

    "Отключаем предупреждения о небезопасном SSL"
    warnings.filterwarnings('ignore')

    app = web.Application()
    app.add_routes([
        web.post('/info/{data}', info),
        web.post('/run/{data}', run)])

    web.run_app(app, port=8080)
