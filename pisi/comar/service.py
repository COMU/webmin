#!/usr/bin/python
# -*- coding: utf-8 -*-

from comar.service import *
import os 

serviceType="server"
serviceDesc=_({"en": "Webmin",
                     "tr": "Webmin"})
start = "/etc/webmin/start"
stop = "/etc/webmin/stop"
pidFile = "/var/webmin/miniserv.pid"
@synchronized
def start():
    os.system("/etc/webmin/start")
@synchronized
def stop():
    stopService("/etc/webmin/stop")
