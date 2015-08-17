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
import base64

baseurl = "http://watchthefullvideofree.com/"
basename = "WTFvideofree"

class wtfvideofreeGenreScreen(MPScreen):

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

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.filmliste.append(("--- Search ---", None))
		self.filmliste.append(("Latest", baseurl))
		self.filmliste.append(("Categories", "categories"))
		self.filmliste.append(("Genres", "genres"))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(wtfvideofreeListScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Latest":
			self.session.open(wtfvideofreeListScreen, Link, Name)
		else:
			self.session.open(wtfvideofreeSubGenreScreen, Link, Name)

class wtfvideofreeSubGenreScreen(MPScreen):

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
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("%s:" % self.Name)
		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = baseurl
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.findall('<ul class="sub-menu">(.*?)</ul>', data, re.S)
		if parse and len(parse) >= 3:
			if self.Link == "categories":
				parsecat = parse[1] + parse[2]
				raw = re.findall('menu-item-object-category\smenu-item-.*?href="(.*?)">(.*?)</a>', parsecat, re.S)
				if raw:
					for (Url, Title) in raw:
						self.filmliste.append((decodeHtml(Title).title(), Url))
			else:
				raw = re.findall('menu-item-object-custom\smenu-item-.*?href="(.*?)">(.*?)</a>', parse[0], re.S)
				if raw:
					for (Url, Title) in raw:
						self.filmliste.append((decodeHtml(Title).title(), Url))
		self.filmliste = list(set(self.filmliste))
		self.filmliste.sort()
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(wtfvideofreeListScreen, Link, Name)

class wtfvideofreeListScreen(MPScreen, ThumbsHelper):

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "%spage/%s/?s=%s" % (baseurl, str(self.page), self.Link)
		else:
			url = self.Link + "page/" + str(self.page) + "/"
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, '', 'var\spbd_alp\s=\s\{"startPage":"\d+","maxPages":"(.*?)","')
		preparse = re.search('class="(video|search)-listing-content(.*?)</body>', data, re.S)
		if preparse:
			raw = re.findall('class="item-thumbnail".*?<a\shref="(.*?)".*?<img\ssrc="(.*?)".*?alt="(.*?)"', preparse.group(2), re.S)
			x = []
			if raw:
				for (url, image, title) in raw:
					if url not in x:
						title = title.replace('Enjoy ','').replace('(HOT)','').replace('(TODAY)','').replace('(TODAY PREMIERE)','').replace('(SPECIAL)','').replace('(Special)','').replace('(NEW)','').replace('(TODAY RELEASE)','').replace('(SPECIAL OF DAY)','').replace('(GOOD)','').replace('(ESTRENO)','')
						self.filmliste.append((decodeHtml(title).strip(), url, image))
						x.append(url)
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), '', None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		cover = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(cover)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][0]
		if Link == None:
			return
		Title = self['liste'].getCurrent()[0][1]
		self.session.open(StreamAuswahl, Link, Title)

class StreamAuswahl(MPScreen):

	def __init__(self, session, Title, Link):
		self.Link = Link
		self.Title = Title
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("%s" %self.Title)

		self.filmliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = self.Link
		getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('class="wordpress-post-tabs(.*?)class="wpts_cr', data, re.S)
		if parse:
			streamsids = re.findall('#tabs-(.*?)".*?(><a href="(http[s]?://(.*?)\/.*?)" target="_blank"|)>((?!<s).*?)<', parse.group(1), re.S)
			if streamsids:
				for (id, x, link, hoster, quality) in streamsids:
					if not link:
						stream = re.findall('id="tabs-'+id+'.*?="(http[s]?://(.*?)\/.*?)"', parse.group(1), re.S)
						if stream:
							if isSupportedHoster(stream[0][1], True):
								hoster = '%s - %s' % (quality, stream[0][1].replace('wtf-is-this.xyz', 'WTFISTHIS redirect'))
								self.filmliste.append((hoster, stream[0][0]))
					else:
						hoster = '%s - %s' % (quality, hoster.replace('wtf-is-this.xyz', 'WTFISTHIS redirect'))
						self.filmliste.append((hoster, link))
		else:
			streamsids = re.findall('center;">.*?<strong>(\w.*?)<.*?<iframe\ssrc="(http[s]?://(.*?)\/.*?)"', data, re.S)
			if streamsids:
				for (quality, link, hoster) in streamsids:
					if isSupportedHoster(hoster, True) or hoster == 'wtf-is-this.xyz':
						hoster = '%s - %s' % (quality, hoster.replace('wtf-is-this.xyz', 'WTFISTHIS redirect'))
						self.filmliste.append((hoster, link))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamHoster = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if url == None:
			return
		if re.search('redirect', streamHoster):
			getPage(url).addCallback(self.wtfisthis).addErrback(self.dataError)
		else:
			get_stream_link(self.session).check_link(url, self.got_link)

	def wtfisthis(self, data):
		url = re.search('<a href="(http://wtf-is-this.xyz/\?r=.*?)"', data, re.S)
		if url:
			url = url.group(1)
			self.tw_agent_hlp = TwAgentHelper()
			self.tw_agent_hlp.getRedirectedUrl(url).addCallback(self.wtfisthisdata).addErrback(self.dataError)
		else:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)

	def wtfisthisdata(self, data):
		getPage(data, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.adfly).addErrback(self.dataError)

	def adfly(self, data):
		ysmm = re.search("var\sysmm\s=\s'(.*?)'", data)
		if ysmm:
			ysmm = ysmm.group(1)
			left = ''
			right = ''
			for c in [ysmm[i:i+2] for i in range(0, len(ysmm), 2)]:
				left += c[0]
				right = c[1] + right
			url = base64.b64decode(left.encode() + right.encode())[2:].decode()
			if re.search(r'go\.php\?u\=', url):
				url = base64.b64decode(re.sub(r'(.*?)u=', '', url)).decode()
			if re.search('wtf-zone\.xyz', url, re.S):
				self.wtfzone(str(url))
			else:
				get_stream_link(self.session).check_link(str(url), self.got_link)
		else:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)

	def wtfzone(self, url):
		if re.search('wtf-zone\.xyz/embed', url, re.S):
			link = url
		else:
			id = re.search('wtf-zone\.xyz/view/.*?/(.*?)$', url)
			if id:
				link = "http://wtf-zone.xyz/embed/%s" % str(id.group(1))
		getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.wtfzonedata).addErrback(self.dataError)

	def wtfzonedata(self, data):
		stream_url = re.search('\'player\'><iframe.*?src="(http.*?)"', data, re.S)
		if stream_url:
			stream_url = stream_url.group(1)
			get_stream_link(self.session).check_link(str(stream_url), self.got_link)
		else:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			title = self.Title
			self.session.open(SimplePlayer, [(self.Title, stream_url)], showPlaylist=False, ltype='wtfvideofree')