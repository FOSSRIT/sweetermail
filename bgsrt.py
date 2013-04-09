'Background Send/Receive Thread'

import email
import email.utils
import gtk
import threading
import time

from tracker import InboundTracker, OutboundTracker
from tags import FLAGS
from utility import check_online

class BGSRT(threading.Thread):
    
    def __init__(self, activity):
        threading.Thread.__init__(self)
        self._activity = activity
        self._config = activity.config
        self._ms = activity.ms

    def _send(self):
        unsent = self._ms.flagged_keys(FLAGS['outbound'])
        if unsent==[]:
            return
        tracker = OutboundTracker(self._activity)
        msgs = [self._ms.get_msg(key) for key in unsent]
        self._config.transport_account.send(msgs, tracker)
    
    def _receive(self):
        tracker = InboundTracker(self._activity)
        self._config.store_account.retrieve_all(tracker)

    def run(self):
        while 1:
            if check_online():
                #self._send()
                self._receive()
            time.sleep(self._config.send_receive_every * 60)
