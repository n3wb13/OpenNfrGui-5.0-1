# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def show_bandwith(bandwith, link):
	res = [(bandwith, link)]
	res.append(MultiContentEntryText(pos=(0, 0), size=(200, 24), font=0, text=bandwith, flags=RT_HALIGN_CENTER))
	return res

class laolaVideosOverviewScreen(MPScreen):

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
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Laola1.tv")

		self.genreliste = []

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste.append(("Live", "http://www.laola1.tv/de-de/calendar/0.html"))
		self.genreliste.append(("Fußball", "http://www.laola1.tv/de-de/fussball/2.html"))
		self.genreliste.append(("Eishockey", "http://www.laola1.tv/de-de/eishockey/41.html"))
		self.genreliste.append(("Volleyball", "http://www.laola1.tv/de-de/volleyball/56.html"))
		self.genreliste.append(("Beach-Volleyball", "http://www.laola1.tv/de-de/beach-volleyball/101.html"))
		self.genreliste.append(("Handball", "http://www.laola1.tv/de-de/handball/143.html"))
		self.genreliste.append(("Tischtennis", "http://www.laola1.tv/de-de/tischtennis/182.html"))
		self.genreliste.append(("Motorsport", "http://www.laola1.tv/de-de/motorsport/239.html"))
		self.genreliste.append(("Mehr Sport", "http://www.laola1.tv/de-de/mehr-sport/404.html"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		link = self['liste'].getCurrent()[0][1]
		if auswahl == "Live":
			self.session.open(laolaLiveScreen, auswahl, link)
		else:
			self.session.open(laolaSelectGenreScreen, auswahl, link)

class laolaLiveScreen(MPScreen):

	def __init__(self, session, name, link):
		self.lname = name
		self.llink = link
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
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Laola1.tv - Live")

		self.genreliste = []

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def char_gen(self, size=1, chars=string.ascii_uppercase):
		return ''.join(random.choice(chars) for x in range(size))

	def loadPage(self):
		getPage(self.llink).addCallback(self.getLiveData).addErrback(self.dataError)

	def getLiveData(self, data):
		live = re.findall('<img\swidth="80"\sheight="45"\ssrc=".*?">.*?<a\shref="(.*?)"><h2>(.*?)</h2>.*?<span\sclass="ititle">Liga:</span><span\sclass="idesc\shalf">(.*?)</span>.*?<span\sclass="ititle\sfull">Streamstart:</span><span\sclass="idesc\sfull">.*?,\s(.*?)</span>.*?<span\sclass="ititle\sfull">Verf&uuml;gbar\sin:</span><span\sclass="idesc\sfull"><span\sstyle="color:\#0A0;">(.*?)<', data, re.S)
		if live:
			for url,sportart,welche,time,where in live:
				sportart = sportart.replace('<div class="hdkennzeichnung"></div>','')
				title = "%s - %s - %s" % (time, sportart, welche)
				self.genreliste.append((title, url))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		self.keyLocked = True
		self.auswahl = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.getLiveData1).addErrback(self.dataError)

	def getLiveData1(self, data):
		if 'Dieser Stream beginnt' in data:
			self.keyLocked = False
			message = self.session.open(MessageBoxExt, _("Event has not yet started."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.keyLocked = False
			match_player = re.findall('<iframe(.*?)src="(.*?)"', data, re.S)
			for iframestuff,possible_player in match_player:
				if 'class="main_tv_player"' in iframestuff:
					player = possible_player
					getPage(player, agent=std_headers).addCallback(self.getLiveData2).addErrback(self.dataError)

	def getLiveData2(self,data):
		match_streamid=re.findall('streamid:\s"(.*?)"', data, re.S)
		streamid = match_streamid[0]
		match_partnerid=re.findall('partnerid:\s"(.*?)"', data, re.S)
		partnerid = match_partnerid[0]
		match_portalid=re.findall('portalid:\s"(.*?)"', data, re.S)
		portalid = match_portalid[0]
		match_sprache=re.findall('sprache:\s"(.*?)"', data, re.S)
		sprache = match_sprache[0]
		match_auth=re.findall('auth\s=\s"(.*?)"', data, re.S)
		auth = match_auth[0]
		match_timestamp=re.findall('timestamp\s=\s"(.*?)"', data, re.S)
		timestamp = match_timestamp[0]
		url = 'http://www.laola1.tv/server/hd_video.php?play='+streamid+'&partner='+partnerid+'&portal='+portalid+'&v5ident=&lang='+sprache
		getPage(url).addCallback(self.getLiveData3,timestamp,auth).addErrback(self.dataError)

	def getLiveData3(self,data,timestamp,auth):
		match_url=re.findall('<url>(.*?)<', data, re.S)
		new_match_url = match_url[0].replace('&amp;','&').replace('l-_a-','l-L1TV_a-l1tv')+'&timestamp='+timestamp+'&auth='+auth
		getPage(new_match_url, agent=std_headers).addCallback(self.getLiveData4).addErrback(self.dataError)

	def getLiveData4(self,data):
		match_new_auth=re.findall('auth="(.*?)"', data, re.S)
		match_new_url=re.findall('url="(.*?)"', data, re.S)
		m3u8_url = match_new_url[0].replace('/z/','/i/').replace('manifest.f4m','master.m3u8')+'?hdnea='+match_new_auth[0]+'&g='+self.char_gen(12)+'&hdcore=3.2.0'
		if config.mediaportal.use_hls_proxy.value:
			self.session.open(SimplePlayer, [(self.auswahl, m3u8_url)], showPlaylist=False, ltype='laola1')
		else:
			getPage(m3u8_url, agent=std_headers).addCallback(self.getLiveData5).addErrback(self.dataError)

	def getLiveData5(self,data):
		self.bandwith_list = []
		match_sec_m3u8=re.findall('BANDWIDTH=(.*?),.*?http(.*?)rebase=on', data, re.S)
		for each in match_sec_m3u8:
			bandwith,url = each
			self.bandwith_list.append(show_bandwith(int(bandwith),url))
		self.bandwith_list.sort()
		select = self.bandwith_list.pop()
		split = str(select).split(',')
		play_url = str(split[1]).replace('\'','').replace('(','').replace(')','').replace(' ','')
		stream_url = "http%s" % play_url
		self.session.open(SimplePlayer, [(self.auswahl, stream_url)], showPlaylist=False, ltype='laola1')

class laolaSelectGenreScreen(MPScreen):

	def __init__(self, session, name, link):
		self.lname = name
		self.llink = link
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
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Laola1.tv - %s" % self.lname)

		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 999

		self.genreliste = []

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def char_gen(self, size=1, chars=string.ascii_uppercase):
		return ''.join(random.choice(chars) for x in range(size))

	def loadPage(self):
		self['page'].setText("%s" % (str(self.page)))
		getPage(self.llink).addCallback(self.getKey).addErrback(self.dataError)

	def getKey(self, data):
		parse = re.search('data-stageid=\s"(.*?)".*?data-call="(.*?)".*?data-page="(.*?)".*?data-filterpage="(.*?)".*?data-startvids="(.*?)".*?data-htag="(.*?)"', data, re.S).groups()
		if "Newest Videos" in self.lname:
			stageid = 1184
		else:
			stageid = int(parse[0])+3

		anzahlblock = 2+(self.page-1)*10
		filterpage = parse[3]
		startvids = parse[4]

		url = "http://www.laola1.tv/nourish.php?stageid=%s&newpage=%s&filterpage=%s&startvids=%s&anzahlblock=%s" % (stageid, self.page, filterpage, startvids, anzahlblock)
		getPage(url, agent=std_headers).addCallback(self.getEventData).addErrback(self.dataError)

	def getEventData(self, data):
		self.genreliste = []
		events = re.findall('<span\sclass="category">(.*?)</span>.*?<span\sclass="date">.*?,\s(.*?)</span>.*?<h2>(.*?)</h2></a>.*?<a\shref="/(.*?)">.*?src="(.*?)"', data, re.S)
		if events:
			for genre,time,desc,url,image in events:
				desc = desc.replace('<div class="hdkenn_list"></div>','')
				genre = genre.replace("Tennis/",'').replace("Eishockey/",'').replace("Fussball/",'').replace("Beach Volleyball/",'').replace("Curling/",'').replace("Tischtennis/",'').replace("Handball/",'').replace("Motorsport/",'').replace("Volleyball/",'')
				title = "%s %s, %s" % (time, decodeHtml(genre), decodeHtml(desc))
				url = "http://www.laola1.tv/%s" % url
				self.genreliste.append((title, url, genre, image))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		self.keyLocked = True
		self.auswahl = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.getData).addErrback(self.dataError)

	def getData(self, data):
		self.keyLocked = False
		match_player = re.findall('<iframe(.*?)src="(.*?)"', data, re.S)
		for iframestuff,possible_player in match_player:
			if 'class="main_tv_player"' in iframestuff:
				player = possible_player
				getPage(player, agent=std_headers).addCallback(self.getData1).addErrback(self.dataError)

	def getData1(self,data):
		match_streamid=re.findall('streamid:\s"(.*?)"', data, re.S)
		streamid = match_streamid[0]
		match_partnerid=re.findall('partnerid:\s"(.*?)"', data, re.S)
		partnerid = match_partnerid[0]
		match_portalid=re.findall('portalid:\s"(.*?)"', data, re.S)
		portalid = match_portalid[0]
		match_sprache=re.findall('sprache:\s"(.*?)"', data, re.S)
		sprache = match_sprache[0]
		match_auth=re.findall('auth\s=\s"(.*?)"', data, re.S)
		auth = match_auth[0]
		match_timestamp=re.findall('timestamp\s=\s"(.*?)"', data, re.S)
		timestamp = match_timestamp[0]
		url = 'http://www.laola1.tv/server/hd_video.php?play='+streamid+'&partner='+partnerid+'&portal='+portalid+'&v5ident=&lang='+sprache
		getPage(url).addCallback(self.getData2,timestamp,auth).addErrback(self.dataError)

	def getData2(self,data,timestamp,auth):
		match_url=re.findall('<url>(.*?)<', data, re.S)
		new_match_url = match_url[0].replace('&amp;','&').replace('l-_a-','l-L1TV_a-l1tv')+'&timestamp='+timestamp+'&auth='+auth
		getPage(new_match_url, agent=std_headers).addCallback(self.getData3).addErrback(self.dataError)

	def getData3(self,data):
		match_new_auth=re.findall('auth="(.*?)"', data, re.S)
		match_new_url=re.findall('url="(.*?)"', data, re.S)
		m3u8_url = match_new_url[0].replace('/z/','/i/').replace('manifest.f4m','master.m3u8')+'?hdnea='+match_new_auth[0]+'&g='+self.char_gen(12)+'&hdcore=3.2.0'
		self.session.open(SimplePlayer, [(self.auswahl, m3u8_url)], showPlaylist=False, ltype='laola1')

	def showInfos(self):
		self.ImageUrl = self['liste'].getCurrent()[0][3]
		CoverHelper(self['coverArt']).getCover(self.ImageUrl)