# -*- coding: utf-8 -*-

import Queue
import threading
from Screens.InfoBarGenerics import *
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

CF_Version = "Clipfish.de v1.18"

CF_siteEncoding = 'utf-8'

"""
Sondertastenbelegung:

Genre Auswahl:
	KeyCancel	: Menu Up / Exit
	KeyOK		: Menu Down / Select

Doku Auswahl:
	Bouquet +/-			: Seitenweise blättern in 1er Schritten Up/Down
	'1', '4', '7',
	'3', 6', '9'		: blättern in 2er, 5er, 10er Schritten Down/Up
	Rot/Blau			: Die Beschreibung Seitenweise scrollen

Stream Auswahl:
	Rot/Blau			: Die Beschreibung Seitenweise scrollen

"""

class ClipfishPlayer(SimplePlayer):

	def __init__(self, session, playList, genreVideos, playIdx=0, playAll=False, listTitle=None, showCover=False):
		self.genreVideos = genreVideos
		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=playAll, listTitle=listTitle, cover=showCover)

	def getVid(self, data):
		if not self.genreVideos:
			m = re.search('NAME="FlashVars".*?data=(.*?)&amp', data)
			if m:
				url = m.group(1)

		if self.genreVideos or not m:
			m = re.search('data: (\'|")(.*?)(\'|")', data, re.S)
			if m:
				url = m.group(2)

		if m:
			if url[:4] != "http":
				url = "http://www.clipfish.de" + url

			twAgentGetPage(url, agent=None, headers=std_headers).addCallback(self.getXml).addErrback(self.dataError)
		else:
			self.dataError('No video data found!')

	def getXml(self, data):
		url = None
		if 'rtmpe:' in data:
			m = re.search('<filename>.*?ondemand/(.*?):(.*?)\?', data)
			if m:
				url = 'http://video.clipfish.de/' + m.group(2)
				if not url.endswith(m.group(1)):
					url += '.' + m.group(1)
		else:
			m = re.search('<filename>.*?clipfish.de/(.*?)(flv|f4v|mp4).*?</filename>', data, re.S)
			if m:
				url = 'http://video.clipfish.de/' + m.group(1).replace('hds-vod-enc/','') + m.group(2)

		if url != None:
			title = self.playList[self.playIdx][0]
			imgurl = self.playList[self.playIdx][2]

			scArtist = ''
			scTitle = title
			if 'Musikvideo' in self.listTitle:
				p = title.find(' - ')
				if p > 0:
					scArtist = title[:p].strip()
					scTitle = title[p+3:].strip()

			self.playStream(scTitle, url, imgurl=imgurl, artist=scArtist)
		else:
			self.dataError('No video data found!')

	def getVideo(self):
		url = self.playList[self.playIdx][1]
		twAgentGetPage(url, agent=None, headers=std_headers).addCallback(self.getVid).addErrback(self.dataError)

