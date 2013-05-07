import gtk
import logging
import sweetmail

from gettext import gettext as _
from sugar.graphics.toolbutton import ToolButton

from taglist import TagList
from msglist import MsgList


class ReadCanvas(gtk.HBox):
    '''temporary playground'''
    
    def __init__(self, activity):
        gtk.HBox.__init__(self)
        self.activity = activity
        self._ms = activity.ms
        self.taglist = TagList(self._ms.tags)
        self.taglist.connect('tag-selected', self.__tag_selected_cb)
        self.pack_start(self.taglist, False, False)
        self.taglist.show_all()   
        self.msglist = MsgList(self._ms)
        self.pack_start(self.msglist)
        self.msglist.show_all()
        self.msglist.set_is_visible(True)

    def __tag_selected_cb(self, widget, uid):
        logging.debug('clicked on tag of uid %d' %uid)
        self.msglist.update_with_query({'tag':uid})

class ReadToolbar(gtk.Toolbar):
    '''
    TODO:
    * the toolbutton's sensitivity depends on context
    '''

    canvas = ReadCanvas

    def __init__(self, activity):        
        gtk.Toolbar.__init__(self)
        self._activity = activity

        self._sendreceive_button = ToolButton('send-and-receive', tooltip=_('Send/receive email'))
        self._sendreceive_button.connect('clicked', self._sendreceive_cb)
        self.insert(self._sendreceive_button, -1)
        self.show_all()
        '''
        self._reply_button = ToolButton('reply', tooltip=_('Write a reply'))
        self._reply_button.connect('clicked', self._reply_msg_cb)
        self.insert(self._reply_button, -1)

        self._forward_button = ToolButton('forward', tooltip=_('Forward this message'))
        self._forward_button.connect('clicked', self._forward_msg_cb)
        self.insert(self._forward_button, -1)
        '''
    def _sendreceive_cb(self, *args):
        sweetmail.mailactivity.run_bgsrt_once(self._activity)
    def _reply_msg_cb(self, *args):
        pass
    
    def _forward_msg_cb(self, *args):
        pass

