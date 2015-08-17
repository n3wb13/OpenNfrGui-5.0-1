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

config.mediaportal.alluc_country = ConfigText(default="EN/DE", fixed_size=False)
keckse = {}

class allucHelper():

	def keyCountry(self):
		if self.keyLocked:
			return
		rangelist = ['EN/DE', 'DE', 'EN']
		if not any(self.Country in item for item in rangelist):
			self.Country = rangelist[-1]
		for x in rangelist:
			if self.Country == x:
				self.Country = rangelist[rangelist.index(x)-len(rangelist)+1]
				break
		config.mediaportal.alluc_country.value = self.Country
		config.mediaportal.alluc_country.save()
		configfile.save()
		self['F4'].setText(self.Country)
		self.loadFirstPage()

	def loadFirstPage(self):
		try:
			self.page = 1
			self.loadPage()
		except:
			pass

	def novideofound(self, error):
		try:
			if error.value.status == '404':
				self.filmliste.append((_("No videos found!"), None, '', False))
				self.ml.setList(map(self._defaultlistleft, self.filmliste))
				self.ml.moveToIndex(0)
				self['name'].setText('')
				self.showInfos()
		except:
			pass
		self.keyLocked = False
		raise error

	def errCancelDeferreds(self, error):
		myerror = error.getErrorMessage()
		if myerror:
			raise error

	def dataError(self, error):
		printl(error,self,"E")
		self.keyLocked = False

class allucMenueScreen(allucHelper, MPScreen):

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
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue"	: self.keyCountry
		}, -1)

		self.Country = config.mediaportal.alluc_country.value
		self['title'] = Label("alluc.to")
		self['ContentTitle'] = Label("Genre:")
		self['F4'] = Label(self.Country)
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.genreliste.append(("Latest Updates", "http://dir.alluc.to/xxx.html?mode=updated"))
		self.genreliste.append(("Most Popular", "http://dir.alluc.to/xxx.html?mode=popular"))
		self.genreliste.append(("Genres", ""))
		self.genreliste.append(("A-Z", "http://dir.alluc.to/xxx.html"))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		elif re.search('A-Z', Name):
			self.session.open(allucAZScreen, Name, Link, self.Country)
		elif re.search('Genre', Name, re.S|re.I):
			self.session.open(allucGenreScreen, Name, self.Country)
		else:
			if self.Country != "EN/DE":
				if re.search('\?', Link):
					Link = '%s&setlang=%s' % (Link, self.Country.lower())
				else:
					Link = '%s?setlang=%s' % (Link, self.Country.lower())
			self.session.open(allucFilmScreen, Link, Name, self.Country)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = "http://dir.alluc.to/xxx.html?mode=search&filter=&sort=&sword=%s&searchmode=" % self.suchString
			self.session.open(allucFilmScreen, Link, Name, self.Country)

