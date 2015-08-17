# -*- coding: utf-8 -*-

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from enigma import gPixmapPtr, ePicLoad, eTimer
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from Tools.Directories import fileExists
from Components.config import config
import mp_globals
from debuglog import printlog as printl
from twagenthelper import twAgentGetPage

glob_icon_num = 0
glob_last_cover = [None, None]

class CoverHelper:

	COVER_PIC_PATH = "/tmp/.Icon%d.jpg"
	NO_COVER_PIC_PATH = "/images/no_coverArt.png"

	def __init__(self, cover, callback=None, nc_callback=None):
		self._cover = cover
		self.picload = ePicLoad()
		self._no_picPath = "%s%s/%s%s" % (mp_globals.pluginPath, mp_globals.skinsPath, config.mediaportal.skin.value, self.NO_COVER_PIC_PATH)
		self._callback = callback
		self._nc_callback = nc_callback
		self.downloadPath = None
		self.coverTimerStart = eTimer()

	def getCoverTimerStart(self):
		self.coverTimerStart.startLongTimer(20)

	def downloadPage(self, url, path):
		d = twAgentGetPage(url)
		f = open(path, 'wb')
		d.addCallback(lambda x: f.write(x))
		d.addBoth(lambda _: f.close())
		d.addCallback(lambda _: path)
		return d

	def getCover(self, url, download_cb=None):
		global glob_icon_num
		global glob_last_cover

		self.getCoverTimerStart()
		if url:
			if url.startswith('http'):
				if glob_last_cover[0] == url and glob_last_cover[1]:
					self.showCoverFile(glob_last_cover[1])
					if download_cb:
						download_cb(glob_last_cover[1])
				else:
					glob_icon_num = (glob_icon_num + 1) % 2
					glob_last_cover[0] = url
					glob_last_cover[1] = None
					self.downloadPath = self.COVER_PIC_PATH % glob_icon_num
					d = self.downloadPage(url, self.downloadPath)
					d.addCallback(self.showCover)
					if download_cb:
						d.addCallback(self.cb_getCover, download_cb)
					d.addErrback(self.dataErrorP)
			elif url.startswith('file://'):
				self.showCoverFile(url[7:])
			else:
				self.showCoverNone()
		else:
			self.showCoverNone()

	def cb_getCover(self, result, download_cb):
		download_cb(result)

	def dataErrorP(self, error):
		printl(error,self,'E')
		self.showCoverNone()

	def showCover(self, picData):
		self.showCoverFile(self.downloadPath)
		glob_last_cover[1] = self.downloadPath
		return self.downloadPath

	def showCoverNone(self):
		if self._nc_callback:
			self._cover.hide()
			self._nc_callback()
		else:
			self.showCoverFile(self._no_picPath)

		return(self._no_picPath)

	def showCoverFile(self, picPath, showNoCoverart=True):
		if fileExists(picPath):
			self._cover.instance.setPixmap(gPixmapPtr())
			scale = AVSwitch().getFramebufferScale()
			size = self._cover.instance.size()
			if mp_globals.fakeScale:
				self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, "#00000000"))
			else:
				self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, "#FF000000"))
			self.updateCover(picPath)
		else:
			printl("Coverfile not found: %s" % picPath, self, "E")
			if showNoCoverart and picPath != self._no_picPath:
				self.showCoverFile(self._no_picPath)

		if self._callback:
			self._callback()

	def updateCover(self, picPath):
		if mp_globals.isDreamOS:
			res = self.picload.startDecode(picPath, False)
		else:
			res = self.picload.startDecode(picPath, 0, 0, False)

		if not res:
			ptr = self.picload.getData()
			if ptr != None:
				w = ptr.size().width()
				h = ptr.size().height()
				ratio = float(w) / float(h)
				if self._nc_callback and ratio > 1.05:
					self.showCoverNone()
				else:
					self._cover.instance.setPixmap(ptr)
					self._cover.show()