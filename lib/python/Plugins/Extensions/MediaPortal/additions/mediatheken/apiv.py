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
from Plugins.Extensions.MediaPortal.resources.configlistext import ConfigListScreenExt
from Plugins.Extensions.MediaPortal.resources.decrypt import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
from Screens.InputBox import InputBox

glob_agent = getUserAgent()
baseurl = 'https://www.amazon.de'
keckse = CookieJar()
loggedin = False
pincode = ''

config.mediaportal.apiv_email = ConfigText(default="", fixed_size=False)
config.mediaportal.apiv_password = ConfigPassword(default="", fixed_size=False)
email = ConfigText(default="", fixed_size=False)
password = ConfigPassword(default="", fixed_size=False)
pinsetup = ConfigPIN(default = 0000, len=4)

class apivMain(MPScreen):

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
			"cancel": self.keyCancel,
			"blue": self.keySetup,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Amazon Prime Instant Video")
		self['ContentTitle'] = Label(_("Genre Selection"))
		self['F4'] = Label(_("Setup"))

		self.suchString = ''
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onFirstExecBegin.append(self.doLogin)

	def doLogin(self):
		self.streamList = []
		if not config.mediaportal.apiv_email.value == "" and not config.mediaportal.apiv_password.value == "":
			self.keySetup()
		elif not fileExists(self.plugin_path + "/userfiles/apiv"):
			self.keySetup()
		else:
			if pincode == '':
				self.session.openWithCallback(self.PINCallback, apivPINScreen, title = _("Enter Security Code:"), windowTitle = "Amazon Prime Instant Video")
			else:
				self.keyLocked = True
				self.ml.setList(map(self._defaultlistcenter, [(_("Please wait..."), None, None)]))
				if not loggedin:
					twAgentGetPage(baseurl + '/gp/sign-in.html', agent=glob_agent, cookieJar=keckse, addlocation=True).addCallback(self.login).addErrback(self.login, True)
				else:
					self.cb_login(None)

	def login(self, data, err=False):
		if not fileExists(self.plugin_path + "/userfiles/apiv"):
			self.keySetup()
		elif fileExists(self.plugin_path + "/userfiles/apiv"):
			fobj = open(self.plugin_path + "/userfiles/apiv","r")
			i = 0
			for line in fobj:
				if i == 0:
					lemail = line.rstrip()
				else:
					lpassword = line.rstrip()
				i = i + 1
			fobj.close()

			mac = getMac()
			cryptpass = str(mac.rstrip())+str(pincode)
			lemail = decrypt(lemail, cryptpass, 256)
			lpassword = decrypt(lpassword, cryptpass, 256)

			formdata = {}
			location = None
			if not err:
				m = re.search('twLocation="(.*?)"', data)
				location = m and m.group(1)
				for m in re.finditer('<input type="hidden" name="(.*?)" value="(.*?)"', data, re.S):
					name, val = m.groups()
					formdata[name] = val

			if formdata and location:
				formdata['email'] = lemail
				formdata['create'] = '0'
				formdata['password'] = lpassword
				twAgentGetPage(location, method='POST', followRedirect=False, postdata=urlencode(formdata), agent=glob_agent, cookieJar=keckse, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.cb_login).addErrback(self.cb_login, True)
			else:
				self.session.open(MessageBoxExt, _("Missing login formdata!"), MessageBoxExt.TYPE_ERROR, title = "Amazon Prime Instant Video")
				printl(str(data),self,'E')

	def cb_login(self, result, err=False):
		global loggedin
		data = str(result)
		if 'id="message_error"' in data:
			errmsg = stripAllTags(re.findall('class="message\serror">(.*?)</div>', data, re.S)[0]).strip()
			if 'Bei der Eingabe Ihrer E-Mail-Adresse/Ihres Kennworts ist ein Fehler aufgetreten.' in errmsg:
				self.session.open(MessageBoxExt, _("Wrong login data, check your eMail and password and try again!"), MessageBoxExt.TYPE_ERROR, title = "Amazon Prime Instant Video")
			else:
				self.session.open(MessageBoxExt, _("Unknown error! (%s)" % errmsg), MessageBoxExt.TYPE_ERROR, title = "Amazon Prime Instant Video")
		elif not err:
			if 'id="message_warning"' in data:
				errmsg = stripAllTags(re.findall('class="message\swarning">(.*?)</div>', data, re.S)[0]).strip()
				if 'und geben Sie dann die Zeichen ein, die in der Abbildung unten gezeigt werden' in errmsg:
					self.session.open(MessageBoxExt, _("Captcha login required!"), MessageBoxExt.TYPE_ERROR, title = "Amazon Prime Instant Video")
				else:
					twAgentGetPage(baseurl, agent=glob_agent, cookieJar=keckse).addCallback(self.layoutFinished).addErrback(self.dataError)
			else:
				twAgentGetPage(baseurl, agent=glob_agent, cookieJar=keckse).addCallback(self.layoutFinished).addErrback(self.dataError)
		else:
			printl(str(result),self,'E')
			if loggedin:
				loggedin = False
				self.doLogin()

	def layoutFinished(self, data):
		global loggedin
		if '"isPrime":1' in data:
			loggedin = True
			self.streamList.append(("Meistgesehene Filme", "filme", baseurl + "/s/ref=atv_sn_piv_cl1_mv_pl?_encoding=UTF8&rh=n%3A3010075031%2Cn%3A3356018031&sort=popularity-rank&page="))
			self.streamList.append(("Kürzlich hinzugefügte Filme", "filme", baseurl + "/s/ref=atv_sn_piv_cl1_mv_ra?_encoding=UTF8&rh=n%3A3010075031%2Cn%3A3356018031%2Cn%3A4190509031&sort=sort=date-desc-rank&page="))
			self.streamList.append(("Filmgenres", "genre_filme", baseurl + "/b/ref=atv_sn_piv_cl1_mv_gn?_encoding=UTF8&node=3794661031"))
			self.streamList.append(("Filmstudios", "genre_filme", baseurl + "/b/ref=atv_sn_piv_cl1_mv_st?_encoding=UTF8&node=4262585031"))
			self.streamList.append(("Filmempfehlungen der Redaktion", "genre_filme", baseurl + "/b/ref=atv_sn_piv_cl1_mv_ep?_encoding=UTF8&node=3794662031"))
			self.streamList.append(("Watchlist Filme", "watchlist_filme", baseurl + "/gp/video/watchlist/movie?ie=UTF8&ref_=sv_atv_7"))
			self.streamList.append(("--------------------------------------------------------", None, None))
			self.streamList.append(("Meistgesehene Serien", "serien", baseurl + "/s/ref=atv_sn_piv_cl2_tv_pl?_encoding=UTF8&rh=n%3A3010075031%2Cn%3A3356019031&sort=popularity-rank&page="))
			self.streamList.append(("Kürzlich hinzugefügte Serien", "serien", baseurl + "/s/ref=atv_sn_piv_cl2_tv_ra?_encoding=UTF8&bbn=3279204031&rh=n%3A3279204031%2Cn%3A3010075031%2Cn%3A3015916031&sort=date-desc-rank&page="))
			self.streamList.append(("Seriengenres", "genre_serien", baseurl + "/b/ref=atv_sn_piv_cl2_tv_gn?_encoding=UTF8&node=3794658031"))
			self.streamList.append(("Serienstudios", "genre_serien", baseurl + "/b/ref=atv_sn_piv_cl2_tv_st?_encoding=UTF8&node=4262588031"))
			self.streamList.append(("Serienempfehlungen der Redaktion", "genre_serien", baseurl + "/b/ref=atv_sn_piv_cl2_tv_ep?_encoding=UTF8&node=3794659031"))
			self.streamList.append(("Watchlist Serien", "watchlist_serien", baseurl + "/gp/video/watchlist/tv?ie=UTF8&ref_=sv_atv_7"))
			self.streamList.append(("--------------------------------------------------------", None, None))
			self.streamList.append(("Suche", "suche", None))
			self.ml.setList(map(self._defaultlistcenter, self.streamList))
			self.keyLocked = False
			self.showInfos()
		elif not 'id="nav-item-signout"' in data:
			loggedin = False
			self.session.open(MessageBoxExt, _("Login failed!"), MessageBoxExt.TYPE_ERROR, title = "Amazon Prime Instant Video")
		else:
			loggedin = False
			self.session.open(MessageBoxExt, _("Unknown error!"), MessageBoxExt.TYPE_ERROR, title = "Amazon Prime Instant Video")

	def keySetup(self):
		if mp_globals.isDreamOS:
			self.session.openWithCallback(self.PINCallback, apivSetupScreen, is_dialog=True)
		else:
			self.session.openWithCallback(self.PINCallback, apivSetupScreen)

	def PINCallback(self, callback=False):
		global loggedin
		if callback:
			loggedin = False
			keckse.clear()
			self.doLogin()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		genre = self['liste'].getCurrent()[0][0]
		section = self['liste'].getCurrent()[0][1]
		url = self['liste'].getCurrent()[0][2]
		if section:
			if section == "filme":
				self.session.open(apivMovieParsing, genre, url, section)
			elif section == "serien":
				self.session.open(apivMovieParsing, genre, url, section)
			elif section == "genre_serien" or section == "genre_filme":
				self.session.open(apivGenreParsing, genre, url, section)
			elif section == "watchlist_filme":
				self.session.open(apivWatchlistParsing, genre, url, "filme")
			elif section == "watchlist_serien":
				self.session.open(apivWatchlistParsing, genre, url, "serien")
			elif section == "suche":
				self.suchen()

	def SuchenCallback(self, callback = None, entry = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			self.session.open(apivSearchParsing, self.suchString)

	def keyCancel(self):
		global pincode
		pincode = ''
		global loggedin
		loggedin = False
		keckse.clear()
		self.close()

class apivPINScreen(InputBox):
	def __init__(self, session, service = "", *args, **kwargs):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/PinInput.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/PinInput.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		InputBox.__init__(self, session = session, text="    ", maxSize=True, type=Input.PIN, *args, **kwargs)
		self["service"] = Label(service)
		self["tries"] = Label("")
		self["title"] = Label(kwargs.get('windowTitle', ''))

		self.onShow.append(self.__onShow)

	def __onShow(self):
		try:
			self._closeHelpWindow()
		except:
			pass

	def gotAsciiCode(self):
		if self["input"].currPos == len(self["input"]) - 1:
			InputBox.gotAsciiCode(self)
			self.key()
		else:
			InputBox.gotAsciiCode(self)

	def keyNumberGlobal(self, number):
		if self["input"].currPos == len(self["input"]) - 1:
			InputBox.keyNumberGlobal(self, number)
			self.key()
		else:
			InputBox.keyNumberGlobal(self, number)

	def go(self):
		pass

	def key(self):
		if len(self["input"].getText()) > 3:
			self.closePinCorrect()

	def closePinCorrect(self, *args):
		global pincode
		pincode = self["input"].getText()
		self.close(True)

	def cancel(self):
		self.close(False)

class apivSetupScreen(Screen, ConfigListScreenExt):

	def __init__(self, session):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/PluginUserDefault.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/PluginUserDefault.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)
		self['title'] = Label("Amazon Prime Instant Video " + _("Setup"))
		self.setTitle("Amazon Prime Instant Video " + _("Setup"))

		self.list = []
		ConfigListScreenExt.__init__(self, self.list)

		global pincode
		if not config.mediaportal.apiv_email.value == "" and not config.mediaportal.apiv_password.value == "":
			email.value = config.mediaportal.apiv_email.value
			password.value = config.mediaportal.apiv_password.value
			pinsetup.value = 0000
		else:
			if not pincode == '':
				try:
					if fileExists(self.plugin_path + "/userfiles/apiv"):
						fobj = open(self.plugin_path + "/userfiles/apiv","r")
						i = 0
						for line in fobj:
							if i == 0:
								lemail = line.rstrip()
							else:
								lpassword = line.rstrip()
							i = i + 1
						fobj.close()

						mac = getMac()
						cryptpass = str(mac.rstrip())+str(pincode)
						email.value = decrypt(lemail, cryptpass, 256)
						password.value = decrypt(lpassword, cryptpass, 256)
						pinsetup.value = int(pincode)
				except:
					pinsetup.value = 0000
					email.value = ''
					password.value = ''
			else:
				pinsetup.value = 0000
				email.value = ''
				password.value = ''

		self.list.append(getConfigListEntry(_("E-Mail:"), email))
		self.list.append(getConfigListEntry(_("Password:"), password))
		self.list.append(getConfigListEntry(_("Security Code:"), pinsetup))

		self["config"].setList(self.list)

		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"ok":		self.saveConfig,
			"cancel":	self.exit
		}, -1)

	def saveConfig(self):
		if not email.value == '' and not password.value == '':
			mac = getMac()
			fobj_out = open(self.plugin_path + "/userfiles/apiv","w")
			if len(str(pinsetup.value)) == 4:
				pinval = str(pinsetup.value).strip()
			elif len(str(pinsetup.value)) == 3:
				pinval = '0'+str(pinsetup.value).strip()
			elif len(str(pinsetup.value)) == 2:
				pinval = '00'+str(pinsetup.value).strip()
			elif len(str(pinsetup.value)) == 1:
				pinval = '000'+str(pinsetup.value).strip()
			cryptpass = str(mac)+pinval
			writeback = encrypt(email.value, cryptpass, 256)+"\n"
			fobj_out.write(writeback)
			writeback = encrypt(password.value, cryptpass, 256)+"\n"
			fobj_out.write(writeback)
			fobj_out.close()
			if not config.mediaportal.apiv_email.value == "" and not config.mediaportal.apiv_password.value == "":
				config.mediaportal.apiv_email.value = ''
				config.mediaportal.apiv_email.save()
				config.mediaportal.apiv_password.value = ''
				config.mediaportal.apiv_password.save()
				configfile.save()
			global pincode
			pincode = ''
			self.close(True)
		else:
			self.exit()

	def exit(self):
		self.close(False)

