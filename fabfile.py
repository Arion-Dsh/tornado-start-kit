#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from fabric.api import local, cd, run, env

env.hosts=['root@arion.life:42',] # ssh host [user@hosts:port]
env.password = '***'



def  setup():
    print('start set www')
    with cd('/srv/www/'):
        run('ls -l')
        run('mkdir -p "tornado/staging"')
        run('git clone --depth=1 https://github.com/Arion-Dsh/tornado-start-kit.git')
   


