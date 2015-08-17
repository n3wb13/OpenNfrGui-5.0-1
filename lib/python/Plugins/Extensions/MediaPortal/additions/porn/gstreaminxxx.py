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
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.twagenthelper import TwAgentHelper, twAgentGetPage

sitechrx = ''

special_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
	'Referer': 'http://gstream.to/'
}

class gstreaminxxxGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode
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
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("GStream.to")
		self['ContentTitle'] = Label(_("Genre Selection"))
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.get_site_cookie1)

	def get_site_cookie1(self):
		self.keyLocked = True
		url = "http://gstream.to"
		twAgentGetPage(url, agent=special_headers, headers={'Cookie': 'overkill_in='+str(time())}).addCallback(self.get_site_cookie2).addErrback(self.dataError)

	def get_site_cookie2(self, data):
		x = re.search('searchfrm', data, re.S)
		if x:
			self.layoutFinished()
			return
		self.keyLocked = True
		raw = re.findall('javascript"\ssrc="(.*?)">.*?scf\(\'(.*?)\'\+\'(.*?)\'.*?', data, re.S)
		url = "http://gstream.to" + str(raw[0][0])
		twAgentGetPage(url, agent=special_headers, headers={'Cookie': 'overkill_in='+str(time())}).addCallback(self.get_site_cookie3, raw[0][1], raw[0][2]).addErrback(self.dataError)

	def get_site_cookie3(self, data, cookie1, cookie2):
		raw = re.findall('escape\(hsh.*?"(.*?)"\)', data, re.S)
		global sitechrx
		sitechrx = str(cookie1) + str(cookie2) + str(raw[0])
		print 'sitechrx='+sitechrx
		self.layoutFinished()

	def layoutFinished(self):
		if self.mode == "porn":
			self.genreliste.append(("--- Search XXX Title Only ---", "661"))
			self.genreliste.append(("--- Search XXX Entire Post ---", "661"))
			self.genreliste.append(("Newest", ""))
			self.genreliste.append(("Amateur", "Amateure1"))
			self.genreliste.append(("Anal", "Anal"))
			self.genreliste.append(("Asian", "Asia"))
			self.genreliste.append(("Big Tits", "GrosseBrueste"))
			self.genreliste.append(("Black", "Ebony"))
			self.genreliste.append(("Blowjob", "Blowjob"))
			self.genreliste.append(("Fetish", "Fetish"))
			self.genreliste.append(("Gay", "Gay"))
			self.genreliste.append(("German", "Deutsch"))
			self.genreliste.append(("Group Sex", "Gruppensex"))
			self.genreliste.append(("Hardcore", "Hardcore"))
			self.genreliste.append(("Interracial", "International"))
			self.genreliste.append(("Lesbian", "Lesben"))
			self.genreliste.append(("Masturbation", "Masturbation"))
			self.genreliste.append(("Teens", "Teens"))
		else:
			self.genreliste.append(("--- Search Title Only ---", "528"))
			self.genreliste.append(("--- Search Entire Post ---", "528"))
			self.genreliste.append(("HD Filme", ""))
			self.genreliste.append(("Aktuelle Kinofilme", "542"))
			self.genreliste.append(("Abenteuer / Fantasy / Western", "596"))
			self.genreliste.append(("Action", "591"))
			self.genreliste.append(("Dokumentarfilme", "751"))
			self.genreliste.append(("Drama / Romanze", "594"))
			self.genreliste.append(("Horror", "593"))
			self.genreliste.append(("Komödie", "592"))
			self.genreliste.append(("Science Fiction", "655"))
			self.genreliste.append(("Thriller", "595"))
			self.genreliste.append(("Trickfilm", "677"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if re.search('--- Search', Name):
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True)
		else:
			self.session.open(gstreaminxxxFilmScreen, Link, Name, self.mode)

	def searchCallback(self, callbackStr):
		Name = self['liste'].getCurrent()[0][0]
		if callbackStr is not None:
			self.session.open(gstreaminxxxFilmScreen, callbackStr, Name, self.mode)

class gstreaminxxxFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, mode):
		self.mode = mode
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

		self['title'] = Label("GStream.to")
		self['ContentTitle'] = Label(self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.tw_agent_hlp = TwAgentHelper(redir_agent=True)
		self.urlRedirected = ''
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.search('Search', self.Name) or self.Name == 'HD Filme':
			if self.urlRedirected =='':
				if self.Name == 'HD Filme':
					baseurl = 'http://gstream.to/search.php?do=process&prefixchoice[]=hd'
				else:
					if re.search('Entire Post', self.Name):
						titleonly = 0
					else:
						titleonly = 1
					if self.mode == "porn":
						searchType = '661'
					else:
						searchType = '528'
					baseurl = 'http://gstream.to/search.php?do=process&childforums=1&do=process&exactname=1&forumchoice[]=%s&query=%s&s=&securitytoken=guest&titleonly=%s' % (searchType,self.Link,titleonly)
				self.tw_agent_hlp.headers.addRawHeader('Cookie', 'sitechrx='+sitechrx+'; overkill_in='+str(time()))
				self.tw_agent_hlp.headers.addRawHeader('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31')
				self.tw_agent_hlp.headers.addRawHeader('Accept-Charset','ISO-8859-1,utf-8;q=0.7,*;q=0.3')
				self.tw_agent_hlp.headers.addRawHeader('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
				self.tw_agent_hlp.headers.addRawHeader('Accept-Language','de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4')
				self.tw_agent_hlp.headers.addRawHeader('Referer','http://gstream.to/')
				self.tw_agent_hlp.getRedirectedUrl(baseurl).addCallback(self.getRedirectedData).addErrback(self.dataError)
			else:
				self.getRedirectedData(self.urlRedirected)
		else:
			if self.mode == "porn":
				baseurl = 'http://gstream.to/forumdisplay.php?s=&f=661&pp=20&sort=lastpost&order=desc&daysprune=-1&prefixid='
				url = baseurl + "%s&page=%s" % (self.Link, str(self.page))
			else:
				url = 'http://gstream.to/forumdisplay.php?f=%s&pp=20&sort=lastpost&order=desc&page=%s' % (self.Link, str(self.page))
			twAgentGetPage(url, agent=special_headers, followRedirect=False, headers={'Cookie': 'sitechrx='+sitechrx+'; overkill_in='+str(time())}).addCallback(self.loadData).addErrback(self.dataError)

	def getRedirectedData(self, urlRedirected):
		self.urlRedirected = urlRedirected
		url = self.urlRedirected + "&page=%s" % str(self.page)
		twAgentGetPage(url, agent=special_headers, headers={'Cookie': 'sitechrx='+sitechrx+'; overkill_in='+str(time())}).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', 'normal">Seite.*?von\s(.*?)</td>')
		Movies = re.findall('class="p1"\shref="(.*?)".*?class="large"\ssrc="(.*?)".*?thread_title_[0-9]+".*?>(.*?)</a>', data, re.S)
		if Movies:
			for (Url, Image, Title) in Movies:
				if Title != "DE. MILFs brauchen anonymen Sex!":
					Url = Url.replace('&amp;','&')
					Url = 'http://gstream.to/' + Url
					if re.search('images-box.com|rapidimg.org|your-imag.es|pics-traderz.org|imgload.biz|lulzimg.com|shareimage.me|pic.ms', str(Image), re.S):
						Image = None
					self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) < 1:
			self.filmliste.append(("No streams found!", None,""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage)
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
		Cover = self['liste'].getCurrent()[0][2]
		self.session.open(gstreaminxxxStreamListeScreen, Link, Title, Cover)

class gstreaminxxxStreamListeScreen(MPScreen):

	def __init__(self, session, streamFilmLink, streamName, cover):
		self.streamFilmLink = streamFilmLink
		self.streamName = streamName
		self.cover = cover
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
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("GStream.to")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.streamName)

		self.tw_agent_hlp = TwAgentHelper()
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.cover)
		self['name'].setText(_('Please wait...'))
		twAgentGetPage(self.streamFilmLink, agent=special_headers, headers={'Cookie': 'sitechrx='+sitechrx+'; overkill_in='+str(time())}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		raw = re.search('<table\sid="post[0-9]+"(.*?)id="post_thanks_box', data, re.S)
		raw = re.sub(r'<!-- 1<script type="text/javascript">jwplayer.key.*?</script>1 -->', "", raw.group(1))
		streams = re.findall('href="(http://(?!gstream\.to/(mirror|img|images)/)(?!www.youtube.com)(?!www.filefactory)(gstream\.to/secure/|)(.*?)\/.*?)[\'|"|\&|<]', raw, re.S)
		if streams:
			for (stream, dummy, dummy2, hostername) in streams:
				if isSupportedHoster(hostername, True):
					hostername = hostername.replace('www.','').replace('embed.','')
					self.filmliste.append((hostername, stream))
			# remove duplicates
			self.filmliste = list(set(self.filmliste))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self['name'].setText(self.streamName)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url == None:
			return
		url = url.replace('&amp;','&')
		self['name'].setText(_('Please wait...'))
		if re.match('.*?gstream.to/secure/', url, re.S|re.I):
			print 'Secured Play'
			self.tw_agent_hlp.headers.addRawHeader('Referer','http://gstream.to/')
			self.tw_agent_hlp.getRedirectedUrl(url).addCallback(self.get_stream).addErrback(self.dataError)
		else:
			print 'Direct Play'
			self.get_stream(url)

	def get_stream(self,url):
		get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		self['name'].setText(self.streamName)
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.session.open(SimplePlayer, [(self.streamName, stream_url)], showPlaylist=False, ltype='gstreaminxxx')