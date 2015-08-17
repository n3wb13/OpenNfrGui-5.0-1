# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.MessageBox import MessageBox
from Components.ActionMap import NumberActionMap
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Components.config import config, configfile
from Tools.Directories import resolveFilename, SCOPE_ACTIVE_SKIN
from enigma import eEnv
import os

class SkinSelectorBase:
	def __init__(self, session, args = None):
		self.skinlist = []
		self.previewPath = ""
		if self.SKINXML and os.path.exists(os.path.join(self.root, self.SKINXML)):
			self.skinlist.append(self.DEFAULTSKIN)
		if self.PICONSKINXML and os.path.exists(os.path.join(self.root, self.PICONSKINXML)):
			self.skinlist.append(self.PICONDEFAULTSKIN)
		if self.NFRSKINXML and os.path.exists(os.path.join(self.root, self.NFRSKINXML)):
			self.skinlist.append(self.NFRDEFAULTSKIN)			
		for root, dirs, files in os.walk(self.root, followlinks=True):
			for subdir in dirs:
				dir = os.path.join(root,subdir)
				if os.path.exists(os.path.join(dir,self.SKINXML)):
					self.skinlist.append(subdir)
			dirs = []

		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["introduction"] = StaticText(_("Press OK to activate the selected skin."))
		self["SkinList"] = MenuList(self.skinlist)
		self["Preview"] = Pixmap()
		self.skinlist.sort()

		self["actions"] = NumberActionMap(["SetupActions", "DirectionActions", "TimerEditActions", "ColorActions"],
		{
			"ok": self.ok,
			"cancel": self.close,
			"red": self.close,
			"green": self.ok,
			"up": self.up,
			"down": self.down,
			"left": self.left,
			"right": self.right,
			"log": self.info,
		}, -1)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		tmp = self.config.value.find("/"+self.SKINXML)
		if tmp != -1:
			tmp = self.config.value[:tmp]
			idx = 0
			for skin in self.skinlist:
				if skin == tmp:
					break
				idx += 1
			if idx < len(self.skinlist):
				self["SkinList"].moveToIndex(idx)
		self.loadPreview()

	def ok(self):
		if self["SkinList"].getCurrent() == self.DEFAULTSKIN:
			skinfile = ""
			skinfile = os.path.join(skinfile, self.SKINXML)
		elif self["SkinList"].getCurrent() == self.PICONDEFAULTSKIN:
			skinfile = ""
			skinfile = os.path.join(skinfile, self.PICONSKINXML)
		elif self["SkinList"].getCurrent() == self.NFRDEFAULTSKIN:
			skinfile = ""
			skinfile = os.path.join(skinfile, self.NFRSKINXML)			
		else:
			skinfile = self["SkinList"].getCurrent()
			skinfile = os.path.join(skinfile, self.SKINXML)

		print "Skinselector: Selected Skin: "+self.root+skinfile
		self.config.value = skinfile
		self.config.save()
		configfile.save()
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply a new skin\nDo you want to restart the GUI now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))

	def up(self):
		self["SkinList"].up()
		self.loadPreview()

	def down(self):
		self["SkinList"].down()
		self.loadPreview()

	def left(self):
		self["SkinList"].pageUp()
		self.loadPreview()

	def right(self):
		self["SkinList"].pageDown()
		self.loadPreview()

	def info(self):
		aboutbox = self.session.open(MessageBox,_("Enigma2 skin selector"), MessageBox.TYPE_INFO)
		aboutbox.setTitle(_("About..."))

	def loadPreview(self):
		if self["SkinList"].getCurrent() == self.DEFAULTSKIN:
			pngpath = "."
			pngpath = os.path.join(os.path.join(self.root, pngpath), "prev.png")
		elif self["SkinList"].getCurrent() == self.PICONDEFAULTSKIN:
			pngpath = "."
			pngpath = os.path.join(os.path.join(self.root, pngpath), "piconprev.png")
		elif self["SkinList"].getCurrent() == self.NFRDEFAULTSKIN:
			pngpath = "."
			pngpath = os.path.join(os.path.join(self.root, pngpath), "piconprev.png")			
		else:
			pngpath = self["SkinList"].getCurrent()
			pngpath = os.path.join(os.path.join(self.root, pngpath), "prev.png")

		if not os.path.exists(pngpath):
			pngpath = resolveFilename(SCOPE_ACTIVE_SKIN, "noprev.png")

		if self.previewPath != pngpath:
			self.previewPath = pngpath

		self["Preview"].instance.setPixmapFromFile(self.previewPath)

	def restartGUI(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)

class SkinSelector(Screen, SkinSelectorBase):
	SKINXML = "skin.xml"
	DEFAULTSKIN = "< Default >"
	PICONSKINXML = None
	PICONDEFAULTSKIN = None
	NFRSKINXML = None
	NFRDEFAULTSKIN = None		

	skinlist = []
	root = os.path.join(eEnv.resolve("${datadir}"),"enigma2")

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		SkinSelectorBase.__init__(self, args)
		Screen.setTitle(self, _("Skin setup"))
		self.skinName = "SkinSelector"
		self.config = config.skin.primary_skin

class LcdSkinSelector(Screen, SkinSelectorBase):
	SKINXML = "skin_display.xml"
	DEFAULTSKIN = "< Default >"
	PICONSKINXML = "skin_display_picon.xml"
	PICONDEFAULTSKIN = "< Default with Picon >"
	NFRSKINXML = "skin_display_nfr.xml"
	NFRDEFAULTSKIN = "< NFR TEAM >"	

	skinlist = []
	root = os.path.join(eEnv.resolve("${datadir}"),"enigma2/display/")

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		SkinSelectorBase.__init__(self, args)
		Screen.setTitle(self, _("Skin setup"))
		self.skinName = "SkinSelector"
		self.config = config.skin.display_skin