class apivGenreParsing(MPScreen):

	def __init__(self, session, genre, url, section):
		self.genre = genre
		self.url = url
		self.section = section
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Amazon Prime Instant Video")
		self['ContentTitle'] = Label("%s" % self.genre)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_('Please wait...'))
		twAgentGetPage(self.url, agent=glob_agent, cookieJar=keckse).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		genre = re.findall('<a\sclass=\'titlelink\'\shref="(http[s]{0,1}://www.amazon.de|)(.*?)">.*?<img.*?alt="(.*?)"\ssrc="(.*?)".*?class="collections-image"', data, re.S)
		if genre:
			for Dummy,Url,Title,Image in genre:
				Image = Image.replace(',TopLeft,0,0_AA200_.jpg','_SX320_QL80_.jpg')
				if Title == '':
					try:
						Title = re.search('Prime/Studios/(.*?)\.', Image).groups()[0].upper()
					except:
						try:
							Title = re.search('Prime/(.*?prime)_', Image).groups()[0].upper().replace('_',' ')
						except:
							Title = re.search('Prime/(.*?)_', Image).groups()[0].upper().replace('.',' ')
				Url = Url.replace('&amp;','&')
				if iso8859_Decode(Title) != "Alles für Kinder bei Prime Instant Video":
					if iso8859_Decode(Title) != "Zeit für kleine Träumer":
						self.streamList.append((iso8859_Decode(Title).replace('&amp;','&'), baseurl+Url+"&page=", Image))
			if len(self.streamList) == 0:
				self.streamList.append((_("Parsing error!"), None))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		movie_title = self['liste'].getCurrent()[0][0]
		movie_url = self['liste'].getCurrent()[0][1]
		if self.section == "genre_filme":
			self.session.open(apivMovieParsing, movie_title, movie_url, "filme")
		elif self.section == "genre_serien":
			self.session.open(apivMovieParsing, movie_title, movie_url, "serien")

