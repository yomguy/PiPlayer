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

from threading import Thread

import os, sys
import time, datetime

from piplayer.tools import *
from piplayer.controller import *

from mpd import MPDClient

            
class PiMPDPlayer(Thread):
    
    osc_port = 12345
    gpio_channel_play = 22
    gpio_channel_stop = 24
    playing = True
    looping = False
    auto_next = False
    up_voluming = False
    down_voluming = False
    alsa_device = 'hw:0'
    gpio_parasite_filter_time = 0.02
    gpio_channel_volume_up = 7
    mpd_host = 'localhost'
    mpd_port = 6600
    max_volume = 100
    min_volume = 5
    timer_period = 30
    volume_incr_time = 0.1

    def __init__(self):
        Thread.__init__(self)
        
        # Playlist
        #self.play_dir = play_dir
        #self.playlist = []
        #self.set_playlist()

        # OSC controller
        #self.osc_controller = OSCController(self.osc_port)
        #self.osc_controller.add_method('/play', 'i', self.osc_play_pause)
        #self.osc_controller.add_method('/stop', 'i', self.osc_stop)
        #self.osc_controller.add_method('/volume_up', 'i', self.osc_volume_up)
        #self.osc_controller.start()
        
        # MPD client
        self.mpd = MPDClient()
        self.mpd.connect(self.mpd_host, self.mpd_port)
        self.reset_timer()
        self.mpd.setvol(self.min_volume)
        self.volume = self.min_volume

        # GPIO controller
        self.gpio_controller = GPIOController()
        self.gpio_controller.add_channel_callback(self.gpio_channel_play, self.gpio_play, 3000)
        self.gpio_controller.add_channel_callback(self.gpio_channel_stop, self.gpio_stop, 1000)
        self.gpio_controller.add_channel_callback(self.gpio_channel_volume_up, self.gpio_volume_up, 1000)
        self.gpio_controller.start()
        
        # Set 'uri' property on uridecodebin
        #self.srcdec.set_property('uri', 'file:///fake')
        #self.play_id = 0
        #self.uri =  self.playlist[self.play_id]
        
        if self.playing:
            self.play()
 
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

    def gpio_parasite_filter(self):
        time.sleep(self.gpio_parasite_filter_time)
        return self.gpio_controller.server.input(self.gpio_channel_play)
            
    def play(self):
        if not self.playing:    
            self.mpd.play()
            self.playing = True
        elif self.auto_next:
            self.next()

    def stop(self):
        if self.playing:
            self.mpd.stop()
            self.playing = False

    def pause(self):
        if self.playing:
            self.mpd.pause()
            self.playing = False

    def volume_up(self):
        if not self.volume == self.max_volume and not self.up_voluming:
            for vol in range(self.volume, self.max_volume+1):
                self.up_voluming = True
                self.mpd.setvol(vol)
                self.volume = vol
                if DEBUG:
                    print 'volume', vol
                time.sleep(self.volume_incr_time)
        self.reset_timer()
        self.up_voluming = False 

    def volume_down(self):
        if not self.volume == self.min_volume and not self.down_voluming:
            for vol in range(self.volume, self.min_volume-1, -1):
                if not self.up_voluming:
                    self.down_voluming = True
                    self.mpd.setvol(vol)
                    self.volume = vol
                    if DEBUG:
                        print 'volume', vol
                    time.sleep(self.volume_incr_time)
        self.down_voluming = False

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

    def osc_volume_up(self, path, value):
        value = value[0]
        if value:
            self.volume_up()

    def gpio_play(self, channel):
        if self.gpio_parasite_filter():
            self.play()

    def gpio_stop(self, channel):
        if self.gpio_parasite_filter():
            self.stop()

    def gpio_volume_up(self, channel):
        self.volume_up()
    
    def gpio_volume_down(self, channel):
        self.volume_down()
    
    def reset_timer(self):
        self.timer = datetime.datetime.now()

    def is_timer_over(self):
        diff = datetime.datetime.now() - self.timer
        if DEBUG:
            print diff
        return diff.total_seconds() >= float(self.timer_period)

    def run(self):
        while True:
            if self.is_timer_over() and not self.up_voluming:
                self.volume_down()
            time.sleep(1)
            

 
