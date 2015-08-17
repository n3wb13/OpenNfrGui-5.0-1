# -*- coding: utf-8 -*-

from imports import *

class SongstoLink:
	def __init__(self, session):
		self.session = session
		self._callback = None
		self._errback = None
		self._baseurl = "http://s.songs.to/data.php?id="
		self.imgurl = ''

	def getLink(self, cb_play, cb_err, sc_title, sc_artist, sc_album, token, imgurl):
		self._callback = cb_play
		self._errback = cb_err
		self.imgurl = imgurl
		if token != '':
			scStream = self._baseurl+token
			self._callback(sc_title, scStream, album=sc_album, artist=sc_artist, imgurl=imgurl)
		else:
			title = urllib2.quote(sc_title.encode("utf8"))
			artist = urllib2.quote(sc_artist.encode("utf8"))
			url = "http://songs.to/json/songlist.php?quickplay=1"
			dataPost = "data=%7B%22data%22%3A%5B%7B%22artist%22%3A%22"+artist+"%22%2C%20%22album%22%3A%22%22%2C%20%22title%22%3A%22"+title+"%22%7D%5D%7D"
			getPage(url, method='POST', postdata=dataPost, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.scDataPost).addErrback(cb_err)

	def scDataPost(self, data):
		m = re.search('"hash":"(.*?)","title":"(.*?)","artist":"(.*?)","album":"(.*?)".*?"cover":"(.*?)"', data)
		if m:
			(scHash, scTitle, scArtist, scAlbum, scCover) = (m.group(1), m.group(2), m.group(3), m.group(4), m.group(5))

			if scHash:
				scStream = self._baseurl+scHash
				self._callback(scTitle, scStream, album=scAlbum, artist=scArtist, imgurl=scCover)
			else:
				self._errback('scHash not found!')
		else:
			m = re.search('"hash":"(.*?)","title":"(.*?)","artist":"(.*?)","album":"(.*?)"', data)
			if m:
				(scHash, scTitle, scArtist, scAlbum) = (m.group(1), m.group(2), m.group(3), m.group(4))

				if scHash:
					found = True
					scStream = self._baseurl+scHash
					self._callback(scTitle, scStream, album=scAlbum, artist=scArtist, imgurl=self.imgurl)
				else:
					self._errback('scHash not found!')
			else:
				self._errback('Song not found!')