class apivStaffelParsing(MPScreen):

	def __init__(self, session, serie, url, coverUrl):
		self.serie = serie
		self.url = url
		self.coverUrl = coverUrl
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Amazon Prime Instant Video")
		self['ContentTitle'] = Label(_("Season Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_('Please wait...'))
		CoverHelper(self['coverArt']).getCover(self.coverUrl)
		twAgentGetPage(self.url, agent=glob_agent, cookieJar=keckse).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('id="dv-season-drop-down"(.*?)</div>', data, re.S)
		if parse:
			staffeln = re.findall('<option\svalue="(.*?):atv_dp_season_select_s.*?"\sdata-a-css-class="dv-dropdown-option"\sdata-a-html-content="Staffel\s(\d+).*?dropdown-prime.*?</option>', parse.group(1), re.S)
			if staffeln:
				for Id,Staffel in staffeln:
					url = baseurl+"/dp/"+Id
					self.streamList.append(("Staffel "+Staffel, url))
				if len(self.streamList) == 0:
					self.streamList.append((_("Parsing error!"), None))
				self.ml.setList(map(self._defaultlistcenter, self.streamList))
				self.keyLocked = False
		else:
			self.streamList.append(("Staffel 1", self.url))
			self.ml.setList(map(self._defaultlistcenter, self.streamList))
			self.keyLocked = False
		self['name'].setText(self.serie)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		serie_staffel = self['liste'].getCurrent()[0][0]
		serie_url = self['liste'].getCurrent()[0][1]
		self.serie = re.sub('\s{0,1}-{0,1}\sStaffel\s{0,2}(\d+)','', self.serie, re.I)
		self.serie = re.sub('\s{0,1}-{0,1}\sSeason\s{0,2}(\d+)','', self.serie, re.I)
		self.session.open(apivEpisodenParsing, self.serie+" "+serie_staffel, serie_url, self.coverUrl)

class apivEpisodenParsing(MPScreen):

	def __init__(self, session, serie, url, coverUrl):
		self.serie = serie
		self.url = url
		self.coverUrl = coverUrl
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Amazon Prime Instant Video")
		self['ContentTitle'] = Label(_("Episode Selection"))
		self['F1'] = Label(_("Text-"))
		self['F4'] = Label(_("Text+"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_('Please wait...'))
		CoverHelper(self['coverArt']).getCover(self.coverUrl)
		twAgentGetPage(self.url, agent=glob_agent, cookieJar=keckse).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		watched_liste = self.readMarkList()
		episoden_raw = re.findall('(<a\shref="http[s]{0,1}://www.amazon.de/gp/product/.*?"\sclass="episode-list-link">.*?<div\sclass="episode-list-badge-container">)', data, re.S)
		if episoden_raw:
			for each in episoden_raw:
				raw = re.findall('<a\shref="http[s]{0,1}://www.amazon.de/gp/product/(.*?)/.*?".*?<span\sclass="episode-title">(.*?)</span>', each, re.S)
				if raw:
					id,title = raw[0]
					title = iso8859_Decode(title).strip()
					url = baseurl+"/dp/"+id
					if self.serie+" Episode "+title in watched_liste:
						self.streamList.append((decodeHtml("Episode "+title), url, True))
					else:
						self.streamList.append((decodeHtml("Episode "+title), url, False))
			if len(self.streamList) == 0:
				self.streamList.append((_("Parsing error!"), None))
			self.ml.setList(map(self._defaultlistleftmarked, self.streamList))
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		self['name'].setText(self.serie)
		twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		handlung = re.search('og:description"\scontent="(.*?)"', data, re.S)
		if handlung:
			streamHandlung = handlung.group(1)
			self['handlung'].setText(decodeHtml(iso8859_Decode(streamHandlung)))
		else:
			self['handlung'].setText("")

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		serie_episode = self['liste'].getCurrent()[0][0]
		serie_url = self['liste'].getCurrent()[0][1]
		self.session.openWithCallback(self.reloadCallback, apivStreamsParsing, self.serie+" "+serie_episode, serie_url, self.coverUrl)

	def reloadCallback(self, callback=None):
		self.loadPage()

	def setupCallback(self, callback=False):
		if callback:
			self.doLogin()

	def readMarkList(self):
		watched_liste = []
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_apiv_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_apiv_watched","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_apiv_watched"):
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_apiv_watched")
			if not leer == 0:
				updates_read = open(config.mediaportal.watchlistpath.value+"mp_apiv_watched" , "r")
				for lines in sorted(updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						watched_liste.append("%s" % (line[0]))
					updates_read.close()
		return watched_liste

class apivMovieParsing(MPScreen):

	def __init__(self, session, genre, url, section="filme"):
		self.genre = genre
		self.url = url
		self.section = section
		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		if section == "filme":
			path = "%s/%s/defaultListScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
			if not fileExists(path):
				path = self.skin_path + mp_globals.skinFallback + "/defaultListScreen.xml"
		else:
			path = "%s/%s/defaultListWideScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
			if not fileExists(path):
				path = self.skin_path + mp_globals.skinFallback + "/defaultListWideScreen.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"red" :	self.keyTxtPageUp,
			"green" : self.keyAdd,
			"blue" : self.keyTxtPageDown
		}, -1)

		self['title'] = Label("Amazon Prime Instant Video")
		self['ContentTitle'] = Label("%s" % self.genre)
		self['Page'] = Label(_("Page:"))
		self['F1'] = Label(_("Text-"))
		self['F2'] = Label(_("Add to Watchlist"))
		self['F4'] = Label(_("Text+"))

		self.dupelist = []
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 1
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_('Please wait...'))
		url = self.url+str(self.page)
		twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data.replace('\\"','"'), '<div\sid="pagn"(.*?)</div>')
		movies = re.findall('data-asin="(.*?)".*?img alt="Produkt-Information" src="(.*?)" onload.*?title="(.*?)"', data, re.S)
		if not movies:
			movies = re.findall('class="\s{0,2}ilo2".*?name="(.*?)".*?class="imageBox">.*?src="(.*?)".*?class="lrg\sbold">(.*?)</span>.*?</ul>', data, re.S)
		if movies:
			for Id,Image,Title in movies:
				Title = re.sub('\s{0,1}-{0,1}\sStaffel\s{0,2}(\d+)','', Title, re.I)
				Title = re.sub('\s{0,1}-{0,1}\sSeason\s{0,2}(\d+)','', Title, re.I)
				Image = Image.replace(',TopLeft,0,0_AA200_.jpg','_SX320_QL80_.jpg')
				if self.section == "serien" and Title not in self.dupelist:
					self.dupelist.append(Title)
					self.streamList.append((decodeHtml(Title), Id, Image))
				elif self.section == "filme":
					self.streamList.append((decodeHtml(Title), Id, Image))
		if len(self.streamList) == 0:
			self.streamList.append((_("Parsing error!"), None, None))
		self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)
		movie_id = self['liste'].getCurrent()[0][1]
		if movie_id:
			filmName = self['liste'].getCurrent()[0][0]
			self['name'].setText(filmName)
			if self.section == "filme":
				url = baseurl+"/dp/"+movie_id
				twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		handlung = re.search('og:description"\scontent="(.*?)"', data, re.S)
		if handlung:
			streamHandlung = handlung.group(1)
			self['handlung'].setText(decodeHtml(iso8859_Decode(streamHandlung)))
		else:
			self['handlung'].setText("")

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		movie_title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		movie_id = self['liste'].getCurrent()[0][1]
		if movie_id:
			if self.section == "filme":
				self.session.open(apivStreamsParsing, movie_title, baseurl+"/dp/"+movie_id, coverUrl)
			elif self.section == "serien":
				self.session.open(apivStaffelParsing, movie_title, baseurl+"/dp/"+movie_id, coverUrl)

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		movie_id = self['liste'].getCurrent()[0][1]
		url = baseurl+"/gp/video/watchlist/ajax/hoverbubble.html?ASIN="+movie_id
		twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.getToken).addErrback(self.dataError)

	def getToken(self, data):
		token = re.findall('token\s=\s"(.*?)"', data)
		if token:
			token = urllib.quote_plus(token[0])
			movie_id = self['liste'].getCurrent()[0][1]
			url = baseurl + "/gp/video/watchlist/ajax/addRemove.html/ref=sr_1_3_watchlist_add?token=%s&dataType=json&ASIN=%s&store=instant-video" % (token, movie_id)
			twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.watchlistPost).addErrback(self.dataError)

	def watchlistPost(self, data):
		movie_title = self['liste'].getCurrent()[0][0]
		message = self.session.open(MessageBoxExt, _("%s was added to the watchlist." % movie_title), MessageBoxExt.TYPE_INFO, timeout=3)

