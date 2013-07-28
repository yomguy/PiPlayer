---------------------------------------------
PiPlayer : audio sample player for the Rpi
---------------------------------------------

a minimalistic gstreamer based media sample player for the Raspberry Pi trigerred by GPIO or OSC callbacks.
  

Usage
------

```
  $ sudo piplayer DIR
```

Example
------------

```
  $ sudo piplayer /path/to/dir/
```

OSC
----

 * port : 12345
 * play address : /play/1
 
GPIO
-----

 * play channel : 22
 * play method : PUD_DOWN between PIN 1 (3.3V Power) and PIN 15 (GPIO 22)
 * stop channel : 24
 * stop method : PUD_DOWN between PIN 1 (3.3V Power) and PIN 18 (GPIO 24)

INSTALL
--------

```
 $ sudo apt-get install python python-pip python-setuptools python-gobject \
                        python-gst0.10 gstreamer0.10-plugins-base gir1.2-gstreamer-0.10 \
                        gstreamer0.10-plugins-good gstreamer0.10-plugins-bad \
                        gstreamer0.10-plugins-ugly gobject-introspection python-liblo

 $ sudo python setup.py install 
```

DAEMON
-------

```
 $ cp -ra etc/* /etc/
 $ update-rc.d piplayer defaults 5 1
```

OPTIONS
--------

Some properties and options (like "auto next" and "looping") are tunable in the PiPlayer class:

```
class PiPlayer(object):
    
    osc_port = 12345
    gpio_channel_play = 22
    gpio_channel_stop = 24
    playing = False
    looping = False
    auto_next = False
    alsa_device = 'hw:0'

    ...
```
