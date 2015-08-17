# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.twagenthelper import TwAgentHelper

config.mediaportal.movie4klang = ConfigText(default="all", fixed_size=False)

m4k = "movie4k.to"
m4k_url = "http://www.movie4k.tv/"
g_url = "http://movie4k.tv/movies-genre-"
t_url = "http://img.movie4k.tv/thumbs/"

movie4kheader = {'Content-Type':'application/x-www-form-urlencoded'}

class m4kGenreScreen(MPScreen):
	def __init__(self, session, mode):
		self.showM4kPorn = mode
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
			"yellow" : self.keyLocale,
			"cancel": self.keyCancel
		}, -1)

		self.locale = config.mediaportal.movie4klang.value
		global movie4kheader
		if self.locale == "de":
			movie4kheader = {'Cookie':'lang=de; onlylanguage=de', 'Content-Type':'application/x-www-form-urlencoded'}
		elif self.locale == "en":
			movie4kheader = {'Cookie':'lang=en; onlylanguage=en', 'Content-Type':'application/x-www-form-urlencoded'}
		elif self.locale == "all":
			movie4kheader = {'Content-Type':'application/x-www-form-urlencoded'}

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Genre:")
		self['F3'] = Label(self.locale)

		self.searchStr = ''

		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		if self.showM4kPorn == "porn":
			self.list.append(("Letzte Updates (XXX)", m4k_url+"xxx-updates.html"))
			self.list.append(('Genres', m4k_url+"genres-xxx.html"))
		else:
			self.list.append(("Kinofilme", m4k_url+"index.php"))
			self.list.append(("Videofilme", m4k_url+"index.php"))
			self.list.append(("Letzte Updates (Filme)", m4k_url+"index.php"))
			self.list.append(("Alle Filme A-Z", "FilmeAZ"))
			self.list.append(("Suche",""))
			self.list.append(("Abenteuer", g_url+"4-"))
			self.list.append(("Action", g_url+"1-"))
			self.list.append(("Biografie", g_url+"6-"))
			self.list.append(("Bollywood", g_url+"27-"))
			self.list.append(("Dokumentation", g_url+"8-"))
			self.list.append(("Drama", g_url+"2-"))
			self.list.append(("Erwachsene", g_url+"58-"))
			self.list.append(("Familie", g_url+"9-"))
			self.list.append(("Fantasy", g_url+"10-"))
			self.list.append(("Geschichte", g_url+"13-"))
			self.list.append(("Horror", g_url+"14-"))
			self.list.append(("Komödie", g_url+"3-"))
			self.list.append(("Kriegsfilme", g_url+"24-"))
			self.list.append(("Krimi", g_url+"7-"))
			self.list.append(("Kurzfilme", g_url+"55-"))
			self.list.append(("Musicals", g_url+"56-"))
			self.list.append(("Musik", g_url+"15-"))
			self.list.append(("Mystery", g_url+"17-"))
			self.list.append(("Reality TV", g_url+"59-"))
			self.list.append(("Romantik", g_url+"20-"))
			self.list.append(("Sci-Fi", g_url+"21-"))
			self.list.append(("Sport", g_url+"22-"))
			self.list.append(("Thriller", g_url+"23-"))
			self.list.append(("Trickfilm", g_url+"5-"))
			self.list.append(("Western", g_url+"25-"))
		self.ml.setList(map(self._defaultlistcenter, self.list))
		self.keyLocked = False

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if name == "Watchlist":
			self.session.open(m4kWatchlist)
		elif name == "Kinofilme":
			self.session.open(m4kFilme, url, name)
		elif name == "Videofilme":
			self.session.open(m4kFilme, url, name)
		elif name == "Letzte Updates (Filme)":
			self.session.open(m4kFilme, url, name)
		elif name == "Alle Filme A-Z":
			self.session.open(m4kABCAuswahl, url, name)
		elif name == "Letzte Updates (XXX)":
			self.session.open(m4kXXXListeScreen, url, name, '')
		elif name == 'Suche':
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True)
		else:
			self.session.open(m4kFilme, url, name)

	def keyLocale(self):
		global movie4kheader
		if self.locale == "de":
			movie4kheader = {'Cookie':'lang=en; onlylanguage=en', 'Content-Type':'application/x-www-form-urlencoded'}
			self.locale = "en"
			config.mediaportal.movie4klang.value = "en"
		elif self.locale == "en":
			movie4kheader = {'Content-Type':'application/x-www-form-urlencoded'}
			self.locale = "all"
			config.mediaportal.movie4klang.value = "all"
		elif self.locale == "all":
			self.locale = "de"
			movie4kheader = {'Cookie':'lang=de; onlylanguage=de', 'Content-Type':'application/x-www-form-urlencoded'}
			config.mediaportal.movie4klang.value = "de"
		config.mediaportal.movie4klang.save()
		configfile.save()
		self['F3'].setText(self.locale)

	def searchCallback(self, callbackStr):
		if callbackStr is not None:
			self.searchStr = callbackStr
			url = m4k_url+"movies.php?list=search&search="+str(self.searchStr)
			name = "Suche: "+ self.searchStr
			self.session.open(m4kFilme, url, name)

