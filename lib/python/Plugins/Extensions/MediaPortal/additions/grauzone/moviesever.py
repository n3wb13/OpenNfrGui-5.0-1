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

glob_agent = 'Mozilla/5.0 (Windows NT 6.1; rv:32.0) Gecko/20100101 Firefox/32.0'
BASE_URL = 'http://moviesever.com'

class movieseverMain(MPScreen):

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

		self['title'] = Label("MoviesEver")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self.streamList.append(("New Added", "/page/"))
		self.streamList.append(("Most Viewed", "/most-viewed/page/"))
		self.streamList.append(("Most Commented", "/most-commented/page/"))
		self.streamList.append(("Most Rated", "/category/action/page/"))
		self.streamList.append(("Action", "/category/action/page/"))
		self.streamList.append(("Adventure", "/category/adventure/page/"))
		self.streamList.append(("Animation", "/category/animation/page/"))
		self.streamList.append(("Biography", "/category/biography/page/"))
		self.streamList.append(("Comedy", "/category/comedy/page/"))
		self.streamList.append(("Drama", "/category/drama/page/"))
		self.streamList.append(("Familie", "/category/familie/page/"))
		self.streamList.append(("Fantasy", "/category/fantasy/page/"))
		self.streamList.append(("History", "/category/history/page/"))
		self.streamList.append(("Horror", "/category/horror/page/"))
		self.streamList.append(("Mystery", "/category/mystery/page/"))
		self.streamList.append(("Romantik", "/category/romance/page/"))
		self.streamList.append(("Sci-Fi", "/category/sci-fi/page/"))
		self.streamList.append(("Thriller", "/category/thriller/page/"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		url = BASE_URL + self['liste'].getCurrent()[0][1]
		self.session.open(movieseverParsing, auswahl, url)

class movieseverParsing(MPScreen, ThumbsHelper):

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

		self['title'] = Label("MoviesEver")
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
		self.getLastPage(data, "<span class='pages'>Seite.*?von\s(\d+)</span>")
		last = re.findall("<span class='pages'>Seite.*?von\s(\d+)</span>", data, re.S)
		if last:
			self.lastpage = int(last[0])
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))

		serien = re.findall('<span class="q-.*?">.*?<img src="(http://moviesever.com/wp-content/uploads/.*?)".*?<div class="movief"><a href="(.*?)">(.*?)</a></div>', data, re.S|re.I)
		if serien:
			for (Image, Url, Title) in serien:
				self.streamList.append((decodeHtml(Title), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page, self.lastpage)
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
		movie_url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(showStreams, stream_name, movie_url, cover)

class showStreams(MPScreen):

	def __init__(self, session, stream_name, movie_url, cover):
		self.stream_name = stream_name
		self.movie_url = movie_url
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

		self['title'] = Label("MoviesEver")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.stream_name)

		self.episoden = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.cover)
		getPage(self.movie_url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		stream2k = re.search('src="(http://stream2k.tv/.*?)"', data)
		if stream2k:
			url = urllib.unquote(stream2k.group(1))
			getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStreams).addErrback(self.dataError)
		else:
			vkpass = re.search('src="(http://vkpass.com/token.*?)"', data)
			if vkpass:
				url = urllib.unquote(vkpass.group(1))
				headers_data = {'Content-Type':'application/x-www-form-urlencoded',
								'Cookie': 'lang=DE; 09ffa5fd853655fda785215db07180d19b9d94a862d=OK',
								'Referer': self.movie_url
								}
				getPage(url, agent=glob_agent, headers=headers_data).addCallback(self.getStreams).addErrback(self.dataError)

	def getStreams(self, data):
		self.streamList = []
		raw_streams = ""
		raw_streams = re.findall('"file":"(.*?)", "label":"(.*?)"', data, re.S)
		raw_streams += re.findall('file:"(.*?)", label:"(.*?)"', data, re.S)
		if raw_streams:
			for streamUrl,streamName in raw_streams:
				self.streamList.append((streamName, streamUrl.replace('\\','')))
			self.keyLocked = False
		else:
			self.streamList.append(("Error", None))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.ml.moveToIndex(0)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_url = self['liste'].getCurrent()[0][1]
		if stream_url is not None:
			mp_globals.player_agent = glob_agent
			self.session.open(SimplePlayer, [(self.stream_name, stream_url, self.cover)], cover=True, showPlaylist=False, ltype='moviesever')