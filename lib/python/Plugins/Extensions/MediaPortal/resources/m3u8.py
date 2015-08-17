# -*- coding: utf-8 -*-
#
#    Copyright (c) 2015 Billy2011, MediaPortal Team
#
# Copyright (C) 2009-2010 Fluendo, S.L. (www.fluendo.com).
# Copyright (C) 2009-2010 Marc-Andre Lureau <marcandre.lureau@gmail.com>

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE" in the source distribution for more information.

import logging
import re
import urllib2
import urlparse
import os
import math

try:
	from debuglog import printlog as printl
	from make_url import make_url
except:
	isDream = False
else:
	isDream = True

class M3U8(object):

	def __init__(self, url=None, cookies=None):
		self.url = url
		self._cookies = cookies

		self._programs = []			# main list of programs & bandwidth
		self._files = {} 			# the current program playlist
		self._first_sequence = None	# the first sequence to start fetching
		self._last_sequence = None	# the last sequence, to compute reload delay
		self._reload_delay = 5		# the initial reload delay
		self._update_tries = None	# the number consecutive reload tries
		self._last_content = None
		self._endlist = False		# wether the list ended and should not be refreshed
		self.target_duration = None
		self.has_new_files = False
		self._encryption_method = None
		self._key_url = None
		self._key = None
		self._iv = None
		self._end_sequence = None
		self._newctr = 0


	def endlist(self):
		return self._endlist

	def has_programs(self):
		return len(self._programs) != 0

	def get_target_dura(self):
		return self.target_duration

	def get_program_playlist(self, program_id=None, bitrate=None):
		# return the (uri, dict) of the best matching playlist
		if not self.has_programs():
			raise Exception('PL has not programs!')

		_, best = min((abs(int(x['BANDWIDTH']) - bitrate), x)
				for x in self._programs)
		return best['uri'], best

	def reload_delay(self):
		# return the time between request updates, in seconds
		if self._endlist or not self._last_sequence:
			raise Exception('ELST or nor LSEQ')

		if self._update_tries == 0:
			ld = self._files[self._last_sequence]['duration']
			self._reload_delay = min(self.target_duration * 3, ld)
			d = self._reload_delay
		elif self._update_tries == 1:
			d = self._reload_delay * 0.5
		elif self._update_tries == 2:
			d = self._reload_delay * 1.5
		else:
			d = self._reload_delay * 3.0

		return int(d)

	def has_files(self):
		return len(self._files) != 0

	def iter_files(self):
		# return an iter on the playlist media files
		if not self.has_files():
			return

		if not self._endlist:
			current = max(self._first_sequence, self._last_sequence - 3)
		else:
			# treat differently on-demand playlists?
			current = self._first_sequence

		while True:
			try:
				f = self._files[current]
				current += 1
				yield f
				if (f.has_key('endlist')):
					break
			except:
				yield None

	def update(self, content):
		# update this "constructed" playlist,
		# return wether it has actually been updated
		self.has_new_files = False
		if self._last_content and content == self._last_content:
			self._update_tries += 1
			return False

		self._update_tries = 0
		self._last_content = content

		def get_lines_iter(c):
			c = c.decode("utf-8-sig")
			for l in c.split('\n'):
				if l.startswith('#EXT'):
					yield l
				elif l.startswith('#'):
					pass
				else:
					yield l

		self._lines = get_lines_iter(content)
		first_line = self._lines.next()
		if not first_line.startswith('#EXTM3U'):
			printl('Invalid first line:\n%r' % content,self,'E')
			raise Exception('Invalid first line: %r' % first_line)

		self.target_duration = None
		discontinuity = False
		allow_cache = None
		i = 0
		for l in self._lines:
			if l.startswith('#EXT-X-STREAM-INF'):
				def to_dict(l):
					i = re.findall('(?:[\w-]*="[\w\.\,]*")|(?:[\w-]*=[\w]*)', l)
					d = {v.split('=')[0]: v.split('=')[1].replace('"','') for v in i}
					return d
				d = to_dict(l[18:])
				uri = self._lines.next()
				if uri.startswith('./'): uri = uri[2:]
				d['uri'] = uri
				self._add_playlist(d)
			elif l.startswith('#EXT-X-TARGETDURATION'):
				self.target_duration = int(l[22:])
			elif l.startswith('#EXT-X-MEDIA-SEQUENCE'):
				self.media_sequence = int(l[22:])
				i = self.media_sequence
			elif l.startswith('#EXT-X-DISCONTINUITY'):
				discontinuity = True
			elif l.startswith('#EXT-X-PROGRAM-DATE-TIME'):
				print l
			elif l.startswith('#EXT-X-BYTE-SIZE'):
				print l
			elif l.startswith('#EXT-X-BYTERANGE'):
				print l
			elif l.startswith('#EXT-X-ALLOW-CACHE'):
				allow_cache = l[19:]
			elif l.startswith('#EXT-X-KEY'):
				i = l[18:].find(',')
				if i > 0:
					self._encryption_method = l[18:18+i].strip()
				else:
					raise Exception("No Encryption method found")

				i=l.find('URI="')
				if i > 0:
					j=l[i+5:].find('"')
					self._key_url = l[i+5:j+i+5]

					j += i+5
					i=l[j:].find('IV=')
					if i > 0:
						self._iv = l[j+i+5:-1].strip().decode("hex")

					url = make_url(self.url, self._key_url)
					opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cookies))
					response = opener.open(url)
					self._key = response.read()
					response.close()
				elif self._encryption_method != 'NONE':
					raise Exception("No Encryption Key-URI found")
			elif l.startswith('#EXTINF'):
				v = l[8:].split(',')
				while True:
					f = self._lines.next().strip()
					if not f.startswith('#'):
						break
				if f.startswith('./'): f = f[2:]
				d = dict(file=f,
						title=v[1].strip(),
						duration=math.trunc(float(v[0])),
						sequence=i,
						discontinuity=discontinuity,
						allow_cache=allow_cache)
				discontinuity = False
				i += 1
				self._set_file(i, d)
				if i > self._last_sequence:
					self._last_sequence = i
			elif l.startswith('#EXT-X-ENDLIST'):
				if i > 0:
					self._files[i]['endlist'] = True
				self._endlist = True
				self._end_sequence = self._last_sequence - 1
				print l
			elif len(l.strip()) != 0:
				print l

		if not self.has_programs() and not self.target_duration:
			raise Exception("Invalid HLS stream: no programs & no duration")

		return True

	def _add_playlist(self, d):
		self._programs.append(d)

	def _set_file(self, sequence, d):
		if not self._files.has_key(sequence):
			self._newctr += 1
		if not self._first_sequence:
			self._first_sequence = sequence
		elif sequence < self._first_sequence:
			self._first_sequence = sequence
		self._files[sequence] = d

	def __repr__(self):
		return "M3U8 %r %r" % (self._programs, self._files)