class show_CF_Genre(MenuHelper):

	def __init__(self, session):

		MenuHelper.__init__(self, session, 0, None, "http://www.clipfish.de", "", self._defaultlistcenter)

		self['title'] = Label(CF_Version)
		self['ContentTitle'] = Label("Genres")

		self.param_qr = ''
		self.menu = []

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_initMenu(self):
		self.mh_buildMenu(self.mh_baseUrl+'/special/tv/shows/')

	def mh_parseCategorys(self, data, category='TV'):

		if category == 'TV':
			self.menu.append((0, "", "TV"))
			self.menu.append((1, "/special", "DSDS"))
			self.menu.append((2, "/dsds/news%s", "News"))
			self.menu.append((2, "/dsds/home%s", "Casting-Videos"))
			self.menu.append((2, "/musikvideos/dsds%s", "Musikvideos"))
			self.menu.append((2, "/dsds/liveshow%s", "Alle Videos aus den Liveshows"))
			self.menu.append((2, "/dsds/recall%s", "Recall - Alle Videos"))
			self.menu.append((2, "/dsds/casting%s", "Alle Casting-Videos"))
			self.menu.append((2, "/dsds/videos%s", "Alle Videos"))
			self.menu.append((2, "/dsds/best-of-dsds%s", "Best of DSDS"))
			self.menu.append((2, "/dsds/2012%s", "2012 - Alle Videos"))
			self.menu.append((2, "/dsds/dsds-8%s", "2011 - Alle Videos"))
			self.menu.append((2, "/dsds/dsds-7%s", "2010 - Alle Videos"))

			self.menu.append((1, "/special", "Let's Dance"))
			self.menu.append((2, "/lets-dance/videos%s", "Alle Videos"))
			self.menu.append((2, "/lets-dance/lets-dance-2013%s", "Alle Videos 2013"))
			self.menu.append((2, "/lets-dance/lets-dance-2012%s", "Alle Videos 2012"))
			self.menu.append((2, "/lets-dance/lets-dance-2011%s", "Alle Videos 2011"))

			self.menu.append((1, "", "Alle TV-Shows"))
			entrys = self.mh_parseData(data)
			if entrys:
				for (url, desc) in entrys:
					self.menu.append((2, url, desc))

			self.menu.append((0, "", "MUSIC"))
			self.menu.append((1, "/musikvideos/charts", "Musikvideo-Charts"))
			self.menu.append((1, "/musikvideos/genre", "Genres"))
			self.menu.append((2, "/207/country-folk", "Country / Folk"))
			self.menu.append((2, "/109/dance-electro", "Dance / Elektro"))
			self.menu.append((2, "/211/hip-hop-rap", "HipHop / Rap"))
			self.menu.append((2, "/4/pop", "Pop"))
			self.menu.append((2, "/5911/christian", "Gospel / Christian"))
			self.menu.append((2, "/163/world-music", "World Music"))
			self.menu.append((2, "/12/klassik", "Klassik"))
			self.menu.append((2, "/55/r-b-soul", "R&B / Soul"))
			self.menu.append((2, "/26/blues-jazz", "Blues / Jazz"))
			self.menu.append((2, "/247/latin", "Latin Music"))
			self.menu.append((2, "/59/metal-hard-rock", "Metal / Hard Rock"))
			self.menu.append((2, "/119/rock-alternative", "Rock / Alternative"))
			self.menu.append((2, "/38/schlager", "Schlager"))

			self.menu.append((1, "/specialmodule/modulemusicvideodatematrix/5337/%d/?relyear=", "Jahrzehnte"))
			self.menu.append((2, "all&special_id=275&list_type=beste", "Alle"))
			self.menu.append((2, "1960&special_id=275&list_type=beste", "1960er"))
			self.menu.append((2, "1970&special_id=275&list_type=beste", "1970er"))
			self.menu.append((2, "1980&special_id=275&list_type=beste", "1980er"))
			self.menu.append((2, "1990&special_id=275&list_type=beste", "1990er"))
			self.menu.append((2, "2000&special_id=275&list_type=beste", "2000er"))
			self.menu.append((2, "2010&special_id=275&list_type=beste", "2010er"))

			self.menu.append((1, "/musikvideos/allevideos/%s", "Alle Musikvideos"))

			self.menu.append((0, "", "FILME"))
			self.menu.append((1, "/special/spielfilme/charts", "Spielfilm-Charts"))
			self.menu.append((1, "/special/spielfilme/genre", "Film-Genres"))
			self.menu.append((2, "/1/action/new/%d/#1", "Action"))
			self.menu.append((2, "/43/science-fiction/new/%d/#43", "SciFi"))
			self.menu.append((2, "/37/drama/new/%d/#37", "Drama"))
			self.menu.append((2, "/31/abenteuer/new/%d/#31", "Abenteuer"))
			self.menu.append((2, "/23/dokumentation/new/%d/#23", "Dokumentation"))
			self.menu.append((2, "/17/kinder/new/%d/#17", "Kinder"))
			self.menu.append((2, "/11/western/new/%d/#11", "Western"))
			self.menu.append((2, "/9/klassiker/new/%d/#9", "Klassiker"))
			self.menu.append((2, "/27/horror/new/%d/#27", "Horror"))
			self.menu.append((2, "/41/thriller/new/%d/#41", "Thriller"))
			self.menu.append((2, "/71/asian/new/%d/#71", "Asian"))
			self.menu.append((2, "/25/erotik/new/%d/#25", "Erotik"))
			self.menu.append((2, "/29/komoedie/new/%d/#29", "Komödie"))
			self.menu.append((2, "/19/krimi/new/%d/#19", "Krimi"))
			self.menu.append((2, "/73/romantik/new/%d/#73", "Romantik"))
			self.menu.append((2, "/63/zeichentrick/new/%d/#63", "Zeichentrick"))

			self.menu.append((1, "/special/kino-trailer/home%s/#111", "Kino-Trailer"))
			self.menu.append((1, "/special", "Kino-Magazine"))
			self.menu.append((2, "/daniele-rizzo/home%s", "Daniele Rizzo - Alle Videos"))
			self.menu.append((2, "/der-ehrliche-dennis/home%s", "Der ehrliche Dennis - Alle Videos"))
			self.menu.append((2, "/seen/home%s", "Seen - Die aktuellen Kino- und DVD-Filme"))
			self.menu.append((2, "/kino-und-co/home%s", "Kino und Co. - Alle Videos"))
			self.getSerienPage()
		elif category == 'SERIEN':
			self.menu.append((0, "", "SERIEN"))
			self.menu.append((1, "/special/mr-bean/home%s", "Mr. Bean"))
			self.menu.append((1, "/special/kill-point/home%s", "Kill Point"))
			self.menu.append((1, "/special/little-britain/home%s", "Little Britain"))
			self.menu.append((1, "/special/the-lost-room/home%s", "The Lost Room"))
			self.menu.append((1, "/special/top-gear/home%s", "Top Gear"))
			self.menu.append((1, "", "Alle Serien"))
			entrys = self.mh_parseData(data)
			if entrys:
				for (url, desc) in entrys:
					self.menu.append((2, url, desc))
			self.getAnimeSerienPage()
		elif category == 'ANIME':
			self.menu.append((0, "", "ANIME"))
			self.menu.append((1, "", "Alle Anime-Serien"))
			entrys = self.mh_parseData(data)
			if entrys:
				for (url, desc) in entrys:
					self.menu.append((2, url, desc))
			self.getComedyShowsPage()
		elif category == 'COMEDY':
			self.menu.append((0, "", "COMEDY"))
			self.menu.append((1, "/special/y-titty/home%s", "Y-Titty - Videos"))
			self.menu.append((1, "/special/freshaltefolie/home%s", "Neues von FreshTorge"))
			self.menu.append((1, "/special/dielochis/home%s", "Neues von den Lochis"))
			self.menu.append((1, "/special/digges-ding-comedy/home%s", "Digges Ding Comedy - Alle Videos"))
			self.menu.append((1, "/special/ape-crime/home%s", "ApeCrime - Alle Videos"))

			self.menu.append((1, "", "Alle Comedy-Shows"))
			entrys = self.mh_parseData(data)
			if entrys:
				for (url, desc) in entrys:
					self.menu.append((2, url, desc))

			self.menu.append((0, "/special", "NEWS"))
			self.menu.append((1, "/news/aktuelles%s", "News und Lifestyle - Alle Videos"))
			self.menu.append((1, "/news/vip%s", "Alle VIP-Videos"))
			self.menu.append((1, "/regional-news/home%s", "Regional News - alle Videos"))
			self.menu.append((1, "/daaruum/home%s", "Neues von Daaruum"))

			self.menu.append((0, "/kategorien", "VIDEOS"))
			self.menu.append((1, "/28/%s", "Eure Empfehlungen"))
			self.menu.append((1, "/2/%s", "Anime & Cartoons"))
			self.menu.append((1, "/3/%s", "Auto"))
			self.menu.append((1, "/1/%s", "Comedy & Humor"))
			self.menu.append((1, "/4/%s", "Freunde & Familie"))
			self.menu.append((1, "/6/%s", "Games & PC"))
			self.menu.append((1, "/7/%s", "Hobbies & Tipps"))
			self.menu.append((1, "/8/%s", "Kino, TV & Werbung"))
			self.menu.append((1, "/9/%s", "Leute & Blogs"))
			self.menu.append((1, "/297/%s", "News & Wissenschaft"))
			self.menu.append((1, "/13/%s", "Party & Events"))
			self.menu.append((1, "/17/%s", "Sexy Videos"))
			self.menu.append((1, "/14/%s", "Sport & Action"))
			self.menu.append((1, "/11/%s", "Stars & Lifestyle"))
			self.menu.append((1, "/15/%s", "Tiere & Natur"))
			self.menu.append((1, "/16/%s", "Urlaub & Reisen"))

			self.menu.append((0, "/suche", "Suche..."))

			self.mh_genMenu2(self.menu)

	def mh_parseData(self, data):
		entrys = []

		if '/serien/alle' in self.mh_lastPageUrl:
			a = data.find('<li class="cf-contentlist-matrix">')
			if a < 0:
				a = 0
			l = data[a:].find('<!-- GENERIC BOX END -->')
			if l < 0:
				l = len(data)
			else:
				l += a
		else:
			a = 0
			l = len(data)

		while a < l:
			m = re.search('<li class="cf-contentlist-matrix">(.*?)</li>', data[a:l], re.S)
			if m:
				a += m.end()
				mitems = re.search('"_top" href="(.*?)/".*?-headline">.*?<div class="cf-contentlist-matrix-.*?">(.*?)</div>.*?<div class="cf-contentlist-matrix">(.*?)</div>', m.group(1).replace('\n',''), re.S)
				if mitems:
					entrys.append((mitems.group(1)+'%s', decodeHtml(mitems.group(2).strip())+' - '+decodeHtml(mitems.group(3).strip())))
			else:
				break
		return entrys

	def mh_callGenreListScreen(self):
		if re.search('Suche...', self.mh_genreTitle):
			self.paraQuery()
		else:
			genreurl = self.mh_genreUrl[0]+self.mh_genreUrl[1]+self.mh_genreUrl[2]
			if not genreurl.startswith('http'):
				genreurl = self.mh_baseUrl+genreurl
			self.session.open(CF_FilmListeScreen, genreurl, self.mh_genreTitle)

	def getComedyShowsPage(self):
		self.mh_lastPageUrl = self.mh_baseUrl+'/special/comedy/shows/'
		twAgentGetPage(self.mh_lastPageUrl, agent=None, headers=std_headers).addCallback(self.mh_parseCategorys, category='COMEDY').addErrback(self.mh_dataError)

	def getAnimeSerienPage(self):
		self.mh_lastPageUrl = self.mh_baseUrl+'/special/anime/alle-serien/'
		twAgentGetPage(self.mh_lastPageUrl, agent=None, headers=std_headers).addCallback(self.mh_parseCategorys, category='ANIME').addErrback(self.mh_dataError)

	def getSerienPage(self):
		self.mh_lastPageUrl = self.mh_baseUrl+'/special/serien/alle/'
		twAgentGetPage(self.mh_lastPageUrl, agent=None, headers=std_headers).addCallback(self.mh_parseCategorys, category='SERIEN').addErrback(self.mh_dataError)

	def paraQuery(self):
		self.param_qr = ''
		self.session.openWithCallback(self.cb_paraQuery, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.param_qr, is_dialog=True)

	def cb_paraQuery(self, callback = None, entry = None):
		if callback != None:
			self.param_qr = callback.strip()
			if len(self.param_qr) > 0:
				qr = self.param_qr.replace(' ', '+')
				genreurl = self.mh_baseUrl+self.mh_genreUrl[0]+'/'+qr+'/video/bestertreffer/%d'
				self.session.open(CF_FilmListeScreen, genreurl, self.mh_genreTitle)