class apivWatchlistParsing(MPScreen):

	def __init__(self, session, genre, url, section):
		self.genre = genre
		self.url = url
		self.section = section
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keyDel
		}, -1)

		self['title'] = Label("Amazon Prime Instant Video")
		self['ContentTitle'] = Label("%s" % self.genre)
		self['F1'] = Label(_("Delete"))

		self.token = None
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_('Please wait...'))
		twAgentGetPage(self.url, agent=glob_agent, cookieJar=keckse).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		token_raw = re.findall("token : '(.*?)'", data)
		if token_raw:
			self.token = token_raw[0]
		movies = re.findall('<div\sclass="packshot-wrapper.*?data-asin="(.*?)".*?<img\salt="(.*?)".*?src="(.*?)"', data, re.S)
		if movies:
			for id,title,image in movies:
				title = re.sub('\s{0,1}-{0,1}\sStaffel\s{0,2}(\d+)','', title, re.I)
				title = re.sub('\s{0,1}-{0,1}\sSeason\s{0,2}(\d+)','', title, re.I)
				self.streamList.append((decodeHtml(title), id, image))
		if len(self.streamList) == 0:
			self.streamList.append((_("Watchlist is currently empty"), None, None))
			self.keyLocked = True
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		filmName = self['liste'].getCurrent()[0][0]
		self.coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(filmName)
		CoverHelper(self['coverArt']).getCover(self.coverUrl)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		movie_title = self['liste'].getCurrent()[0][0]
		movie_id = self['liste'].getCurrent()[0][1]
		self.coverUrl = self['liste'].getCurrent()[0][2]
		movie_url = baseurl+"/dp/"+movie_id
		if self.section == "filme":
			self.session.open(apivStreamsParsing, movie_title, movie_url, self.coverUrl)
		elif self.section == "serien":
			self.session.open(apivStaffelParsing, movie_title, movie_url, self.coverUrl)

	def keyDel(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		movie_id = self['liste'].getCurrent()[0][1]
		url = baseurl+"/gp/video/watchlist/ajax/hoverbubble.html?ASIN="+movie_id
		twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.getToken).addErrback(self.dataError)

	def getToken(self, data):
		token = re.findall('token\s=\s"(.*?)"', data)
		if token:
			token = urllib.quote_plus(token[0])
			movie_id = self['liste'].getCurrent()[0][1]
			url = baseurl + "/gp/video/watchlist/ajax/addRemove.html/ref=sr_1_3_watchlist_remove?token=%s&dataType=json&ASIN=%s&store=instant-video" % (token, movie_id)
			twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.watchlistPost).addErrback(self.dataError)

	def watchlistPost(self, data):
		self.loadPage()

