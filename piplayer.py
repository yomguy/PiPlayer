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
import os, sys, time
import urlparse, urllib


def path2url(path):
    return urlparse.urljoin(
      'file:', urllib.pathname2url(path))


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
        self.method = self.server.PUD_DOWN
        
    def add_channel_callback(self, channel, callback):
        self.server.setup(channel, self.server.IN, pull_up_down=self.method)
        self.server.add_event_detect(channel, self.method, callback=callback, bouncetime=1000)
        
    def run(self):
        pass


class Playlist(object):
    
    playlist = []
    
            
class AudioPlayer(object):
    
    osc_port = 12345
    gpio_channel_play = 22
    gpio_channel_stop = 24
    playing = False
    looping = True
    alsa_device = 'hw:1'
    
    
    def __init__(self, play_dir):    
        self.play_dir = play_dir
        self. playlist = []
        self.set_playlist()
        print self.playlist
        
        # OSC controller
        self.osc_controller = OSCController(self.osc_port)
        self.osc_controller.add_method('/play', 'i', self.osc_play_stop)
        self.osc_controller.add_method('/stop', 'i', self.osc_play_stop)
        self.osc_controller.start()
 
        # GPIO controller
        self.gpio_controller = GPIOController()
        self.gpio_controller.add_channel_callback(self.gpio_channel_play, self.gpio_play)
        self.gpio_controller.add_channel_callback(self.gpio_channel_stop, self.gpio_stop)
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
        
        self.play()
 
    def on_pad_added(self, element, pad):
        caps = pad.get_caps()
        name = caps[0].get_name()
        #print 'on_pad_added:', name
        if name == 'audio/x-raw-float' or name == 'audio/x-raw-int':
            if not self.apad.is_linked(): # Only link once
                pad.link(self.apad)
 
    def on_eos(self, bus, msg):
        self.next()
 
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
                
    def next(self):
        self.play_id += 1
        if self.play_id >= len(self.playlist):
            self.play_id = 0    
        self.uri =  self.playlist[self.play_id]
        self.pipeline.set_state(gst.STATE_NULL)
        self.srcdec.set_property('uri', self.uri)
        self.pipeline.set_state(gst.STATE_PLAYING)
        print self.play_id
        
    def play(self):
        if not self.playing:
            #self.play_id = 0
            #self.next()
            print self.uri
            self.pipeline.set_state(gst.STATE_PLAYING)
            self.playing = True
        else:
            self.next()
    
    def stop(self):
        if self.playing:
            self.pipeline.set_state(gst.STATE_NULL)
            self.playing = False

    def osc_play_stop(self, path, value):
        value = value[0]
        if value and not self.playing:
            self.play()
        else:
            self.stop()
            
    def gpio_play(self, channel):
        self.play()

    def gpio_stop(self, channel):
        self.stop()
            
    def run(self):
        self.mainloop.run()

    def quit(self):
        self.mainloop.quit()
        
        
if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print """ piplayer.py : a RPi gstreamer based media sample player trigerred by GPIO or OSC callbacks 
  usage : sudo python piplayer.py DIR
  example : sudo python piplayer.py /path/to/dir/
    OSC : 
      port : 12345
      play address : /play/1
    GPIO :
      play channel : 22
      play method : PUD_DOWN between PIN 1 (3.3V Power) and PIN 15 (GPIO 22)
      stop channel : 24
      stop method : PUD_DOWN between PIN 1 (3.3V Power) and PIN 18 (GPIO 24)  
"""
    else:
        path = sys.argv[-1]
        player = AudioPlayer(path)
        player.run()
    
