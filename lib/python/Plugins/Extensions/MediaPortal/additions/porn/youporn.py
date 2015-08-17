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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import TwAgentHelper
from Plugins.Extensions.MediaPortal.resources.aes_crypt import aes_decrypt_text

class youpornGenreScreen(MPScreen):

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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("YouPorn.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.youporn.com/categories/alphabetical/"
		getPage(url, headers={'Cookie': 'age_verified=1', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('<li\sclass=".*?"><a\shref="/category/(.*?)"\sclass=""\stitle="(.*?)"><span', data, re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "http://www.youporn.com/category/" + Url + '?page='
				self.genreliste.append((Title, Url))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Channels", "http://www.youporn.com/channels/most_subscribed/alltime/?page="))
			self.genreliste.insert(0, ("Popular by Country", "http://www.youporn.com/categories/"))
			self.genreliste.insert(0, ("Most Discussed", "http://www.youporn.com/most_discussed/?page="))
			self.genreliste.insert(0, ("Most Favorited", "http://www.youporn.com/most_favorited/?page="))
			self.genreliste.insert(0, ("Most Viewed", "http://www.youporn.com/most_viewed/?page="))
			self.genreliste.insert(0, ("Top Rated", "http://www.youporn.com/top_rated/?page="))
			self.genreliste.insert(0, ("Newest", "http://www.youporn.com/?page="))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Channels":
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(youpornChannelScreen, Link, Name)
		elif Name == "Popular by Country":
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(youpornCountryScreen, Link, Name)
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(youpornFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = 'http://www.youporn.com/search/?query=%s&page=' % (self.suchString)
			self.session.open(youpornFilmScreen, Link, Name)

class youpornCountryScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("YouPorn.com")
		self['ContentTitle'] = Label("Country Auswahl")
		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.genreliste = []
		url = self.Link
		getPage(url, headers={'Cookie': 'age_verified=1', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('class="categoryViewFlags">Popular\sby\sCountry(.*?)</div>', data, re.S)
		Cats = re.findall('<a\shref="(.*?)".*?/span>(.*?)</a>', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "http://www.youporn.com" + Url + "?page="
				self.genreliste.append((Title.strip(), Url))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(youpornFilmScreen, Link, Name)

class youpornChannelScreen(MPScreen, ThumbsHelper):

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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("YouPorn.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.genreliste = []
		url = "%s%s" % (self.Link, str(self.page))
		getPage(url, headers={'Cookie': 'age_verified=1', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		self.getLastPage(data, 'id="pagination">(.*?)</nav>')
		Cats = re.findall('<div\sclass="img"><a\shref="(.*?)"><img\ssrc="(.*?)"\salt="(.*?)"', data, re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				Url = "http://www.youporn.com" + Url + '?page='
				self.genreliste.append((Title, Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.genreliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(youpornFilmScreen, Link, Name)

class youpornFilmScreen(MPScreen, ThumbsHelper):

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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("YouPorn.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.tw_agent_hlp = TwAgentHelper(redir_agent=True)
		self.tw_agent_hlp.headers.addRawHeader('Cookie','age_verified=1')
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = "%s%s" % (self.Link, str(self.page))
		self.tw_agent_hlp.getWebPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'id="pagination">(.*?)</nav>')
		parse = re.search('Sub menu dropdown.*?/Sub menu dropdown(.*?)Our Friends', data, re.S)
		if not parse:
			parse = re.search('Sub menu dropdown.*?/Sub menu dropdown(.*?)pagination', data, re.S)
		if parse:
			Movies = re.findall('class="videoBox.*?<a\shref="(.*?)">.*?<img\ssrc=".*?"\salt="(.*?)".*?data-thumbnail="(.*?)".*?class="duration">(.*?)</span>.*?class="rating\sup"><i>(.*?)</i>', parse.group(1), re.S)
			if Movies:
				for (Url, Title, Image, Runtime, Rating) in Movies:
					Url = Url.replace("&amp;","&")
					self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Rating))
		if len(self.filmliste) == 0:
			self.filmliste.append(('Keine Filme gefunden.', '', None, '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		rating = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s\nRating: %s" % (runtime, rating))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = 'http://www.youporn.com' + self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link, headers={'Cookie': 'age_verified=1', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = None
		Title = self['liste'].getCurrent()[0][0]
		encrypted_links = re.findall(r'encryptedQuality720URL\s=\s\'([a-zA-Z0-9+/]+={0,2})\',', data)
		for encrypted_link in encrypted_links:
			videoPage = aes_decrypt_text(encrypted_link, Title, 32)
		if videoPage:
			Title = '%s_720p' % Title
		else:
			videoPage = re.findall('videoSrc\s=\s\'(.*?)\',', data, re.S)
			if videoPage:
				videoPage = videoPage[-1]
		if videoPage:
			self.keyLocked = False
			self.session.open(SimplePlayer, [(Title, videoPage)], showPlaylist=False, ltype='youporn')