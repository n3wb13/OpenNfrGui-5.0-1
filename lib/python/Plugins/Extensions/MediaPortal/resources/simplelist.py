# -*- coding: utf-8 -*-

from os.path import isfile
import glob
from Plugins.Extensions.MediaPortal.plugin import _
from imports import *
from simpleplayer import SimplePlayer, SimplePlaylistIO
from Components.FileList import FileList
from debuglog import printlog as printl
from configlistext import ConfigListScreenExt

if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/SerienFilm/MovieSelection.pyo'):
	from Plugins.Extensions.SerienFilm.MovieSelection import MovieSelection
else:
	from Screens.MovieSelection import MovieSelection
from Plugins.Extensions.MediaPortal.resources.hlsplayer import *

class simplelistGenreScreen(MPScreen):

	def __init__(self, session):

		self.plugin_path = mp_globals.pluginPath
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/defaultGenreScreen.xml" % (self.skin_path, config.mediaportal.skin.value)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/defaultGenreScreen.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config.mediaportal.minitv.value)
		MPScreen.__init__(self, session)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"menu": self.keyMenu,
			"red": self.keyCancel,
			"blue": self.deleteEntry
		}, -1)

		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/mediainfo/plugin.pyo"):
			self.filelist_path = config.plugins.mediainfo.savetopath.value
		else:
			self.filelist_path = "/media/hdd/movie/"

		self.keyLocked = True
		self['title'] = Label("SimpleList")
		self['ContentTitle'] = Label("")
		self['name'] = Label(_("Selection:"))
		self['F1'] = Label("")
		self['F2'] = Label("")
		self['F3'] = Label("")
		self['F4'] = Label(_("Delete"))
		self['F4'].hide()

		self.last_pl_number = config.mediaportal.sp_pl_number.value
		self.last_videodir = config.movielist.last_videodir.value
		config.movielist.last_videodir.value = self.filelist_path
		self.last_selection = None
		self.filelist = []
		self.genreliste = []
		self.playlist_num = 1
		self.menu_level = 0
		self.last_menu_idx = 0
		self.ltype = ''
		self.m3u_title = None
		self.lastservice = None
		self.sp_option = ""

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onClose.append(self._onClose)

		self.onLayoutFinish.append(self.buildMenulist)

	def buildMenulist(self):
		self['F1'].setText(_("Exit"))
		self['ContentTitle'].setText(_('List overview'))
		self.genreliste.append(('1', _('Video List'), ''))
		path = config.mediaportal.watchlistpath.value + 'mp_global_pl_*'
		list = glob.glob(path)
		for fn in list:
			n = int(re.search('mp_global_pl_(\d+)', fn).group(1))
			self.genreliste.append(('2', 'Global Playlist-%02d' % n, n))
		self.genreliste.sort(key=lambda t : t[0]+t[1].lower())

		path = self.plugin_path + "/userfiles/" + '*.m3u'
		list = glob.glob(path)
		for upath in list:
			fn = upath.split('/')[-1]
			wpath = config.mediaportal.watchlistpath.value + fn
			try:
				shutil.copyfile(upath, wpath)
			except:
				pass

		path = config.mediaportal.watchlistpath.value + '*.m3u'
		list = glob.glob(path)
		list.sort(key=lambda t : t.lower())
		for fn in list:
			self.genreliste.append(('3', fn.split('/')[-1], fn))

		self.ml.setList(map(self.simplelistListEntry, self.genreliste))
		self.keyLocked = False

	def loadFileList(self):
		self.ltype = 'sl_movies'
		self['F4'].hide()
		self.session.openWithCallback(self.getSelection, MovieSelection, selectedmovie=self.last_selection)

	def getSelection(self, current):
		from ServiceReference import ServiceReference
		if current:
			if type(current) == tuple:
				current = current[0]
			sref = ServiceReference(current)
			self.last_selection = current
			url = sref.getPath()
			fn = sref.getServiceName()
			self.session.openWithCallback(self.loadFileList, SimplePlayer, [(fn, url)], showPlaylist=False, ltype=self.ltype, googleCoverSupp=config.mediaportal.simplelist_gcoversupp.value, embeddedCoverArt=True)
		else:
			self.keyCancel()

	def globalList(self):
		self.ltype = 'sl_glob_playlist'
		self['ContentTitle'].setText("Global Playlist-%02d" % self.playlist_num)
		self['F4'].show()
		self.filelist = SimplePlaylistIO.getPL('mp_global_pl_%02d' % self.playlist_num)
		if self.filelist == []:
			self.keyLocked = True
			self['F4'].hide()
			self.filelist.append((_("No entrys found!"), "", "dump"))
		else:
			self['F4'].show()
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.filelist))
		self['liste'].moveToIndex(0)

	def deleteEntry(self):
		if self.ltype != 'sl_glob_playlist' or not len(self.filelist):
			return
		idx = self['liste'].getSelectedIndex()
		SimplePlaylistIO.delEntry('mp_global_pl_%02d' % self.playlist_num, self.filelist, idx)
		self.ml.setList(map(self._defaultlistleft, self.filelist))

	def loadM3UList(self, m3ufile):
		self.ltype = 'sl_m3ulist'
		self.m3u_title = m3ufile.split('/')[-1]
		self['ContentTitle'].setText(self.m3u_title)
		self['F4'].show()
		self.filelist = []
		extm3u = extinf = False
		self.sp_option = title = path = ""
		try:
			with open(m3ufile, "rU") as inf:
				for line in inf:
					line = line.strip()
					if not extm3u and '#EXTM3U' in line:
						extm3u = True
						if '$MODE' in line:
							self.sp_option = line.split('=')[-1].strip()

						if self.sp_option != "IPTV":
							self.sp_option = "MP3"
					elif  extm3u and not extinf and line.startswith('#EXTINF:'):
						extinf = True
						m = re.search('\s*[-]*\d+(,|\s)(.+)', line[8:])
						if m:
							title = m.group(2).split(',')[-1].strip()
					elif extm3u and extinf and line:
						path = line

					if extinf and path:
						self.filelist.append((title, path, ''))
						title = path = ""
						extinf = False
		except IOError, e:
			printl(e,self,'E')

		if self.filelist == []:
			self.keyLocked = True
			self['F4'].hide()
			self.filelist.append((_("No entrys found!"), "", "dump"))
		else:
			self['F4'].show()
			self.keyLocked = False

		self.ml.setList(map(self._defaultlistleft, self.filelist))
		self['liste'].moveToIndex(0)

	def keyMenu(self):
		self.session.open(SimplelistConfig)

	def keyOK(self):
		if self.keyLocked:
			return
		if self.menu_level == 1:
			if self.ltype == 'sl_glob_playlist':
				idx = self['liste'].getSelectedIndex()
				self.session.open(SimplePlayer, [], playIdx=idx, playList2=self.filelist, plType='global', ltype=self.ltype, playAll=True, googleCoverSupp=config.mediaportal.simplelist_gcoversupp.value, useResume=False)
			elif self.ltype == 'sl_m3ulist':
				idx = self['liste'].getSelectedIndex()
				force_hls_player = config.mediaportal.use_hls_proxy.value or self.filelist[idx][1].startswith('newtopia-stream')
				if force_hls_player and ('.m3u8' in self.filelist[idx][1])>0:
					if not config.mediaportal.use_hls_proxy.value:
						self.session.open(MessageBoxExt, _("If you want to play this stream, you have to activate the HLS-Player in the MP-Setup"), MessageBoxExt.TYPE_INFO)
						return
				if ('X-Forwarded-For=' in self.filelist[idx][1])>0:
					if not config.mediaportal.use_hls_proxy.value:
						self.session.open(MessageBoxExt, _("If you want to play this stream, you have to activate the HLS-Player in the MP-Setup"), MessageBoxExt.TYPE_INFO)
						return

				self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
				self.session.openWithCallback(self.restoreLastService, SimplePlayer, self.filelist, playIdx=idx, ltype=self.ltype, playAll=True, googleCoverSupp=config.mediaportal.simplelist_gcoversupp.value, useResume=False, listTitle=self.m3u_title, playerMode=self.sp_option)
		else:
			self['F1'].setText(_("Return"))
			self.last_menu_idx = self['liste'].getSelectedIndex()
			sel = self['liste'].getCurrent()[0][0]
			title = self['liste'].getCurrent()[0][1]
			self['ContentTitle'].setText(title)
			self.menu_level = 1
			if sel == '1':
				self.loadFileList()
			elif sel == '3':
				fpath = self['liste'].getCurrent()[0][2]
				self.loadM3UList(fpath)
			else:
				self.playlist_num = self['liste'].getCurrent()[0][2]
				self.globalList()

	def _onClose(self):
		config.movielist.last_videodir.value = self.last_videodir

	def keyCancel(self):
		if self.menu_level == 0:
			self.close()
		else:
			self['F1'].setText(_("Exit"))
			self.menu_level = 0
			self.keyLocked = False
			self.ltype = ''
			self['F4'].hide()
			self['ContentTitle'].setText(_('List overview'))
			self.ml.setList(map(self.simplelistListEntry, self.genreliste))
			self['liste'].moveToIndex(self.last_menu_idx)

	def restoreLastService(self):
		if config.mediaportal.restorelastservice.value == "1" and not config.mediaportal.backgroundtv.value:
			self.session.nav.playService(self.lastservice)

class SimplelistConfig(Screen, ConfigListScreenExt):

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
		self['title'] = Label(_("SimpleList Configuration"))
		self.list = []
		self.list.append(getConfigListEntry(_('Global playlist number'), config.mediaportal.sp_pl_number))
		self.list.append(getConfigListEntry(_('Google coversupport'), config.mediaportal.simplelist_gcoversupp))
		ConfigListScreenExt.__init__(self, self.list)
		self['setupActions'] = ActionMap(['MP_Actions'],
		{
			'ok': 		self.keySave,
			'cancel': 	self.keyCancel
		},-2)