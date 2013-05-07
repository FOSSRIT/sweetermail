import gobject
import gtk
import logging

from gettext import gettext as _
from sugar.activity import activity
from sugar.graphics.toolbox import Toolbox
from os.path import join as path_join

import configure
import mailstore
import read

#let's focus on reading for now!
#import contacts
#import write

from bgsrt import BGSRT # background send/receive thread ;p
    
class HomeToolbar(activity.ActivityToolbar):
    
    def __init__(self, mailactivity):
        activity.ActivityToolbar.__init__(self, mailactivity)
        self.keep.props.visible = False
        self.share.props.visible = False
        self.canvas = None
    
class mailactivityToolbox(activity.ActivityToolbox):
    
    canvas_by_index = {}

    def __init__(self, mailactivity):

        gtk.gdk.threads_init()
        
        Toolbox.__init__(self)

        home_toolbar = HomeToolbar(mailactivity)
        self.add_toolbar(_('Home'), home_toolbar)
        home_toolbar.show()
    
        read_toolbar = read.ReadToolbar(mailactivity)
        self.add_toolbar(_('Read'), read_toolbar)
        read_toolbar.show()
        
        #if it's not reading or getting mail, we don't need it right now!
        '''
        write_toolbar = write.WriteToolbar(mailactivity)
        self.add_toolbar(_('Write'), write_toolbar)
        write_toolbar.show()
       
        contacts_toolbar = contacts.ContactsToolbar(mailactivity)
        self.add_toolbar(_('Contacts'), contacts_toolbar)
        ontacts_toolbar.show()

        configure_toolbar = configure.ConfigureToolbar(mailactivity)
        self.add_toolbar(_('Configure'), configure_toolbar)
        configure_toolbar.show()
        '''
        self.toolbars =  {0: home_toolbar,
                         1: read_toolbar,
                         #2: write_toolbar,
                         #3: contacts_toolbar,
                         #4: configure_toolbar
                         }
        
        self.connect('current-toolbar-changed', self.__toolbar_changed_cb, mailactivity)

    def __toolbar_changed_cb(self, widget, idx, mailactivity):
        toolbar = self.toolbars[idx]
        if toolbar.canvas is not None:
            canvas = toolbar.canvas(mailactivity)
            mailactivity.set_canvas(canvas)
            canvas.show_all()

class mailactivity(activity.Activity):

    def __init__(self, handle):
        gtk.gdk.threads_init()

        activity.Activity.__init__(self, handle)
        
        #the config file goes in the data directory of the activity!
        configFilePath = self.get_activity_root() #
        configFilePath += "/data/config.txt"
        
        self._config = configure.Configuration(configFilePath)
        
        self._ms = mailstore.MailStore(path_join(activity.get_activity_root(), 'data'))
        
        toolbox = mailactivityToolbox(self)
        self.set_toolbox(toolbox)
        toolbox.show()
        
        toolbox.current_toolbar = 1 # default to 'Read' for now
        #bgsrt = BGSRT(self)
        #bgsrt.start()
    def run_bgsrt_once(self):
        bgsrt = BGSRT(self)
        bgsrt.start()
#        self.connect('visibility-notify-event', self.__visibility_notify_event_cb)
#        self.connect('window-state-event', self.__window_state_event_cb)
    
    # overriding add_alert and remove_alert; want more than one visible
    def add_alert(self, alert):
        alert.show()
        self._alerts.append(alert)
        self._vbox.pack_start(alert, False)
        self._vbox.reorder_child(alert, 1)
        self._vbox.set_child_packing(alert, 0, 0, 1, gtk.PACK_START)
        
    def remove_alert(self, alert):
        if alert in self._alerts:
            self._alerts.remove(alert)
            self._vbox.remove(alert)
            
    config = property(lambda self: self._config)
    
    ms = property(lambda self: self._ms)
