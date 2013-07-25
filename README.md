---------------------------------------------
PiPlayer : audio sample player for the Rpi
---------------------------------------------

a gstreamer based media sample player for the Raspberry Pi trigerred by GPIO or OSC callbacks.
  

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
 $ sudp python setup.py install 
```

DAEMON
-------

```
 $ cp -ra etc/* /etc/
 $ update-rc.d piplayer defaults 5 1
```