from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Tools.LoadPixmap import LoadPixmap
from Screens.Console import Console
from Components.Label import Label
from Components.MenuList import MenuList
from Plugins.Plugin import PluginDescriptor
from Screens.Standby import TryQuitMainloop
#from Plugins.Extensions.PersianPalace import *
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from boxbranding import getBoxType,  getImageDistro, getMachineName, getMachineBrand, getBrandOEM, getImageVersion
from os import environ
import os
import gettext
lang = language.getLanguage()
environ['LANGUAGE'] = lang[:2]
gettext.bindtextdomain('enigma2', resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain('enigma2')
gettext.bindtextdomain('InfopanelManager', '%s%s' % (resolveFilename(SCOPE_PLUGINS), 'Extensions/Infopanel/locale/'))

def _(txt):
    t = gettext.dgettext('PackageManager', txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t


class InfopanelManagerScreen(Screen):
    skin = """
    		<screen name="InfopanelManagerScreen" position="center,160" size="900,450" title="Package Manager For NFR">
		<ePixmap position="10,385" zPosition="1" size="35,27" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/pics/red.png" transparent="1" alphatest="on" />
		<ePixmap position="180,385" zPosition="1" size="35,27" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/pics/green.png" transparent="1" alphatest="on" />
		<ePixmap position="550,385" zPosition="1" size="35,27" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/pics/yellow.png" transparent="1" alphatest="on" />
		<widget source = "key_red" render="Label" position="50,385" zPosition="2" size="120,26" valign="center" halign="center" font="Regular;22" transparent="1" />
		<widget source = "key_green" render="Label" position="200,385" zPosition="2" size="350,26" valign="center" halign="center" font="Regular;22" transparent="1" />
		<widget source = "key_yellow" render="Label" position="580,385" zPosition="2" size="120,26" valign="center" halign="center" font="Regular;22" transparent="1" />
         <eLabel position="10,375" size="880,2" backgroundColor="blue" foregroundColor="blue" />
		<widget source="menu" render="Listbox" position="10,10" size="880,330" >
		<convert type="TemplatedMultiContent">
		{"template": [
		MultiContentEntryText(pos = (120, 2), size = (580, 28), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
		MultiContentEntryText(pos = (120, 32), size = (580, 18), font=1, flags = RT_HALIGN_LEFT, text = 2), # index 3 is the Description
		MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (100, 100), png = 3), # index 4 is the pixmap
		],
		"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
		"itemHeight": 110
		}
		</convert>
		</widget>
		</screen> """
                            
    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        self['shortcuts'] = ActionMap([
            'ShortcutActions',
            'WizardActions',
            'EPGSelectActions'], {
            'ok': self.OK,
            'cancel': self.exit,
            'back': self.exit,
            'red': self.exit,
            'green': self.restartGUI,
            'yellow': self.reboot })
        self['key_red'] = StaticText(_('Close'))
        self['key_green'] = StaticText(_('Restart enigma'))
        self['key_yellow'] = StaticText(_('Restart'))
        self.list = []
        self['menu'] = List(self.list)
        self.mList()

    
    def mList(self):
        self.list = []
        onepng = LoadPixmap(cached = True, path = resolveFilename(SCOPE_PLUGINS, 'Extensions/Infopanel/images/tar.png'))
        twopng = LoadPixmap(cached = True, path = resolveFilename(SCOPE_PLUGINS, 'Extensions/Infopanel/images/ipk1.png'))
        treepng = LoadPixmap(cached = True, path = resolveFilename(SCOPE_PLUGINS, 'Extensions/Infopanel/images/ipk.png'))
        fivepng = LoadPixmap(cached = True, path = resolveFilename(SCOPE_PLUGINS, 'Extensions/Infopanel/images/clear.png'))
        self.list.append((_('ipk Installer'), 'two', _('Install ipk Files From /tmp /media/usb /media/hdd /media/sda1'), twopng))
        self.list.append((_('Advanced ipk Installer'), 'tree', _('--force-reinstall --force-overwrite'), twopng))
        self.list.append((_('tar.gz , bh.tgz , nab.tgz Installer'), 'one', _('Install Above Formats From /tmp /media/usb /media/hdd /media/sda1'), onepng))
        self.list.append((_('TMP USB HDD Cleaner'), 'five', _('Remove ipk , tar.gz , bh.tgz , nab.tgz , zip , rar Files'), fivepng))
        self['menu'].setList(self.list)

    
    def infoKey(self):
        self.session.openWithCallback(self.mList, info)

    
    def exit(self):
        self.close()

    
    def restartGUI(self):
	self.session.open(TryQuitMainloop, 3)

    
    def reboot(self):
        os.system('reboot')

    
    def OK(self):
        item = self['menu'].getCurrent()[1]
        if item is 'one':
            self.session.openWithCallback(self.mList, InstallTarGZ)
        elif item is 'two':
            self.session.openWithCallback(self.mList, InstallIpk)
        elif item is 'tree':
            self.session.openWithCallback(self.mList, AdvInstallIpk)
        elif item is 'five':
            os.system('rm -rf /tmp/*.ipk /tmp/*.gz /tmp/*.tgz /tmp/*.zip /tmp/*.rar /media/usb/*.ipk /media/usb/*.gz /media/usb/*.tgz /media/usb/*.zip /media/usb/*.rar /media/hdd/*.ipk /media/hdd/*.gz /media/hdd/*.tgz /media/hdd/*.zip /media/hdd/*.rar /media/sda1/*.ipk /media/sda1/*.gz /media/sda1/*.tgz /media/sda1/*.zip /media/sda1/*.rar')
            self.mbox = self.session.open(MessageBox, _('All ipk , tar.gz , bh.tgz , nab.tgz , zip , rar Files Removed From /tmp /media/usb /media/hdd /media/sda1'), MessageBox.TYPE_INFO, timeout = 3)



class InstallTarGZ(Screen):
    skin = """
    		<screen name="InstallTarGZ" position="center,160" size="900,450" title="Select tar.gz , bh.tgz , nab.tgz Files">
		<widget source="menu" render="Listbox" position="10,10" size="880,300" scrollbarMode="showOnDemand">
		<convert type="TemplatedMultiContent">
		{"template": [
		MultiContentEntryText(pos = (70, 2), size = (630, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
		MultiContentEntryText(pos = (80, 29), size = (630, 18), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
		MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (50, 50), png = 2), # index 4 is the pixmap
		],
		"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
		"itemHeight": 60
		}
		</convert>
		</widget>
		<ePixmap position="10,385" zPosition="1" size="35,27" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/pics/red.png" transparent="1" alphatest="on" />
		<ePixmap position="180,385" zPosition="1" size="35,27" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/pics/green.png" transparent="1" alphatest="on" />
		<widget source = "key_red" render="Label" position="50,385" zPosition="2" size="120,26" valign="center" halign="center" font="Regular;22" transparent="1" />
		<widget source = "key_green" render="Label" position="220,385" zPosition="2" size="350,26" valign="center" halign="left" font="Regular;22" transparent="1" />
        <eLabel position="10,375" size="880,2" backgroundColor="blue" foregroundColor="blue" />
		</screen>"""
                            
    def __init__(self, session, args = None):
        Screen.__init__(self, session)
        self.session = session
        self.list = []
        self['menu'] = List(self.list)
        self.nList()
        self['actions'] = ActionMap([
            'OkCancelActions',
            'ColorActions'], {
            'cancel': self.cancel,
            'ok': self.okInst,
            'green': self.okInst,
            'red': self.cancel}, -1)
        self.list = []
        self['key_red'] = StaticText(_('Close'))
        self['key_green'] = StaticText(_('Install'))

    
    def nList(self):
        global fileplace1
        self.list = []
        ipklist = os.popen('ls -lh  /tmp/*.tar.gz /tmp/*.bh.tgz /tmp/*.nab.tgz /media/usb/*.tar.gz /media/usb/*.bh.tgz /media/usb/*.nab.tgz /media/hdd/*.tar.gz /media/hdd/*.bh.tgz /media/hdd/*.nab.tgz /media/sda1/*.tar.gz /media/sda1/*.bh.tgz /media/sda1/*.nab.tgz')
        ipkminipng = LoadPixmap(cached = True, path = resolveFilename(SCOPE_PLUGINS, 'Extensions/Infopanel/images/tarmini.png'))
        for line in ipklist.readlines():
            dstring = line.split('/')
            
            try:
                if dstring[1] == 'tmp':
                    endstr = len(dstring[0] + dstring[1]) + 2
                    fileplace1 = dstring[1]       
                else:
                    endstr = len(dstring[0] + dstring[1] + dstring[2]) + 3
                    fileplace1 = dstring[1] + "/" + dstring[2]  
                self.list.append((line[endstr:], dstring[0], ipkminipng))
            except:
                pass


        self['menu'].setList(self.list)

    
    def okInst(self):
        
        try:
            item = self['menu'].getCurrent()
            name = item[0]
            pecommand1 = 'tar -C/ -xzpvf /%s/%s' % (fileplace1, name)
            self.session.open(Console, title = _('Install tar.gz , bh.tgz , nab.tgz'), cmdlist = [
                pecommand1])
        except:
            pass

    def cancel(self):
        self.close()



class InstallIpk(Screen):
    skin = """
    		<screen name="InstallIpk" position="center,160" size="900,450" title="Select ipk Files">
		<widget source="menu" render="Listbox" position="10,10" size="880,300" scrollbarMode="showOnDemand">
		<convert type="TemplatedMultiContent">
		{"template": [
		MultiContentEntryText(pos = (70, 2), size = (630, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
		MultiContentEntryText(pos = (80, 29), size = (630, 18), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
		MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (50, 50), png = 2), # index 4 is the pixmap
		],
		"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
		"itemHeight": 60
		}
		</convert>
		</widget>
		<ePixmap position="10,385" zPosition="1" size="35,27" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/pics/red.png" transparent="1" alphatest="on" />
		<ePixmap position="180,385" zPosition="1" size="35,27" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/pics/green.png" transparent="1" alphatest="on" />
		<widget source = "key_red" render="Label" position="50,385" zPosition="2" size="120,26" valign="center" halign="center" font="Regular;22" transparent="1" />
		<widget source = "key_green" render="Label" position="220,385" zPosition="2" size="350,26" valign="center" halign="left" font="Regular;22" transparent="1" />
        <eLabel position="10,375" size="880,2" backgroundColor="blue" foregroundColor="blue" />
		</screen>"""
                    
    def __init__(self, session, args = None):
        Screen.__init__(self, session)
        self.session = session
        self.list = []
        self['menu'] = List(self.list)
        self.nList()
        self['actions'] = ActionMap([
            'OkCancelActions',
            'ColorActions'], {
            'cancel': self.cancel,
            'ok': self.okInst,
            'green': self.okInst,
            'red': self.cancel}, -1)
        self.list = []
        self['key_red'] = StaticText(_('Close'))
        self['key_green'] = StaticText(_('Install'))


    
    def nList(self):
        global fileplace2
        self.list = []
        ipklist = os.popen('ls -lh  /tmp/*.ipk /media/usb/*.ipk /media/hdd/*.ipk /media/sda1/*.ipk')
        ipkminipng = LoadPixmap(cached = True, path = resolveFilename(SCOPE_PLUGINS, 'Extensions/Infopanel/images/ipkmini.png'))
        for line in ipklist.readlines():
            dstring = line.split('/')
            
            try:
                if dstring[1] == 'tmp':
                    endstr = len(dstring[0] + dstring[1]) + 2
                    fileplace2 = dstring[1]  
                else:
                    endstr = len(dstring[0] + dstring[1] + dstring[2]) + 3
                    fileplace2 = dstring[1] + "/" + dstring[2]
                self.list.append((line[endstr:], dstring[0], ipkminipng))
            except:
                pass


        self['menu'].setList(self.list)

    
    def okInst(self):
        
        try:
            item = self['menu'].getCurrent()
            name = item[0]
            pecommand1 = 'opkg install /%s/%s' % (fileplace2, name)
            self.session.open(Console, title = 'Install ipk Packages', cmdlist = [
                pecommand1])
        except:
            pass
    
    def cancel(self):
        self.close()

class AdvInstallIpk(Screen):
    skin = """
    		<screen name="AdvInstallIpk" position="center,160" size="900,450" title="Select ipk Files">
		<widget source="menu" render="Listbox" position="10,10" size="880,300" scrollbarMode="showOnDemand">
		<convert type="TemplatedMultiContent">
		{"template": [
		MultiContentEntryText(pos = (70, 2), size = (630, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
		MultiContentEntryText(pos = (80, 29), size = (630, 18), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
		MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (50, 50), png = 2), # index 4 is the pixmap
		],
		"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
		"itemHeight": 60
		}
		</convert>
		</widget>
		<ePixmap position="10,385" zPosition="1" size="35,27" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/pics/red.png" transparent="1" alphatest="on" />
		<ePixmap position="180,385" zPosition="1" size="35,27" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/pics/green.png" transparent="1" alphatest="on" />
		<widget source = "key_red" render="Label" position="50,385" zPosition="2" size="120,26" valign="center" halign="center" font="Regular;22" transparent="1" />
		<widget source = "key_green" render="Label" position="220,385" zPosition="2" size="350,26" valign="center" halign="left" font="Regular;22" transparent="1" />
        <eLabel position="10,375" size="880,2" backgroundColor="blue" foregroundColor="blue" />
		</screen>"""

    def __init__(self, session, args = None):
        Screen.__init__(self, session)
        self.session = session
        self.list = []
        self['menu'] = List(self.list)
        self.nList()
        self['actions'] = ActionMap([
            'OkCancelActions',
            'ColorActions'], {
            'cancel': self.cancel,
            'ok': self.okInst,
            'green': self.okInst,
            'red': self.cancel}, -1)
        self.list = []
        self['key_red'] = StaticText(_('Close'))
        self['key_green'] = StaticText(_('Install'))

    
    def nList(self):
        global fileplace4
        self.list = []
        ipklist = os.popen('ls -lh  /tmp/*.ipk /media/usb/*.ipk /media/hdd/*.ipk /media/sda1/*.ipk')
        ipkminipng = LoadPixmap(cached = True, path = resolveFilename(SCOPE_PLUGINS, 'Extensions/Infopanel/images/ipkmini.png'))
        for line in ipklist.readlines():
            dstring = line.split('/')
            
            try:
                if dstring[1] == 'tmp':
                    endstr = len(dstring[0] + dstring[1]) + 2
                    fileplace4 = dstring[1] 
                else:
                    endstr = len(dstring[0] + dstring[1] + dstring[2]) + 3
                    fileplace4 = dstring[1] + "/" + dstring[2]
                self.list.append((line[endstr:], dstring[0], ipkminipng))
            except:
                pass


        self['menu'].setList(self.list)

    
    def okInst(self):
        
        try:
            item = self['menu'].getCurrent()
            name = item[0]
            pecommand1 = 'opkg install --force-reinstall --force-overwrite /%s/%s' % (fileplace4, name)
            self.session.open(Console, title = 'Install ipk Packages', cmdlist = [
                pecommand1])
        except:
            pass
    
    def cancel(self):
        self.close()

def PELock():
    
    try:
        gettitle = gettitle
        import pe
        petitle = gettitle()
        return petitle
    except:
        return False



def main(session, **kwargs):
    if PELock() == False:
        return None
    None.open(InfopanelManagerScreen)


#def Plugins(**kwargs):
#    return PluginDescriptor(name = _('Package Manager'), description = _('Special Version For EOS'), where = [
#        PluginDescriptor.WHERE_PLUGINMENU,
#        PluginDescriptor.WHERE_EXTENSIONSMENU], icon = 'PackageManager.png', fnc = main)
