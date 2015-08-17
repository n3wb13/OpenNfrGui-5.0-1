# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

baseurl = "http://www.movie25.ag/"

class movie25GenreScreen(MPScreen):

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
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Movie25")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = [ ('New Releases',baseurl + "movies/new-releases/"),
		                    ('Last Added',baseurl + "movies/latest-added/"),
		                    ('Featured Movies',baseurl + "movies/featured-movies/"),
		                    ('Latest HQ Movies',baseurl + "movies/latest-hd-movies/"),
		                    ('Most Viewed',baseurl + "movies/most-viewed/"),
		                    ('Most Voted',baseurl + "movies/most-voted/"),
                            ('Action',baseurl + "movies/action/"),
                            ('Adventure',baseurl + "movies/adventure/"),
                            ('Animation',baseurl + "movies/animation/"),
                            ('Biography',baseurl + "movies/biography/"),
                            ('Comedy',baseurl + "movies/comedy/"),
                            ('Crime',baseurl + "movies/crime/"),
                            ('Documentary',baseurl + "movies/documentary/"),
                            ('Drama',baseurl + "movies/drama/"),
                            ('Family',baseurl + "movies/family/"),
                            ('History',baseurl + "movies/history/"),
                            ('Horror',baseurl + "movies/horror/"),
                            ('Music',baseurl + "movies/music/"),
                            ('Musical',baseurl + "movies/musical/"),
                            ('Mystery',baseurl + "movies/mystery/"),
                            ('Romance',baseurl + "movies/romance/"),
                            ('Sci-Fi',baseurl + "movies/sci-fi/"),
                            ('Short',baseurl + "movies/short/"),
                            ('Sport',baseurl + "movies/sport/"),
                            ('Thriller',baseurl + "movies/thriller/"),
                            ('War',baseurl + "movies/war/"),
                            ('Western',baseurl + "movies/western/"),
                            ('Movie Title 0-9',baseurl + "movies/0-9/"),
                            ('Movie Title A',baseurl + "movies/a/"),
                            ('Movie Title B',baseurl + "movies/b/"),
                            ('Movie Title C',baseurl + "movies/c/"),
                            ('Movie Title D',baseurl + "movies/d/"),
                            ('Movie Title E',baseurl + "movies/e/"),
                            ('Movie Title F',baseurl + "movies/f/"),
                            ('Movie Title G',baseurl + "movies/g/"),
                            ('Movie Title H',baseurl + "movies/h/"),
                            ('Movie Title I',baseurl + "movies/i/"),
                            ('Movie Title J',baseurl + "movies/j/"),
                            ('Movie Title K',baseurl + "movies/k/"),
                            ('Movie Title L',baseurl + "movies/l/"),
                            ('Movie Title M',baseurl + "movies/m/"),
                            ('Movie Title N',baseurl + "movies/n/"),
                            ('Movie Title O',baseurl + "movies/o/"),
                            ('Movie Title P',baseurl + "movies/p/"),
                            ('Movie Title Q',baseurl + "movies/q/"),
                            ('Movie Title R',baseurl + "movies/r/"),
                            ('Movie Title S',baseurl + "movies/s/"),
                            ('Movie Title T',baseurl + "movies/t/"),
                            ('Movie Title U',baseurl + "movies/u/"),
                            ('Movie Title V',baseurl + "movies/v/"),
                            ('Movie Title W',baseurl + "movies/w/"),
                            ('Movie Title X',baseurl + "movies/x/"),
                            ('Movie Title Y',baseurl + "movies/y/"),
                            ('Movie Title Z',baseurl + "movies/z/"),]

		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		streamGenreName = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		print streamGenreName, streamGenreLink

		self.session.open(movie25FilmeListeScreen, streamGenreLink, streamGenreName)

class movie25FilmeListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
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

		self['title'] = Label("Movie25")
		self['ContentTitle'] = Label("%s:" % self.streamGenreName)


		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['Page'].setText(str(self.page)+ " of")
		url = "%s%s" % (self.streamGenreLink, str(self.page))
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		lastpage = re.findall('<div class="count_text">.*?\d/(.*\d)&nbsp', data, re.S)
		if lastpage:
			self.lastpage = lastpage[0]
			self['page'].setText(lastpage[0])
		else:
			self.lastpage = 999

		data=data.replace('\r','').replace('\n','').replace('\t','').replace('&nbsp;','')
		movies = re.findall('<div class="movie_pic"><a href="(.*?)".*?title="(.*?)".*?src="(.*?)"', data, re.S)
		if movies:
			self.filmliste = []
			for (link,title,image) in movies:
				link = "http://www.movie25.ag" + link
				self.filmliste.append((decodeHtml(title),link,image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage)
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		self.session.open(movie25StreamListeScreen, streamLink, streamName)

class movie25StreamListeScreen(MPScreen):

	def __init__(self, session, streamGenreLink, streamGenreName):
		self.streamGenreLink = streamGenreLink
		self.streamGenreName = streamGenreName
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Movie25")
		self['ContentTitle'] = Label("Streams for %s:" % self.streamGenreName)


		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.streamGenreLink, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		streams = re.findall('<li id="link_name">(.*?)</li>.*?<li id="playing_button"><a href="(.*?)" target', data, re.S)
		if streams:
			self.filmliste = []
			for (name,link) in streams:
				link = baseurl + link
				name=name.replace('\r','').replace('\n','').replace('\t','').replace('&nbsp;','')
				if isSupportedHoster(name, True):
					self.filmliste.append((decodeHtml(name.strip()),link))
			if len(self.filmliste) == 0:
				self.filmliste.append((_('No supported streams found!'), None))
			self.ml.setList(map(self._defaultlisthoster, self.filmliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		if streamLink == None:
			return
		getPage(streamLink, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getLink).addErrback(self.dataError)

	def getLink(self, data):
		link = re.findall("onclick=\"location.href='(http://.*?)'", data, re.S)
		if link:
			get_stream_link(self.session).check_link(link[0], self.got_link, False)
		else:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.session.open(SimplePlayer, [(self.streamGenreName, stream_url)], showPlaylist=False, ltype='movie25')