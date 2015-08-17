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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

sitechrx = ''

special_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
	'Referer': 'http://playporn.to/'
}

class playpornGenreScreen(MPScreen):

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
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("PlayPorn.to")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.get_site_cookie1)

	def get_site_cookie1(self):
		self.keyLocked = True
		url = "http://playporn.to"
		twAgentGetPage(url, headers=special_headers).addCallback(self.get_site_cookie2).addErrback(self.dataError)

	def get_site_cookie2(self, data):
		x = re.search('searchform', data, re.S)
		if x:
			self.layoutFinished()
			return
		self.keyLocked = True
		raw = re.findall('javascript"\ssrc="(.*?)">.*?scf\(\'(.*?)\'\+\'(.*?)\'.*?', data, re.S)
		url = "http://playporn.to" + str(raw[0][0])
		twAgentGetPage(url, headers=special_headers).addCallback(self.get_site_cookie3, raw[0][1], raw[0][2]).addErrback(self.dataError)

	def get_site_cookie3(self, data, cookie1, cookie2):
		raw = re.findall('escape\(hsh.*?"(.*?)"\)', data, re.S)
		global sitechrx
		sitechrx = str(cookie1) + str(cookie2) + str(raw[0])
		print 'sitechrx='+sitechrx
		self.layoutFinished()

	def layoutFinished(self):
		self.genreliste.append(("--- Search ---", "callSuchen"))
		self.genreliste.append(("Newest", "http://playporn.to/category/xxx-movie-stream/page/"))
		self.genreliste.append(("Amateur", "http://playporn.to/category/xxx-movie-stream/amateure/page/"))
		self.genreliste.append(("Anal", "http://playporn.to/category/xxx-movie-stream/anal/page/"))
		self.genreliste.append(("Asian", "http://playporn.to/category/xxx-movie-stream/asian-girls/page/"))
		self.genreliste.append(("Big Tits", "http://playporn.to/category/xxx-movie-stream/big-tits-stream/page/"))
		self.genreliste.append(("Black", "http://playporn.to/category/xxx-movie-stream/black/page/"))
		self.genreliste.append(("Blowjob", "http://playporn.to/category/xxx-movie-stream/oral-blowjob/page/"))
		self.genreliste.append(("Fetish", "http://playporn.to/category/xxx-movie-stream/fetish/page/"))
		self.genreliste.append(("German", "http://playporn.to/category/xxx-movie-stream/deutsch/page/"))
		self.genreliste.append(("Group Sex", "http://playporn.to/category/xxx-movie-stream/gangbang-gruppensex/page/"))
		self.genreliste.append(("Hardcore", "http://playporn.to/category/xxx-movie-stream/hardcore-fuck/page/"))
		self.genreliste.append(("Lesbian", "http://playporn.to/category/xxx-movie-stream/lesben-sex/page/"))
		self.genreliste.append(("Masturbation", "http://playporn.to/category/xxx-movie-stream/masturbation-toys/page/"))
		self.genreliste.append(("Mature", "http://playporn.to/category/xxx-movie-stream/mature-milf-xxx-movie-stream/page/"))
		self.genreliste.append(("Pornstars", "http://playporn.to/category/xxx-movie-stream/pornstars/page/"))
		self.genreliste.append(("Teens", "http://playporn.to/category/xxx-movie-stream/teens-sex/page/"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()

		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(playpornFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = '%s' % (self.suchString)
			Name = "--- Search ---"
			self.session.open(playpornFilmScreen, Link, Name)

class playpornFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("PlayPorn.to")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://playporn.to/page/%s/?s=%s&submit=Search" % (str(self.page), self.Link)
		else:
			url = "%s%s/" % (self.Link, str(self.page))
		twAgentGetPage(url, agent=special_headers, headers={'Cookie': 'sitechrx='+sitechrx}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', 'class=\'pages\'>.*?of\s(.*?)</span>')
		Movies = re.findall('class="photo-thumb-image"><a\shref="(.*?)"\stitle="(.*?)".*?[thumbindex"|img]\ssrc=[\'|"](.*?)[\'|"].*?class="fix"', data, re.S)
		if Movies:
			for (Url, Title, Image) in Movies:
				if re.search('images-box.com|rapidimg.org', str(Image), re.S):
					Image = None
				self.filmliste.append((decodeHtml(Title), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste,0,1,2,None,None,self.page,self.lastpage)
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(playpornStreamListeScreen, Link, Title)

class playpornStreamListeScreen(MPScreen):

	def __init__(self, session, streamFilmLink, streamName):
		self.streamFilmLink = streamFilmLink
		self.streamName = streamName
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
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("PlayPorn.to")
		self['ContentTitle'] = Label("Streams:")
		self['name'] = Label(self.streamName)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		twAgentGetPage(self.streamFilmLink, agent=special_headers, headers={'Cookie': 'sitechrx='+sitechrx}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('<div\sid="single-photo"(.*?)id="footer-out', data, re.S)
		streams = re.findall('(http[s]?://(?!playporn.to)(?!streamcloud.eu/favicon.ico)(.*?)\/.*?)[\'|"|\&|<]', parse.group(1), re.S)
		if streams:
			for (stream, hostername) in streams:
				if isSupportedHoster(hostername, True):
					hostername = hostername.replace('www.','').replace('embed.','')
					self.filmliste.append((hostername, stream))
			# remove duplicates
			self.filmliste = list(set(self.filmliste))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		if streamLink == None:
			return
		self.get_stream(streamLink)

	def get_stream(self,url):
		get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.session.open(SimplePlayer, [(self.streamName, stream_url)], showPlaylist=False, ltype='playporn')