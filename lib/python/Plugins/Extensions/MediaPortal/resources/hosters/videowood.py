# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def videowood(self, data):
	stream_url = re.search('file: (\'|")(.*?.mp4)(\'|")', data)
	if stream_url:
		self._callback(stream_url.group(2))
	else:
		self.stream_not_found()