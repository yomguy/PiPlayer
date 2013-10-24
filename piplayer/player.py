#!/usr/bin/env python
#
# Based on:
# decodebin.py - Audio autopluging example using 'decodebin' element
# Copyright (C) 2006 Jason Gerard DeRose <jderose@jasonderose.org>
# Copyright (C) 2006 yokamaru https://gist.github.com/yokamaru/850506
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

# Doc : https://code.google.com/p/raspberry-gpio-python/wiki/Inputs


DEBUG = False

import gobject
gobject.threads_init()
import pygst
pygst.require("0.10")
import gst
import os, sys
import time

from piplayer.tools import *
from piplayer.controller import *

            
class PiPlayer(object):
    
    osc_port = 12345
    gpio_channel_play = 22
    gpio_channel_stop = 24
    playing = False
    looping = False
    auto_next = False
    alsa_device = 'hw:0'
    gpio_parasite_filter_time = 0.02
    
    def __init__(self, play_dir):
        # Playlist
        self.play_dir = play_dir
        self. playlist = []
        self.set_playlist()
        
        # OSC controller
        self.osc_controller = OSCController(self.osc_port)
        self.osc_controller.add_method('/play', 'i', self.osc_play_pause)
        self.osc_controller.add_method('/stop', 'i', self.osc_stop)
        self.osc_controller.start()
 
        # GPIO controller
        self.gpio_controller = GPIOController()
        self.gpio_controller.add_channel_callback(self.gpio_channel_play, self.gpio_play, 3000)
        self.gpio_controller.add_channel_callback(self.gpio_channel_stop, self.gpio_stop, 1000)
        self.gpio_controller.start()
        
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
        #self.srcdec.set_property('uri', 'file:///fake')
        self.play_id = 0
        self.uri =  self.playlist[self.play_id]
        self.srcdec.set_property('uri', self.uri)
 
        # Connect handler for 'pad-added' signal
        self.srcdec.connect('pad-added', self.on_pad_added)
 
        # Eq
        #self.eq = gst.element_factory_make('equalizer-10bands')
        #self.eq.set_property('band0', -24.0)
 
        # ALSA
        self.sink.set_property('device', self.alsa_device)
       
        # Add elements to pipeline
        self.pipeline.add(self.srcdec, self.conv, self.rsmpl, self.sink)
 
        # Link *some* elements
        # This is completed in self.on_new_decoded_pad()
        gst.element_link_many(self.conv, self.rsmpl, self.sink)
 
        # Reference used in self.on_new_decoded_pad()
        self.apad = self.conv.get_pad('sink')

        # The MainLoop
        self.mainloop = gobject.MainLoop()
        
        if self.playing:
            self.play()
 
    def on_pad_added(self, element, pad):
        caps = pad.get_caps()
        name = caps[0].get_name()
        #print 'on_pad_added:', name
        if name == 'audio/x-raw-float' or name == 'audio/x-raw-int':
            if not self.apad.is_linked(): # Only link once
                pad.link(self.apad)
 
    def on_eos(self, bus, msg):
        if self.auto_next:
            self.next()
        else:
            self.stop()
 
    def on_tag(self, bus, msg):
        taglist = msg.parse_tag()
        print 'on_tag:'
        for key in taglist.keys():
            print '\t%s = %s' % (key, taglist[key])
 
    def on_error(self, bus, msg):
        error = msg.parse_error()
        print 'on_error:', error[1]
        self.mainloop.quit()
    
    def set_playlist(self):
        for root, dirs, files in os.walk(self.play_dir):
            for filename in files:
                path = root + os.sep + filename
                self.playlist.append(path2url(path))
        self.playlist.sort()
                
    def next(self):
        self.play_id += 1
        if self.play_id >= len(self.playlist):
            self.play_id = 0
        self.uri =  self.playlist[self.play_id]
        self.pipeline.set_state(gst.STATE_NULL)
        self.srcdec.set_property('uri', self.uri)
        self.pipeline.set_state(gst.STATE_PLAYING)
        if DEBUG:
            print self.play_id, self.uri

    def gpio_parasite_filter(self):
        time.sleep(self.gpio_parasite_filter_time)
        return self.gpio_controller.server.input(self.gpio_channel_play)
            
    def play(self):
        if not self.playing:    
            self.pipeline.set_state(gst.STATE_PLAYING)
            self.playing = True
        elif self.auto_next:
            self.next()

    def stop(self):
        if self.playing:
            self.pipeline.set_state(gst.STATE_NULL)
            self.playing = False

    def pause(self):
        if self.playing:
            self.pipeline.set_state(gst.STATE_PAUSED)
            self.playing = False
            
    def osc_play_pause(self, path, value):
        value = value[0]
        if value and not self.playing:
            self.play()
        else:
            self.pause()

    def osc_stop(self, path, value):
        value = value[0]
        if value and self.playing:
            self.stop()
            
    def gpio_play(self, channel):
        if self.gpio_parasite_filter():
            self.play()

    def gpio_stop(self, channel):
        if self.gpio_parasite_filter():
            self.stop()
            
    def run(self):
        self.mainloop.run()

    def quit(self):
        self.mainloop.quit()

 
