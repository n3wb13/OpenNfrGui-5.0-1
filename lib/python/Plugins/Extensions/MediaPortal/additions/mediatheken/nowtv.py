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
from Plugins.Extensions.MediaPortal.resources.playrtmpmovie import PlayRtmpMovie

BASE_URL = "https://api.nowtv.de/v3/"

def remove_start(s, start):
	if s.startswith(start):
		return s[len(start):]
	return s

class nowtvFirstScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("NOW TV")
		self['ContentTitle'] = Label(_("Stations:"))
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.senderliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.senderliste.append(("RTL", "rtl", "http://cdn.static-fra.de/nowtv/default/rtl_portrait.jpg"))
		self.senderliste.append(("VOX", "vox", "http://cdn.static-fra.de/nowtv/default/vox_portrait.jpg"))
		self.senderliste.append(("RTL2", "rtl2", "http://cdn.static-fra.de/nowtv/default/rtl2_portrait.jpg"))
		self.senderliste.append(("RTLNITRO", "nitro",  "http://cdn.static-fra.de/nowtv/default/nitro_portrait.jpg"))
		self.senderliste.append(("SUPER RTL", "superrtl", "http://cdn.static-fra.de/nowtv/default/superrtl_portrait.jpg"))
		self.senderliste.append(("n-tv", "ntv", "http://cdn.static-fra.de/nowtv/default/ntv_portrait.jpg"))
		self.ml.setList(map(self._defaultlistcenter, self.senderliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.senderliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)
		Name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_("Selection:") + " " + Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Image = self['liste'].getCurrent()[0][2]
		self.session.open(nowtvSubGenreScreen, Link, Name, Image)

class nowtvSubGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Image):
		self.Link = Link
		self.Name = Name
		self.Image = Image
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/defaultGenreScreenCover.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreenCover.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("NOW TV")
		self['ContentTitle'] = Label(_("Selection:"))
		self['name'] = Label(_("Selection:") + " " + self.Name)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = BASE_URL + "formats?fields=title,seoUrl,icon,defaultImage169Logo,defaultImage169Format&filter=%7B%22Station%22:%22" + self.Link + "%22,%22Disabled%22:%220%22,%22CategoryId%22:%7B%22containsIn%22:%5B%22serie%22,%22news%22%5D%7D%7D&maxPerPage=1000"
		twAgentGetPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		nowdata = json.loads(data)
		for node in nowdata["items"]:
			if str(node["icon"]) == "new" or str(node["icon"]) == "free":
				image = str(node["defaultImage169Logo"])
				if image == "":
					image = str(node["defaultImage169Format"])
				if image == "":
					image = self.Image
				self.filmliste.append((str(node["title"]), str(node["seoUrl"]), image))
		self.filmliste.sort(key=lambda t : t[0].lower())
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)
		Name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_("Selection:") + " " + self.Name + ":" + Name)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Name = self.Name + ":" + self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Image = self['liste'].getCurrent()[0][2]
		self.session.open(nowtvStaffelScreen, Link, Name, Image)

class nowtvStaffelScreen(MPScreen):

	def __init__(self, session, Link, Name, Image):
		self.Link = Link
		self.Name = Name
		self.Image = Image
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("NOW TV")
		self['ContentTitle'] = Label(_("Seasons:"))
		self['name'] = Label(_("Selection:") + " " + self.Name)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = BASE_URL + "formats/seo?fields=formatTabs.*&name=" + self.Link + ".php"
		twAgentGetPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		nowdata = json.loads(data)
		for node in nowdata["formatTabs"]["items"]:
			self.filmliste.append((str(node["headline"]), str(node["id"]), str(node["visible"]),str(node["tv"])))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		CoverHelper(self['coverArt']).getCover(self.Image)
		self.showInfos()

	def showInfos(self):
		Name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_("Selection:") + " " + self.Name + ":" + Name)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Name = self.Name + ":" + self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(nowtvEpisodenScreen, Link, Name, self.Image)

class nowtvEpisodenScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Image):
		self.Link = Link
		self.Name = Name
		self.Image = Image
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
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self['title'] = Label("NOW TV")
		self['ContentTitle'] = Label(_("Episodes:"))
		self['name'] = Label(_("Selection:") + " " + self.Name)
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = BASE_URL + "formatlists/" + self.Link + "?fields=*,formatTabPages.*,formatTabPages.container.movies.*,formatTabPages.container.movies.format.*,formatTabPages.container.movies.livestreamEvent.*,formatTabPages.container.movies.pictures,formatTabPages.container.movies.files.*"
		twAgentGetPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		nowdata = json.loads(data)
		for node in nowdata["formatTabPages"]["items"]:
			try:
				for nodex in node["container"]["movies"]["items"]:
					try:
						if nodex["free"]:
							try:
								image = "http://autoimg.rtl.de/rtlnow/%s/660x660/formatimage.jpg" % nodex["pictures"]["default"][0]["id"]
							except:
								image = self.Image
							try:
								file = str(nodex["files"]["items"][0]["path"])
								file = re.sub(r'/(.+)/((\d+)/(.*))', r'/\1/videos/\2', file)
								file = file.strip('/')
							except:
								file = None
							self.filmliste.append((str(nodex["title"]), str(nodex["id"]), str(nodex["articleLong"]), image, file))
					except:
						continue
			except:
				continue
		if len(self.filmliste) == 0:
			self.filmliste.append((_('Currently no free episodes available!'), None, None, None))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		Descr = self['liste'].getCurrent()[0][2]
		Image = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(decodeHtml(Descr))
		CoverHelper(self['coverArt']).getCover(Image)
		Name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_("Selection:") + " " + self.Name + ":" + Name)

	def keyOK(self):
		id = self['liste'].getCurrent()[0][1]
		if self.keyLocked or id == None:
			return
		url = 'https://api.nowtv.de/v3/movies/%s?fields=files' % id
		getPage(url, agent=std_headers).addCallback(self.get_stream).addErrback(self.dataError)

	def get_stream(self, data):
		videoPrio = int(config.mediaportal.videoquali_others.value)
		if videoPrio == 2:
			bw = 1300
		elif videoPrio in (0, 1):
			bw = 600

		nowdata = json.loads(data)
		format = None
		for node in nowdata["files"]["items"]:
			if node['type'] != u'video/x-f4v':
				continue
			_bw = node.get('bitrate', 0)
			app, play_path = remove_start(node['path'], '/').split('/', 1)
			format = {
				'url': 'rtmpe://fms.rtl.de',
				'app': app,
				'play_path': 'mp4:%s' % play_path,
				'page_url': 'http://%s.rtl.de' % app,
				'player_url': 'http://cdn.static-fra.de/now/vodplayer.swf',
				'tbr': _bw,
				}
			if _bw == bw:
				break

		if format:
			Name = self['liste'].getCurrent()[0][0]
			if config.mediaportal.useRtmpDump.value:
				final = "{url}' --playpath={play_path} --app={app} --swfVfy={player_url} --pageUrl={page_url} --timeout=120'".format(**format)
				movieinfo = [str(final),Name]
				self.session.open(PlayRtmpMovie, movieinfo, Name, playCallback=self.playRtmpStream)
			else:
				final = "{url} swfVfy=1 playpath={play_path} app={app} swfUrl={player_url} pageUrl={page_url} timeout=120".format(**format)
				self.session.open(SimplePlayer, [(Name, str(final))], showPlaylist=False, ltype='nowtv')
		else:
			self.session.open(MessageBoxExt, _("No Streams found!"), MessageBoxExt.TYPE_INFO)

	def playRtmpStream(self, movietitle, moviepath, movie_img, cont_cb=None, exit_cb=None):
		self.playrtmp_cont_callback = cont_cb
		self.playrtmp_exit_callback = exit_cb
		self.session.openWithCallback(self.cb_Player, SimplePlayer, [(movietitle, moviepath, movie_img)], cover=False, showPlaylist=False, ltype='rtlnow-rtmp', useResume=False, bufferingOpt = 'rtmpbuffering')

	def cb_Player(self, retval=None):
		if retval == 'continue':
			self.playrtmp_cont_callback()
		else:
			self.playrtmp_exit_callback()