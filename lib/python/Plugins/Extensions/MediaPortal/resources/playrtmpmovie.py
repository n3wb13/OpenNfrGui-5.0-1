# -*- coding:utf-8 -*-

from Plugins.Extensions.MediaPortal.plugin import _
import mp_globals
from imports import *
from messageboxext import MessageBoxExt
from Components.config import config
from urllib2 import Request, urlopen
from enigma import eTimer, eConsoleAppContainer, eBackgroundFileEraser
from Components.Slider import Slider
from Components.Sources.StaticText import StaticText
from os import path as os_path, readlink as os_readlink, system as os_system
from Tools import ASCIItranslit

class PlayRtmpMovie(Screen):

	def __init__(self, session, movieinfo, movietitle, playCallback=None):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/PlayRtmpMovie.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/PlayRtmpMovie.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)
		self['title'] = Label("Caching...")
		self.setTitle("Caching...")

		self.playCallback = playCallback
		self.url = movieinfo[0]
		self.filename = movieinfo[1]
		self.movietitle = movietitle
		self.movieinfo = movieinfo
		self.destination = config.mediaportal.storagepath.value
		#self.moviepath = self.destination + ASCIItranslit.legacyEncode(self.filename)
		self.moviepath = self.destination + ".rtmp_movie"

		self.streamactive = False
		self.isVisible = True

		self.container=eConsoleAppContainer()
		if mp_globals.isDreamOS:
			self.container.appClosed_conn = self.container.appClosed.connect(self.copyfinished)
			self.container.stdoutAvail_conn = self.container.stdoutAvail.connect(self.progressUpdate)
			self.container.stderrAvail_conn = self.container.stderrAvail.connect(self.progressUpdate)
		else:
			self.container.appClosed.append(self.copyfinished)
			self.container.stdoutAvail.append(self.progressUpdate)
			self.container.stderrAvail.append(self.progressUpdate)
		self.container.setCWD(self.destination)

		self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()

		self.BgFileEraser = eBackgroundFileEraser.getInstance()

		self.filesize = 0.0 # in bytes

		self.dummyfilesize = False
		self.lastcmddata = None
		self.lastlocalsize = 0.0
		self.localsize = 0.0
		self.isplaying = False
		self.autoplaythreshold = config.mediaportal.autoplayThreshold.value

		self["key_green"] = Button(_("Play"))
		self["key_red"] = Button(_("Cancel"))
		self["key_blue"] = Button(_("Hide"))

		self["label_filename"] = StaticText("File: %s" % (self.filename))
		self["label_progress"] = StaticText("Progress: N/A")
		self["label_speed"] = StaticText("Speed: N/A")
		self["label_timeleft"] = StaticText("Time left: N/A")

		self["actions"] = ActionMap(["MP_Actions"],
		{
			"cancel": self.exit,
			"ok": self.okbuttonClick,
			"red": self.exit,
			"green": self.playfile,
			"blue": self.visibility
		}, -1)

		self.StatusTimer = eTimer()
		if mp_globals.isDreamOS:
			self.StatusTimer_conn = self.StatusTimer.timeout.connect(self.UpdateStatus)
		else:
			self.StatusTimer.callback.append(self.UpdateStatus)

		self.activityslider = Slider(0, 100)
		self["activityslider"] = self.activityslider

		self.onFirstExecBegin.append(self.firstExecBegin)

	def firstExecBegin(self):
		self.progressperc = 0
		if not fileExists("/usr/bin/rtmpdump"):
			message = self.session.open(MessageBoxExt, _("RTMPDump is required for playback of this stream, please install it first."), MessageBoxExt.TYPE_INFO, timeout=10)
			self.exit()

		if not self.checkStoragePath():
			self.exit()

		self.copyfile()

	def okbuttonClick(self):
		if self.isVisible == False:
			self.visibility()

	def checkStoragePath(self):
		tmppath = config.mediaportal.storagepath.value
		if tmppath != "/tmp" and tmppath != "/media/ba":
			if os_path.islink(tmppath):
				tmppath = os_readlink(tmppath)
			loopcount = 0
			while not os_path.ismount(tmppath):
				loopcount += 1
				tmppath = os_path.dirname(tmppath)
				if tmppath == "/" or tmppath == "" or loopcount > 50:
					self.session.open(MessageBoxExt, _("Error: Can not create cache-folders inside flash memory. Check your Cache-Folder Settings!"), type=MessageBoxExt.TYPE_INFO, timeout=20)
					return False

		os_system("mkdir -p "+config.mediaportal.storagepath.value)
		if not os_path.exists(config.mediaportal.storagepath.value):
			self.session.open(MessageBoxExt, _("Error: No write permission to create cache-folders. Check your Cache-Folder Settings!"), type=MessageBoxExt.TYPE_INFO, timeout=20)
			return False
		else:
			return True

	def updateSPProgressbar(self):
		import mp_globals
		if self.isplaying and mp_globals.yt_download_progress_widget:
			mp_globals.yt_download_progress_widget.setValue(self.progressperc)

	def UpdateStatus(self):
		#print "UpdateStatus:"
		if self.progressperc > 0 and fileExists(self.moviepath, 'r'):
			self.localsize = float(os_path.getsize(self.moviepath))
			self.filesize = round(self.localsize/self.progressperc*100, 0)
			self.dummyfilesize = True
		else:
			self.localsize = 0.0

		if int(self.progressperc) > 0:
			self["activityslider"].setValue(self.progressperc)
			reactor.callLater(1, self.updateSPProgressbar)

		if self.lastlocalsize > 0.0:
			transferspeed = int((self.localsize - self.lastlocalsize) / 1024.0 / 5)
			kbytesleft = int(round((self.filesize - self.localsize) / 1024.0, 0))
			if kbytesleft < 0:
				kbytesleft = 0
			if transferspeed > 0:
				timeleft = round(float(kbytesleft) / transferspeed / 60.0, 1)
			else:
				timeleft = 0
		else:
			transferspeed = 0
			kbytesleft = 0
			timeleft = 0

		self.lastlocalsize = self.localsize

		self["label_speed"].setText("Speed: " + str(transferspeed) + " KBit/s")
		self["label_progress"].setText("Progress: " + str(int(self.localsize / 1024.0 / 1024.0 + 0.5)) + "MB of " + str(int(self.filesize / 1024.0 / 1024.0 + 0.5)) + "MB (" + str(self.progressperc) + "%)")
		self["label_timeleft"].setText("Time left: " + str(timeleft) + " Minutes")
		#print "sz: ",self.localsize," lsz: ", self.lastlocalsize, " dsz: ", self.dummyfilesize, " fsz: ",self.filesize
		if self.progressperc >= self.autoplaythreshold and not self.isplaying:
			self.playfile()
		self.StatusTimer.start(5000, True)

	def copyfile(self):
		#print "copyfile:"
		if self.url[0:4] == "rtmp":
			cmd = "rtmpdump -r '%s' -o '%s'" % (self.url, self.moviepath)
		else:
			self.session.openWithCallback(self.exit, MessageBoxExt, _("This stream can not get saved on HDD\nProtocol %s not supported :(") % self.url[0:5], MessageBoxExt.TYPE_ERROR)
			return

		if fileExists(self.moviepath, 'r'):
			self.localsize = os_path.getsize(self.moviepath)
			if self.localsize > 0 and self.localsize >= self.filesize:
				cmd = "echo File already downloaded! Skipping download ..."
			elif self.localsize == 0:
				self.BgFileEraser.erase(self.moviepath)

		self.StatusTimer.start(1000, True)
		self.streamactive = True

		print "[PlayRtmp] execute command: " + cmd
		self.container.execute(cmd)

	def progressUpdate(self, data):
