# -*- coding: utf-8 -*-
###############################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2015
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
###############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

class livestreamtvMain(MPScreen):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("live-stream.tv")
		self['ContentTitle'] = Label(_("Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		url = "http://www.live-stream.tv/online/fernsehen/ard.html"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		sender = re.findall('<div\sclass="nownext_entry"><div\sclass="nownext_image"><a\shref="(.*?)"><img\ssrc="(.*?)"\salt="(.*?).Live\sStream"></a></div><div\sclass="nownext_title">(.*?)</div><div\sclass="nownext_progress"><div\sclass="nownext_progressbar".*?<div\sstyle=".*?">(.*?)</div></div></div><div\sclass="fc"></div></div>', data, re.S|re.I)
		if sender:
			for url,image,station,title,time in sender:
				if station != "Fussball":
					self.streamList.append((decodeHtml(time + ' - ' + title), title, station, url, time, image))
			self.ml.setList(map(self.livestreamtvListEntry, self.streamList))
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		self.station = self['liste'].getCurrent()[0][2]
		url = "http://embed.live-stream.tv/%s" % self.station
		getPage(url).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		title = self['liste'].getCurrent()[0][1]
		get_packedjava = re.findall("(eval.function.*?)</script>", data, re.S)
		if get_packedjava:
			sJavascript = get_packedjava[0]
			sUnpacked = unpack(sJavascript)
			if sUnpacked:
				stream_ip = re.findall('streamer:"(rtmp://.*?)"', sUnpacked)
				if stream_ip:
					stream_ip = stream_ip[0]
					stream_url = "%s app=live/ swfUrl=http://static.live-stream.tv/player/player.swf pageUrl=http://www.live-stream.tv/online/fernsehen/%s.html playpath=%s.stream" % (stream_ip, self.station, self.station)
					self.session.open(SimplePlayer, [(self.station.upper() + ' - ' + title, stream_url)], showPlaylist=False, ltype='livestreamtv')