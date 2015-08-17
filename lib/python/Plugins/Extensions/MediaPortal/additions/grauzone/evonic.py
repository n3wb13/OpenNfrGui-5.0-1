# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.configlistext import ConfigListScreenExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

config.mediaportal.evonic_userName = ConfigText(default="USERNAME", fixed_size=False)
config.mediaportal.evonic_userPass = ConfigPassword(default="PASSWORD", fixed_size=False)
config.mediaportal.evonic_sortABC = ConfigYesNo(default = False)

std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5',
}

ck = {}

class showevonicGenre(MPScreen):

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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"green": self.loginSetup,
			"menu": self.loginSetup,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label("Try Login...")
		self['F2'] = Label(_("Setup"))

		self.loginOK = False
		self.genreliste = []
		self.searchText = ""
		self.stoken = ""
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onFirstExecBegin.append(self.login)

	def login(self):
		self.username = config.mediaportal.evonic_userName.value
		self.password = config.mediaportal.evonic_userPass.value
		print "Login:", self.username, self.password
		self['ContentTitle'].setText("Try Login..")

		if self.username == "USERNAME" and self.password == "PASSWORD":
			if mp_globals.isDreamOS:
				self.session.openWithCallback(self.callBackSetup, meSetupScreen, is_dialog=True)
			else:
				self.session.openWithCallback(self.callBackSetup, meSetupScreen)
		else:
			self.loginUrl = 'http://evonic.tv/forum/login.php?do=login'
			loginData = {'vb_login_username': self.username, 'vb_login_password': self.password, 'do': 'login'}
			getPage(self.loginUrl, method='POST',
					postdata=urlencode(loginData), cookies=ck,
					headers={'Content-Type':'application/x-www-form-urlencoded','User-agent': 'Mozilla/4.0', 'Referer': 'http://www.hellboundhackers.org/index.php', }).addCallback(self.loginRefresh).addErrback(self.dataError)

	def loginRefresh(self, data):
		if "Danke" in str(data):
			self.loginOK = True
			cookieuser = '1'
			password_md5 = md5.md5(self.password).hexdigest()

			loginData = {'vb_login_username': self.username,
						 's': '',
						 'securitytoken': 'guest',
						 'do': 'login',
						 'vb_login_md5password': password_md5,
						 'vb_login_md5password_utf': password_md5,
						 'cookieuser' : cookieuser
						 }

			getPage(self.loginUrl, method="POST",
					postdata=urlencode(loginData), headers={'Content-Type': 'application/x-www-form-urlencoded'},
					followRedirect=True, timeout=30, cookies=ck).addCallback(self.loginDone).addErrback(self.dataError)
		else:
			self.loginOK = False
			self['ContentTitle'].setText("Login fehlgeschlagen !")

	def accountInfos(self, data):
		print "hole member status infos.."
		if re.match('.*?Status:.*?Premium Member', data, re.S|re.I):
			statusUrl = 'http://evonic.tv/forum/payments.php'
			getPage(statusUrl, method="GET",
					headers={'Content-Type': 'application/x-www-form-urlencoded'},
					followRedirect=True, timeout=30, cookies=ck).addCallback(self.accountInfosData).addErrback(self.dataError)
		else:
			self['ContentTitle'].setText("Du bist kein Premium Member !")

	def accountInfosData(self, data):
		print "hole account infos.."
		infos = re.findall('<dt>Startdatum</dt>.*?<dd>(.*?)</dd>.*?<dt>L.*?t aus am</dt>.*?<dd>(.*?)</dd>.*?<p class="description">(.*?)</p>', data, re.S)
		if infos:
			print infos
			(reg, bis, was) = infos[0]
			#acci = "Benutzer: %s - %s: Registriert: %s -> %s" % (self.username, was, reg, bis)
			acci = "%s: -> %s" % (was, bis)
			print acci
			self['ContentTitle'].setText(str(acci))

	def loginDone(self, data):
		getPage(self.loginUrl, method="GET", headers={'Content-Type': 'application/x-www-form-urlencoded'},
				followRedirect=True, timeout=30, cookies=ck).addCallback(self.accountInfos).addErrback(self.dataError)

		secutoken = re.findall('var SECURITYTOKEN = "(.*?)"', data, re.S)
		if secutoken:
			self.stoken = secutoken[0]
			print "SECURITYTOKEN:", self.stoken

		self.genreListe = []
		self.genreListe.append(("Watchlist", "dump"))
		self.genreListe.append(("Suche", "suche"))
		self.genreListe.append(("Aktuelle Filme", "http://evonic.tv/forum/content.php?r=3938-Aktuelle-HD-Filme&page="))
		self.genreListe.append(("Neueinsteiger", "http://evonic.tv/forum/content.php?r=1969-Aktuelle-HD-Filme&page="))
		self.genreListe.append(("Cineline", "http://evonic.tv/forum/list.php?r=category/169&page="))
		self.genreListe.append(("HD-Collection", "http://evonic.tv/forum/content.php?r=3501-hd-collection&page="))
		self.genreListe.append(("Serien Charts", "http://evonic.tv/forum/content.php?r=1997-serien-charts&page="))
		self.genreListe.append(("HD-Serien", "http://evonic.tv/forum/content.php?r=5993-Serien&page="))
		self.genreListe.append(("Century", "dump"))
		self.genreListe.append(("Imdb", "dump"))
		self.genreListe.append(("Imdb Top 1000", "dump"))
		self.genreListe.append(("3D-Charts", "http://evonic.tv/forum/content.php?r=5440-3d-charts&page="))
		self.genreListe.append(("3D", "http://evonic.tv/forum/content.php?r=4225-3d-filme&page="))
		self.genreListe.append(("HD-Charts", "http://evonic.tv/forum/content.php?r=1989-HD-Charts&page="))
		self.genreListe.append(("Alle HD Premium Streams", "http://evonic.tv/forum/content.php?r=1669-hd-filme&page="))
		self.genreListe.append(("Abenteuer", "http://evonic.tv/forum/list.php?r=category/65-HD-Abenteuer&page="))
		self.genreListe.append(("Action", "http://evonic.tv/forum/list.php?r=category/35-HD-Action&page="))
		self.genreListe.append(("Biografie", "http://evonic.tv/forum/list.php?r=category/70-HD-Biografie&page="))
		self.genreListe.append(("Doku", "http://evonic.tv/forum/list.php?r=category/64-HD-Doku&page="))
		self.genreListe.append(("Drama", "http://evonic.tv/forum/list.php?r=category/36-HD-Drama&page="))
		self.genreListe.append(("Fantasy", "http://evonic.tv/forum/list.php?r=category/37-HD-Fantasy&page="))
		self.genreListe.append(("Horror", "http://evonic.tv/forum/list.php?r=category/38-HD-Horror&page="))
		self.genreListe.append(("Komödie", "http://evonic.tv/forum/list.php?r=category/39-HD-Kom%F6die&page="))
		self.genreListe.append(("Kriegsfilm", "http://evonic.tv/forum/list.php?r=category/66-HD-Kriegsfilm&page="))
		self.genreListe.append(("Krimi", "http://evonic.tv/forum/list.php?r=category/56-HD-Krimi&page="))
		self.genreListe.append(("Musik", "http://evonic.tv/forum/list.php?r=category/63-HD-Musik&page="))
		self.genreListe.append(("Mystery", "http://evonic.tv/forum/list.php?r=category/62-HD-Mystery&page="))
		self.genreListe.append(("Romanze", "http://evonic.tv/forum/list.php?r=category/40-HD-Romanze&page="))
		self.genreListe.append(("SciFi", "http://evonic.tv/forum/list.php?r=category/41-HD-SciFi&page="))
		self.genreListe.append(("Thriller", "http://evonic.tv/forum/list.php?r=category/42-HD-Thriller&page="))
		self.genreListe.append(("Zeichentrick", "http://evonic.tv/forum/list.php?r=category/43-HD-Zeichentrick&page="))
		self.ml.setList(map(self._defaultlistcenter, self.genreListe))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		if not self.keyLocked and self.loginOK:
			enterAuswahlLabel = self['liste'].getCurrent()[0][0]
			enterAuswahlLink = self['liste'].getCurrent()[0][1]

			print "Select:", enterAuswahlLabel, enterAuswahlLink

			if enterAuswahlLabel == "Century":
				self.session.open(meCenturyScreen)
			elif enterAuswahlLabel == "Imdb":
				self.session.open(meImdbScreen)
			elif enterAuswahlLabel == "Watchlist":
				self.session.open(meWatchlistScreen)
			elif enterAuswahlLabel == "Imdb Top 1000":
				self.session.open(meTimdbGenreScreen, self.stoken)
			elif enterAuswahlLabel == "Suche":
				self.session.openWithCallback(self.mySearch, VirtualKeyBoardExt, title = (_("Search:")), text = self.searchText, is_dialog=True)
			else:
				self.session.open(meMovieScreen, enterAuswahlLink, enterAuswahlLabel)

	def mySearch(self, callback = None):
		print 'mySearch'
		if callback != None:
			self.searchTxt = callback
			self.session.open(meSearchScreen, self.searchTxt, self.stoken)

	def loginSetup(self):
		if mp_globals.isDreamOS:
			self.session.openWithCallback(self.callBackSetup, meSetupScreen, is_dialog=True)
		else:
			self.session.openWithCallback(self.callBackSetup, meSetupScreen)

	def callBackSetup(self, answer):
		if answer:
			self.login()

