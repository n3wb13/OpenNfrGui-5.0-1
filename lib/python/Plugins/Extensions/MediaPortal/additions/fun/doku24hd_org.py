# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
from Plugins.Extensions.MediaPortal.additions.fun.youtube import YT_ListScreen

D24HD_Version = "DOKU24HD v0.95"

D24HD_siteEncoding = 'utf-8'

"""
Sondertastenbelegung:

Genre Auswahl:
	KeyCancel		: Menu Up / Exit
	KeyOK			: Menu Down / Select

Doku Auswahl:
	Bouquet +/-				: Seitenweise blättern in 1er Schritten Up/Down
	'1', '4', '7',
	'3', 6', '9'			: blättern in 2er, 5er, 10er Schritten Down/Up
	Rot/Blau				: Die Beschreibung Seitenweise scrollen

Stream Auswahl:
	Rot/Blau				: Die Beschreibung Seitenweise scrollen
"""

class show_D24HD_Genre(MenuHelper):

	def __init__(self, session):

		baseUrl = "http://doku24hd.org"
		MenuHelper.__init__(self, session, 0, None, baseUrl, "", self._defaultlistcenter)

		self['title'] = Label(D24HD_Version)
		self['ContentTitle'] = Label("Genres")

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_parseCategorys(self, data):
		print 'mh_parseCategorys:'
		th_ex = ['Home','Live','Stream','TV']
		menu_marker = '"menu-geschichte"'
		menu=self.scanMenu(data,menu_marker,themes_ex=th_ex,base_url=self.mh_baseUrl)
		if menu:
			menu.insert(0, (0, '/category/doku', 'DOKU'))
			menu.insert(0, (0, '/category/trailer-kino-news', 'Trailer & Kino News'))
			menu.insert(0, (0, '/category/movies', 'Movies'))
			menu.insert(0, (0, '', 'Meistgesehene Beiträge'))
			menu.append((0, '/category/hd', 'HD'))
			menu.insert(0, (0, '', 'Neueste Beiträge'))
			menu.insert(0, (0, '/category/autoupload', 'Gast Uploads'))
		self.mh_genMenu2(menu)

	def mh_callGenreListScreen(self):
		genreurl = self.mh_baseUrl+self.mh_genreUrl[self.mh_menuLevel]
		print 'GenreURL:',genreurl
		self.session.open(D24HD_FilmListeScreen, genreurl, self.mh_genreTitle)

