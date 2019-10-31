#!/bin/bash

if [ -z ${1} ]; then

    echo 'input leeroy buld number'
    echo '    ./deploy.sh 1'

else

    docker build . -f leeroy.Dockerfile --squash --compress -t registry.lab.kube.yamoney.ru/leeroy:${1} && \
    docker push registry.lab.kube.yamoney.ru/leeroy:${1} && \
    kubectl set image deployment -n xerxes leeroy leeroy=registry.lab.kube.yamoney.ru/leeroy:${1}

fi
