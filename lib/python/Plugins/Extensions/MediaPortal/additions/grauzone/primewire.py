# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import TwAgentHelper
import base64

class PrimeWireGenreScreen(MPScreen):

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
			"ok"    : self.keyOK,
			"0": self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("PrimeWire.ag")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.primewire.ag/"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('class="opener-menu-genre">(.*)class="opener-menu-section', data, re.S)
		Cats = re.findall('<a\shref="(.*?)">(.*?)</a>', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "http://www.primewire.ag" + Url + "&page="
				self.genreliste.append((Title, Url))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Featured Movies", "http://www.primewire.ag/index.php?sort=featured&page="))
			self.genreliste.insert(1, ("Popular Movies", "http://www.primewire.ag/index.php?sort=views&page="))
			self.genreliste.insert(2, ("Top Rated Movies", "http://www.primewire.ag/index.php?sort=ratings&page="))
			self.genreliste.insert(3, ("Newly Released Movies", "http://www.primewire.ag/index.php?sort=release&page="))
			self.genreliste.insert(4, ("TV Shows", "http://www.primewire.ag/?tv=&sort=views&page="))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(PrimeWireFilmlisteScreen, url, auswahl)

class PrimeWireFilmlisteScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Url, Genre):
		self.Url = Url
		self.Genre = Genre
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
			"ok"    : self.keyOK,
			"0": self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("PrimeWire.ag")
		self['ContentTitle'] = Label("Genre: %s" % self.Genre)
		self['Page'] = Label(_("Page:"))


		self.streamList = []
		self.handlung = ""
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = "%s%s" % (self.Url, str(self.page))
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.lastpage = re.findall('<div class="number_movies_result">(.*?)\sitems found</div>', data)
		if self.lastpage:
			self.lastpage = int(self.lastpage[0].replace(',',''))/24+1
		else:
			self.lastpage = 999
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		chMovies = re.findall('<div\sclass="index_item\sindex_item_ie">.*?<a\shref="(.*?)"\stitle="Watch.(.*?)"><img\ssrc="(.*?)"', data, re.S)
		if chMovies:
			for (chUrl,chTitle,chImage) in chMovies:
				chUrl = "http://www.primewire.ag" + chUrl
				chImage = "http:"+chImage
				self.streamList.append((decodeHtml(chTitle),chUrl,chImage))
				self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.keyLocked = False
			self.th_ThumbsQuery(self.streamList,0,1,2,None,None, self.page, self.lastpage)
			self.showInfos()

	def showInfos(self):
		self.image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(self.image)
		url = self['liste'].getCurrent()[0][1]
		getPage(url, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		Handlung = re.search('display:block;">(.*?)</p></td>', data, re.S)
		if Handlung:
			self.handlung = Handlung.group(1).strip()
		else:
			self.handlung = ""
		self['handlung'].setText(decodeHtml(self.handlung))

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if self.Genre == "TV Shows":
			self.session.open(PrimeWireEpisodeScreen, Link, Name)
		else:
			self.session.open(PrimeWireStreamsScreen, Link, Name, self.image, self.handlung)

class PrimeWireEpisodeScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0": self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("PrimeWire.ag")
		self['ContentTitle'] = Label("Episoden: %s" % self.Name)


		self.streamList = []
		self.handlung = ""
		self.image = None
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		getPage(self.Link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('class="choose_tabs">(.*?)class="download_link">', data, re.S)
		if parse:
			episoden = re.findall('class="tv_episode_item.*?">.*?<a\shref="(.*?)">.*?episode_name">\s{0,2}-\s{0,2}(.*?)</span', parse.group(1), re.S|re.I)
		if episoden:
			for (url,title) in episoden:
				episodes = re.findall('season-(.*?)-episode-(.*?)$', url, re.S)
				if int(episodes[0][0]) < 10:
					season = "S0"+str(episodes[0][0])
				else:
					season = "S"+str(episodes[0][0])
				if int(episodes[0][1]) < 10:
					episode = "E0"+str(episodes[0][1])
				else:
					episode = "E"+str(episodes[0][1])
				Title = "%s%s - %s" % (season, episode, title)
				url = "http://www.primewire.ag" + url
				self.streamList.append((decodeHtml(Title),url))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		url = self['liste'].getCurrent()[0][1]
		getPage(url, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		Image = re.search('og:image"\scontent="(.*?)"', data, re.S)
		Handlung = re.search('display:block;">(.*?)</p></td>', data, re.S)
		if Handlung:
			self.handlung = Handlung.group(1).strip()
		else:
			self.handlung = ""
		if Image:
			self.image = Image.group(1)
		else:
			self.image = None
		self['handlung'].setText(decodeHtml(self.handlung))
		CoverHelper(self['coverArt']).getCover(self.image)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(PrimeWireStreamsScreen, Link, Name, self.image, self.handlung)

class PrimeWireStreamsScreen(MPScreen):

	def __init__(self, session, Link, Name, Image, Handlung):
		self.Link = Link
		self.Name = Name
		self.image = Image
		self.handlung = Handlung
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0": self.closeAll,
			"cancel": self.keyCancel,
		}, -1)

		self['title'] = Label("PrimeWire.ag")
		self['ContentTitle'] = Label("Streams: %s" % self.Name)

		self.tw_agent_hlp = TwAgentHelper()
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		print self.Link
		getPage(self.Link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		streams = re.findall('<a href="/external.php\?title=.*?&url=(.*?)&domain=.*?document.writeln\(\'(.*?)\'\)', data, re.S)
		if streams:
			for (Url, StreamHoster) in streams:
				if isSupportedHoster(StreamHoster, True):
					self.streamList.append((StreamHoster, Url))
			if len(self.streamList) == 0:
				self.streamList.append((_('No supported streams found!'), None))
			else:
				self.keyLocked = False
		else:
			self.streamList.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.streamList))
		self['handlung'].setText(self.handlung)
		CoverHelper(self['coverArt']).getCover(self.image)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		url = base64.b64decode(url)
		print url
		get_stream_link(self.session).check_link(url, self.got_link, False)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.session.open(SimplePlayer, [(self.Name, stream_url, self.image)], showPlaylist=False, ltype='primewire', cover=True)