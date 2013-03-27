import gtk

class ContactsCanvas(gtk.Button):
    def __init__(self, mailactivity):
        gtk.Button.__init__(self, 'CONTACTS')

class ContactsToolbar(gtk.Toolbar):

    def __init__(self, mailactivity):        
        gtk.Toolbar.__init__(self)
        self.mailactivity = mailactivity
        self.canvas = ContactsCanvas