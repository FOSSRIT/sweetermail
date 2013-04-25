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

### Code map

* sweetmail.py - the main activity, calls a bunch of stuff
  * configure.py - parses %activityroot%/data/config.txt to get pop3 account credentials
    * accounts.py - defines the types of accounts and their subtypes. the main pop3 function is in accounts.POPStoreAccount.retreive_all. 
  * bgsrt.py - the "background send/receive thread", hoping to phase this out into only being run at startup, and at user request
  * tracker.py - this doesn't appear to do much right now, it appears it WANTS to be an error reporter type thing, letting the user know where in a given process it failed
  * utility.py - only used for check_online() right now, which is dependent on Network Manager.
  * EVERYTHING ELSE - have not played with much, as it isn't directly related to pop stuff...

### TODO:

* ~~code review~~
* ~~get this thing running~~
* ~~find the applicable libraries~~
* get reading functional - in progress
  * ~~needs mail fetching - wyatt can do this!~~
  * needs mailbox functionality - ability to select and open messages - kody and alex can do this!
  * default to opening inbox tag
  * send receive button needs to call bgsrt.run()
  * stop downloading messages that we already have! Compare against metadata.db?
* get sending functional

### stretch goals
1. Make pretty icons and artwork
1. SSL / TLS support
1. attachment / image support
1. better error reporting besides a log file

### Super Stretch (tm)
1. openPGP