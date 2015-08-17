# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def go180upload(self, data):
	url = None
	get_packedjava = re.findall("<script type=.text.javascript.>(eval.function.*?)</script>", data, re.S)
	if get_packedjava:
		sJavascript = get_packedjava[1]
		sUnpacked = unpack(sJavascript)
		if sUnpacked:
			stream_url = re.search('param\sname="src"value="(.*?)"/>', sUnpacked, re.S)
			if stream_url:
				url = stream_url.group(1)
			else:
				stream_url = re.search('file.\',.\'(.*?).\'\)', sUnpacked)
				if stream_url:
					url = stream_url.group(1)
	if url:
		self._callback(url)
	else:
		self.stream_not_found()