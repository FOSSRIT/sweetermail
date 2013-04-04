SweeterMail
===========
_It's like foster care_

### To install:
- get a reasonable linux dev environment
- install sugar-build (http://sugarlabs.org/~buildbot/docs/build.html)
- install sugar-emulator and sugar-session (package names may vary from distro to disro)
- sudo python setup.py install
- run the emulator! (sugar-emulator -F for windowed mode)
- see how shitty it looks!

### TODO:

* ~~code review~~
* ~~get this thing running~~
* ~~find the applicable libraries~~
* get reading functional - in progress
* configure.py needs _store_account implemented
* get sending functional

### stretch goals
1. Make pretty icons and artwork
1. SSL / TLS support

### Super Stretch (tm)
1. openPGP

The chain to read mail
sweetmail->read->pop->bgsrt

`python read._sendreceive_cb` needs to call the appropriate function to fetch mail.

I'm not sure which one(s) it needs to call.