class apivSearchParsing(MPScreen):

	def __init__(self, session, searchSTRING):
		self.searchSTRING = searchSTRING
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"red" :	self.keyTxtPageUp,
			"green" : self.keyAdd,
			"blue" : self.keyTxtPageDown
		}, -1)

		self['title'] = Label("Amazon Prime Instant Video")
		self['ContentTitle'] = Label("Suche: %s" % self.searchSTRING)
		self['Page'] = Label(_("Page:"))
		self['F2'] = Label(_("Add to Watchlist"))

		self.dupelist = []
		self.page = 1
		self.lastpage = 1
		self.token = None
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_('Please wait...'))
		url = baseurl + "/s/ref=sr_nr_n_7?fst=as%3Aoff&rh=n%3A3279204031%2Ck%3A"+self.searchSTRING+"&ie=UTF8&keywords="+self.searchSTRING+"&page="+str(self.page)
		twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data.replace('\\"','"'), '<div\sid="pagn"(.*?)</div>')
		results = re.findall('data-asin="(.*?)".*?<img alt="Produkt-Information" src="(.*?)".*?title="(.*?)" ', data, re.S)
		if results:
			for id,image,title in results:
				if re.search('\s{0,1}-{0,1}\sStaffel\s{0,2}(\d+)', title, re.I):
					section = "serien"
				elif re.search('\s{0,1}-{0,1}\sSeason\s{0,2}(\d+)', title, re.I):
					section = "serien"
				else:
					section = "filme"
				image = image.replace(',TopLeft,0,0_AA160_.jpg','_SX320_QL80_.jpg')
				title = re.sub('\s{0,1}-{0,1}\sStaffel\s{0,2}(\d+)','', title, re.I)
				title = re.sub('\s{0,1}-{0,1}\sSeason\s{0,2}(\d+)','', title, re.I)
				if title not in self.dupelist:
					self.dupelist.append(title)
					self.streamList.append((decodeHtml(title), id, image, section))
		if len(self.streamList) == 0:
			self.streamList.append((_("No search results!"), None, None, None))
		self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		self.coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(self.coverUrl)
		movie_id = self['liste'].getCurrent()[0][1]
		section = self['liste'].getCurrent()[0][3]
		if movie_id:
			filmName = self['liste'].getCurrent()[0][0]
			self['name'].setText(filmName)
		if section == "filme":
			url = baseurl+"/dp/"+movie_id
			twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		handlung = re.search('og:description"\scontent="(.*?)"', data, re.S)
		if handlung:
			streamHandlung = handlung.group(1)
			self['handlung'].setText(decodeHtml(iso8859_Decode(streamHandlung)))
		else:
			self['handlung'].setText("")

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		movie_title = self['liste'].getCurrent()[0][0]
		self.coverUrl = self['liste'].getCurrent()[0][2]
		movie_id = self['liste'].getCurrent()[0][1]
		section = self['liste'].getCurrent()[0][3]
		if movie_id:
			movie_url = baseurl+"/dp/"+movie_id
			if section == "filme":
				self.session.open(apivStreamsParsing, movie_title, movie_url, self.coverUrl)
			elif section == "serien":
				self.session.open(apivStaffelParsing, movie_title, movie_url, self.coverUrl)

	def keyAdd(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		movie_id = self['liste'].getCurrent()[0][1]
		url = baseurl+"/gp/video/watchlist/ajax/hoverbubble.html?ASIN="+movie_id
		twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.getToken).addErrback(self.dataError)

	def getToken(self, data):
		token = re.findall('token\s=\s"(.*?)"', data)
		if token:
			token = urllib.quote_plus(token[0])
			movie_id = self['liste'].getCurrent()[0][1]
			url = baseurl + "/gp/video/watchlist/ajax/addRemove.html/ref=sr_1_3_watchlist_add?token=%s&dataType=json&ASIN=%s&store=instant-video" % (token, movie_id)
			twAgentGetPage(url, agent=glob_agent, cookieJar=keckse).addCallback(self.watchlistPost).addErrback(self.dataError)

	def watchlistPost(self, data):
		movie_title = self['liste'].getCurrent()[0][0]
		message = self.session.open(MessageBoxExt, _("%s was added to the watchlist." % movie_title), MessageBoxExt.TYPE_INFO, timeout=3)