class allucGenreScreen(MPScreen):

	def __init__(self, session, Name, Country):
		self.Name = Name
		self.Country = Country
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

		self['title'] = Label("alluc.to / Filter: %s" % self.Country)
		self['ContentTitle'] = Label("%s" % self.Name)
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		if self.Country != "EN/DE":
			self.Lang = "?setlang=%s" % self.Country.lower()
		else:
			self.Lang = ''
		url = "http://dir.alluc.to/adult/genres.html"
		getPage(url, cookies=keckse, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		preparse = re.search('select_genre(.*?)select_year', data, re.S|re.I)
		if preparse:
			Cats = re.findall('value="(.*?)\|.*?>(.*?)<', preparse.group(1))
			if Cats:
				for CatID, Cat in Cats:
					self.genreliste.append((Cat, CatID))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self['name'].setText("")

	def keyOK(self):
		if self.keyLocked:
			return
		Cat = self['liste'].getCurrent()[0][0]
		CatID = self['liste'].getCurrent()[0][1]
		if self.Country != "EN/DE":
			Link = "http://dir.alluc.to/movies/%s/%s.html?setlang=%s" % (Cat, CatID, self.Country.lower())
		else:
			Link = "http://dir.alluc.to/movies/%s/%s.html" % (Cat, CatID)
		Title = "%s Selection: %s" % (self.Name.split(' ', 1)[0], Cat)
		self.session.open(allucFilmScreen, Link, Title, self.Country)

class allucAZScreen(MPScreen):

	def __init__(self, session, Name, Url, Country):
		self.Name = Name
		self.Url = Url
		self.Country = Country
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

		self['title'] = Label("alluc.to / Filter: %s" % self.Country)
		self['ContentTitle'] = Label("%s" % self.Name)
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		abc = ["#","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
		for letter in abc:
			self.genreliste.append((letter, True))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		abc = self['liste'].getCurrent()[0][0]
		Title = "%s Selection: %s" % (self.Name.split(' ', 1)[0], abc)
		if abc == "#":
			abc = '%23'
		if self.Country != "EN/DE":
			Link = "%s?mode=showall&letter=%s&setlang=%s" % (self.Url, abc, self.Country.lower())
		else:
			Link = "%s?mode=showall&letter=%s" % (self.Url, abc)
		self.session.open(allucFilmScreen, Link, Title, self.Country)

class allucFilmScreen(allucHelper, MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Country='EN/DE'):
		self.Link = Link.replace(' ', '%20')
		self.Name = Name
		self.Country = Country
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
			"blue" : self.keyPageNumber
		}, -1)

		self['title'] = Label("alluc.to / Filter: %s" % self.Country)
		self['ContentTitle'] = Label("%s" % self.Name)
		self['F4'] = Label(_("Page"))

		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.filmliste = []
		self.Cover = ''
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.deferreds = []
		self.ds = defer.DeferredSemaphore(tokens=1)

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.search("Search", self.Name):
			if self.page > 1:
				Url = "%s&page=%s" % (self.Link, self.page)
			else:
				Url = self.Link
		else:
			Url = self.Link
		getPage(Url, cookies=keckse, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.novideofound).addErrback(self.dataError)

	def loadPageData(self, data):
		if re.search('Search', self.Name):
			self['Page'].setText(_("Page:"))
			self.getLastPage(data, 'class="catnavigator"\sclass="page"(.*?)</div>', '.*>\[(\d+)\]<')
			preparse = re.search('catmenubox(.*?)<div class="footer">', data, re.S|re.I)
			if preparse:
				Movies = re.findall('class="newlinks"\shref="(.*?)"\stitle="watch\s(.*?)\sonline".*?<div class(.*?)newlinkscaption', preparse.group(1), re.S)
				if Movies:
					for Url, Title, Lang in Movies:
						if re.search('alt="german"', Lang):
							Lang = '1'
						else:
							Lang = '2'
						Title = Title.strip()
						Type = re.findall('^(.*?)/.*?', Url)
						if Type:
							Title = '%s - %s' % (Type[0].capitalize(), Title)
						Url = 'http://dir.alluc.to/%s' % Url
						self.filmliste.append((decodeHtml(Title), Url, Lang, False))
		else:
			preparse = re.search('catcontent(.*?)footerbox', data, re.S|re.I)
			if preparse:
				Movies = re.findall('class="linklist2">\s+<a\shref="(.*?)"\stitle="watch\s(.*?)\sonline', preparse.group(1), re.S)
				if Movies:
					for Url, Title in Movies:
						if not re.match('.*?\?mode=', Url):
							Url = 'http://dir.alluc.to/%s' % Url
							Title = decodeHtml(Title)
							if self.Country == 'DE':
								Lang = '1'
							elif self.Country == 'EN':
								Lang = '2'
							else:
								Lang = '15'
							self.filmliste.append((Title, Url, Lang, False))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"), None, '', False))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self['name'].setText('')
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, None,None, 'og:image"\scontent="(.*?)"', self.page, self.lastpage)
		self.showInfos()

	def showInfos(self):
		for items in self.deferreds:
			items.cancel()
		self.deferreds = []
		if self['liste'].getCurrent()[0][1] != None:
			Title = self['liste'].getCurrent()[0][0]
			Url = self['liste'].getCurrent()[0][1]
			self['name'].setText(Title)
			d = self.ds.run(getPage, Url, cookies=keckse, agent=std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageInfos).addErrback(self.errCancelDeferreds).addErrback(self.dataError)
			self.deferreds.append(d)

	def loadPageInfos(self, data):
		Info = re.findall('og:image"\scontent="(.*?)".*?og:description" content="(.*?)"', data, re.S)
		if Info:
			if re.match('.*?alluc.jpg', Info[0][0]):
				self.Cover = None
			else:
				self.Cover = Info[0][0]
			if re.match('.*?alluc.to', Info[0][1]):
				Handlung = 'There is no description for this movie yet'
			else:
				Handlung = decodeHtml(Info[0][1].strip())
		else:
			Handlung = 'No Description found.'
			self.Cover = None
		self['handlung'].setText(Handlung)
		CoverHelper(self['coverArt']).getCover(self.Cover)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link == None:
			return
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(StreamAuswahl, Title ,Link, self.Cover)

