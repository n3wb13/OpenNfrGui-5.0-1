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
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
import base64

config.mediaportal.streamxxx_sort = ConfigText(default="date", fixed_size=False)
glob_cookies = CookieJar()

class streamxxxGenreScreen(MPScreen):

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
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("StreamXXX")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.genreliste.append(("--- Search ---", None))
		self.genreliste.append(("New Movies and Clips", "http://streamxxx.tv/new-movies/"))
		self.genreliste.append(("Movies", "http://streamxxx.tv/category/movies/"))
		self.genreliste.append(("International Movies", "http://streamxxx.tv/category/movies/international-movies/"))
		self.genreliste.append(("International Movies - German", "http://streamxxx.tv/category/international-movies/?s=german"))
		self.genreliste.append(("International Movies - French", "http://streamxxx.tv/category/international-movies/?s=french"))
		self.genreliste.append(("Film Porno Italiani", "http://streamxxx.tv/category/movies/film-porno-italian/"))
		self.genreliste.append(("Clips", "Clips"))
		self.genreliste.append(("Tags", "Tags"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(streamxxxFilmScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Clips" or Name == "Tags":
			self.session.open(streamxxxSubGenreScreen, Link, Name)
		else:
			self.session.open(streamxxxFilmScreen, Link, Name)

class streamxxxSubGenreScreen(MPScreen):

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("StreamXXX")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		url = "http://streamxxx.tv/"
		twAgentGetPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if self.Link == "Tags":
			preparse = re.search('<div class="tagcloud">(.*?)</div>', data, re.S)
			if preparse:
				parse = re.findall('href=\'(.*?)\'.*?;\'>(.*?)</a>', preparse.group(1), re.S)
		else:
			preparse = re.search('>Clips</a>(.*?)</ul>', data, re.S)
			if preparse:
				parse = re.findall('class="menu-item menu-item-type-custom menu-item-object-custom menu-item-\d+"><a href="(.*?)">(.*?)<', preparse.group(1), re.S)
		if parse:
			self.genreliste = []
			for (Url, Title) in parse:
				self.genreliste.append((decodeHtml(Title), Url))
			self.genreliste.sort()
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False
		self['name'].setText("")

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if self.Name == "Pornstars" or self.Name == "Site-Rips":
			self.session.open(streamxxxStreamListeScreen, Link, Name)
		else:
			self.session.open(streamxxxFilmScreen, Link, Name)

class streamxxxFilmScreen(MPScreen, ThumbsHelper):

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
			"red" : self.keyTxtPageUp,
			"green" : self.keyPageNumber,
			"yellow" : self.keySort,
			"blue" : self.keyTxtPageDown
		}, -1)

		self.sort = config.mediaportal.streamxxx_sort.value
		self['title'] = Label("StreamXXX")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['F1'] = Label(_("Text-"))
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(self.sort.title())
		self['F4'] = Label(_("Text+"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://streamxxx.tv/page/%s/?s=%s" % (str(self.page), self.Link)
		elif re.search('/\?s=', self.Link):
			urlpart = self.Link.split("?s=")
			url = "%spage/%s/?s=%s" % (urlpart[0],str(self.page),urlpart[1])
		else:
			url = self.Link + "page/" + str(self.page) + "/"
		if self.sort != '':
			if re.search('/\?s=', url):
				url = "%s&orderby=%s" % (url, self.sort)
			else:
				url = "%s/?orderby=%s" % (url, self.sort)
		twAgentGetPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', 'class=\'pages\'>Page.*?of\s(.*?)</span>')
		MoviesL = re.findall('role="main">(.*?)class="loop-nav pag-nav">', data, re.S)
		if MoviesL:
			for item in MoviesL:
				Movies = re.findall('<a class="clip-link".*?title="(.*?)"\shref="(.*?)".*?<img\ssrc="(.*?)".*?datetime.*?>(.*?)<.*?<p class="entry-summary">(.*?)</p>', item, re.S)
				if Movies:
					for (Title, Url, Image, Date, Summary) in Movies:
						Summary = Summary.replace("// ","").replace("\r\n ","").strip()
						Summary = "".join([s for s in Summary.splitlines(True) if s.strip("\r\n")])
						self.filmliste.append((decodeHtml(Title), Url, Image, Date, Summary))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		Date = self['liste'].getCurrent()[0][3]
		Summary = self['liste'].getCurrent()[0][4]
		handlung = "Date: %s\n%s" % (Date,Summary)
		self['name'].setText(Title)
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Image = self['liste'].getCurrent()[0][2]
		if Link == None:
			return
		self.session.open(streamxxxStreamListeScreen, Link, Title, Image)

	def keySort(self):
		if self.keyLocked:
			return
		rangelist = [
					['Date', 'date'],
					['Title', 'title'],
					['Views', 'views'],
					['Likes', 'likes'],
					['Comments', 'comments'],
					['Random', 'rand']
					]
		self.session.openWithCallback(self.returnkeySort, ChoiceBoxExt, title=_('Select Sorting'), list = rangelist)

	def returnkeySort(self, data):
		if data:
			self.sort = data[1]
			self['F3'].setText(self.sort.title())
			config.mediaportal.streamxxx_sort.value = self.sort
			config.mediaportal.streamxxx_sort.save()
			configfile.save()
			self.loadPage()

class streamxxxStreamListeScreen(MPScreen):

	def __init__(self, session, streamFilmLink, streamName, streamImage):
		self.streamFilmLink = streamFilmLink
		self.streamName = streamName
		self.streamImage = streamImage
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
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("StreamXXX")
		self['ContentTitle'] = Label("Streams:")
		self['name'] = Label(_("Please wait..."))

		self.captchainfo = {}
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.streamImage)
		self.keyLocked = True
		self.filmliste = []
		twAgentGetPage(self.streamFilmLink, cookieJar=glob_cookies, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('<span class="stream">(.*?)<div id="extras">', data, re.S)
		streams = re.findall('(http[s]?://(.*?)\/.*?)[\'|"|\&|<]', parse.group(1) , re.S)
		if streams:
			for (stream, hostername) in streams:
				if stream[-1] == "/":
					stream = stream[:-1]
				if isSupportedHoster(hostername, True):
					hostername = hostername.replace('www.','')
					self.filmliste.append((hostername, stream))
		if len(self.filmliste) == 0:
			if re.search('data:image/jpeg;base64', data,re.S):
				self.getCaptchaCookie(data)
			else:
				self.filmliste.append((_("No supported streams found!"), None))
		self.filmliste = list(set(self.filmliste))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False
		self['name'].setText(self.streamName)

	def getCaptchaCookie(self, data):
		p1 = re.search('content-protector-token.*?value="(.*?)"', data, re.S)
		p2 = re.search('content-protector-ident-(.*?)"', data, re.S)
		p3 = re.search('src="data:image/jpeg;base64,(.*?)"', data, re.S)
		if p1 and p2 and p3:
			jpgfile = ('/tmp/captcha.jpg')
			g = open(jpgfile, "w")
			g.write(base64.decodestring(p3.group(1)))
			g.close()
			self.captchainfo = {
				'content-protector-expires': "0",
				'content-protector-token': p1.group(1),
				'content-protector-ident': p2.group(1),
				'content-protector-submit':'Submit'
				}
			self.session.openWithCallback(self.captchaCallback, VirtualKeyBoardExt, title = (_("Captcha input:")), text = "", captcha = "/tmp/captcha.jpg", is_dialog=True)

	def captchaCallback(self, callback=None, entry=None):
		if callback != None or callback != "":
			self.captchainfo.update({'content-protector-password': callback})
			twAgentGetPage(self.streamFilmLink, cookieJar=glob_cookies, method='POST', postdata=urlencode(self.captchainfo), headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def keyOK(self):
		if self.keyLocked:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		if streamLink == None:
			return
		get_stream_link(self.session).check_link(streamLink, self.got_link)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.session.open(SimplePlayer, [(self.streamName, stream_url, self.streamImage)], showPlaylist=False, ltype='streamxxx', cover=True)