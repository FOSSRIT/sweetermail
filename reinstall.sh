#!/bin/bash
killall -9 sugar-emulator
sudo python setup.py install
sugar-emulator&
tail -F ~/.sugar/default/logs/org.sugarlabs.Sweetmail-1.log