class D24HD_FilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName):
		self.genreLink = genreLink
		self.genreName = genreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/dokuListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/dokuListScreen.xml"
		print path
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions", "EPGSelectActions","DirectionActions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"upUp" : self.key_repeatedUp,
			"rightUp" : self.key_repeatedUp,
			"leftUp" : self.key_repeatedUp,
			"downUp" : self.key_repeatedUp,
			"upRepeated" : self.keyUpRepeated,
			"downRepeated" : self.keyDownRepeated,
			"rightRepeated" : self.keyRightRepeated,
			"leftRepeated" : self.keyLeftRepeated,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"1" : self.key_1,
			"3" : self.key_3,
			"4" : self.key_4,
			"6" : self.key_6,
			"7" : self.key_7,
			"9" : self.key_9,
			"0"	: self.closeAll,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self.sortOrder = 0
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label(D24HD_Version)

		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))
		self['Page'] = Label(_("Page:"))

		self.filmQ = Queue.Queue(0)
		self.hanQ = Queue.Queue(0)
		self.picQ = Queue.Queue(0)
		self.updateP = 0
		self.eventL = threading.Event()
		self.eventP = threading.Event()
		self.keyLocked = True
		self.dokusListe = []
		self.page = 0
		self.pages = 0;
		self.newDocs = 'Neueste Beiträge' == genreName
		self.mostViewed = 'Meistgesehene Beiträge' == genreName

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		#print genreName
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		print "loadPage:"
		url = "%s/page/%d/" % (self.genreLink, max(self.page,1))

		if self.page:
			self['page'].setText("%d / %d" % (self.page,self.pages))

		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()
		print "eventL ",self.eventL.is_set()

	def loadPageQueued(self):
		print "loadPageQueued:"
		self['name'].setText(_('Please wait...'))
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		print url
		twAgentGetPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		print "dataError:"
		printl(error,self,"E")
		self.dokusListe = []
		self.dokusListe.append((_("No dokus / streams found!"),"","",""))
		self.ml.setList(map(self._defaultlistleft, self.dokusListe))

	def loadPageData(self, data):
		print "loadPageData:",len(data)
		self.dokusListe = []
		data = data.replace('\n', '')

		if self.newDocs:
			mg = re.search('"name">Neueste ᴴᴰ Beiträge<(.*?</div>\s*</div>)\s*</div>\s*</div>\s*</div>', data)
			if mg:
				data = mg.group(1)
		elif self.mostViewed:
			mg = re.search('"name">Meistgesehene ᴴᴰ Beiträge<(.*?</div>\s*</div>)\s*</div>\s*</div>\s*</div>', data)
			if mg:
				data = mg.group(1)

		l = len(data)
		a = 0
		while a < l:
			mg = re.search('id="post-(.*?)</div>\s*</div>', data[a:])
			if mg:
				print 'mg found'
				a += mg.end()
				m1 = re.search('title="(.*?)"\s*href="(.*?)">.*?<img.*?src="(.*?)".*?="entry-summary">(.*?)</p>', mg.group(1))
				if m1:
					print 'm1 found'
					desc = decodeHtml(m1.group(4).strip())
					url = m1.group(2)
					img = m1.group(3)
					tit = decodeHtml(m1.group(1).replace('ᴴᴰ','').strip())
					self.dokusListe.append((tit, url, img, desc))
			else:
				break

		if self.dokusListe:
			print "Dokus found !"
			if not self.pages:
				m = re.search("='pages'>Seite 1 von (\d+)<", data)
				try:
					pages = int(m.group(1))
				except:
					pages = 1

				if pages > self.pages:
					self.pages = pages

			if not self.page:
				self.page = 1
			print "Page: %d / %d" % (self.page,self.pages)
			self['page'].setText("%d / %d" % (self.page,self.pages))

			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			self.th_ThumbsQuery(self.dokusListe,0,1,2,None,None, self.page, self.pages, mode=1)
			self.loadPicQueued()
		else:
			print "No dokus found!"
			self.dokusListe.append((_("No dokus found!"),"","",""))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()

	def loadPic(self):
		print "loadPic:"

		if self.picQ.empty():
			self.eventP.clear()
			print "picQ is empty"
			return

		if self.updateP:
			print "Pict. or descr. update in progress"
			print "eventP: ",self.eventP.is_set()
			print "updateP: ",self.updateP
			return

		while not self.picQ.empty():
			self.picQ.get_nowait()

		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][2]
		#print "streamName: ",streamName
		#print "streamPic: ",streamPic
		#print "streamUrl: ",streamUrl
		self.updateP = 1
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)

	def getHandlung(self, desc):
		print "getHandlung:"
		if desc == None:
			print "No Infos found !"
			self['handlung'].setText(_("No further information available!"))
			return
		self.setHandlung(desc)

	def setHandlung(self, data):
		print "setHandlung:"
		self['handlung'].setText(data)

	def ShowCoverFileExit(self):
		print "showCoverExitFile:"
		self.updateP = 0;
		self.keyLocked	= False
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
			self.loadPic()

	def loadPicQueued(self):
		print "loadPicQueued:"
		self.picQ.put(None)
		if not self.eventP.is_set():
			self.eventP.set()
		desc = self['liste'].getCurrent()[0][3]
		self.getHandlung(desc)
		self.loadPic()
		print "eventP: ",self.eventP.is_set()

	def parseYTStream(self, data):
		print "parseYTStream:"
		mvid = re.search('id="video">(.*?)</div', data, re.S)
		if not mvid:
			print "No stream found"
			self.got_link(None)
			return
		m2 = re.search('//www.youtube.*?com/(embed|v|p)/(.*?)(\?|" |&amp)', mvid.group(1))
		if m2:
			print "Streams found"
			dhVideoId = m2.group(2)
			dhTitle = self['liste'].getCurrent()[0][0]
			if 'p' == m2.group(1):
				url = 'http://gdata.youtube.com/feeds/api/playlists/PL'+dhVideoId+'?'
				self.session.open(YT_ListScreen, url, dhTitle, title=D24HD_Version)
			else:
				self.session.open(
					YoutubePlayer,
					[(dhTitle, dhVideoId, None)],
					showPlaylist=False
					)
		else:
			self.parseStreamsStream(mvid.group(1))

	def parseStreamsStream(self, data):
		print "parseStreamsStream:"
		m2 = re.search('src="(.*?)"',data, re.I)
		if m2:
			print "Streams found"
			streamLink = m2.group(1)
			print streamLink
			if re.search('(putlocker|sockshare|streamclou|xvidstage|filenuke|movreel|nowvideo|xvidstream|uploadc|vreer|MonsterUploads|Novamov|Videoweed|Divxstage|Ginbig|Flashstrea|Movshare|yesload|faststream|Vidstream|PrimeShare|flashx|Divxmov|Putme|Click.*?Play|BitShare)', streamLink, re.I):
				get_stream_link(self.session).check_link(streamLink, self.got_link)
			else:
				self.parseDailymotionStream(data)
		else:
			self.parseDailymotionStream(data)

	def parseDailymotionStream(self, data):
		print "parseDailymotionStream:"
		m2 = re.search('src="http://www.dailymotion.com/embed/video/(.*?)\?', data)
		if m2:
			print "Streams found"
			id = m2.group(1)
			DailyMotionLink(self.got_link, id)
		else:
			print "No stream found"
			self.got_link(None)

	def got_link(self, stream_url):
		print "got_link:"
		if not stream_url:
			message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(title, stream_url, None)], cover=False, showPlaylist=False, ltype='doku24hd.org')

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		streamLink = self['liste'].getCurrent()[0][1]
		print streamLink
		twAgentGetPage(streamLink).addCallback(self.parseYTStream).addErrback(self.dataError)

	def keyUpRepeated(self):
		#print "keyUpRepeated"
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		#print "keyDownRepeated"
		if self.keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		#print "key_repeatedUp"
		if self.keyLocked:
			return
		self.loadPicQueued()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def keyPageDown(self):
		#print "keyPageDown()"
		self.keyPageDownFast(1)

	def keyPageUp(self):
		#print "keyPageUp()"
		self.keyPageUpFast(1)

	def keyPageUpFast(self,step):
		if self.keyLocked:
			return
		#print "keyPageUpFast: ",step
		oldpage = self.page
		if (self.page + step) <= self.pages:
			self.page += step
		else:
			self.page = 1
		#print "Page %d/%d" % (self.page,self.pages)
		if oldpage != self.page:
			self.loadPage()

	def keyPageDownFast(self,step):
		if self.keyLocked:
			return
		print "keyPageDownFast: ",step
		oldpage = self.page
		if (self.page - step) >= 1:
			self.page -= step
		else:
			self.page = self.pages
		#print "Page %d/%d" % (self.page,self.pages)
		if oldpage != self.page:
			self.loadPage()

	def key_1(self):
		#print "keyPageDownFast(2)"
		self.keyPageDownFast(2)

	def key_4(self):
		#print "keyPageDownFast(5)"
		self.keyPageDownFast(5)

	def key_7(self):
		#print "keyPageDownFast(10)"
		self.keyPageDownFast(10)

	def key_3(self):
		#print "keyPageUpFast(2)"
		self.keyPageUpFast(2)

	def key_6(self):
		#print "keyPageUpFast(5)"
		self.keyPageUpFast(5)

	def key_9(self):
		#print "keyPageUpFast(10)"
		self.keyPageUpFast(10)

