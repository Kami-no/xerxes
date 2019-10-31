#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import getenv

jenkins_srv = 'https://jenkins.any.ru'
jenkins_user = getenv('secret_jenkins_user')
jenkins_pass = getenv('secret_jenkins_pass')
jenkins_app_deploy = 'job/ADM/job/prod/job'

jenkins_base = {
    'srv': 'https://jenkins1.any.ru',
    'user': getenv('secret_jenkins_base_user'),
    'pass': getenv('secret_jenkins_base_pass'),
    'path': 'job/ADM/job/prod/job'}

jenkins_pcidss = {
    'srv': 'https://jenkins2.any.ru',
    'user': getenv('secret_jenkins_pcidss_user'),
    'pass': getenv('secret_jenkins_pcidss_pass'),
    'path': 'job/Tasks/job'}
