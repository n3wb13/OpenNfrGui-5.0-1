# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def openload(self, data):
	stream_url = re.search('video\ssource.*?"src",\s"(.*?)\?', data)
	if not stream_url:
		stream_url = re.search('<source.*?src=.(.*?)\?', data)
	if stream_url:
		url = urllib.unquote(stream_url.group(1)).replace('\/', '/')
		self._callback(url)
	else:
		self.stream_not_found()