class DailyMotionLink:

	def __init__(self, callback, id):
		self._callback = callback
		self.videoQuality = int(config.mediaportal.videoquali_others.value)
		self.getStreamPage(id)

	def getStreamPage(self, id):
		url = "http://www.dailymotion.com/embed/video/"+id
		twAgentGetPage(url).addCallback(self.getStreamUrl).addErrback(self.dataError)

	def dataError(self, error):
		print "dataError:"
		self._callback(None)

	def getStreamUrl(self, content):
		if content.find('"statusCode":410') > 0 or content.find('"statusCode":403') > 0:
			self._callback(None)
		else:
			matchFullHD = re.compile('"stream_h264_hd1080_url":"(.+?)"', re.DOTALL).findall(content)
			matchHD = re.compile('"stream_h264_hd_url":"(.+?)"', re.DOTALL).findall(content)
			matchHQ = re.compile('"stream_h264_hq_url":"(.+?)"', re.DOTALL).findall(content)
			matchSD = re.compile('"stream_h264_url":"(.+?)"', re.DOTALL).findall(content)
			matchLD = re.compile('"stream_h264_ld_url":"(.+?)"', re.DOTALL).findall(content)
			url = ""
			if matchFullHD and self.videoQuality == 2:
				url = urllib.unquote_plus(matchFullHD[0]).replace("\\", "")
			elif matchHD and (self.videoQuality in (1, 2)):
				url = urllib.unquote_plus(matchHD[0]).replace("\\", "")
			elif matchHQ and (self.videoQuality in (1, 2)):
				url = urllib.unquote_plus(matchHQ[0]).replace("\\", "")
			elif matchSD and (self.videoQuality  in (0, 1, 2)):
				url = urllib.unquote_plus(matchSD[0]).replace("\\", "")
			elif matchLD:
				url = urllib.unquote_plus(matchLD[0]).replace("\\", "")

			self._callback(url)