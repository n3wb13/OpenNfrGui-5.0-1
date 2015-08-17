﻿# -*- coding: utf-8 -*-
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

class atvGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("ATV Mediathek")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "http://atv.at/mediathek"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('class="mod_programs">(.*?)/mod_programs', data, re.S)
		if parse:
			raw = re.findall('href="(.*?)">.*?src="(.*?)"\salt="(.*?)"', parse.group(), re.S)
			if raw:
				for ( Content, Image, Title) in raw:
					print Title
					if Title != "ATV Aktuell Österreich Trend":
						self.filmliste.append((decodeHtml(Title), Content, Image))
				self.ml.setList(map(self._defaultlistcenter, self.filmliste))
				self.keyLocked = False
				self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
				self.showInfos()

	def showInfos(self):
		name = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(decodeHtml(name))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(atvListScreen, Link, Name)

class atvListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
		}, -1)

		self['title'] = Label("ATV Mediathek")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['Page'] = Label(_("Page:"))

		self.filmliste = []
		self.handlung = ''
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		getPage(self.Link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('<!--\smod_teasers\s-->(.*?)<!--\s/mod_teasers\s-->', data, re.S)
		if not re.match('http://atv.at/uri/', self.Link):
			handlung = re.search('<meta\sname="description"\scontent="(.*?)"', data, re.S)
			if handlung:
				self.handlung = handlung.group(1)
		if parse:
			raw = re.findall('<li class="teaser">.*?href="(.*?)".*?teaser_image_file(/|\%252F)(.*?jpg).*?class="title">(.*?)<', parse.group(), re.S)
			if raw:
				for (Url, x, Image, Title) in raw:
					Image = 'http://atv.at/static/assets/cms/media_items/teaser_image_file/%s' % Image
					self.filmliste.append((decodeHtml(Title), Url, Image))
		nextpage = re.search('data-jsb="url=(.*?)" style=.*?Weitere Folgen', data, re.S)
		if nextpage:
			self.Link = urllib.unquote_plus(nextpage.group(1))
			self.loadPage()
		if len(self.filmliste) == 0:
			self.filmliste.append(("No channels found.", "",""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.showInfos()
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None ,1 ,1, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		self['handlung'].setText(decodeHtml(self.handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		getPage(Link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStreamLink).addErrback(self.dataError)

	def getStreamLink(self, data):
		Name = self['liste'].getCurrent()[0][0]
		Linkliste = []
		part = re.search('jsb_video/VideoPlaylist(.*?)/detail_content', data, re.S)
		if part:
			raw = re.findall('quot;(rtsp:\\\/\\\/109.68.230.208:1935\\\/vod\\\/_definst_\\\/.*?.mp4)', part.group(1), re.S)
			if raw:
				for Link in raw:
					Link = Link.replace('\/','/')
					Streampart = "Teil %s" % str(len(Linkliste)+1)
					Linkliste.append((Streampart, Link))
		if len(Linkliste) == 1:
			self.session.open(SimplePlayer, [(Name, Linkliste[0][1])], showPlaylist=False, ltype='atv')
		elif len(Linkliste) >= 1:
			self.session.open(atvPartScreen, Name, Linkliste)

class atvPartScreen(MPScreen):

	def __init__(self, session, Name, Linkliste):
		self.Linkliste = Linkliste
		self.Name = Name
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
		}, -1)

		self['title'] = Label("ATV Mediathek")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label("%s" % self.Name)

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.parseData)

	def parseData(self):
		self.ml.setList(map(self._defaultlistcenter, self.Linkliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		playIdx = self['liste'].getSelectedIndex()
		self.session.open(SimplePlayer, self.Linkliste, playIdx=playIdx, showPlaylist=False, playAll=True, ltype='atv')