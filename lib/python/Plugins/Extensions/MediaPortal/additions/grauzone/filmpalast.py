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

class filmPalastMain(MPScreen):

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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FilmPalast.to")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self.streamList.append(("Neueste Filme", "movies/new/page/"))
		self.streamList.append(("Serien", "serien/view/"))
		self.streamList.append(("Abenteuer", "search/genre/Abenteuer/"))
		self.streamList.append(("Action", "search/genre/Action/"))
		self.streamList.append(("Adventure", "search/genre/Adventure/"))
		self.streamList.append(("Animation", "search/genre/Animation/"))
		self.streamList.append(("Biographie", "search/genre/Biographie/"))
		self.streamList.append(("Comedy", "search/genre/Comedy/"))
		self.streamList.append(("Crime", "search/genre/Crime/"))
		self.streamList.append(("Documentary", "search/genre/Documentary/"))
		self.streamList.append(("Drama", "search/genre/Drama/"))
		self.streamList.append(("Familie", "search/genre/Familie/"))
		self.streamList.append(("Fantasy", "search/genre/Fantasy/"))
		self.streamList.append(("History", "search/genre/History/"))
		self.streamList.append(("Horror", "search/genre/Horror/"))
		self.streamList.append(("Komödie", "search/genre/Kom%C3%B6die/"))
		self.streamList.append(("Krieg", "search/genre/Krieg/"))
		self.streamList.append(("Krimi", "search/genre/Krimi/"))
		self.streamList.append(("Musik", "search/genre/Musik/"))
		self.streamList.append(("Mystery", "search/genre/Mystery/"))
		self.streamList.append(("Romanze", "search/genre/Romanze/"))
		self.streamList.append(("Sci-Fi", "search/genre/Sci-Fi/"))
		self.streamList.append(("Sport", "search/genre/Sport/"))
		self.streamList.append(("Thriller", "search/genre/Thriller/"))
		self.streamList.append(("Western", "search/genre/Western/"))
		self.streamList.append(("Zeichentrick", "search/genre/Zeichentrick/"))
		self.streamList.append(("0-9", "search/alpha/0-9/"))
		for c in xrange(26):
			self.streamList.append((chr(ord('A') + c), 'search/alpha/' + chr(ord('A') + c) + '/'))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		url = 'http://www.filmpalast.to/' + self['liste'].getCurrent()[0][1]
		if auswahl == "Serien":
			self.session.open(filmPalastSerieParsing, auswahl, url)
		else:
			self.session.open(filmPalastParsing, auswahl, url)

class filmPalastSerieParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FilmPalast.to")
		self['ContentTitle'] = Label("%s" % self.genre)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		raw = re.findall('<section id="serien">(.*?)</section>', data, re.S)
		if raw:
			serien = re.findall('<a href="(http://www.filmpalast.to/serien/serie/.*?/(\d+))">', raw[0])
			if serien:
				for url,staffel in serien:
					title = re.findall('http://www.filmpalast.to/serien/serie/(.*?)/', url)
					title = "%s - Staffel %s" % (title[0].replace('_',' '), staffel)
					self.streamList.append((decodeHtml(title), url))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
			self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(filmPalastEpisodenParsing, stream_name, url)

class filmPalastEpisodenParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FilmPalast.to")
		self['ContentTitle'] = Label(_("Episode Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		episoden = re.findall('<a href="(http://www.filmpalast.to/movies/.*?)" title="(.*?)"> <img src="(.*?)" class="cover-opacity"', data)
		if episoden:
			for (url, title, image) in episoden:
				image = "http://www.filmpalast.to"+image
				self.streamList.append((decodeHtml(title), url, image))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
			self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(filmPalastStreams, stream_name, url, cover)

class filmPalastParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("FilmPalast.to")
		self['ContentTitle'] = Label("%s" % self.genre)

		self['Page'] = Label(_("Page:"))

		self.page = 1
		self.lastpage = 1
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = self.url+str(self.page)
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, 'id="paging">(.*?)</div>')
		movies = re.findall('<a href="(http://www.filmpalast.to/.*?)" title="(.*?)"> <img src="(.*?.jpg)"', data)
		if movies:
			for (Url, Title, Image) in movies:
				Image = "http://www.filmpalast.to" + Image
				self.streamList.append((decodeHtml(Title), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
			self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(filmPalastStreams, stream_name, url, cover)

class filmPalastStreams(MPScreen):

	def __init__(self, session, stream_name, url, cover):
		self.stream_name = stream_name
		self.url = url
		self.cover = cover
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("FilmPalast.to")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.stream_name)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.streamList = []
		streams = re.findall('class="hostBg.*?stream-src.*?href="(http://(.*?)\/.*?)"', data, re.S)
		if streams:
			for (Url, Hoster) in streams:
					if isSupportedHoster(Hoster, True):
						Hoster = Hoster.replace('www.','')
						self.streamList.append((Hoster, Url))
			self.ml.setList(map(self._defaultlisthoster, self.streamList))
			CoverHelper(self['coverArt']).getCover(self.cover)
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamUrl = self['liste'].getCurrent()[0][1]
		print streamUrl
		get_stream_link(self.session).check_link(streamUrl, self.playfile)

	def playfile(self, stream_url):
		if stream_url != None:
			self.session.open(SimplePlayer, [(self.stream_name, stream_url, self.cover)], showPlaylist=False, ltype='filmpalast', cover=True)