class StreamAuswahl(allucHelper, MPScreen):

	def __init__(self, session, Title, Link, Cover):
		self.Link = Link
		self.Title = Title
		self.Cover = Cover
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("alluc.to / Filter: %s" % config.mediaportal.alluc_country.value)
		self['ContentTitle'] = Label("Hosterlist %s" %self.Title)


		self.filmliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		getPage(self.Link, cookies=keckse, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('Direct\sLinks(.*?)id="comments"', data, re.S)
		if parse:
			parts = re.split('grouphosterlabel', parse.group(1) )
			for hosterpart in parts[1:]:
				hoster = re.search('".*?(\w+)\s\((\d+)\)', hosterpart, re.S)
				if hoster:
					hostername = hoster.group(1).strip()
					streamcount = hoster.group(2)
					if hostername == 'Played':
						hostername = 'Played.to'
					if isSupportedHoster(hostername, True):
						self.filmliste.append((hostername, streamcount, hosterpart))
		if len(self.filmliste) == 0:
			self.filmliste.append(('No supported Hoster found!', '0', ''))
		self.ml.setList(map(self.allucHostersEntry, self.filmliste))
		self['name'].setText('')
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		hoster = self['liste'].getCurrent()[0][0]
		data = self['liste'].getCurrent()[0][2]
		if data == None:
			return
		self.session.open(SubStreamAuswahl, self.Title, hoster, data)

class SubStreamAuswahl(MPScreen):

	def __init__(self, session, Title, Hoster, Data):
		self.Title = Title
		self.Hoster = Hoster
		self.Data = Data
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("alluc.to / Filter: %s" % config.mediaportal.alluc_country.value)
		self['ContentTitle'] = Label("Streamlist %s" %self.Title)

		self.keyLocked = True
		self.tw_agent_hlp = TwAgentHelper()
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		streamparts = re.split('collinkname', self.Data )
		for streampart in streamparts[1:]:
			hits = re.findall('class="openlink.*?>(.*?)<.*?openlink.*?href="(.*?)".*?ratingscore.*?>(.*?)<.*?Hits">(.*?)<', streampart, re.S)
			if hits:
				url = "http://dir.alluc.to/%s" % hits[0][1]
				self.filmliste.append((self.Hoster, hits[0][0].strip(), url, hits[0][2].strip(), hits[0][3].strip()))
		if len(self.filmliste) == 0:
			self.filmliste.append((None, _('No supported streams found!'), '', '', ''))
		self.ml.setList(map(self.allucSubHostersEntry, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][2]
		self['name'].setText(_("Please wait..."))
		if url == None:
			return

		user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
		self.tw_agent_hlp.headers.addRawHeader('User-Agent', user_agent)
		self.tw_agent_hlp.getRedirectedUrl(url).addCallback(self.get_redirect).addErrback(self.dataError)
		self['name'].setText("%s" % self.Title)

	def get_redirect(self, url):
		get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.session.open(SimplePlayer, [(self.Title, stream_url)], showPlaylist=False, ltype='alluc')