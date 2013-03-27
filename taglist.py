import gobject
import gtk
import hippo
import logging

from sugar import profile
from sugar.graphics import style
from sugar.graphics.icon import Icon, CanvasIcon
from sugar.graphics.palette import Palette
from sugar.graphics.roundbox import CanvasRoundBox

class TagPalette(Palette):

    def __init__(self, tag):
        tag_icon = Icon(file='icons/'+tag.icon+'.svg',
                        xo_color=profile.get_color(),
                        icon_size=gtk.ICON_SIZE_SMALL_TOOLBAR)
        Palette.__init__(self, primary_text=tag.label, icon=tag_icon)
        self._tag = tag
        
class TagIcon(CanvasIcon):
    
    def __init__(self, tag):
        CanvasIcon.__init__(self, size=style.STANDARD_ICON_SIZE/2, cache=True,
                            file_name='icons/'+tag.icon+'.svg')
        self._uncolor()
        self._tag = tag
        self.connect('hovering-changed', self.__hovering_changed_event_cb)
        self.connect('button-release-event', self.__button_release_event_cb)
        
    def create_palette(self):
        palette = TagPalette(self._tag)
        #palette.connect('erase-activated', self.__erase_activated_cb)
        return palette

    def _color(self):
        self.props.xo_color = profile.get_color()

    def _uncolor(self):
        self.props.stroke_color = style.COLOR_BUTTON_GREY.get_svg()
        self.props.fill_color = style.COLOR_TRANSPARENT.get_svg()

    def __hovering_changed_event_cb(self, icon, hovering):
        if hovering:
            self._color()
        else:
            self._uncolor()

    def __button_release_event_cb(self, icon, event):
        logging.debug('popping down palette')
        self.palette.popdown(immediate=True)
        self._uncolor()
        
class TagEntry(CanvasRoundBox):
    
    __gsignals__ = {
        'tag-selected': (gobject.SIGNAL_RUN_FIRST,
                         gobject.TYPE_NONE, ([str])),
    }

    def __init__(self, tag):
        CanvasRoundBox.__init__(self, spacing=style.DEFAULT_SPACING/2,
                              padding_top=style.DEFAULT_PADDING/2,
                              padding_bottom=style.DEFAULT_PADDING/2,
                              padding_left=style.DEFAULT_PADDING/2,
                              padding_right=style.DEFAULT_PADDING/2,
                              box_height=style.GRID_CELL_SIZE/2,
                              orientation=hippo.ORIENTATION_HORIZONTAL)

        self._icon = TagIcon(tag)
        self.append(self._icon)
        
        label = hippo.CanvasText(text=tag.label,
                                 xalign=hippo.ALIGNMENT_CENTER,
                                 font_desc=style.FONT_NORMAL.get_pango_desc(),
                                 box_width=style.GRID_CELL_SIZE*2)
        self.append(label)
        
        self._tag = tag

        self.connect('hovering-changed', self.__hovering_changed_event_cb)
        self.connect('button-release-event', self.__button_release_event_cb)
        
    def __hovering_changed_event_cb(self, widget, hovering):
        self._icon.emit('hovering-changed', hovering)
        
    def __button_release_event_cb(self, widget, event):
        if event.button==1:
            self.emit('tag-selected', self._tag.uid)
        else:
            self._icon.emit('button-release-event', event)

class TagList(gtk.VBox):
    
    __gsignals__ = {'tag-selected': (gobject.SIGNAL_RUN_FIRST,
                                     gobject.TYPE_NONE,
                                     [gobject.TYPE_INT])
    }

    def __tag_selected_cb(self, widget, uid):
        self._selected = uid
        self.emit('tag-selected', int(uid))
    
    def __init__(self, tags):
        gtk.VBox.__init__(self)
        
        # TODO: add buttons for adding / remove a tag, UI elements for new tag
        
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_flags(gtk.HAS_FOCUS|gtk.CAN_FOCUS)
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        
        self.pack_start(scrolled_window)
        scrolled_window.show()

        canvas = hippo.Canvas()
        scrolled_window.add_with_viewport(canvas)
        #scrolled_window.child.set_shadow_type(gtk.SHADOW_NONE)
        canvas.show()
        
        self._box = hippo.CanvasBox(spacing=style.DEFAULT_SPACING,
                                    padding_top=style.DEFAULT_PADDING*2,
                                    padding_bottom=style.DEFAULT_PADDING*2,
                                    padding_left=style.DEFAULT_PADDING*2,
                                    padding_right=style.DEFAULT_PADDING*2,
                                    background_color = style.COLOR_WHITE.get_int())
        canvas.set_root(self._box)
        
        for tag in tags:
            entry = TagEntry(tag)
            entry.connect('tag-selected', self.__tag_selected_cb)
            self._box.append(entry)