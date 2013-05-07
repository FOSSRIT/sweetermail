import hippo
import logging

from sugar.graphics import style

from staricon import StarIcon
from mailicon import MailIcon

class MessageEntry(hippo.CanvasBox):
    
    _WHO_COL_WIDTH = style.GRID_CELL_SIZE * 4
    _WHEN_COL_WIDTH = style.GRID_CELL_SIZE * 3
    
    def __init__(self):
        self.activity = activity;
        hippo.CanvasBox.__init__(self,
                                 spacing=style.DEFAULT_SPACING,
                                 padding_top=style.DEFAULT_PADDING,
                                 padding_bottom=style.DEFAULT_PADDING,
                                 padding_left=style.DEFAULT_PADDING * 2,
                                 padding_right=style.DEFAULT_PADDING * 2,
                                 box_height=style.GRID_CELL_SIZE,
                                 orientation=hippo.ORIENTATION_HORIZONTAL)

        self._mobject = None
        
        self._is_selected = False
        
        self.star_icon = self._create_star_icon()
        self.append(self.star_icon)

        self.mail_icon = self._create_mail_icon()
        self.append(self.mail_icon)
        
        self.what = self._create_what()
        self.append(self.what, hippo.PACK_EXPAND)
        
        self.who = self._create_who()
        self.append(self.who)
        
        self.when = self._create_when()
        self.append(self.when)
    
    def _create_star_icon(self):
        star_icon = StarIcon(False)
        star_icon.connect('button-release-event',
                          self.__star_icon_button_release_event_cb)
        return star_icon

    def _create_mail_icon(self):
        mail_icon = MailIcon(False)
        #TODO: implement the "open message yo" callback
        mail_icon.connect('button-release-event',
                          self.__mail_icon_button_release_event_cb)
        return mail_icon

    def _create_what(self):
        what = hippo.CanvasText(text='',
                                 xalign=hippo.ALIGNMENT_START,
                                 font_desc=style.FONT_NORMAL.get_pango_desc(),
                                 size_mode=hippo.CANVAS_SIZE_ELLIPSIZE_END)
        return what

    def _create_who(self):
        who = hippo.CanvasText(text='',
                                xalign=hippo.ALIGNMENT_START,
                                font_desc=style.FONT_NORMAL.get_pango_desc(),
                                box_width=self._WHO_COL_WIDTH)
        return who
    
    def _create_when(self):
        when = hippo.CanvasText(text='',
                                xalign=hippo.ALIGNMENT_START,
                                font_desc=style.FONT_NORMAL.get_pango_desc(),
                                box_width=self._WHEN_COL_WIDTH)
        return when

    def _update_color(self):
        if self._mobject.unseen:
            self.props.background_color = style.COLOR_WHITE.get_int()
        else:
            self.props.background_color = style.COLOR_WHITE.get_int()
            
    def __star_icon_button_release_event_cb(self, button, event):
        mobject = self._mobject
        if mobject.starred:
            mobject.unmark('starred')
        else:
            mobject.mark('starred')
        self.star_icon.props.star = mobject.starred
        return True

    def __mail_icon_button_release_event_cb(self, button, event):
        mobject = self._mobject
        logging.debug("Contents of potatoes: " + self.activity.readpane)
        self.activity.readpane.msglist.refresh(True)
        return True
    
    def set_selected(self, is_selected):
        self._is_selected = is_selected
        self._update_color()
    
    def set_mobject(self, mobject):
        self._mobject = mobject
        self._is_selected = False
        
        self.star_icon.props.star = mobject.starred
        logging.debug(mobject.starred)
        self.what.props.text = mobject.what
        self.who.props.text = mobject.who
        self.when.props.text = mobject.when
        
        self._update_color()
    
    mobject = property(lambda self: self._mobject, set_mobject)
    
    def update_date(self):
        self.when.props.text = self._mobject.when
