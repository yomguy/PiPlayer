#!/usr/bin/env python
#
# Based on:
# decodebin.py - Audio autopluging example using 'decodebin' element
# Copyright (C) 2006 Jason Gerard DeRose <jderose@jasonderose.org>
# Copyright (C) 2006 yokamaru https://gist.github.com/yokamaru/850506
# Copyright (C) 2013 Guillaume Pellerin

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


import gobject
gobject.threads_init()
import pygst
pygst.require("0.10")
import gst
from threading import Thread
import sys
import liblo


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

            
class AudioPlayer(Thread):
    
    def __init__(self, uri):
        Thread.__init__(self)
        
        self.uri = uri
        
        # The controller
        self.controller = OSCController(12345)
        self.controller.add_method('/play', 'i', self.play_stop)
        self.controller.start()
 
        # The pipeline
        self.pipeline = gst.Pipeline()
 
        # Create bus and connect several handlers
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self.on_eos)
        #self.bus.connect('message::tag', self.on_tag)
        self.bus.connect('message::error', self.on_error)
 
        # Create elements
        self.srcdec = gst.element_factory_make('uridecodebin')
        self.conv = gst.element_factory_make('audioconvert')
        self.rsmpl = gst.element_factory_make('audioresample')
        self.sink = gst.element_factory_make('alsasink')
 
        # Set 'uri' property on uridecodebin
        self.srcdec.set_property('uri', self.uri)
 
        # Connect handler for 'pad-added' signal
        self.srcdec.connect('pad-added', self.on_pad_added)
 
        # Add elements to pipeline
        self.pipeline.add(self.srcdec, self.conv, self.rsmpl, self.sink)
 
        # Link *some* elements
        # This is completed in self.on_new_decoded_pad()
        gst.element_link_many(self.conv, self.rsmpl, self.sink)
 
        # Reference used in self.on_new_decoded_pad()
        self.apad = self.conv.get_pad('sink')
 
        # The MainLoop
        self.mainloop = gobject.MainLoop()
 
    def on_pad_added(self, element, pad):
        caps = pad.get_caps()
        name = caps[0].get_name()
        #print 'on_pad_added:', name
        if name == 'audio/x-raw-float' or name == 'audio/x-raw-int':
            if not self.apad.is_linked(): # Only link once
                pad.link(self.apad)
 
    def on_eos(self, bus, msg):
        #print 'on_eos'
        self.pipeline.set_state(gst.STATE_NULL)
        #self.mainloop.quit()
 
    def on_tag(self, bus, msg):
        taglist = msg.parse_tag()
        print 'on_tag:'
        for key in taglist.keys():
            print '\t%s = %s' % (key, taglist[key])
 
    def on_error(self, bus, msg):
        error = msg.parse_error()
        print 'on_error:', error[1]
        self.mainloop.quit()
 
    def play_stop(self, path, value):
        value = value[0]
        if value:
            self.pipeline.set_state(gst.STATE_NULL)
            self.pipeline.set_state(gst.STATE_PLAYING)
        else:
            self.pipeline.set_state(gst.STATE_NULL)
    
    def update_uri(uri):
        self.uri = uri
        self.srcdec.set_property('uri', self.uri)
        
    def run(self):
        self.mainloop.run()

        
if __name__ == '__main__':
    uri = sys.argv[-1]
    player = AudioPlayer(uri)
    player.start()
    