class apivStreamsParsing(MPScreen):

	def __init__(self, session, mtitle, url, coverUrl):
		self.mtitle = mtitle
		self.url = url
		self.coverUrl = coverUrl
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
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Amazon Prime Instant Video")
		self['ContentTitle'] = Label(_("Stream Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_('Please wait...'))
		CoverHelper(self['coverArt']).getCover(self.coverUrl)
		twAgentGetPage(self.url, agent=glob_agent, cookieJar=keckse).addCallback(self.getflashvars).addErrback(self.dataError)

	def getflashvars(self, data):
		values = {}
		values['asin'] = re.findall('"pageAsin":"(.*?)"', data, re.S)[0]
		values['sessionID'] = re.findall("ue_sid='(.*?)'", data, re.S)[0]
		values['marketplace'] = re.findall("ue_mid='(.*?)'", data, re.S)[0]
		values['customer'] = re.findall('"customerID":"(.*?)"', data, re.S)[0]
		values['deviceID'] = values['customer'] + str(int(time() * 1000)) + values['asin']
		csrftoken = re.findall('"csrfToken":"(.*?)"', data, re.S)[0]
		csrftoken = urllib.quote_plus(csrftoken)
		twAgentGetPage(baseurl+"/gp/video/streaming/player-token.json?callback=jQuery&csrftoken="+csrftoken, agent=glob_agent, cookieJar=keckse).addCallback(self.getToken, values).addErrback(self.dataError)

	def getToken(self, data, values):
		try:
			token = re.findall('"([^"]*).*"([^"]*)"', data)
		except:
			return
		url = 'https://atv-ext-eu.amazon.com/cdp/catalog/GetStreamingUrlSets'
		url += '?asin=' + values['asin']
		#url += '&deviceTypeID=A324MFXUEZFF7B'
		url += '&deviceTypeID=A35LWR0L7KC0TJ'
		url += '&firmware=WIN%2016,0,0,235%20PlugIn'
		url += '&customerID=' + values['customer']
		url += '&deviceID=' + values['deviceID']
		url += '&marketplaceID=' + values['marketplace']
		url += '&token=' + token[0][1]
		url += '&format=json'
		url += '&version=1'
		url += '&xws-fa-ov=true'
		twAgentGetPage(str(url)+"&audioTrackId=deu_dialog_0", agent=glob_agent, cookieJar=keckse).addCallback(self.getStreams, "Deutsch").addErrback(self.dataError)
		twAgentGetPage(str(url)+"&audioTrackId=eng_dialog_0", agent=glob_agent, cookieJar=keckse).addCallback(self.getStreams, "Englisch").addErrback(self.dataError)

	def getStreams(self, data, language):
		lang = language + " - "
		data = json.loads(data)
		sessionId = data['message']['body']['urlSets']['streamingURLInfoSet'][0]['sessionId']
		cdn = data['message']['body']['urlSets']['streamingURLInfoSet'][0]['cdn']
		rtmpurls = data['message']['body']['urlSets']['streamingURLInfoSet'][0]['streamingURLInfo']
		title = data['message']['body']['metadata']['title']

		if rtmpurls:
			for rtmpurl in rtmpurls:
				rtmpurlSplit = re.findall("([^:]*):\/\/([^\/]+)\/([^\/]+)\/([^\?]+)(\?.*)?", rtmpurl['url'])
				if rtmpurlSplit:
					url = 'http://azeufms-vodfs.fplive.net/' + rtmpurl['url'][rtmpurl['url'].find('mp4:')+4:]
					if language == "Englisch":
						if not re.search('_eng_', str(url), re.I):
							break
					stream_info = re.findall('video_(.*?)_(.*?)_audio_(.*?)_(.*?kbps).*?$', str(url), re.I)
					if stream_info:
						info = str(stream_info[0][0]) + ' - ' + str(stream_info[0][1]) + ' - ' + str(stream_info[0][2]).upper() + ' - ' + str(stream_info[0][3])
						if ("[OV]" in self.mtitle) or ("[OmU]" in self.mtitle):
							lang = ""
						if str(stream_info[0][0]) != "336p":
							self.streamList.append((lang+info, url))
					else:
						stream_info = re.findall('(video.*?\.mp4)', str(url), re.I)
						if stream_info:
							stream_info = str(stream_info[0])
							self.streamList.append((lang+" - "+stream_info, url))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self['name'].setText(self.mtitle)
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]

		if re.search('Staffel\s{0,2}(\d+)', str(self.mtitle), re.I):
			self.addMarkList(str(self.mtitle))
		self.session.open(SimplePlayer, [(str(self.mtitle), str(url), self.coverUrl)], showPlaylist=False, ltype='apiv', cover=True)

	def readMarkList(self):
		watched_liste = []
		if not fileExists(config.mediaportal.watchlistpath.value+"mp_apiv_watched"):
			open(config.mediaportal.watchlistpath.value+"mp_apiv_watched","w").close()
		if fileExists(config.mediaportal.watchlistpath.value+"mp_apiv_watched"):
			leer = os.path.getsize(config.mediaportal.watchlistpath.value+"mp_apiv_watched")
			if not leer == 0:
				updates_read = open(config.mediaportal.watchlistpath.value+"mp_apiv_watched" , "r")
				for lines in sorted(updates_read.readlines()):
					line = re.findall('"(.*?)"', lines)
					if line:
						watched_liste.append("%s" % (line[0]))
					updates_read.close()
		return watched_liste

	def addMarkList(self, name):
		watched_liste = self.readMarkList()
		added = False
		if fileExists(config.mediaportal.watchlistpath.value+"mp_apiv_watched"):
			read = open(config.mediaportal.watchlistpath.value+"mp_apiv_watched" , "a")
			if not name in watched_liste:
				read.write('"%s"\n' % (name))
				added = True
			read.close()
		if added:
			print "added %s to MarkList" % name
		else:
			print "%s already exist in MarkList" % name