class m4kWatchlist(MPScreen):
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"red" : self.keyDel,
			"info": self.update
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("Watchlist")
		self['F1'] = Label(_("Delete"))

		self.streamList = []
		self.streamMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.streamMenuList.l.setFont(0, gFont('mediaportal', mp_globals.fontsize))
		self.streamMenuList.l.setItemHeight(mp_globals.fontsize + 2 * mp_globals.sizefactor)
		self['liste'] = self.streamMenuList

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPlaylist)

	def loadPlaylist(self):
		self.streamList = []
		if fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist"):
			readStations = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist","r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(stationName, stationLink, stationLang, stationTotaleps) = data[0]
					self.streamList.append((stationName, stationLink, stationLang, stationTotaleps, "0"))
			self.streamList.sort()
			self.streamMenuList.setList(map(self.m4kWatchSeriesListEntry, self.streamList))
			readStations.close()
			self.keyLocked = False

	def update(self):
		self.count = len(self.streamList)
		self.counting = 0

		if fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp"):
			self.write_tmp = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp" , "a")
			self.write_tmp.truncate(0)
		else:
			self.write_tmp = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp" , "a")

		if len(self.streamList) != 0:
			self.keyLocked = True
			self.streamList2 = []
			ds = defer.DeferredSemaphore(tokens=1)
			downloads = [ds.run(self.download,item[1]).addCallback(self.check_data, item[0], item[1], item[2], item[3]).addErrback(self.dataError) for item in self.streamList]
			finished = defer.DeferredList(downloads).addErrback(self.dataError)

	def download(self, item):
		return getPage(item)

	def check_data(self, data, sname, surl, slang, stotaleps):
		count_all_eps = 0
		self.counting += 1
		self['title'].setText("Update %s/%s" % (self.counting,self.count))

		staffeln = re.findall('<FORM name="episodeform(.*?)">(.*?)</FORM>', data, re.S)
		for (staffel, ep_data) in staffeln:
			episodes = re.findall('<OPTION value=".*?".*?>Episode.(.*?)</OPTION>', ep_data, re.S)
			count_all_eps += int(len(episodes))
			last_new_ep = staffel, episodes[-1]
		new_eps =  int(count_all_eps) - int(stotaleps)

		self.write_tmp.write('"%s" "%s" "%s" "%s"\n' % (sname, surl, slang, count_all_eps))

		self.streamList2.append((sname, surl, slang, str(stotaleps), str(new_eps)))
		self.streamList2.sort()
		self.streamMenuList.setList(map(m4kWatchSeriesListEntry, self.streamList2))

		if self.counting == self.count:
			self['title'].setText("Update done.")
			self.write_tmp.close()
			shutil.move(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp", config.mediaportal.watchlistpath.value+"mp_m4k_watchlist")
			self.keyLocked = False

		if last_new_ep:
			(staffel, episode) = last_new_ep
			if int(staffel) < 10:
				staffel3 = "S0"+str(staffel)
			else:
				staffel3 = "S"+str(staffel)

			if int(episode) < 10:
				episode3 = "E0"+str(episode)
			else:
				episode3 = "E"+str(episode)

			SeEp = "%s%s" % (staffel3, episode3)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(m4kSerienStaffeln, url, stream_name)

	def keyDel(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		selectedName = self['liste'].getCurrent()[0][0]

		writeTmp = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp","w")
		if fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist"):
			readStations = open(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist","r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(stationName, stationLink, stationLang, stationTotaleps) = data[0]
					if stationName != selectedName:
						writeTmp.write('"%s" "%s" "%s" "%s"\n' % (stationName, stationLink, stationLang, stationTotaleps))
			readStations.close()
			writeTmp.close()
			shutil.move(config.mediaportal.watchlistpath.value+"mp_m4k_watchlist.tmp", config.mediaportal.watchlistpath.value+"mp_m4k_watchlist")
			self.loadPlaylist()

class m4kABCAuswahl(MPScreen):
	def __init__(self, session, url, name):
		self.url = url
		self.name = name
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

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("%s" % self.name)

		self.keyLocked = True

		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.list = []
		abc = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","#"]
		for letter in abc:
			self.list.append((letter))
		self.ml.setList(map(self._defaultlistcenter, self.list))
		self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0]
		if auswahl == '#':
			auswahl = '1'
		if self.url == 'FilmeAZ':
			name = "%s" % auswahl
			url = m4k_url+'movies-all-%s-' % auswahl
			self.session.open(m4kFilme, url, name)

class m4kFilme(MPScreen, ThumbsHelper):
	def __init__(self, session, url, name):
		self.url = url
		self.name = name
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyPageNumber,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
			}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("%s" % self.name)
		if self.url == m4k_url+'genres-xxx.html':
			self['name'] = Label("")
		else:
			self['name'] = Label(_("Please wait..."))

		if self.name == "Kinofilme" \
		or self.name == "Videofilme" \
		or self.name == "Letzte Updates (Filme)" \
		or "Suche" in self.name \
		or self.url == m4k_url+'genres-xxx.html':
			self['F2'] = Label("")
		else:
			self['F2'] = Label(_("Page"))

		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.list = []
		if self.name == "Kinofilme" \
		or self.name == "Videofilme" \
		or self.name == "Letzte Updates (Filme)" \
		or "Suche" in self.name:
			getPage(self.url, agent=std_headers, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)
		if self.url == m4k_url+'genres-xxx.html':
			getPage(self.url, agent=std_headers, headers=movie4kheader).addCallback(self.loadXXXPageData).addErrback(self.dataError)
		else:
			url = '%s%s%s' % (self.url, self.page, '.html')
			getPage(url, agent=std_headers, headers=movie4kheader).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadXXXPageData(self, data):
		self.XXX = True
		xxxGenre = re.findall('<TD\sid="tdmovies"\swidth="155">.*?<a\shref="(xxx-genre.*?)">(.*?)</a>', data, re.S)
		if xxxGenre:
			self.list = []
			for url, title in xxxGenre:
				url = '%s%s' % (m4k_url, url)
				title = title.replace("\t","")
				title = title.strip(" ")
				self.list.append((decodeHtml(title),url))
			self.ml.setList(map(self._defaultlistleft, self.list))
		self.keyLocked = False

	def loadPageData(self, data):
		self.XXX = False
		if not self.name == "Kinofilme" \
		and not self.name == "Videofilme" \
		and not self.name == "Letzte Updates (Filme)" \
		and not "Suche" in self.name \
		and not self.url == m4k_url+"genres-xxx.html":
			self['Page'].setText(_("Page:"))
			self.getLastPage(data, 'id="boxwhite"(.*?)</div><!--maincontent2', '.*>(\d+)\s<')

		if self.name == "Videofilme":
			kino = re.findall('<div style="float: left;"><a href="(.*?)"><img src=".*?" alt=".*?" title="(.*?)" border="0" style="width:105px;max-width:105px;max-height:160px;min-height:140px', data, re.S)
			if kino:
				for (url,title) in kino:
					url = '%s%s' % (m4k_url, url)
					title = title.strip()
					self.list.append((decodeHtml(title),url))
				self.ml.setList(map(self._defaultlistleft, self.list))
		if self.name == "Kinofilme":
			kino = re.findall('style="float:left">.*?href="(.*?)".*?src=".*?".*?title="(.*?)".*?src="(.*?)"', data, re.S)
			if kino:
				for (url,title,lang) in kino:
					url = '%s%s' % (m4k_url, url)
					title = title.strip()
					title = title.replace(' kostenlos','')
					self.list.append((decodeHtml(title),url,'',lang))
				self.ml.setList(map(self.kinoxlistleftflagged, self.list))
		if self.name == "Letzte Updates (Filme)":
			kino = re.findall('valign="top".*?height="100.*?href="(.*?)".*?color="#000000" size="-1"><strong>(.*?)</strong>', data, re.S)
			if kino:
				for (url,title) in kino:
					url = '%s%s' % (m4k_url, url)
					title = title.strip()
					self.list.append((decodeHtml(title),url))
				self.ml.setList(map(self._defaultlistleft, self.list))
		else:
			kino = re.findall('id="coverPreview.*?href="(.*?)">(.*?)</a>.*?tdmovies.*?width="25.*?src=.*?width="25.*?src="(.*?)"', data, re.S)
			if kino:
				for (url,title,lang) in kino:
					url = '%s%s' % (m4k_url, url)
					title = title.strip()
					self.list.append((decodeHtml(title),url,'',lang))
				self.ml.setList(map(self.kinoxlistleftflagged, self.list))
		self.keyLocked = False
		self.th_ThumbsQuery(self.list, 0, 1, None, None, '<img src="https://img.movie4k.*?/thumbs/(.*?)"', self.page, self.lastpage, coverlink=t_url)
		self.showInfos()

	def showInfos(self):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self['name'].setText(decodeHtml(name.strip()))
		if self.url == m4k_url+'genres-xxx.html':
			self['handlung'].setText("")
		else:
			self['handlung'].setText("Description Loading...")
			getPage(url, agent=std_headers, headers=movie4kheader).addCallback(self.showHandlung).addErrback(self.dataError)

	def showHandlung(self, data):
		if re.match('.*?<img src="https://img.movie4k.*?/thumbs/', data, re.S):
			cover = re.findall('<img src="https://img.movie4k.*?/thumbs/(.*?)"', data, re.S)
			self.pic = cover[0]
		if re.match('.*?class="moviedescription">.*?</div>', data, re.S):
			desc = re.findall('class="moviedescription">(.*?)<', data, re.S)
			desc = desc[0]
		else:
			desc = "No Description found!"
		if re.match('.*?src="/img/smileys/.*?.gif', data, re.S):
			quali = re.findall('src="/img/smileys/(.*?).gif"', data, re.S)
			if quali[0] == "5":
				quali = "top - 5/5"
			if quali[0] == "4":
				quali = "very well - 4/5"
			if quali[0] == "3":
				quali = "average - 3/5"
			if quali[0] == "2":
				quali = "bad - 2/5"
			if quali[0] == "1":
				quali = "very bad - 1/5"
		else:
			quali = "N/A"

		pic = "%s%s" %(t_url,self.pic)
		CoverHelper(self['coverArt']).getCover(pic)
		if quali == "N/A":
			handlung = decodeHtml(desc)
		else:
			handlung = "Quality: "+quali+"\n"+ decodeHtml(desc)
		self['handlung'].setText(decodeHtml(handlung).strip())
		self['F1'].setText(_("Text-"))
		self['F4'].setText(_("Text+"))

	def keyOK(self):
		if self.keyLocked:
			return
		if self.XXX == True:
			name= self['liste'].getCurrent()[0][0]
			url = self['liste'].getCurrent()[0][1]
			self.session.open(m4kXXXListeScreen, url, name, 'X')
		else:
			name = self['liste'].getCurrent()[0][0]
			url = self['liste'].getCurrent()[0][1]
			self.session.open(m4kStreamListeScreen, url, name, "movie")

class m4kXXXListeScreen(MPScreen, ThumbsHelper):
	def __init__(self, session, url, name, genre):
		self.url = url
		self.name = name
		self.genre = False
		if genre == 'X':
			self.genre = True

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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"green" : self.keyPageNumber,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"blue" :  self.keyTxtPageDown,
			"red" :  self.keyTxtPageUp
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label("XXX Auswahl")
		if self.genre == True:
			self['F2'] = Label(_("Page"))

		self.keyLocked = True
		self.keckse = {}
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.lastpage = 1

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		if self.genre == True:
			shortUrl = re.findall(m4k_url+'xxx-genre-[0-9]*[0-9]*.*?',self.url)
			shortUrlC = str(shortUrl[0])
			url = shortUrlC + '-' + str(self.page) + '.html'
		else:
			url = str(self.url)
		getPage(url, agent=std_headers, headers={'Cookie': 'xxx2=ok', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if self.genre == True:
			self['Page'].setText(_("Page:"))
			self.getLastPage(data, 'id="boxwhite"(.*?)</div><!--maincontent2', '.*>(\d+)\s<')

		self.list=[]
		if self.genre == False:
			serien = re.findall('id="tdmovies.*?width="380.*?href="(.*?)">(.*?)<.*?src=.*?src="(.*?)"', data, re.S)
		else:
			serien = re.findall('id="coverPreview.*?href="(.*?)">(.*?)</a>.*?tdmovies.*?width="25.*?src=.*?width="25.*?src="(.*?)"', data, re.S)
		if serien:
			for url,title,lang in serien:
				url = "%s%s" % (m4k_url, url)
				title = title.replace("\t","")
				title = title.strip(" ")
				self.list.append((decodeHtml(title), url,'',lang,''))
			self.ml.setList(map(self.kinoxlistleftflagged, self.list))
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		name = self['liste'].getCurrent()[0][0]
		self['name'].setText(name)
		url = self['liste'].getCurrent()[0][1]
		getPage(url, agent=std_headers, cookies=self.keckse, headers=movie4kheader).addCallback(self.showHandlung).addErrback(self.dataError)

	def showHandlung(self, data):
		if re.match('.*?<img src="https://img.movie4k.*?/thumbs/', data, re.S):
			cover = re.findall('<img src="https://img.movie4k.*?/thumbs/(.*?)"', data, re.S)
			self.pic = cover[0]
		if re.match('.*?src="/img/smileys/.*?.gif', data, re.S):
			quali = re.findall('src="/img/smileys/(.*?).gif"', data, re.S)
			if quali[0] == "5":
				quali = "top - 5/5"
			if quali[0] == "4":
				quali = "very well - 4/5"
			if quali[0] == "3":
				quali = "average - 3/5"
			if quali[0] == "2":
				quali = "bad - 2/5"
			if quali[0] == "1":
				quali = "very bad - 1/5"
		if re.match('.*?class="moviedescription">.*?</div>', data, re.S):
			desc = re.findall('class="moviedescription">(.*?)<', data, re.S)
			desc = desc[0]
			pic = "%s%s" % (t_url,self.pic)
			CoverHelper(self['coverArt']).getCover(pic)
			if desc and quali:
				handlung = "Quality: "+quali+"\n"+ decodeHtml(desc)
				self['handlung'].setText(decodeHtml(handlung).strip())
				self['F1'].setText(_("Text-"))
				self['F4'].setText(_("Text+"))
			elif desc and not quali:
				handlung = decodeHtml(desc)
				self['F1'].setText(_("Text-"))
				self['F4'].setText(_("Text+"))
			else:
				self['handlung'].setText(_("No information found."))
		self.th_ThumbsQuery(self.list, 0, 1, None, None, '<img src="https://img.movie4k.*?/thumbs/(.*?)"', self.page, self.lastpage, coverlink=t_url)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(m4kStreamListeScreen, url, name, "movie")

class m4kStreamListeScreen(MPScreen):
	def __init__(self, session, url, name, which):
		self.url = url
		self.name = name
		self.which = which
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
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(m4k)
		self['ContentTitle'] = Label(_("Stream Selection"))


		self.coverUrl = None
		self.base_url = m4k_url
		self.tw_agent_hlp = TwAgentHelper(redir_agent=True)
		self.keyLocked = True
		self.list = []
		self.keckse = {}
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_("Please wait..."))
		self.tw_agent_hlp.getWebPage(self.url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if re.match('.*?<img src="https://img.movie4k.*?/thumbs/', data, re.S):
			cover = re.findall('<img src="https://img.movie4k.*?/thumbs/(.*?)"', data, re.S)
			self.pic = cover[0]
			self.cover = "%s%s" %(t_url,self.pic)
			CoverHelper(self['coverArt']).getCover(self.cover)
		if self.which == "movie":
			streams = []
			dupe = []
			hosters = re.findall('<tr id=.*?tablemoviesindex2.*?>(.*?)</td></tr>', data, re.S)
			if hosters:
				self.list = []
				for hoster_raw in hosters:
					hoster_data = re.findall('href.*?"(.*?)">(.*?)<img.*?&nbsp;(.*?)<', hoster_raw)
					if hoster_data:
						(h_url, h_date, h_name) = hoster_data[0]
						hoster_url = "%s%s" % (m4k_url, h_url.replace('\\',''))
						if not hoster_url in dupe:
							dupe.append(hoster_url)
							if isSupportedHoster(h_name, True):
								self.list.append((h_name, hoster_url,h_date,'',''))
								self['name'].setText(self.name)
			else:
				hosters = re.findall('<a target="_blank" href="(http://(.*?)\..*?)"><img border=0', data, re.S)
				if hosters:
					(h_url, h_name) = hosters[0]
					print h_url, h_name.capitalize()
					if isSupportedHoster(h_name, True):
						self.list.append((h_name.capitalize(),h_url,'', '',''))
						self['name'].setText(self.name)
		else:
			hoster = re.findall('"tablemoviesindex2.*?<a href.*?"(.*?.html).*?style.*?src.*?"/img/.*?.[gif|png].*?> \&nbsp;(.*?)</a></td></tr>', data, re.S)
			if hoster:
				for url,hostername in hoster:
					url = "%s%s" % (m4k_url,url)
					if isSupportedHoster(hostername, True):
						self.list.append((hostername,url,'','',''))
						self['name'].setText(self.name)
		if len(self.list) == 0:
			self.list.append(("", "", "No supported streams found."))
			self.ml.setList(map(self.kxStreamListEntry, self.list))
			self.showInfosData(data)
		else:
			self.ml.setList(map(self.kxStreamListEntry, self.list))
			self.keyLocked = False
			self.showInfosData(data)
		self['name'].setText(self.name)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		self.tw_agent_hlp.getWebPage(streamLink).addCallback(self.get_streamlink, streamLink).addErrback(self.dataError)

	def get_streamlink(self, data, streamLink):
		if re.match('.*?(http://img.movie4k.*?/img/parts/teil1_aktiv.png|http://img.movie4k.*?/img/parts/teil1_inaktiv.png|http://img.movie4k.*?/img/parts/part1_active.png|http://img.movie4k.*?/img/parts/part1_inactive.png)', data, re.S):
			self.session.open(m4kPartListeScreen, streamLink, self.name)
		elif isSupportedHoster(streamLink, True):
			get_stream_link(self.session).check_link(streamLink, self.got_link, False)
			return
		else:
			link = re.search('<a\starget="_blank"\shref="(.*?)"><img\sborder=0\ssrc="http://img.movie4k.*?/img/click_link.jpg"', data, re.S|re.I)
			if link:
				get_stream_link(self.session).check_link(link.group(1), self.got_link, False)
				return
			link = re.search('<iframe\swidth=".*?"\sheight=".*?"\sframeborder="0"\ssrc="(.*?)"\sscrolling="no"></iframe>', data, re.S|re.I)
			if link:
				get_stream_link(self.session).check_link(link.group(1), self.got_link, False)
				return
			link = re.search('<iframe\ssrc="(.*?)"\sframeborder=0\smarginwidth=0\smarginheight=0\sscrolling=no\swidth=.*?height=.*?></iframe>', data, re.S|re.I)
			if link:
				get_stream_link(self.session).check_link(link.group(1), self.got_link, False)
				return
			link = re.search("<iframe\sstyle=.*?src='(.*?)'\sscrolling='no'></iframe>", data, re.S|re.I)
			if link:
				get_stream_link(self.session).check_link(link.group(1), self.got_link, False)
				return
			link = re.search('<div\sid="emptydiv"><iframe.*?src=["|\'](.*?)["|\']', data, re.S|re.I)
			if link:
				get_stream_link(self.session).check_link(link.group(1), self.got_link, False)
				return
			link = re.search('<div\sid="emptydiv"><script type="text/javascript"\ssrc=["|\'](.*?)["|\']>', data, re.S|re.I)
			if link:
				get_stream_link(self.session).check_link(link.group(1).replace('?embed',''), self.got_link, False)
				return
			link = re.search('<object\sid="vbbplayer".*?src=["|\'](.*?)["|\']', data, re.S|re.I)
			if link:
				get_stream_link(self.session).check_link(link.group(1), self.got_link, False)
				return
			link = re.search('<param\sname="movie"\svalue="(.*?)"', data, re.S|re.I)
			if link:
				get_stream_link(self.session).check_link(link.group(1), self.got_link, False)
				return
			link = re.search('<a target="_blank" href="(.*?)"><img border=0 src="/img/click_link.jpg"', data, re.S|re.I)
			if link:
				get_stream_link(self.session).check_link(link.group(1), self.got_link, False)
				return
			link = re.search('<iframe\ssrc="(.*?)"\swidth=".*?"\sheight=".*?"\sframeborder="0"\sscrolling="no"></iframe>', data, re.S|re.I)
			if link:
				get_stream_link(self.session).check_link(link.group(1), self.got_link, False)
				return
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)

	def got_link(self, stream_url):
		if stream_url == None:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			if not fileExists(config.mediaportal.watchlistpath.value+"mp_m4k_watched"):
				open(config.mediaportal.watchlistpath.value+"mp_m4k_watched","w").close()
			self.update_liste = []
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_m4k_watched")
			if not leer == 0:
				self.updates_read = open(config.mediaportal.watchlistpath.value+"mp_m4k_watched" , "r")
				for lines in sorted(self.updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						self.update_liste.append("%s" % (line[0]))
				self.updates_read.close()

				updates_read2 = open(config.mediaportal.watchlistpath.value+"mp_m4k_watched" , "a")
				check = ("%s" % self.name)
				if not check in self.update_liste:
					updates_read2.write('"%s"\n' % (self.name))
					updates_read2.close()
				else:
					print "dupe %s" % (self.name)
			else:
				updates_read3 = open(config.mediaportal.watchlistpath.value+"mp_m4k_watched" , "a")
				updates_read3.write('"%s"\n' % (self.name))
				updates_read3.close()

			self.session.open(SimplePlayer, [(self.name, stream_url, self.cover)], showPlaylist=False, ltype='movie4k', cover=True)