class meSearchScreen(MPScreen):

	def __init__(self, session, search, stoken):
		self.search = search
		self.stoken = stoken
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"green" : self.addWatchlist,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label("Suche: %s" % self.search)
		self['F2'] = Label(_("Add to Watchlist"))

		self.searchList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://evonic.tv/forum/ajaxlivesearch.php?do=search"
		print self.search, self.stoken

		postData = {'do': 'search',
					 'keyword': self.search,
					 'lsasort': 'lastpost',
					 'lsasorttype': 'DESC',
					 'lsatype': 0,
					 'lsawithword': 1,
					 'lsazone': '',
					 's': '',
					 'securitytoken': self.stoken
					 }

		getPage(url, method="POST", postdata=urlencode(postData), cookies=ck,
			headers={'Content-Type': 'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest', 'Referer': 'http://evonic.tv/forum/content.php'},
			followRedirect=True, timeout=30).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		found = re.findall('<span><a href=".*?" title="Stream">Stream</a></span>.*?<a href="(http://evonic.tv/forum/showthread.php\?t=.*?)" title="(.*?)">', data, re.S)
		#found = re.findall('<span><a href=".*?" title="Stream">Stream</a></span>.*?<a href="http://evonic.tv/forum/showthread.php\?t=(.*?)" title="(.*?)">', data, re.S)
		if found:
			self.searchList = []
			for link,title in found:
				#link = "http://evonic.tv/forum/content.php?r=%s" % id
				print title, link
				self.searchList.append((title,link))
		self.ml.setList(map(self._defaultlistleft, self.searchList))

		if len(self.searchList) != 0:
			self.keyLocked = False
			self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		check = self['liste'].getCurrent()
		if check == None:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		print self.streamName, streamLink
		getPage(streamLink, method="GET", cookies=ck,
			headers={'Content-Type': 'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest', 'Referer': 'http://evonic.tv/forum/content.php'},
			followRedirect=True, timeout=30).addCallback(self.loadRefreshData).addErrback(self.dataError)

	def loadRefreshData(self, data):
		refreshUrl = re.findall('<meta http-equiv="refresh" content="0; URL=(.*?)">', data, re.S)
		if refreshUrl:
			print refreshUrl
			if re.match('.*?Collection', self.streamName, re.S|re.I):
				print "Collection"
				self.session.open(meCollectionScreen, self.streamName, refreshUrl[0], "")
			else:
				getPage(refreshUrl[0], cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStream, refreshUrl[0]).addErrback(self.dataError)

	def getStream(self, data, url):
		#print data
		if re.search('http://evonic.tv/server/Serien', data, re.S|re.I):
			pic = None
			pic = re.findall('<div class="article cms_clear restore postcontainer"><div align="center"><img src="(http://evonic.tv/images/.*?)"', data)
			if pic:
				pic = pic[0]
			self.session.open(meSerienScreen, self.streamName, url, pic)
		else:
			self.genreListe2 = []
			findStream = re.findall('"(http://evonic.tv/server/Premium.*?)" target="Videoframe"><b>(.*?)</b>', data)
			if findStream:
				print "Premium", findStream
				for stream, name in findStream:
					name = re.sub('<.*?>', '', name)
					self.genreListe2.append((name, stream.replace('"','')))

			findStream2 = re.findall('"http://evonic.tv/server/Free-Member.php.mov=.*?"  target="Videoframe"><b>(.*?)</b>', data)
			if findStream2:
				print "Free", findStream2
				for stream, name in findStream2:
					name = re.sub('<.*?>', '', name)
					self.genreListe2.append((name, stream.replace('"','')))

			m = re.search('//www.youtube.*?com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
			if m:
				trailerId = m.group(2)
			else: trailerId = None

			self.session.open(meHosterScreen, self.streamName, self.genreListe2, "", trailer_id=trailerId)

	def addWatchlist(self):
		if self.keyLocked:
			return
		check = self['liste'].getCurrent()
		if check == None:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		getPage(streamLink, cookies=ck, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Referer': 'http://evonic.tv/forum/content.php'}, timeout=30).addCallback(self.loadRefresh, streamLink).addErrback(self.dataError)

	def loadRefresh(self, data, streamLink):
		refreshUrl = re.findall('<meta http-equiv="refresh" content="0; URL=(.*?)">', data, re.S)
		if refreshUrl:
			print refreshUrl
			getPage(refreshUrl[0], cookies=ck, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Referer': 'http://evonic.tv/forum/content.php'}, timeout=30).addCallback(self.getCat, refreshUrl[0]).addErrback(self.dataError)

	def getCat(self, data, streamLink):
		#print data
		cat = "Movie"
		if re.search('Collection', self.streamName, re.S):
			cat = "HD-Collection"
		elif re.search('Serie', self.streamName, re.S):
			cat = "HD-Serien"
		elif re.search('http://evonic.tv/server/Serien', data, re.S|re.I):
			cat = "HD-Serien"

		print cat, self.streamName, streamLink

		if not fileExists(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist"):
			print "erstelle watchlist"
			open(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist","w").close()

		if fileExists(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist"):
			print "schreibe watchlist", self.streamName, streamLink
			writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist","a")
			writePlaylist.write('"%s" "%s" "%s"\n' % (cat, self.streamName, streamLink))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("%s was added to the watchlist." % self.streamName), MessageBoxExt.TYPE_INFO, timeout=3)

class meMovieScreen(MPScreen):

	def __init__(self, session, enterAuswahlLink, enterAuswahlLabel):
		self.enterAuswahlLink = enterAuswahlLink
		self.enterAuswahlLabel = enterAuswahlLabel
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.addWatchlist,
			"yellow": self.sortMode
		}, -1)

		self.keyLocked = True
		self.showStreams = False
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label(self.enterAuswahlLabel)
		self['F2'] = Label(_("Add to Watchlist"))
		self['F3'] = Label(_("Sort A-Z"))

		self['Page'] = Label(_("Page:"))

		self.page = 1
		self.lastpage = 999
		self.genreListe = []
		self.genreListe_backup = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def sortMode(self):
		if config.mediaportal.evonic_sortABC.value:
			config.mediaportal.evonic_sortABC.value = False
		else:
			config.mediaportal.evonic_sortABC.value = True
		config.mediaportal.evonic_sortABC.save()
		configfile.save()
		self.loadPage()

	def sortList(self):
		if len(self.genreListe) > 0:
			if config.mediaportal.evonic_sortABC.value:
				self.genreListe.sort(key=lambda x: x[0])
				self['F3'].setText(_("Sort A-Z"))
			else:
				self['F3'].setText(_("Sort Normal"))
			self.ml.setList(map(self._defaultlistleft, self.genreListe))
			self.ml.moveToIndex(0)

	def loadPage(self):
		self.showStreams = False
		url = "%s%s" % (self.enterAuswahlLink,str(self.page))
		getPage(url, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.genreListe = []
		self.genreListe_backup = []
		if self.enterAuswahlLabel == "Aktuelle Filme":
			print "parsing: Aktuelle Filme"
			totalPages = re.findall('<span class="first_last"><a href=".*?page=(.*?)"', data, re.S)
			if totalPages:
				self['page'].setText("%s / %s" % (self.page, totalPages[0]))
			search = re.findall('<h3 class="article_preview">.*?<a href="(.*?)"><span>[AZ:]?(.*?)</span></a>.*?<div class="cms_article_section_location">.*?>IMDB(.*?)</a>.*?<img class="cms_article_preview_image" src="(.*?)" alt="Vorschau"', data,re.S)
			if search:
				for enterLink,enterName,enterImdb,enterPic in search:
					enterName = decodeHtml2(enterName)
					enterTitle = enterName.replace("HD:", "").strip() + ' (IMDB:' + enterImdb + ')'
					self.genreListe.append((enterTitle, enterLink, enterPic.replace('http://my-entertainment.biz','http://evonic.tv'), enterImdb))
				self.genreListe_backup = self.genreListe
				self.sortList()
				self.keyLocked = False
				self.showInfos()
		elif self.enterAuswahlLabel == "3D-Charts":
			print "parsing: 3D Charts"
			totalPages = re.findall('<span class="first_last"><a href=".*?page=(.*?)"', data, re.S)
			if totalPages:
				self['page'].setText("%s / %s" % (self.page, totalPages[0]))

			search3D = re.findall('<h3 class="article_preview">.*?<a href="(.*?)"><span>[AZ:]?(.*?)</span></a>.*?<div class="cms_article_section_location">.*?>IMDB(.*?)</a>.*?<img class="cms_article_preview_image" src="(.*?)" alt="Vorschau"', data,re.S)
			if search3D:
				for enterLink,enterName,enterImdb,enterPic in search3D:
					enterName = decodeHtml2(enterName)
					enterTitle = enterName.replace("HD:", "").strip() + ' (IMDB:' + enterImdb + ')'
					self.genreListe.append((enterTitle, enterLink, enterPic.replace('http://my-entertainment.biz','http://evonic.tv')))
				self.genreListe_backup = self.genreListe
				self.sortList()
				self.keyLocked = False
				self.showInfos()
		elif self.enterAuswahlLabel == "HD-Charts":
			print "parsing: HD Charts"
			totalPages = re.findall('<span class="first_last"><a href=".*?page=(.*?)"', data, re.S)
			if totalPages:
				print totalPages
				self['page'].setText("%s / %s" % (self.page, totalPages[0]))

			searchHD = re.findall('<h3 class="article_preview">.*?<a href="(.*?)"><span>[AZ:]?(.*?)</span></a>.*?<div class="cms_article_section_location">.*?>IMDB(.*?)</a>.*?<img class="cms_article_preview_image" src="(.*?)" alt="Vorschau"', data,re.S)
			if searchHD:
				for enterLink,enterName,enterImdb,enterPic in searchHD:
					enterName = decodeHtml2(enterName)
					enterTitle = enterName.replace("HD:", "").strip() + ' (IMDB:' + enterImdb + ')'
					self.genreListe.append((enterTitle, enterLink, enterPic.replace('http://my-entertainment.biz','http://evonic.tv')))
				self.genreListe_backup = self.genreListe
				self.sortList()
				self.keyLocked = False
				self.showInfos()
		elif self.enterAuswahlLabel == "3D":
			print "parsing: 3D"
			totalPages = re.findall('<span class="first_last"><a href=".*?page=(.*?)"', data, re.S)
			if totalPages:
				print totalPages
				self['page'].setText("%s / %s" % (self.page, totalPages[0]))

			movies3D = re.findall('<h3 class="article_preview">.*?<a href="(.*?)"><span>[AZ:]?(.*?)</span></a>.*?<div class="cms_article_section_location">.*?>IMDB(.*?)</a>.*?<img class="cms_article_preview_image" src="(.*?)" alt="Vorschau"', data,re.S)
			if movies3D:
				self.genreListe = []
				for enterLink,enterName,enterImdb,enterPic in movies3D:
					enterName = decodeHtml2(enterName)
					enterTitle = enterName.replace("HD:", "").strip() + ' (IMDB:' + enterImdb + ')'
					self.genreListe.append((enterTitle, enterLink, enterPic.replace('http://my-entertainment.biz','http://evonic.tv')))
				self.genreListe_backup = self.genreListe
				self.sortList()
				self.keyLocked = False
				self.showInfos()
			else:
				self.lastPage = self.page
		elif self.enterAuswahlLabel == "Alle HD Premium Streams":
			print "parsing: Alle Premium"
			totalPages = re.findall('<span class="first_last"><a href=".*?page=(.*?)"', data, re.S)
			if totalPages:
				print totalPages
				self['page'].setText("%s / %s" % (self.page, totalPages[0]))

			movies3D = re.findall('<h3 class="article_preview">.*?<a href="(.*?)"><span>[AZ:]?(.*?)</span></a>.*?<div class="cms_article_section_location">.*?>IMDB(.*?)</a>.*?<img class="cms_article_preview_image" src="(.*?)" alt="Vorschau"', data,re.S)
			if movies3D:
				self.genreListe = []
				for enterLink,enterName,enterImdb,enterPic in movies3D:
					enterName = decodeHtml2(enterName)
					enterTitle = enterName.replace("HD:", "").strip() + ' (IMDB:' + enterImdb + ')'
					self.genreListe.append((enterTitle, enterLink, enterPic.replace('http://my-entertainment.biz','http://evonic.tv')))
				self.genreListe_backup = self.genreListe
				self.sortList()
				self.keyLocked = False
				self.showInfos()
			else:
				self.lastPage = self.page

		elif (self.enterAuswahlLabel == "HD-Serien" or self.enterAuswahlLabel == "Serien Charts"):
			print "parsing: Serien"
			totalPages = re.findall('<span class="first_last"><a href=".*?page=(.*?)"', data, re.S)
			if totalPages:
				print totalPages
				self['page'].setText("%s / %s" % (self.page, totalPages[0]))

			result = re.findall('<h3 class="article_preview">.*?<a href="(.*?)">.*?<span>[A-Z][A-Z][:](.*?)</span>.*?<img class="cms_article_preview_image" src="(.*?)" alt="Vorschau" />', data, re.S)
			if result:
				for enterLink, enterName, enterPic in result:
					enterName = decodeHtml2(enterName)
					self.genreListe.append((enterName, enterLink, enterPic.replace('http://my-entertainment.biz','http://evonic.tv')))
				self.genreListe_backup = self.genreListe
				self.sortList()
				self.showInfos()
				self.keyLocked = False
			else:
				self['handlung'].setText("Nichts gefunden...")

		elif self.enterAuswahlLabel == "Neueinsteiger":
			print "parsing: Neueinsteiger"
			totalPages = re.search('>Seite \d+ von (\d+)</a>', data, re.S)
			if totalPages:
				print "Last page:",totalPages.group(1)
				self['page'].setText("%s / %s" % (self.page, totalPages.group(1)))

			movies = re.findall('<h3 class="article_preview">.*?<a href="(.*?)"><span>.*?:(.*?)</span></a>.*?<div class="cms_article_section_location">.*?<ol class="commalist">.*?<li><a href=".*?">(.*?)</a></li>.*?<img class="cms_article_preview_image" src="(.*?)" alt="Vorschau"', data, re.S)
			if movies:
				self.genreListe = []
				for enterLink,enterName,enterGenre,enterPic in movies:
					enterName = decodeHtml2(enterName)
					enterTitle = enterName.replace("HD:", "").strip()
					self.genreListe.append((enterTitle, enterLink, enterPic.replace('http://my-entertainment.biz','http://evonic.tv'), enterGenre))
				self.genreListe_backup = self.genreListe
				self.sortList()
				self.keyLocked = False
				self.showInfos()
		else:
			print "parsing: Sonstige Genres"
			totalPages = re.search('>Seite \d+ von (\d+)</a>', data, re.S)
			if totalPages:
				print "Last page:",totalPages.group(1)
				self['page'].setText("%s / %s" % (self.page, totalPages.group(1)))

			movies = re.findall('<h3 class="article_preview">.*?<a href="(.*?)"><span>[AZ:]?(.*?)</span></a>.*?<div class="cms_article_section_location">.*?>IMDB(.*?)</a>.*?<img class="cms_article_preview_image" src="(.*?)" alt="Vorschau"', data,re.S)
			if movies:
				self.genreListe = []
				for enterLink,enterName,enterImdb,enterPic in movies:
					enterName = decodeHtml2(enterName)
					enterTitle = enterName.replace("HD:", "").strip() + ' (IMDB:' + enterImdb + ')'
					self.genreListe.append((enterTitle, enterLink, enterPic.replace('http://my-entertainment.biz','http://evonic.tv')))
				self.genreListe_backup = self.genreListe
				self.sortList()
				self.keyLocked = False
				self.showInfos()

	def addWatchlist(self):
		if self.keyLocked:
			return
		check = self['liste'].getCurrent()
		if check == None:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]

		print self.enterAuswahlLabel, self.streamName, streamLink

		if not fileExists(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist"):
			print "erstelle watchlist"
			open(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist","w").close()

		if fileExists(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist"):
			print "schreibe watchlist", self.enterAuswahlLabel, self.streamName, streamLink
			writePlaylist = open(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist","a")
			writePlaylist.write('"%s" "%s" "%s"\n' % (self.enterAuswahlLabel, self.streamName, streamLink))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("%s was added to the watchlist." % self.streamName), MessageBoxExt.TYPE_INFO, timeout=3)

	def keyOK(self):
		if self.keyLocked:
			return
		check = self['liste'].getCurrent()
		if check == None:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		print self.streamName, streamLink
		if self.enterAuswahlLabel == "HD-Serien" or self.enterAuswahlLabel == "Serien Charts":
			self.session.open(meSerienScreen, self.streamName, streamLink, self.streamPic)
		elif self.enterAuswahlLabel == "HD-Collection":
			self.session.open(meCollectionScreen, self.streamName, streamLink, self.streamPic)
		elif self.enterAuswahlLabel == "Neueinsteiger":
			genre = self['liste'].getCurrent()[0][3]
			print genre
			if re.search('serie', genre, re.I):
				self.session.open(meSerienScreen, self.streamName, streamLink, self.streamPic)
			else:
				getPage(streamLink, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStream).addErrback(self.dataError)
		else:
			getPage(streamLink, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		self.genreListe2 = []
		findStream = re.findall('"(http://evonic.tv/server/Premium.*?)".*?target="Videofram.*?"><b>(.*?)</b>', data)
		if findStream:
			print "Premium", findStream
			for stream, name in findStream:
				name = re.sub('<.*?>', '', name)
				self.genreListe2.append((name, stream.replace('"','')))

		findStream2 = re.findall('"(http://evonic.tv/server/Free-Member.php.mov=.*?)".*?target="Videofram.*?"><b>(.*?)</b>', data)
		if findStream2:
			print "Free", findStream2
			for stream, name in findStream2:
				name = re.sub('<.*?>', '', name)
				self.genreListe2.append((name, stream.replace('"','')))

		m = re.search('//www.youtube.*?com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
		if m:
			trailerId = m.group(2)
		else: trailerId = None

		self.session.open(meHosterScreen, self.streamName, self.genreListe2, self.streamPic, trailer_id=trailerId)

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self.streamPic = self['liste'].getCurrent()[0][2]
		self['name'].setText(streamName)
		CoverHelper(self['coverArt']).getCover(self.streamPic)
		self.loadHandlung()

	def loadHandlung(self):
		streamFilmLink = self['liste'].getCurrent()[0][1]
		print "loadHandlung...", streamFilmLink
		getPage(streamFilmLink, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.setHandlung).addErrback(self.dataError)

	def setHandlung(self, data):
		handlung = re.findall('<div class="bbcode_quote_container"></div>(.*?)<', data, re.S)
		if handlung:
			handlung = re.sub(r"\s+", " ", handlung[0])
			handlung = decodeHtml2(handlung)
			self['handlung'].setText(handlung.strip())
		else:
			self['handlung'].setText(_("No information found."))

class meSerienScreen(MPScreen):

	def __init__(self, session, eName, eLink, streamPic):
		self.eName = eName
		self.eLink = eLink
		self.streamPic = streamPic
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
			"green" : self.keyTrailer,
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label(_("Episode Selection"))
		self['name'] = Label(self.eName)

		self['Page'] = Label(_("Page:"))
		self['F2'] = Label(_("Trailer"))
		self['F2'].hide()

		self.trailerId = None
		self.page = 1
		self.eListe = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.streamPic)
		getPage(self.eLink, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getEpisoden).addErrback(self.dataError)

	def getEpisoden(self, data):
		m = re.search('//www.youtube\.com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
		if m:
			self.trailerId = m.group(2)
			self['F2'].show()

		self.watched_liste = []
		self.mark_last_watched = []
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_evonic_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_evonic_watched","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_evonic_watched"):
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_evonic_watched")
			if not leer == 0:
				self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_evonic_watched" , "r")
				for lines in sorted(self.updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						self.watched_liste.append("%s" % (line[0]))
				self.updates_read.close()

		staffeln = re.findall('<img src="http://evonic.tv/images/unbenanyn.jpg"(.*?)<iframe src="http://evonic.tv/images/hdtvschaer.jpg"', data, re.S|re.I)
		print "count %s staffeln" % len(staffeln)
		if staffeln:
			staffelcount = 0
			for each in staffeln:
				staffelcount += 1
				eps = re.findall('<a href="(.*?)" target="Videoframe.*?"><b><span style="color: black;">(.*?)</span>', each, re.S|re.I)
				if eps:
					for link,epTitle in eps:
						if int(staffelcount) < 10:
							setStaffel = "S0%s" % str(staffelcount)
						else:
							setStaffel = "S%s" % str(staffelcount)
						print "Staffel "+setStaffel, epTitle, link

						dupe_streamname = "%s - %s" % (self.eName, setStaffel + "E" + epTitle)
						if dupe_streamname in self.watched_liste:
							self.eListe.append((setStaffel + "E" + epTitle, link, True))
						else:
							self.eListe.append((setStaffel + "E" + epTitle, link, False))
					self.ml.setList(map(self._defaultlistleftmarked, self.eListe))
					self.ml.moveToIndex(0)
					self.keyLocked = False
				else:
					print "parsing fehler.."

	def keyOK(self):
		if self.keyLocked:
			return
		check = self['liste'].getCurrent()
		if check == None:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		print self.streamName, streamLink
		getPage(streamLink, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStreamUrl).addErrback(self.dataError)

	def getStreamUrl(self, data):
		print "get Stream Url.."
		if self.streamName == "Premium":
			stream_url = re.findall('src="(.*?)"', data, re.S)
			if stream_url:
				print stream_url
				self.session.open(SimplePlayer, [(self.eName + " " + self.streamName, stream_url[0], self.streamPic)], showPlaylist=False, ltype='ME', cover=True)
				self.markAsWatched()
		else:
			print data
			stream_url = re.findall('src="(.*?)"', data, re.S)
			if stream_url:
				print stream_url
				self.session.open(SimplePlayer, [(self.eName + " " + self.streamName, stream_url[0], self.streamPic)], showPlaylist=False, ltype='ME', cover=True)
				self.markAsWatched()

	def markAsWatched(self):
		self.stream_name = "%s - %s" % (self.eName, self.streamName)
		print self.stream_name
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_evonic_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_evonic_watched","w").close()

		self.update_liste = []
		leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_evonic_watched")
		if not leer == 0:
			self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_evonic_watched" , "r")
			for lines in sorted(self.updates_read.readlines()):
				line = re.findall('"(.*?)"', lines)
				if line:
					print line[0]
					self.update_liste.append("%s" % (line[0]))
			self.updates_read.close()

			updates_read2 = open(config.mediaportal.watchlistpath.value+"mp_evonic_watched" , "a")
			check = ("%s" % self.stream_name)
			if not check in self.update_liste:
				print "update add: %s" % (self.stream_name)
				updates_read2.write('"%s"\n' % (self.stream_name))
				updates_read2.close()
			else:
				print "dupe %s" % (self.stream_name)
		else:
			updates_read3 = open(config.mediaportal.watchlistpath.value+"mp_evonic_watched" , "a")
			print "[update add: %s" % (self.stream_name)
			updates_read3.write('"%s"\n' % (self.stream_name))
			updates_read3.close()

	def keyTrailer(self):
		if self.trailerId:
			self.session.open(
				YoutubePlayer,
				[(self.eName+' - Trailer', self.trailerId, self.streamPic)],
				playAll = False,
				showPlaylist=False,
				showCover=True
				)

class meCenturyScreen(MPScreen):

	def __init__(self, session):
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label("Century Auswahl")

		self.yearList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.yearList = []
		self.yearList.append(('Jahr 2013','http://evonic.tv/forum/list.php?r=category/217&page='))
		self.yearList.append(('Jahr 2012','http://evonic.tv/forum/list.php?r=category/216&page='))
		self.yearList.append(('Jahr 2011','http://evonic.tv/forum/list.php?r=category/215&page='))
		self.yearList.append(('Jahr 2010','http://evonic.tv/forum/list.php?r=category/214&page='))
		self.yearList.append(('Jahr 2009','http://evonic.tv/forum/list.php?r=category/213&page='))
		self.yearList.append(('Jahr 2008','http://evonic.tv/forum/list.php?r=category/212&page='))
		self.yearList.append(('Jahr 2007','http://evonic.tv/forum/list.php?r=category/211&page='))
		self.yearList.append(('Jahr 2006','http://evonic.tv/forum/list.php?r=category/210&page='))
		self.yearList.append(('Jahr 2005','http://evonic.tv/forum/list.php?r=category/209&page='))
		self.yearList.append(('Jahr 2004','http://evonic.tv/forum/list.php?r=category/208&page='))
		self.yearList.append(('Jahr 2003','http://evonic.tv/forum/list.php?r=category/207&page='))
		self.yearList.append(('Jahr 2002','http://evonic.tv/forum/list.php?r=category/206&page='))
		self.yearList.append(('Jahr 2001','http://evonic.tv/forum/list.php?r=category/205&page='))
		self.yearList.append(('Jahr 2000','http://evonic.tv/forum/list.php?r=category/204&page='))
		self.yearList.append(('Jahr 1990','http://evonic.tv/forum/list.php?r=category/203&page='))
		self.yearList.append(('Jahr 1980','http://evonic.tv/forum/list.php?r=category/202&page='))
		self.yearList.append(('Jahr 1970','http://evonic.tv/forum/list.php?r=category/201&page='))
		self.yearList.append(('Jahr 1960','http://evonic.tv/forum/list.php?r=category/200&page='))
		self.yearList.append(('Jahr 1950','http://evonic.tv/forum/list.php?r=category/199&page='))
		self.ml.setList(map(self._defaultlistcenter, self.yearList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		check = self['liste'].getCurrent()
		if check == None:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]

		print self.streamName, streamLink
		self.session.open(meMovieScreen, streamLink, self.streamName)

class meImdbScreen(MPScreen):

	def __init__(self, session):
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label("Imdb")

		self.imdbList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.imdbList = []
		self.imdbList.append(('IMDB 8.0','http://evonic.tv/forum/list.php?r=category/161&page='))
		self.imdbList.append(('IMDB 7.0','http://evonic.tv/forum/list.php?r=category/162&page='))
		self.imdbList.append(('IMDB 6.0','http://evonic.tv/forum/list.php?r=category/163&page='))
		self.imdbList.append(('IMDB 5.0','http://evonic.tv/forum/list.php?r=category/164&page='))
		self.imdbList.append(('IMDB 4.0','http://evonic.tv/forum/list.php?r=category/165&page='))
		self.imdbList.append(('IMDB 3.0','http://evonic.tv/forum/list.php?r=category/166&page='))
		self.imdbList.append(('IMDB 2.0','http://evonic.tv/forum/list.php?r=category/167&page='))
		self.ml.setList(map(self._defaultlistcenter, self.imdbList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		check = self['liste'].getCurrent()
		if check == None:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]

		print self.streamName, streamLink
		self.session.open(meMovieScreen, streamLink, self.streamName)

class meCollectionScreen(MPScreen):

	def __init__(self, session, eName, eLink, streamPic):
		self.eName = eName
		self.eLink = eLink
		self.streamPic = streamPic
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" 	: self.keyTrailer,
		}, -1)

		self.keyLocked = True
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label("Collection")
		self['Page'] = Label(_("Page:"))
		self['F2'] = Label("Trailer")
		self['F2'].hide()

		self.trailerId = None
		self.page = 1
		self.eListe = []
		self.coverdata = False
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.streamPic)
		getPage(self.eLink, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getEpisoden).addErrback(self.dataError)

	def getEpisoden(self, data):
		self.coverdata = data
		self.eListe = []
		titles = re.compile('\r\n<.*?>\r*\n*(.*?)<*b*r*\s*/*>*\r*\n*<*b*r*\s*/*>*\r*\n*\s*<div style=".*?">').findall(data)
		if titles:
			for title in titles:
				if title:
					if not re.search('Platzhalte', title):
						title = re.sub('<.*?>|</font','', title)
						self.eListe.append((title, "Platzhalter"))

			self.trailer = []
			a = 0
			for title, dummy in self.eListe:
				i = data[a:].find(title)
				if i >= 0:
					a += i
					m = re.search('%s(.*?)http://evonic.tv/server/' % title, data[a:], re.S)
					if m:
						a += m.end()
						mf = re.search('//www.youtube.*?com/(embed|v|p)/(.*?)(\?|" |&amp)', m.group(1))
						if mf:
							self.trailer.append(mf.group(2))
						else:
							self.trailer.append('')

			self.ml.setList(map(self._defaultlistleft, self.eListe))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		check = self['liste'].getCurrent()
		if check == None:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		print self.streamName
		getPage(self.eLink, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		streams = []
		searchSTRING = self.streamName.replace('(','\(').replace(')','\)')
		streams = re.findall(searchSTRING+'.*?<a href="(http://evonic.tv/server/Premium-Membe.*?.php.*?)"', data, re.S)
		if streams:
			print self.streamName, streams[0]
		self.session.open(meServerScreen, self.streamName, streams, self.streamPic)

	def showInfos(self):
		if self.keyLocked or not self['liste'].getCurrent(): return
		idx = self['liste'].getSelectedIndex()
		if self.trailer and idx < len(self.trailer):
			self.trailerId = self.trailer[idx]
			self['F2'].show()
		else:
			self.trailerId = None
			self['F2'].hide()

		if self.coverdata:
			streamName = self['liste'].getCurrent()[0][0]
			self['name'].setText(streamName)
			img_raw = re.findall(streamName+'.*?<img src="(http://evonic.tv/images/.*?)" border="0"', self.coverdata, re.S)
			if img_raw:
				self.streamPic = img_raw[0]
				print streamName, self.streamPic
				CoverHelper(self['coverArt']).getCover(self.streamPic)

	def keyTrailer(self):
		if self.trailerId:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(
				YoutubePlayer,
				[(title+' - Trailer', self.trailerId, self.streamPic)],
				playAll = False,
				showPlaylist=False,
				showCover=True
				)

class meTimdbGenreScreen(MPScreen):

	def __init__(self, session, stoken):
		self.stoken = stoken
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label("IMDb - Top 1000 Suche")

		self['Page'] = Label(_("Page:"))

		self.filmliste = []
		self.page = 1
		self.lastpage = 20

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		self.start = 1
		self.start = (self.page * 50) - 49

		url = "http://www.imdb.de/search/title?groups=top_1000&sort=user_rating,desc&start=%s" % str(self.start)
		print url
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded', 'User-agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0', 'Accept-Language':'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		movies = re.findall('<td class="number">(.*?)</td>.*?<img src="(.*?)".*?<a href="/title/.*?">(.*?)</a>.*?<span class="year_type">(.*?)</span><br>.*?<div class="rating rating-list".*?title="Users rated this (.*?\/)', data, re.S)
		if movies:
			for place,image,title,year,rates in movies:
				rates = "%s10" % rates
				image_raw = image.split('@@')
				image = "%s@@._V1_SX214_.jpg" % image_raw[0]
				self.filmliste.append((place, decodeHtml(title), year, rates, image))
			self.ml.setList(map(self.timdbEntry, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		platz = self['liste'].getCurrent()[0][0]
		title = self['liste'].getCurrent()[0][1]
		coverUrl = self['liste'].getCurrent()[0][4]
		self['page'].setText("%s / 20" % str(self.page))
		CoverHelper(self['coverArt']).getCover(coverUrl)
		self['name'].setText(platz+" "+title)

	def keyOK(self):
		if self.keyLocked:
			return

		self.searchTitle = self['liste'].getCurrent()[0][1]
		print self.searchTitle

		self.session.openWithCallback(self.mySearch, VirtualKeyBoardExt, title = (_("Search:")), text = self.searchTitle, is_dialog=True)

	def mySearch(self, callback = None):
		print 'mySearch'
		if callback != None:
			self.session.open(meSearchScreen, callback, self.stoken)

class meWatchlistScreen(MPScreen):

	def __init__(self, session):
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"red"	: self.delWatchListEntry,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label("Watchlist")
		self['F1'] = Label("Del")

		self.watchListe = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.watchListe = []
		if fileExists(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist"):
			print "read watchlist"
			readStations = open(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist","r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(which, title, link) = data[0]
					print which, title, link
					self.watchListe.append((which, title, link))
			print "Load Watchlist.."
			self.watchListe.sort()
			self.ml.setList(map(self.evonicWatchListEntry, self.watchListe))
			self.ml.moveToIndex(0)
			readStations.close()
			self.keyLocked = False
			self.showInfos()

	def delWatchListEntry(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		entryDeleted = False
		selectedName = self['liste'].getCurrent()[0][1]

		writeTmp = open(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist.tmp","w")
		if fileExists(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist"):
			readWatchlist = open(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist","r")
			for rawData in readWatchlist.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(genre, title, link) = data[0]
					if title != selectedName:
						writeTmp.write('"%s" "%s" "%s"\n' % (genre, title, link))
					else:
						if entryDeleted:
							writeTmp.write('"%s" "%s" "%s"\n' % (genre, title, link))
						else:
							entryDeleted = True
			readWatchlist.close()
			writeTmp.close()
			shutil.move(config.mediaportal.watchlistpath.value+"mp_evonic_watchlist.tmp", config.mediaportal.watchlistpath.value+"mp_evonic_watchlist")
			self.loadPage()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		streamWhich = self['liste'].getCurrent()[0][0]
		self.streamName = self['liste'].getCurrent()[0][1]
		streamLink = self['liste'].getCurrent()[0][2]

		print streamWhich, self.streamName, streamLink

		if re.match('.*?Serien', streamWhich, re.S|re.I):
			self.session.open(meSerienScreen, self.streamName, streamLink, "")
		elif re.match('.*?Collection', streamWhich, re.S|re.I):
			self.session.open(meCollectionScreen, self.streamName, streamLink, "")
		else:
			getPage(streamLink, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		#print data
		print "get streams.."
		self.genreListe2 = []
		findStream = re.findall('"(http://evonic.tv/server/Premium.*?)" target="Videoframe"><b>(.*?)</b>', data)
		if findStream:
			print "Premium", findStream
			for stream, name in findStream:
				name = re.sub('<.*?>', '', name)
				self.genreListe2.append((name, stream.replace('"','')))

		findStream2 = re.findall('"http://evonic.tv/server/Free-Member.php.mov=.*?"  target="Videoframe"><b>(.*?)</b>', data)
		if findStream2:
			print "Free", findStream2
			for stream, name in findStream2:
				name = re.sub('<.*?>', '', name)
				self.genreListe2.append((name, stream.replace('"','')))

		m = re.search('//www.youtube\.com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
		if m:
			trailerId = m.group(2)
		else: trailerId = None
		self.session.open(meHosterScreen, self.streamName, self.genreListe2, "", trailer_id=trailerId)

class meServerScreen(MPScreen):

	def __init__(self, session, eName, eLink, streamPic):
		self.eName = eName
		self.eLink = eLink
		self.streamPic = streamPic
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label("Collection")

		self.page = 1
		self.eListe = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.eListe = []
		CoverHelper(self['coverArt']).getCover(self.streamPic)
		if len(self.eLink) != 0:
			print self.eLink
			for server in self.eLink:
				print server
				if "Free-Member" in server:
					self.eListe.append(("Free-Member", server))
				elif "Premium-Member" in server:
					self.eListe.append(("Premium-Member", server))
			self.ml.setList(map(self._defaultlistcenter, self.eListe))
			self.keyLocked = False
			self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		check = self['liste'].getCurrent()
		if check == None:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]

		print self.streamName, streamLink
		getPage(streamLink, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStreamUrl).addErrback(self.dataError)

	def getStreamUrl(self, data):
		print "get Stream Url.."
		if self.streamName == "Premium":
			stream_url = re.findall('src="(http://.*?)"', data, re.S)
			if stream_url:
				print stream_url
				self.session.open(SimplePlayer, [(self.eName + " " + self.streamName, stream_url[0], self.streamPic)], showPlaylist=False, ltype='ME', cover=True)
		else:
			print data
			stream_url = re.findall('src="(http://.*?)"', data, re.S)
			if stream_url:
				print stream_url
				self.session.open(SimplePlayer, [(self.eName + " " + self.streamName, stream_url[0], self.streamPic)], showPlaylist=False, ltype='ME', cover=True)

class meHosterScreen(MPScreen):

	def __init__(self, session, eName, eListe, streamPic, trailer_id=None):
		self.eName = eName
		self.eListe = eListe
		self.streamPic = streamPic
		self.trailerId = trailer_id
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
			"green" : self.keyTrailer,
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("evonic.tv")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.eName)
		self['F2'] = Label(_("Trailer"))
		if not self.trailerId:
			self['F2'].hide()

		self.page = 1
		self.genreListe = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.ml.setList(map(self._defaultlistcenter, self.eListe))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		check = self['liste'].getCurrent()
		if check == None:
			return
		self.streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		print self.streamName, streamLink
		getPage(streamLink, cookies=ck, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getStreamUrl).addErrback(self.dataError)

	def getStreamUrl(self, data):
		print "get Stream Url.."
		stream_url = re.findall('src="(http://.*?)"', data, re.S)
		if stream_url:
			print stream_url
			self.session.open(SimplePlayer, [(self.eName + " " + self.streamName, stream_url[0], self.streamPic)], showPlaylist=False, ltype='ME', cover=True)

	def keyTrailer(self):
		if self.trailerId:
			self.session.open(
				YoutubePlayer,
				[(self.eName+' - Trailer', self.trailerId, self.streamPic)],
				playAll = False,
				showPlaylist=False,
				showCover=True
				)

class meSetupScreen(Screen, ConfigListScreenExt):

	def __init__(self, session):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/PluginUserDefault.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/PluginUserDefault.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)
		self['title'] = Label("Evonic " + _("Setup"))
		self.setTitle("Evonic " + _("Setup"))

		self.list = []
		ConfigListScreenExt.__init__(self, self.list)

		self.list.append(getConfigListEntry(_("Username:"), config.mediaportal.evonic_userName))
		self.list.append(getConfigListEntry(_("Password:"), config.mediaportal.evonic_userPass))
		self["config"].setList(self.list)

		self["setupActions"] = ActionMap(["MP_Actions"],
		{
			"ok":		self.saveConfig,
			"cancel":	self.exit
		}, -1)

	def saveConfig(self):
		print "save"
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close(True)

	def exit(self):
		self.close(False)