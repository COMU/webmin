#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2010 TUBITAK/UEKAE
# Licensed under the GNU General Public License, version 2.
# See the file http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt

from pisi.actionsapi import shelltools
from pisi.actionsapi import autotools
from pisi.actionsapi import pisitools
from pisi.actionsapi import get

def install():
    shelltools.export("HOME",get.workDIR())
    work_dir = get.workDIR()+"/"+get.srcDIR()
    shelltools.system("find %s -name '*.cgi' ;find %s -name '*.pl' | perl %s/perlpath.pl /usr/bin/perl -" % (work_dir, work_dir, work_dir))
    pisitools.dodir("/usr/share/webmin")

    pisitools.dodir("/etc/webmin")
    pisitools.dodir("/var/log/webmin")
    pisitools.dodir("/tmp/.webmin")
    shelltools.export("config_dir", "%s/etc/webmin" % get.installDIR())
    shelltools.export("var_dir", "%s/var/log/webmin" % get.installDIR())
    shelltools.export("perl", "/usr/bin/perl")
    shelltools.export("autoos", "1")
    shelltools.export("port", "10000")
    shelltools.export("login", "root")
    shelltools.export("crypt", "XXX")
    shelltools.export("host", "$HOSTNAME")
    shelltools.export("ssl", "1")
    shelltools.export("atboot", "1")
    shelltools.export("nostart", "1")
    shelltools.export("nochown", "1")
    shelltools.export("autothird","1")
    shelltools.export("nouninstall", "1")
    shelltools.export("noperlpath","1")
    shelltools.export("nopostinstall","1")
    shelltools.export("tempdir", "%s/tmp/.webmin" % get.installDIR())
    shelltools.system("./setup.sh %s/usr/share/webmin"  % get.installDIR())
    pisitools.dosed("%s/etc/webmin/install-dir" % get.installDIR(),get.installDIR()+"/", "/")
    pisitools.dosed("%s/etc/webmin/miniserv.conf" % get.installDIR(),get.installDIR()+"/", "/")
    pisitools.dosed("%s/etc/webmin/reload" % get.installDIR(),get.installDIR()+"/", "/")

    pisitools.dosed("%s/etc/webmin/restart" % get.installDIR(),get.installDIR()+"/", "/")

    pisitools.dosed("%s/etc/webmin/start" % get.installDIR(),get.installDIR()+"/", "/")
    pisitools.dosed("%s/etc/webmin/stop" % get.installDIR(),get.installDIR()+"/", "/")
    pisitools.dosed("%s/etc/webmin/var-path" % get.installDIR(),get.installDIR()+"/", "/")
