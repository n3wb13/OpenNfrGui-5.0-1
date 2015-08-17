# -*- coding: utf-8 -*-
#    HLS-Player for MediaPortal
#
#    Copyright (c) 2015 Billy2011, MediaPortal Team
#
# Copyright (C) 2009-2010 Fluendo, S.L. (www.fluendo.com).
# Copyright (C) 2009-2010 Marc-Andre Lureau <marcandre.lureau@gmail.com>
# Copyright (C) 2010 Zaheer Abbas Merali  <zaheerabbas at merali dot org>
# Copyright (C) 2010 Andoni Morales Alastruey <ylatuya@gmail.com>
# Copyright (C) 2014 Juan Font Alonso <juanfontalonso@gmail.com>

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE" in the source distribution for more information.

import os
import argparse

from twisted.web import server, resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import reactor, defer
from twisted.web.client import getPage

from fetcher import HLSFetcher
from m3u8 import M3U8

from Components.config import config
from enigma import eBackgroundFileEraser, iPlayableService, eTimer
import mp_globals
import simpleplayer
from simpleplayer import SimplePlayer
from debuglog import printlog as printl
from messageboxext import MessageBoxExt
#from Screens.MessageBox import MessageBox as MessageBoxExt
from utopialink import UtopiaLink
from httpplayer import GSTPlayer

class HLSControler:

	def __init__(self, fetcher=None):
		self.fetcher = fetcher
		self.player = None
		self._check_playing = False

		self._player_sequence = None
		self._n_segments_keep = None
		self.checkTimer = eTimer()
		if mp_globals.isDreamOS:
			self.checkTimer_conn = self.checkTimer.timeout.connect(self.checkPlaying)
		else:
			self.checkTimer.callback.append(self.checkPlaying)

	def set_player(self, player):
		self.player = player
		if player:
			self.player.connect_about_to_finish(self.on_player_about_to_finish)
			self.player.connect_about_to_play(self.on_player_about_to_play)
			self._n_segments_keep = self.fetcher.n_segments_keep

	def _start(self, first_file):
		(path, l, f) = first_file
		self._player_sequence = f['sequence']
		if self.player:
			self.player.set_uri((path, False))
			self.player.play()

	def start(self):
		if self.fetcher:
			d = self.fetcher.start()
			d.addCallback(self._start)

	def _set_next_uri(self):
		if self._n_segments_keep != -1:
			self.fetcher.delete_cache(lambda x:
				x <= self._player_sequence - self._n_segments_keep)
		self._player_sequence += 1
		d = self.fetcher.get_file(self._player_sequence)
		d.addCallback(self.player.set_uri)

	def on_player_about_to_finish(self):
		reactor.callLater(0, self._set_next_uri)

	def clientFinished(self, result, err=False):
		self._check_playing = True
		self.player.stop()
		self.checkTimer.start(5000, True)

	def on_player_about_to_play(self):
		self._check_playing = False

	def checkPlaying(self):
		if self._check_playing:
			if self.player:
				if (not self.player._playing and not self.player._seeking) or not self.player._request:
					self.fetcher.stop()
					self.player.finishPlayer(self.player._request)
					self.player = None
			elif self.fetcher:
				self.fetcher.stop()

class HLSProxy(resource.Resource):
	isLeaf = True
	players = {}

	def render_GET(self, request):
		options = self.getOptions(request)
		d = defer.succeed(request)
		d.addCallback(self.getUrl, options)
		if 'uid' in request.args:
			uuid = request.args['uid'][0]
			if len(uuid) != 36: uuid = None
		else:
			uuid = None
		d.addCallback(self.setupHLSPlayer, uuid, request, options)
		d.addErrback(self.reqError, request)
		return NOT_DONE_YET

	def setupHLSPlayer(self, url, uuid, request, options):
		if uuid and url:
			if not self.players.has_key(uuid):
				self.players.clear()
				c = HLSControler(HLSFetcher(url, options=options))
				p = GSTPlayer(request, keep=options.get('keep',3))
				self.players[uuid] = p
				p_infos = {}
				p_infos['controller'] = c
				p_infos['seek_cache'] = []
				p.initProxyInfos(p_infos)
				request.notifyFinish().addCallback(c.clientFinished).addErrback(c.clientFinished, True)
				c.set_player(p)
				c.start()
			else:
				p = self.players[uuid]
				request.setHeader('Content-Type', 'video/MP4')
				request.notifyFinish().addCallback(p._proxy_infos['controller'].clientFinished).addErrback(p._proxy_infos['controller'].clientFinished, True)
				p.doSeek(request)
		else:
			raise Exception("No HLS-URL or UID in request args!")

	def getOptions(self, request):
		options = {}
		if 'bitrate' in request.args:
			options['bitrate'] = int(request.args['bitrate'][0])
		if 'path' in request.args:
			options['path'] = request.args['path'][0]
		if 'referer' in request.args:
			options['referer'] = request.args['referer'][0]
		if 'keep' in request.args:
			options['keep'] = int(request.args['keep'][0])
		if 'buffer' in request.args:
			options['buffer'] = int(request.args['buffer'][0])
		return options

	def getUrl(self, request, options):
		try:
			url = request.args['url'][0]
		except:
			raise Exception('No HLS-URL in request args!')
		else:
			return url

	def reqError(self, err, request):
		printl('[HLSProxy] Error:\n'+str(err),self,'E')
		if not request._disconnected:
			request.setResponseCode(400)
			request.write(str(err))
			request.finish()
		return NOT_DONE_YET

site = server.Site(HLSProxy())
server_port = None

def start_hls_proxy():
	global server_port
	if server_port == None:
		server_port = reactor.listenTCP(config.mediaportal.hls_proxy_port.value, site)
		mp_globals.hls_proxy_port = server_port.getHost().port
		print 'Started HLS-Proxy on port '+str(mp_globals.hls_proxy_port)