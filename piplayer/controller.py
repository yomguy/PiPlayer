#!/usr/bin/env python
#
# Based on:
# Copyright (C) 2013 Guillaume Pellerin <yomguy@parisson.com>

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


from threading import Thread


class OSCController(Thread):

    def __init__(self, port):
        Thread.__init__(self)
        import liblo
        self.port = port
        try:
            self.server = liblo.Server(self.port)
        except liblo.ServerError, err:
            print str(err)

    def add_method(self, path, type, method):
        self.server.add_method(path, type, method)

    def run(self):
        while True:
            self.server.recv(100)

            
class GPIOController(Thread):

    def __init__(self):
        Thread.__init__(self)
        import RPi.GPIO as GPIO
        self.server = GPIO
        self.server.setmode(self.server.BCM)
        self.method = self.server.RISING
        
    def add_channel_callback(self, channel, callback, bouncetime):
        self.server.setup(channel, self.server.IN, pull_up_down=self.method)
        self.server.add_event_detect(channel, self.method, callback=callback, bouncetime=bouncetime)
        
    def run(self):
        pass

