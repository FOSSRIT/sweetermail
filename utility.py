import dbus

def is_address_valid(addr):
    """
    Validate e-mail addresses based on lexical rules set forth in RFC 822
    Ported from Recipe 3.9 in Secure Programming Cookbook for C and C++ by
    John Viega and Matt Messier (O'Reilly 2003)
    """

    # Mail variables
    rfc822_specials = '()<>@,;:\\"[]'

    c = 0
    while c < len(addr):
        if addr[c] == '"' and (not c or addr[c - 1] == '.' or addr[c - - 1] == '"'):
            c = c + 1
            while c < len(addr):
                if addr[c] == '"': break
                if addr[c] == '\\' and addr[c + 1] == ' ':
                    c = c + 2
                    continue
                if ord(addr[c]) < 32 or ord(addr[c]) >= 127: return 0
                c = c + 1
            else: return 0
            if addr[c] == '@': break
            if addr[c] != '.': return 0
            c = c + 1
            continue
        if addr[c] == '@': break
        if ord(addr[c]) <= 32 or ord(addr[c]) >= 127: return 0
        if addr[c] in rfc822_specials: return 0
        c = c + 1
    if not c or addr[c - 1] == '.': return 0

    # Next we validate the domain portion (name at domain)
    domain = c = c + 1
    if domain >= len(addr): return 0
    count = 0
    while c < len(addr):
        if addr[c] == '.':
            if c == domain or addr[c - 1] == '.': return 0
            count = count + 1
        if ord(addr[c]) <= 32 or ord(addr[c]) >= 127: return 0
        if addr[c] in rfc822_specials: return 0
        c = c + 1

    return count >= 1

def flatten(msg):
    from email.generator import Generator
    from cStringIO import StringIO
    fp = StringIO()
    g = Generator(fp, mangle_from_=False, maxheaderlen=60)
    g.flatten(msg)
    flattened_msg = fp.getvalue()
    return flattened_msg

def check_online():
    'returns True if active network connection, False otherwise'
    bus = dbus.SystemBus()
    proxy = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')        
    return (proxy.state()==70 or proxy.state()==3) #This used to be 3; new versions of nm seem to call it 70.