class CF_FilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName):
		self.genreLink = genreLink
		self.genreName = genreName
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/dokuListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/dokuListScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "ColorActions", "SetupActions", "NumberActions", "MenuActions", "EPGSelectActions", "DirectionActions"], {
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
			"0"	: self.closeAll,
			"1" : self.key_1,
			"3" : self.key_3,
			"4" : self.key_4,
			"6" : self.key_6,
			"7" : self.key_7,
			"9" : self.key_9,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self.sortOrder = 0
		self.baseUrl = "http://www.clipfish.de"
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label(CF_Version)
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))
		self['Page'] = Label(_("Page:"))


		self.filmQ = Queue.Queue(0)
		self.eventL = threading.Event()
		self.keyLocked = True
		self.musicListe = []
		self.kekse = CookieJar()
		self.page = 0
		self.pages = 0;
		self.genreSpecials = False
		self.genreVideos = re.match('VIDEOS', self.genreName) or '/allevideos' in self.genreLink
		self.genreSpielfilme = 'spielfilme/genre' in self.genreLink
		self.showCover = '/spielfilme/genre' in self.genreLink
		self.genreMusicCharts = '-Charts' in self.genreName
		self.genreSearch = re.match('Suche...', self.genreName)
		self.genreSpecial = '/special/' in self.genreLink and not self.genreMusicCharts
		self.genreSpecialModule = '/specialmodule/' in self.genreLink
		self.lurlpart = ''

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		if self.page == 0:
			page = 1
		else:
			page = self.page

		if self.genreVideos:
			link = self.genreLink % 'neu'
			url = "%s/%d/" % (link, page)
		elif self.genreSpielfilme or self.genreSearch or self.genreSpecialModule:
			url = self.genreLink % page
		elif self.genreSpecial:
			if self.lurlpart:
				s = self.lurlpart % page
			else:
				s = ''
			url = self.genreLink % s
		elif self.genreMusicCharts:
			url = self.genreLink
		else:
			url = "%s/beste/%d/#" % (self.genreLink, page)

		if self.page:
			self['page'].setText("%d / %d" % (self.page,self.pages))

		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()

	def loadPageQueued(self):
		self['name'].setText(_('Please wait...'))
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()

		twAgentGetPage(url, agent=None, cookieJar=self.kekse, headers=std_headers).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		printl(error,self,"E")
		self['handlung'].setText("Fehler:\n" + str(error))

	def loadPageData(self, data):
		a = 0
		l = len(data)
		self.musicListe = []
		stSearch = '<h2>STAFFEL 1 - FOLGE' in data
		while a < l:
			if self.genreMusicCharts:
				mg = re.search('intern cf-left-col50-left">(.*?)"cf-charts-text">', data[a:], re.S)
			elif self.genreSearch:
				mg = re.search('"liz_cf-video-list-item-image">(.*?)</li>', data[a:], re.S)
			elif stSearch:
				mg = re.search('"cf-video-list-item-image ">(.*?)</a>', data[a:], re.S)
			else:
				mg = re.search('<li id="cf-video-item_(.*?)</li>', data[a:], re.S)

			if mg:
				a += mg.end()
				if 'cf-paycontent' in mg.group(1):
					continue

				if self.genreMusicCharts or self.genreSearch or stSearch:
					m1 = re.search('href="(.*?)".*?<img.*?src="(.*?)".*?alt="(.*?)"', mg.group(1), re.S)
				else:
					m1 = re.search('href="(.*?)".*?title="(.*?)">.*?<img.*?src="(.*?)"', mg.group(1), re.S)

				if m1:
					if self.genreMusicCharts or self.genreSearch or stSearch:
						title = decodeHtml(m1.group(3))
						url = m1.group(1)
						img = m1.group(2)
					else:
						title = decodeHtml(m1.group(2))
						url = m1.group(1)
						img = m1.group(3)

					if url[:4] != "http":
						url = "%s%s" % (self.baseUrl, url)

					self.musicListe.append((title, url, img))
			else:
				a = l

		if len(self.musicListe) == 0:
			self.pages = 0
			self.musicListe.append((_('No videos found!'),'',''))
		else:
			menu_len = len(self.musicListe)

			if not self.pages:
				m1 = re.search('<div class="pager">(.*?)</div>', data, re.S)
				if m1:
					m2 = re.findall('".*?href="(.*?)".*?>(\d*?)</a>', m1.group(1))

				if m1 and m2:
					try:
						self.lurlpart = '/' + m2[0][0].split('/')[-2] + '/%d'
					except:
						pass

					pages = 0
					for u,i in m2:
						x = int(i)
						if x > pages:
							pages = x

					if pages > 999:
						self.pages = 999
					else:
						self.pages = pages
				else:
					self.pages = 1

				self.page = 1
				self['page'].setText("%d / %d" % (self.page,self.pages))

		self.ml.setList(map(self._defaultlistleft, self.musicListe))
		self.th_ThumbsQuery(self.musicListe, 0, 1, 2, None, None, self.page, self.pages, mode=1)
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		desc = None
		self.getHandlung(desc)

		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
		self.keyLocked	= False

		url = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(url)

	def getHandlung(self, desc):
		if desc == None:
			self['handlung'].setText("Keine weiteren Info's vorhanden.")
			return
		self.setHandlung(desc)

	def setHandlung(self, data):
		self['handlung'].setText(decodeHtml(data))

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return

		self.session.open(
			ClipfishPlayer,
			self.musicListe,
			self.genreVideos,
			self['liste'].getSelectedIndex(),
			playAll = True,
			listTitle = self.genreName,
			showCover = self.showCover
			)

	def keyUpRepeated(self):
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		if self.keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		if self.keyLocked:
			return
		self.showInfos()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def keyPageDown(self):
		self.keyPageDownFast(1)

	def keyPageUp(self):
		self.keyPageUpFast(1)

	def keyPageUpFast(self,step):
		if self.keyLocked:
			return
		oldpage = self.page
		if (self.page + step) <= self.pages:
			self.page += step
		else:
			self.page = 1
		if oldpage != self.page:
			self.loadPage()

	def keyPageDownFast(self,step):
		if self.keyLocked:
			return
		oldpage = self.page
		if (self.page - step) >= 1:
			self.page -= step
		else:
			self.page = self.pages
		if oldpage != self.page:
			self.loadPage()

	def key_1(self):
		self.keyPageDownFast(2)

	def key_4(self):
		self.keyPageDownFast(5)

	def key_7(self):
		self.keyPageDownFast(10)

	def key_3(self):
		self.keyPageUpFast(2)

	def key_6(self):
		self.keyPageUpFast(5)

	def key_9(self):
		self.keyPageUpFast(10)