#		print 'progressUpdate:'
		self.lastcmddata = data
		if data.endswith('%)'):
			startpos = data.rfind("sec (")+5
			if startpos and startpos != -1:
				self.progressperc = int(float(data[startpos:-4]))
				if self.progressperc > 100:
					self.progressperc = 100

	def copyfinished(self,retval):
		#print "copyfinished:"
		self.container.kill()
		self.streamactive = False
		self.progressperc = 100
		self.filesize = float(os_path.getsize(self.moviepath))
		if not self.isplaying:
			self.playfile()
		self.UpdateStatus()

	def playfile(self):
		from Plugins.Extensions.MediaPortal.resources.simpleplayer import SimplePlayer
		if self.lastlocalsize > 0:
			if len(self.movieinfo) == 3:
				movie_img = self.movieinfo[2]
			else:
				movie_img = None
			self.isplaying = True
			if not self.playCallback:
				self.session.openWithCallback(self.MoviePlayerCallback, SimplePlayer, [(self.movietitle, self.moviepath, movie_img)], showPlaylist=False, ltype='playrtmp')
			else:
				self.playCallback(self.movietitle, self.moviepath, movie_img, self.MoviePlayerCallback, self.exit)
		else:
			self.session.openWithCallback(self.exit, MessageBoxExt, _("Error downloading file:\n%s") % self.lastcmddata, MessageBoxExt.TYPE_ERROR)

	def MoviePlayerCallback(self, response=None):
		print "movieplayercallback:",response
		if self.isVisible == False:
			self.visibility()

	def visibility(self):
		if self.isVisible == True:
			self.isVisible = False
			self.hide()
		else:
			self.isVisible = True
			self.show()

	def exit(self, retval=None):
#		if self.isVisible == False:
#			self.visibility()
#			return

		self.container.kill()
		self.BgFileEraser.erase(self.moviepath)

		try:
			self.StatusTimer.stop()
			del self.StatusTimer
		except:
			pass
		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.session.nav.playService(self.lastservice)
		self.close()