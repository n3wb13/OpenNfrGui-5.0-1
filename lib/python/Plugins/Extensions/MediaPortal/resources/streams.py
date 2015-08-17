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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
from imports import *
import mp_globals
from keyboardext import VirtualKeyBoardExt
from userporn import Userporn
from firedriveshared import FirediveFilmScreen
from packer import unpack, detect
from jsunpacker import cJsUnpacker
from debuglog import printlog as printl
from messageboxext import MessageBoxExt

# cookies
ck = {}
cj = {}
rdbcookies = {}
timeouttime = 15

def isSupportedHoster(linkOrHoster, check=False):
	if not check:
		return False
	if not linkOrHoster:
		return False

	printl("check hoster: %s" % linkOrHoster,'',"S")

	host = linkOrHoster.lower().strip()
	if re.search(mp_globals.hosters[0], host):
		printl("match1: %s" % linkOrHoster,'',"H")
		return True
	elif re.search(mp_globals.hosters[1], host):
		printl("match2: %s" % linkOrHoster,'',"H")
		return True

	printl("hoster not supported",'',"W")
	return False

class get_stream_link:

	# hosters
	from hosters.auengine import auengine
	from hosters.bestreams import bestreams, bestreamsCalllater, bestreamsPostData
	from hosters.bitshare import bitshare, bitshare_start
	from hosters.cloudyvideos import cloudyvideos, cloudyvideosGetPage, cloudyvideos_postData, cloudyvideosEmbed, cloudyvideos_postDataEmbed
	from hosters.cloudzilla import cloudzilla
	from hosters.divxpress import divxpress, divxpressPostdata
	from hosters.epornik import epornik
	from hosters.exashare import exashare
	from hosters.faststream import faststream
	from hosters.filehoot import filehoot
	from hosters.firedrive import firedrive, firedriveData
	from hosters.flashx import flashx, flashxSmilData
	from hosters.flyflv import flyflv, flyflvData
	from hosters.go180upload import go180upload
	from hosters.google import google
	from hosters.ilook import ilook
	from hosters.kodik import kodik, kodikData
	from hosters.letwatch import letwatch
	from hosters.mooshare import mooshare
	from hosters.movshare import movshare, movshare_code1, movshare_base36decode, movshare_xml
	from hosters.mp4upload import mp4upload
	from hosters.mrfile import mrfile
	from hosters.one_two_three_stream import one_two_three_stream
	from hosters.openload import openload
	from hosters.powerwatch import powerwatch, powerwatchGetPage, powerwatch_postData
	from hosters.powvideo import powvideo
	from hosters.rapidvideo import rapidvideo
	from hosters.realvid import realvid
	from hosters.sharesix import sharesix
	from hosters.streamin import streamin
	from hosters.streamit import streamit
	from hosters.thefile import thefile
	from hosters.thevideo import thevideo
	from hosters.trollvid import trollvid
	from hosters.videonest import videonest
	from hosters.videowood import videowood
	from hosters.vidbull import vidbull
	from hosters.vidspot import vidspot
	from hosters.vidwoot import vidwoot
	from hosters.vivo import vivo, vivoPostData
	from hosters.vkme import vkme
	from hosters.videomega import videomega
	from hosters.vidxden import vidxden, vidxdenPostdata
	from hosters.vidto import vidto
	from hosters.vodlocker import vodlocker, vodlockerGetPage, vodlockerData
	from hosters.yourupload import yourupload
	from hosters.zettahost import zettahost

	def __init__(self, session):
		self._callback = None
		self.session = session
		self.showmsgbox = True
		useProxy = config.mediaportal.premiumize_use.value
		self.puser = config.mediaportal.premiumize_username.value
		self.ppass = config.mediaportal.premiumize_password.value
		self.ruser = config.mediaportal.realdebrid_username.value
		self.rpass = hashlib.md5(config.mediaportal.realdebrid_password.value).hexdigest()
		self.papiurl = "http://api.premiumize.me/pm-api/v1.php?method=directdownloadlink&params[login]=%s&params[pass]=%s&params[link]=" % (self.puser, self.ppass)
		self.rapiurl = "https://real-debrid.com/ajax/login.php?user=%s&pass=%s" % (self.ruser, self.rpass)
		self.rdb = 0
		self.prz = 0

		self.data_p = None
		self.vidplay_url = None
		self.hugekey = None

	def callPremium(self, link):
		if self.prz == 1 and config.mediaportal.premiumize_use.value:
			getPage(self.papiurl+link).addCallback(self.papiCallback, link).addErrback(self.errorload)
		elif self.rdb == 1 and config.mediaportal.realdebrid_use.value:
			getPage(self.rapiurl, cookies=rdbcookies).addCallback(self.rapiCallback, link).addErrback(self.errorload)

	def rapiCallback(self, data, link):
		if re.search('"error":0,', data):
			url = "https://real-debrid.com/ajax/unrestrict.php?link=%s" % link
			getPage(url, cookies=rdbcookies, timeout=15).addCallback(self.rapiCallback2, link).addErrback(self.errorload)
		elif re.search('"error":1,', data):
			self.session.open(MessageBoxExt, _("Real-Debrid.com: Your login informations are incorrect!"), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('"error":2,', data):
			self.session.open(MessageBoxExt, _("Real-Debrid.com: Suspended / not activated account!"), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('"error":3,', data):
			self.session.open(MessageBoxExt, _("Real-Debrid.com: Too many failed logins!"), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('"error":4,', data):
			self.session.open(MessageBoxExt, _("Real-Debrid.com: Incorrect captcha answer!"), MessageBoxExt.TYPE_INFO, timeout=3)

	def rapiCallback2(self, data, link):
		if re.search('"error":0,', data):
			stream_url = re.findall('main_link":"(.*?)"', data, re.S|re.I)
			if stream_url:
				mp_globals.realdebrid = True
				mp_globals.premiumize = False
				self._callback(stream_url[0].replace('\\',''))
			else:
				self.stream_not_found()
		elif self.prz == 1 and config.mediaportal.premiumize_use.value:
			self.rdb = 0
			getPage(self.papiurl+link).addCallback(self.papiCallback, link).addErrback(self.errorload)
		elif re.search('"error":2,', data):
			self.session.open(MessageBoxExt, _("Real-Debrid.com: Upgrade your account now to generate a link!"), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('"error":4,', data):
			self.session.open(MessageBoxExt, _("Real-Debrid.com: Hoster is not supported or link format not recognized!"), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('"error":6,', data):
			self.session.open(MessageBoxExt, _("Real-Debrid.com: Daily limit reached!"), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('"error":9,', data):
			self.session.open(MessageBoxExt, _("Real-Debrid.com: No server is available for this hoster!"), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('"error":11,', data):
			self.session.open(MessageBoxExt, _("Real-Debrid.com: Your file is unavailable on the hoster!"), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.stream_not_found()

	def papiCallback(self, data, link):
		if re.search('status":200', data):
			stream_url = re.findall('"stream_location":"(.*?)"', data, re.S|re.I)
			if not stream_url:
				stream_url = re.findall('"location":"(.*?)"', data, re.S|re.I)
			if stream_url:
				mp_globals.premiumize = True
				mp_globals.realdebrid = False
				self._callback(stream_url[0].replace('\\',''))
			else:
				self.stream_not_found()
		elif self.rdb == 1 and config.mediaportal.realdebrid_use.value:
			self.prz = 0
			getPage(self.rapiurl, cookies=rdbcookies).addCallback(self.rapiCallback, link).addErrback(self.errorload)
		elif re.search('status":400', data):
			message = self.session.open(MessageBoxExt, _("premiumize: No valid link."), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('status":401', data):
			message = self.session.open(MessageBoxExt, _("premiumize: Login failed."), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('status":402', data):
			message = self.session.open(MessageBoxExt, _("premiumize: You are no Premium-User."), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('status":403', data):
			message = self.session.open(MessageBoxExt, _("premiumize: No Access."), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('status":404', data):
			message = self.session.open(MessageBoxExt, _("premiumize: File not found."), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('status":428', data):
			message = self.session.open(MessageBoxExt, _("premiumize: Hoster currently not available."), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('status":502', data):
			message = self.session.open(MessageBoxExt, _("premiumize: Unknown technical error."), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('status":503', data):
			message = self.session.open(MessageBoxExt, _("premiumize: Temporary technical error."), MessageBoxExt.TYPE_INFO, timeout=3)
		elif re.search('status":509', data):
			message = self.session.open(MessageBoxExt, _("premiumize: Fair use limit exhausted."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.stream_not_found()

	def check_link(self, data, got_link, showmsgbox=True):
		print "check_link"
		self._callback = got_link
		self.showmsgbox = showmsgbox
		if data:
			if re.search("http://.*?putlocker.com/(file|embed|get)/", data, re.S):
				link = data.split('/')[-1]
				if link:
					link = 'http://www.firedrive.com/file/%s' % link
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.firedrive, link).addErrback(self.errorload)

			elif re.search("http://.*?firedrive.com/share/", data, re.S):
				link = data
				self.session.open(FirediveFilmScreen, link, self.check_link, self._callback)

			elif re.search("http://.*?firedrive.com/(file|embed)/", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.firedrive, link).addErrback(self.errorload)

			elif re.search("http://.*?sockshare.com/(file|embed)/", data, re.S | re.I):
				link = data.replace('file','embed')
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.streamPutlockerSockshare, link, "sockshare").addErrback(self.errorload)

			elif re.search("http://streamcloud.eu/", data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value:
					link = re.search("(http://streamcloud.eu/\w+)", data, re.S)
					if link:
						link = link.group(1)
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					getPage(link, cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.streamcloud).addErrback(self.errorload)

			elif re.search('rapidgator.net|rg.to', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('depositfiles.com|dfiles.eu', data, re.S):
				link = data.replace("dfiles.eu", "depositfiles.com")
				if config.mediaportal.premiumize_use.value:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('filepost.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('turbobit.net', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('4shared.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('shareflare.net', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('vip-file.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('uptobox.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('filerio.com|filerio.in', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('depfile.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('uploadto.us|ultramegabit.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('filer.net', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('extmatrix.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('datafile.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('hugefiles.net', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('filefactory.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('gigapeta.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 0
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('salefiles.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('kingfiles.net', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('speedyshare.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('uploadable.ch', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 0
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('oboom.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('uploaded.net|uploaded.to|ul.to', data, re.S):
				link = data
				if config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('1fichier.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('letitbit.net', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('nowvideo', data, re.S):
				if re.search('embed.nowvideo.', data, re.S):
					ID = re.search('http://embed.nowvideo.\w+/embed.php.*?[\?|&]v=(\w+)', data, re.S)
					if ID:
						data = 'http://www.nowvideo.sx/video/' + ID.group(1)
				link = data
				#print link
				if config.mediaportal.premiumize_use.value:
					getPage(self.papiurl+link).addCallback(self.papiCallback, link).addErrback(self.errorload)
				else:
					getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.movshare, link, "nowvideo").addErrback(self.errorload)

			elif re.search('videoweed.es', data, re.S):
				link = data
				#print link
				if config.mediaportal.premiumize_use.value:
					getPage(self.papiurl+link).addCallback(self.papiCallback, link).addErrback(self.errorload)
				else:
					getPage(link, cookies=cj, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.movshare, link, "videoweed").addErrback(self.errorload)

			elif re.search('novamov.com', data, re.S):
				link = data
				#print link
				if config.mediaportal.premiumize_use.value:
					getPage(self.papiurl+link).addCallback(self.papiCallback, link).addErrback(self.errorload)
				else:
					getPage(link, cookies=cj, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.movshare, link, "novamov").addErrback(self.errorload)

			elif re.search('movshare.net', data, re.S):
				link = data
				#print link
				getPage(link, cookies=cj, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.movshare, link, "movshare").addErrback(self.errorload)

			elif re.search('http://.*?bitshare.com', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.bitshare).addErrback(self.errorload)

			elif re.search('http://.*?purevid.com', data, re.S):
				link = data
				if config.mediaportal.premiumize_use.value or config.mediaportal.realdebrid_use.value:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)

			elif re.search('http://xvidstage.com', data, re.S):
				link = data
				#print "xvidstage"
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.xvidstage_post, link).addErrback(self.errorload)

			elif re.search('http://filenuke.com', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.filenuke, link).addErrback(self.errorload)

			elif re.search('http://movreel.com/', data, re.S):
				link = data
				#print link
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.movreel_data, link).addErrback(self.errorload)

			elif re.search('epornik.com/', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.epornik).addErrback(self.errorload)

			elif re.search('http://xvidstream.net/', data, re.S):
				link = data
				#print link
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.xvidstream).addErrback(self.errorload)

#			elif re.search('http://.*?uploadc.com', data, re.S):
#				link = data
#				#print link
#				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.uploadc, link).addErrback(self.errorload)

			elif re.search('http://vreer.com', data, re.S):
				link = data
				#print link
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vreer, link).addErrback(self.errorload)

			elif re.search('flashstream.in', data, re.S):
				link = data
				#print link
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.flashstream).addErrback(self.errorload)

			elif re.search('(divxstage|cloudtime)', data, re.S):
				link = data
				#print link
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.movshare, link, "cloudtime").addErrback(self.errorload)

			elif re.search('(faststream|fastvideo)', data, re.S):
				if re.search('(faststream|fastvideo)\.in/embed', data, re.S):
					link = data
				else:
					id = re.search('(faststream|fastvideo)\.in/(\w+)', data)
					if id:
						link = "http://%s.in/embed-%s-720x480.html" % (id.group(1), id.group(2))
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.faststream).addErrback(self.errorload)

			elif re.search('primeshare', data, re.S):
				link = data
				#print link
				getPage(link, cookies=cj, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.primeshare, link).addErrback(self.errorload)

			elif re.search('http://vidstream.in', data, re.S):
				link = data
				#print link
				getPage(link, cookies=cj, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vidstream_in, link).addErrback(self.errorload)

			elif re.search('video.istream.ws/embed', data, re.S):
				link = data
				#print link
				getPage(link, cookies=cj, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.check_istream_link).addErrback(self.errorload)

			elif re.search('http:/.*?flashx.tv', data, re.S):
				if re.search('flashx.tv/embed', data, re.S):
					link = data
				else:
					id = re.search('flashx.tv/(dl\?|)(.*?)($|\.html)', data)
					if id:
						link = "http://flashx.tv/embed-%s-640x468.html" % id.group(2)
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.flashx).addErrback(self.errorload)

			elif re.search('sharesix.com/', data, re.S):
				link = data
				post_data = urllib.urlencode({'method_free': 'Free'})
				postagent = 'Enigma2 Mediaplayer'
				mp_globals.player_agent = postagent
				getPage(link, method='POST', postdata=post_data, agent=postagent , headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.sharesix).addErrback(self.errorload)

			elif re.search('userporn.com', data, re.S):
				link = data
				#print link
				self.userporn_tv(link)

			elif re.search('ecostream.tv', data, re.S):
				link = data
				getPage(link, cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.eco_read, link).addErrback(self.errorload)

			elif re.search('http://(www\.|)played.to', data, re.S):
				if re.search('http://(www\.|)played.to/embed', data, re.S):
					id = re.search('embed-(\w+)', data)
					if id:
						link = "http://played.to/%s" % id.group(1)
					else:
						self.stream_not_found()
				else:
					link = data
				getPage(link, cookies=cj, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.played, link).addErrback(self.errorload)

			elif re.search('stream2k.com', data, re.S):
				link = data
				getPage(link, headers={'referer':link}).addCallback(self.stream2k).addErrback(self.errorload)

			elif re.search('limevideo.net', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.lmv, link).addErrback(self.errorload)

			elif re.search('videomega.tv', data, re.S):
				link = data
				if re.search('iframe.php', link):
					twAgentGetPage(link, followRedirect=False, headers={'Accept': '*/*', 'Referer': 'http://videomega.tv'}).addCallback(self.videomega).addErrback(self.errorload)
				else:
					id = link.split('ref=')
					if id:
						link = "http://videomega.tv/iframe.php?ref=%s" % id[1]
						twAgentGetPage(link, followRedirect=False, headers={'Accept': '*/*', 'Referer': 'http://videomega.tv'}).addCallback(self.videomega).addErrback(self.errorload)
					else:
						self.stream_not_found()

			elif re.search('vk.com|vk.me', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vkme).addErrback(self.errorload)

			elif re.search('mightyupload.com/embed', data, re.S):
				link = data
				getPage(link, timeout=timeouttime, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.mightyupload).addErrback(self.errorload)

			elif re.search('mightyupload.com', data, re.S):
				link = data
				id = link.split('/')
				url = "http://www.mightyupload.com/embed-%s.html" % id[3]
				print url
				getPage(url, timeout=timeouttime, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.mightyupload).addErrback(self.errorload)

			elif re.search('http://youwatch.org', data, re.S):
				link = data
				id = link.split('org/')
				url = "http://youwatch.org/embed-%s.html" % id[1]
				getPage(url, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.youwatch).addErrback(self.errorload)

			elif re.search('vidx.to', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vidx, link).addErrback(self.errorload)

			elif re.search('allmyvideos.net', data, re.S):
				link = data
				if re.search('allmyvideos.net/embed', link, re.S):
					print "1"
					getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.allmyvids).addErrback(self.errorload)
				else:
					print "2"
					id = re.findall('allmyvideos.net/(.*?)$', link)
					if id:
						new_link = "http://allmyvideos.net/embed-%s.html" % id[0]
						getPage(new_link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.allmyvids).addErrback(self.errorload)
					else:
						self.stream_not_found()

			elif re.search('promptfile.com', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.promptfile, link).addErrback(self.errorload)

			elif re.search('mooshare.biz', data, re.S):
				link = data
				if re.search('mooshare\.biz/embed-', data, re.S):
					link = data
				else:
					id = re.search('mooshare\.biz/(\w+)', data)
					if id:
						link = "http://mooshare.biz/embed-%s-960x560.html?play=1&confirm=Close+Ad+and+Watch+as+Free+User" % id.group(1)
				getPage(link, headers={'Cache-Control':'max-age=0','Referer':link,'Host':'mooshare.biz','Accept-Language': 'en-US,en;q=0.5'}).addCallback(self.mooshare).addErrback(self.errorload)

			elif re.search("http://shared.sx", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.sharedsxData, link).addErrback(self.errorload)

			elif re.search("http://cloudyvideos.com", data, re.S):
				link = data
				if re.search('cloudyvideos.com/embed', link, re.S):
					id = re.search('embed-(.*?)-', link, re.S)
					link = 'http://cloudyvideos.com/' + id.group(1)
					#getPage(link, timeout=timeouttime, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.cloudyvideosEmbed, link).addErrback(self.errorload)
					getPage(link, timeout=timeouttime, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.cloudyvideos, link).addErrback(self.errorload)
				else:
					getPage(link, timeout=timeouttime, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.cloudyvideos, link).addErrback(self.errorload)

			elif re.search("auengine.com", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.auengine).addErrback(self.errorload)

			elif re.search("mp4upload.com", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.mp4upload).addErrback(self.errorload)

			elif re.search("videonest.net", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.videonest).addErrback(self.errorload)

			elif re.search("vidwoot.com", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vidwoot).addErrback(self.errorload)

			elif re.search("yourupload.com", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.yourupload).addErrback(self.errorload)

			elif re.search("trollvid.net", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.trollvid).addErrback(self.errorload)

			elif re.search("vidplay", data, re.S):
				link = data
				getPage(link, agent=mp_globals.std_headers, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vidplay_readPostData, link).addErrback(self.errorload)

			elif re.search("vidbull.com", data, re.S):
				id = re.search('/embed-(.*?)-', data, re.S)
				if not id:
					id = re.search('vidbull.com/(.*?)$', data, re.S)
				if id:
					link = 'http://www.vidbull.com/%s' % id.group(1)
					spezialagent = 'Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/BuildID) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'
					getPage(link, agent=spezialagent, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vidbull).addErrback(self.errorload)

			elif re.search("vodlocker.com", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vodlocker, link).addErrback(self.errorload)

			elif re.search('vidxden.com', data, re.S):
				if re.search('vidxden.com/embed', data, re.S):
					link = data
				else:
					id = re.findall('vidxden.com/(.*?)$', data)
					if id:
						link = "http://vidxden.com/embed-%s-width-653-height-362.html" % id[0]
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vidxden, link).addErrback(self.errorload)

			elif re.search("cloudzilla\.to", data, re.S):
				if re.search('cloudzilla\.to/embed', data, re.S):
					link = data
				else:
					id = data.split('/')[-1]
					if id:
						link = "http://cloudzilla.to/embed/%s" % id
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.cloudzilla).addErrback(self.errorload)

			elif re.search("180upload\.com", data, re.S):
				postpar = "fuief444"
				if re.search('/embed', data, re.S):
					link = data
					id = re.search('/embed-(.*?)-', link, re.S)
					if id:
						filecode = id.group(1)
				else:
					data = data.replace('http://','').replace('.html','')
					id = data.split('/')[1]
					if id:
						filecode = id
					link = "http://180upload.com/embed-%s-640x360.html" % id
				post_data = urllib.urlencode({'op' :'video_embed', 'file_code' : filecode, postpar : '5'})
				getPage(link, method='POST', postdata=post_data, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.go180upload).addErrback(self.errorload)

			elif re.search("mrfile\.me", data, re.S):
				if re.search('mrfile\.me/embed', data, re.S):
					link = data
				else:
					data = data.replace('http://','')
					id = data.split('/')[1]
					if id:
						link = "http://mrfile.me/embed-%s-645x353.html" % id
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.mrfile).addErrback(self.errorload)

			elif re.search("flyflv\.com", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.flyflv).addErrback(self.errorload)

			elif re.search("videowood\.tv", data, re.S):
				link = data
				if re.search('videowood\.tv/embed', data, re.S):
					link = data
				else:
					id = re.search('videowood\.tv/.*?/(\w+)', data)
					if id:
						link = "http://videowood.tv/embed/%s" % id.group(1)
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.videowood).addErrback(self.errorload)

			elif re.search("streamin\.to", data, re.S):
				if re.search('streamin\.to/embed', data, re.S):
					link = data
				else:
					data = data.replace('http://','')
					id = data.split('/')[1]
					if id:
						link = "http://streamin.to/embed-%s-640x360.html" % id
				spezialagent = 'Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/BuildID) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'
				getPage(link, cookies=ck,  agent=spezialagent, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.streamin).addErrback(self.errorload)

			elif re.search("123-stream\.eu", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.one_two_three_stream).addErrback(self.errorload)

			elif re.search("vivo.sx", data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vivo, link).addErrback(self.errorload)

			elif re.search("http://realvid\.net", data, re.S):
				if re.search('realvid\.net/embed', data, re.S):
					link = data
				else:
					id = re.findall('realvid\.net/(.*?)$', data)
					if id:
						link = "http://realvid.net/embed-%s.html" % id[0]
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.realvid).addErrback(self.errorload)

			elif re.search('bestreams\.net/', data, re.S):
				link = data
				getPage(link, cookies=ck, headers={'Accept-Language': 'en-US,en;q=0.5'}).addCallback(self.bestreams, link, ck).addErrback(self.errorload)

			elif re.search('thefile\.me/', data, re.S):
				if re.search('thefile\.me/embed-', data, re.S):
					link = data
				else:
					id = re.search('thefile\.me/(\w+)', data)
					if id:
						link = "http://thefile.me/embed-%s.html" % id.group(1)
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.thefile).addErrback(self.errorload)

			elif re.search('vidto\.me/', data, re.S):
				if re.search('vidto\.me/embed-', data, re.S):
					link = data
				else:
					id = re.search('vidto\.me/(\w+)', data)
					if id:
						link = "http://vidto.me/embed-%s-640x360.html" % id.group(1)
				ck.update({'referer':'%s' % link })
				getPage(link, cookies=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vidto).addErrback(self.errorload)

			elif re.search('vidspot\.net/', data, re.S):
				if re.search('vidspot\.net/embed', data, re.S):
					link = data
				else:
					id = re.findall('vidspot\.net/(.*?)$', data)
					if id:
						link = "http://vidspot.net/embed-%s.html" % id[0]
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vidspot).addErrback(self.errorload)

			elif re.search('zettahost\.tv/', data, re.S):
				if re.search('zettahost\.tv/embed-', data, re.S):
					link = data
				else:
					id = re.search('zettahost\.tv/(\w+)', data)
					if id:
						link = "http://zettahost.tv/embed-%s.html" % id.group(1)
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.zettahost).addErrback(self.errorload)

			elif re.search('streamit.to/', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.streamit).addErrback(self.errorload)

			elif re.search('kodik\.biz/', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.kodik).addErrback(self.errorload)

			elif re.search('docs\.google\.com/', data, re.S):
				link = data
				mp_globals.player_agent = 'Enigma2 Mediaplayer'
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.google).addErrback(self.errorload)

			elif re.search('rapidvideo\.ws', data, re.S):
				if re.search('rapidvideo\.ws/embed', data, re.S):
					link = data
				else:
					id = re.findall('rapidvideo\.ws/(.*?)$', data)
					if id:
						link = "http://rapidvideo.ws/embed-%s.html" % id[0]
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.rapidvideo).addErrback(self.errorload)

			elif re.search('powerwatch.pw', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.powerwatch, link).addErrback(self.errorload)

			elif re.search('ilook\.to', data, re.S):
				if re.search('ilook\.to.*?_embed.php', data, re.S):
					link = data
				else:
					id = re.findall('ilook\.to/(.*?)/', data)
					if id:
						link = "http://ilook.to/plugins/mediaplayer/site/_embed.php?u=%s&w=640&h=320" % id[0]
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.ilook).addErrback(self.errorload)

			elif re.search('vid\.gg', data, re.S):
				if re.search('vid\.gg/embed', data, re.S):
					link = data
				else:
					id = re.findall('vid\.gg/video/(.*?)$', data)
					if id:
						link = "http://www.vid.gg/embed/?id=%s" % id[0]
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.movshare, link, "vidgg").addErrback(self.errorload)

			elif re.search('openload\.io', data, re.S):
				link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.openload).addErrback(self.errorload)

			elif re.search('thevideo\.me', data, re.S):
				if re.search('thevideo\.me/embed-', data, re.S):
					link = data
				else:
					id = re.findall('thevideo\.me/(.*?)$', data)
					if id:
						link = "http://www.thevideo.me/embed-%s-640x360.html" % id[0]
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.thevideo).addErrback(self.errorload)

			elif re.search('exashare\.com', data, re.S):
				if re.search('exashare\.com/embed-', data, re.S):
					link = data
				else:
					id = re.findall('exashare\.com/(.*?)$', data)
					if id:
						link = "http://www.exashare.com/embed-%s-620x330.html" % id[0]
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.exashare).addErrback(self.errorload)

			elif re.search('letwatch\.us', data, re.S):
				if re.search('letwatch\.us/embed-', data, re.S):
					link = data
				else:
					id = re.findall('letwatch\.us/(.*?)$', data)
					if id:
						link = "http://letwatch.us/embed-%s-640x360.html" % id[0]
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.letwatch).addErrback(self.errorload)

			elif re.search('filehoot\.com', data, re.S):
				if re.search('filehoot\.com/embed', data, re.S):
					link = data
				else:
					id = re.search('filehoot\.com/(\w+)', data)
					if id:
						link = "http://filehoot.com/embed-%s-1046x562.html" % id.group(1)
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.filehoot).addErrback(self.errorload)

			elif re.search('powvideo\.net/', data, re.S):
				id = re.search('powvideo\.net/(embed-|)(\w+)', data)
				if id:
					referer = "http://powvideo.net/embed-%s-954x562.html" % id.group(2)
					link = "http://powvideo.net/iframe-%s-954x562.html" % id.group(2)
					getPage(link, headers={'Referer':referer, 'Accept-Language': 'en-US,en;q=0.5'}).addCallback(self.powvideo).addErrback(self.errorload)

			elif re.search('divxpress\.com', data, re.S):
				if re.search('divxpress\.com/embed', data, re.S|re.I):
					id = re.search('divxpress.com/embed-(.*?)-', data)
					if id:
						link = "http://www.divxpress.com/%s" % id.group(1)
				else:
					link = data
				getPage(link, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.divxpress, link).addErrback(self.errorload)

			else:
				message = self.session.open(MessageBoxExt, _("No supported Stream Hoster, try another one!"), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			message = self.session.open(MessageBoxExt, _("Invalid Stream link, try another Stream Hoster!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def stream_not_found(self):
		if self.showmsgbox:
			message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			self._callback(None)

	def sharedsxData(self, data, url):
		print 'data'
		p1 = re.search('type="hidden" name="hash".*?value="(.*?)"', data)
		p2 = re.search('type="hidden" name="expires".*?value="(.*?)"', data)
		p3 = re.search('type="hidden" name="timestamp".*?value="(.*?)"', data)
		if p1 and p2 and p3:
			info = urlencode({'hash': p1.group(1),
							'expires': p2.group(1),
							'timestamp': p3.group(1)})
			print info
			reactor.callLater(3, self.sharedsxCalllater, url, method='POST', cookies=ck, postdata=info,headers={'Content-Type':'application/x-www-form-urlencoded', 'Accept-Language': 'en-gb, en;q=0.9, de;q=0.8'})
			message = self.session.open(MessageBoxExt, _("Stream starts in 3 sec."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.stream_not_found()

	def sharedsxCalllater(self, *args, **kwargs):
		print "drin"
		getPage(*args, **kwargs).addCallback(self.sharedsxPostData).addErrback(self.errorload)

	def sharedsxPostData(self, data):
		print 'postdata'
		stream_url = re.search('data-url="(.*?)"', data)
		if stream_url:
			print stream_url
			self._callback(stream_url.group(1))
		else:
			self.stream_not_found()

	def promptfile(self, data, url):
		chash = re.findall('type="hidden" name="chash" value="(.*?)"', data, re.S)
		if chash:
			dataPost = {'chash': chash[0]}
			getPage(url, method='POST', postdata=urlencode(dataPost), headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.promptfilePost).addErrback(self.errorload)
		else:
			self.stream_not_found()

	def promptfilePost(self, data):
		stream_url = re.findall("url: '(.*?)'", data, re.S)
		if stream_url:
			self._callback(stream_url[0])
		else:
			self.stream_not_found()

	def allmyvids(self, data):
		print "drin"
		stream_url = re.findall('file"\s:\s"(.*?)",', data)
		if stream_url:
			print stream_url
			self._callback(stream_url[0])
		else:
			self.stream_not_found()

	def mixturecloud(self, data):
		file = re.findall("'file': '(.*?)'", data, re.S)
		streamer = re.findall("'streamer':'(.*?)'", data, re.S)
		if file and streamer:
			stream_url = "%s&file=%s" % (streamer[0], file[0])
			print stream_url
			self._callback(stream_url)
		else:
			self.stream_not_found()

	def vidx(self, data, url):
		op = re.findall('type="hidden" name="op".*?value="(.*?)"', data, re.S)
		id = re.findall('type="hidden" name="id".*?value="(.*?)"', data, re.S)
		fname = re.findall('type="hidden" name="fname".*?value="(.*?)"', data, re.S)
		referer = re.findall('type="hidden" name="referer".*?value="(.*?)"', data, re.S)
		hash = re.findall('type="hidden" name="hash".*?value="(.*?)"', data, re.S)

		if op and id and fname and referer and hash:
			info = urlencode({
				'fname': fname[0],
				'hash': hash[0],
				'id': id[0],
				'imhuman': "Weiter",
				'op': "download1",
				'referer': referer[0],
				'usr_login': ""})
			print info
			reactor.callLater(10, self.vidx_data, url, method='POST', postdata=info, headers={'Content-Type':'application/x-www-form-urlencoded'})
			self.session.open(MessageBoxExt, _("Stream starts in 10 sec."), MessageBoxExt.TYPE_INFO, timeout=10)
		else:
			self.stream_not_found()

	def vidx_data(self, *args, **kwargs):
		print "drin"
		getPage(*args, **kwargs).addCallback(self.vidx_data2).addErrback(self.errorload)

	def vidx_data2(self, data):
		print "get stream"
		stream_url = re.findall('file: "(.*?)"', data, re.S)
		if stream_url:
			self._callback(stream_url[0])
		else:
			self.stream_not_found()

	def youwatch(self, data):
		print 'youwatch data'
		get_packedjava = re.search("<script type=.text.javascript.>(eval.function.*?)</script>", data, re.S)
#		print get_packedjava.group(1)
		if get_packedjava and detect(get_packedjava.group(1)):
			print 'get_packedjava'
			sJavascript = get_packedjava.group(1)
			sUnpacked = unpack(sJavascript)
			if sUnpacked:
				print "unpacked"
#				print sUnpacked
				stream_url = re.search('file:"(.*?)"', sUnpacked, re.S)
				if stream_url:
					print stream_url.group(1)
					self._callback(stream_url.group(1))
					return

		self.stream_not_found()

	def mightyupload(self, data):
		stream_url = re.findall("file:\s'(.*?)'", data)
		if stream_url:
			self._callback(stream_url[0])
		else:
			get_packedjava = re.findall("<script type=.text.javascript.>eval.function(.*?)</script>", data, re.S)
			if get_packedjava:
				print get_packedjava
				if len(get_packedjava) > 1:
					sJavascript = get_packedjava[1]
					sUnpacked = cJsUnpacker().unpackByString(sJavascript)
					if sUnpacked:
						print "unpacked"
						print sUnpacked
						if re.search('type="video/divx', sUnpacked):
							print "DDIIIIIIIIIVVVXXX"
							stream_url = re.findall('type="video/divx"src="(.*?)"', sUnpacked)
							if stream_url:
								print stream_url[0]
								self._callback(stream_url[0])
								return
						elif re.search("file", sUnpacked):
							print "FFFFFFFFLLLLLLLLLLLVVVVVVVV"
							stream_url = re.findall("file','(.*?)'", sUnpacked)
							if stream_url:
								print stream_url[0]
								self._callback(stream_url[0])
								return
			self.stream_not_found()

	def lmv(self, data, url):
		dataPost = {}
		r = re.findall('input type="hidden".*?name="(.*?)".*?value="(.*?)"', data, re.S)
		for name, value in r:
			dataPost[name] = value
			dataPost.update({'method_free':'Continue to Video'})
		print dataPost
		getPage(url, method='POST', postdata=urlencode(dataPost), headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.lmv2, url).addErrback(self.errorload)

	def lmv2(self, data, url):
		dataPost = {}
		r = re.findall('input type="hidden".*?name="(.*?)".*?value="(.*?)"', data, re.S)
		for name, value in r:
			dataPost[name] = value
			dataPost.update({'method_free':'Continue to Video'})
		print dataPost
		getPage(url, method='POST', postdata=urlencode(dataPost), headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.lmvPlay).addErrback(self.errorload)

	def lmvPlay(self, data):
		print data
		get_packedjava = re.findall("<script type=.text.javascript.>eval.function(.*?)</script>", data, re.S)
		if get_packedjava:
			print get_packedjava
			sJavascript = get_packedjava[0]
			sUnpacked = cJsUnpacker().unpackByString(sJavascript)
			if sUnpacked:
				print "unpacked"
				print sUnpacked
				if re.search('type="video/divx', sUnpacked):
					print "DDIIIIIIIIIVVVXXX"
					stream_url = re.findall('type="video/divx"src="(.*?)"', sUnpacked)
					if stream_url:
						print stream_url[0]
						self._callback(stream_url[0])
						return
				elif re.search("file", sUnpacked):
					print "FFFFFFFFLLLLLLLLLLLVVVVVVVV"
					stream_url = re.findall("file','(.*?)'", sUnpacked)
					if stream_url:
						print stream_url[0]
						self._callback(stream_url[0])
						return

		self.stream_not_found()

	def stream2k(self, data):
		file = re.findall("file: '(.*?)'", data, re.S)
		if file:
			self._callback(file[0])
		else:
			self.stream_not_found()

	def played(self, data, url):
		op = re.findall('type="hidden" name="op".*?value="(.*?)"', data, re.S)
		id = re.findall('type="hidden" name="id".*?value="(.*?)"', data, re.S)
		fname = re.findall('type="hidden" name="fname".*?value="(.*?)"', data, re.S)
		referer = re.findall('type="hidden" name="referer".*?value="(.*?)"', data, re.S)
		hash = re.findall('type="hidden" name="hash".*?value="(.*?)"', data, re.S)
		if op and id and fname and referer:
			info = urlencode({
				'fname': fname[0],
				'id': id[0],
				'imhuman': "Continue to Video",
				'op': "download1",
				'referer': "",
				'hash': hash[0],
				'usr_login': ""})

			print info
			getPage(url, method='POST', cookies=cj, postdata=info, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.played_data).addErrback(self.errorload)
		else:
			self.stream_not_found()

	def played_data(self, data):
		print data
		stream_url = re.findall('file: "(.*?)"', data, re.S)
		if stream_url:
			print stream_url[0]
			self._callback(stream_url[0])
		else:
			self.stream_not_found()

	def eco_read(self, data, kurl):
		id = re.findall('<div id="play" data-id="(.*?)">', data, re.S)
		analytics = re.findall("anlytcs='(.*?)'", data, re.S)
		footerhash = re.findall("var footerhash='(.*?)'", data, re.S)
		superslots = re.findall("var superslots='(.*?)'", data, re.S)
		print "id:", id
		print "analytics:", analytics
		print "footerhash:", footerhash
		print "superslots:", superslots
		if id and footerhash and superslots:
			tpm = footerhash[0] + superslots[0]
			postString = {'id': id[0], 'tpm':tpm}
			print postString
			url = "http://www.ecostream.tv/js/ecoss.js"
			getPage(url, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self.eco_get_api_url, postString, kurl).addErrback(self.errorload)

	def eco_get_api_url(self, data, postString, kurl):
		api_url = re.findall('post\(\'(.*?)\'.*?#play', data)
		api_url = 'http://www.ecostream.tv'+api_url[-1]
		print "Ecostream api url:", api_url
		getPage(api_url, method='POST', cookies=ck, postdata=urlencode(postString), headers={'Content-Type': 'application/x-www-form-urlencoded', 'Referer': kurl, 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.eco_data).addErrback(self.errorload)

	def eco_data(self, data):
		print "hole stream"
		stream_url = re.findall('"url":"(.*?)"', data, re.S)
		if stream_url:
			stream_url = "http://www.ecostream.tv%s" % stream_url[0]
			print stream_url
			self._callback(stream_url)
		else:
			self.stream_not_found()

	def errorload(self, error):
		print "[streams]:", error
		self.stream_not_found()

	def vidstream_in(self, data, url):
		id = re.findall('type="hidden" name="id".*?value="(.*?)"', data, re.S)
		fname = re.findall('type="hidden" name="fname".*?value="(.*?)"', data, re.S)
		hash = re.findall('type="hidden" name="hash".*?value="(.*?)"', data, re.S)
		if id and fname and hash:
			print id, fname, hash
			post_data = urlencode({'op': "download1", 'usr_login': "", 'id': id[0], 'fname': fname[0], 'hash': hash[0], 'referer': "", 'imhuman': "	Proceed+to+video"})
			#getPage(url, method='POST', cookies=cj, postdata=post_data, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.vidstream_in_data).addErrback(self.errorload)
			reactor.callLater(6, self.vidstream_in_getPage, url, method='POST', cookies=cj, postdata=post_data, headers={'Content-Type':'application/x-www-form-urlencoded'})
			message = self.session.open(MessageBoxExt, _("Stream starts in 6 sec."), MessageBoxExt.TYPE_INFO, timeout=6)
		else:
			self.stream_not_found()
	def vidstream_in_getPage(self, *args, **kwargs):
		print "drin"
		getPage(*args, **kwargs).addCallback(self.vidstream_in_data).addErrback(self.errorload)

	def vidstream_in_data(self, data):
		stream_url = re.findall('file: "(.*?)"', data, re.S)
		if stream_url:
			self._callback(stream_url[0])
		else:
			self.stream_not_found()

	def primeshare(self, data, url):
		hash = re.findall('<input type="hidden".*?name="hash".*?value="(.*?)"', data)
		if hash:
			info = urlencode({'hash': hash[0]})
			print info
			reactor.callLater(16, self.primeshare_getPage, url, method='POST', cookies=cj, postdata=info, headers={'Content-Type':'application/x-www-form-urlencoded'})
			message = self.session.open(MessageBoxExt, _("Stream starts in 16 sec."), MessageBoxExt.TYPE_INFO, timeout=16)
		else:
			self.stream_not_found()

	def primeshare_getPage(self, *args, **kwargs):
		print "drin"
		getPage(*args, **kwargs).addCallback(self.primeshare_data).addErrback(self.errorload)

	def primeshare_data(self, data):
		print "data received"#, data
		stream_url = re.findall('file: \'(.*?)\'', data, re.S)
		if stream_url:
			self._callback(stream_url[0])
		else:
			stream_url = re.findall("provider: 'stream'.*?url: '(http://.*?primeshare.tv.*?)'", data, re.S)
			if not stream_url:
				stream_url = re.findall("'\$\.download\('(http://.*?primeshare.tv:443.*?)'", data, re.S)
			if stream_url:
				self._callback(stream_url[0])
			else:
				self.stream_not_found()

	def flashstream(self, data):
		get_packedjava = re.findall("<script type=.text.javascript.>eval.function(.*?)</script>", data, re.S)
		if get_packedjava:
			sJavascript = get_packedjava[1]
			sUnpacked = cJsUnpacker().unpackByString(sJavascript)
			if sUnpacked:
				if re.search('type="video/divx', sUnpacked):
					print "DDIIIIIIIIIVVVXXX"
					stream_url = re.findall('type="video/divx"src="(.*?)"', sUnpacked)
					if stream_url:
						print stream_url[0]
						self._callback(stream_url[0])
						return
				elif re.search("'file'", sUnpacked):
					print "FFFFFFFFLLLLLLLLLLLVVVVVVVV"
					stream_url = re.findall("'file','(.*?)'", sUnpacked)
					if stream_url:
						self._callback(stream_url[0])
						return

		self.stream_not_found()

	def uploadc(self, data, url):
		print 'uploadc data'
		ipcount_val = re.findall('<input type="hidden" name="ipcount_val".*?value="(.*?)">', data)
		referer = re.findall('<input type="hidden" name="referer".*?value="(.*?)">', data)
		id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data)
		fname = re.findall('<input type="hidden" name="fname".*?alue="(.*?)">', data)
		if id and fname and ipcount_val and referer:
			post_data = urllib.urlencode({'ipcount_val' : ipcount_val[0], 'op' : 'download2', 'usr_login' : '', 'id' : id[0], 'fname' : fname[0], 'method_free' : 'Slow access', 'referer': referer[0]})
			print post_data
			getPage(url, method='POST', postdata = post_data, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.uploadc_post).addErrback(self.errorload)
		else:
			print "keine post infos gefunden.\n",data
			self.stream_not_found()

	def uploadc_post(self, data):
		print data
		stream = re.findall("'file','(.*?)'", data, re.S)
		get_packedjava = re.findall("<script type=.text.javascript.>eval.function(.*?)</script>", data, re.S)
		if stream:
			print stream
			self._callback(stream[0])
			return

		elif get_packedjava:
			sJavascript = get_packedjava[1]
			print sJavascript
			sUnpacked = cJsUnpacker().unpackByString(sJavascript)
			if sUnpacked:
				print sUnpacked
				stream_url = re.findall('type="video/divx"src="(.*?)"', sUnpacked)
				if stream_url:
					print stream_url[0]
					self._callback(stream_url[0])
					return

		self.stream_not_found()

	def uploadc_start(self, url):
		if url:
			self._callback(url)
		else:
			self.stream_not_found()

	def xvidstream(self, data):
		get_packedjava = re.findall("<script type=.text.javascript.>eval.function(.*?)</script>", data, re.S)
		if get_packedjava:
			sJavascript = get_packedjava[1]
			sUnpacked = cJsUnpacker().unpackByString(sJavascript)
			if sUnpacked:
				#print sUnpacked
				stream_url = re.findall('type="video/divx"src="(.*?)"', sUnpacked)
				if stream_url:
					print stream_url[0]
					self._callback(stream_url[0])
					return

		self.stream_not_found()

	def movreel_data(self, data, url):
		id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data)
		rand = re.findall('<input type="hidden" name="rand".*?value="(.*?)">', data)
		if id and rand:
			post_data = urllib.urlencode({'op': 'download2', 'usr_login': '', 'id': id[0], 'rand': rand[0], 'referer': '', 'method_free': ' Kostenloser Download'})
			getPage(url, method='POST', postdata = post_data, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.movreel_post_data2).addErrback(self.errorload)
		else:
			self.stream_not_found()

	def movreel_post_data2(self, data):
		get_packedjava = re.findall("<script type=.text.javascript.>eval.function(.*?)</script>", data, re.S)
		if get_packedjava:
			sJavascript = get_packedjava[0]
			sUnpacked = cJsUnpacker().unpackByString(sJavascript)
			if sUnpacked:
				if re.search('setup\({file', sUnpacked):
					stream_url = re.search('setup\({file:"0://(.*?)"', sUnpacked)
					if stream_url:
						stream = "http://%s" % stream_url.group(1).replace("//","/")
						self._callback(stream)
						return
				else:
					stream_url = re.search('"video/divx"src="(.*?)"', sUnpacked)
					if stream_url:
						stream = stream_url.group(1)
						self._callback(stream)
						return

		self.stream_not_found()

	def filenuke(self, data, url):
		print "drin "
		#id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data)
		#fname = re.findall('<input type="hidden" name="fname".*?alue="(.*?)">', data)
		#if id and fname:
		#	post_data = urllib.urlencode({'op': 'download1', 'usr_login': '', 'id': id[0], 'fname': fname[0], 'referer': '', 'method_free': 'free'})
		#else: #TODO new filenuke coding, unknown if old still needed
		post_data = urllib.urlencode({'method_free': 'free'})
		postagent = 'Enigma2 Mediaplayer'
		getPage(url, method='POST', postdata=post_data, agent=postagent , headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.filenuke_data).addErrback(self.errorload)

	def filenuke_data(self, data):
		print "drin"
		#  unknown if old still needed
		#get_packedjava = re.findall("<script type=.text.javascript.>eval.function(.*?)</script>", data, re.S)
		#if get_packedjava:
		#	print get_packedjava
		#	sJavascript = get_packedjava[1]
		#	sUnpacked = cJsUnpacker().unpackByString(sJavascript)
		#	if sUnpacked:
		#		print "unpacked"
		#		print sUnpacked
		#		if re.search('type="video/divx', sUnpacked):
		#			print "DDIIIIIIIIIVVVXXX"
		#			stream_url = re.findall('type="video/divx"src="(.*?)"', sUnpacked)
		#			if stream_url:
		#				print stream_url[0]
		#				self._callback(stream_url[0])
		#				return
		#		elif re.search("file", sUnpacked):
		#			print "FFFFFFFFLLLLLLLLLLLVVVVVVVV"
		#			stream_url = re.findall("file','(.*?)'", sUnpacked)
		#			if stream_url:
		#				print stream_url[0]
		#				self._callback(stream_url[0])
		#				return
		#else:
		print "find uncoded url"
		#stream_url = re.findall("var\slnk1\s=\s'(.*?)'", data, re.S)
		stream_url = re.findall("var\slnk.*?=\s'(.*?)'", data, re.S)
		if stream_url:
			mp_globals.player_agent = 'Enigma2 Mediaplayer'
			stream_url = stream_url[0]
			self._callback(stream_url)
		else:
			self.stream_not_found()

	def streamProxyPutlockerSockshare(self, data):
		m = re.search("'file': '(.*?)'", data, re.S)
		if m:
			self._callback(m.group(1))
		else:
			self.stream_not_found()

	def streamPutlockerSockshare(self, data, url, provider):
		if re.search('File Does not Exist', data, re.S):
			message = self.session.open(MessageBoxExt, "File Does not Exist, or Has Been Removed", MessageBoxExt.TYPE_INFO, timeout=5)
		elif re.search('Encoding to enable streaming is in progress', data, re.S):
			message = self.session.open(MessageBoxExt, "Encoding to enable streaming is in progress. Try again soon.", MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			print "provider:", provider
			enter = re.findall('<input type="hidden" value="(.*?)" name="fuck_you">', data)
			print "enter:", enter
			values = {'fuck_you': enter[0], 'confirm': 'Close+Ad+and+Watch+as+Free+User'}
			user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
			headers = { 'User-Agent' : user_agent}
			cookiejar = cookielib.LWPCookieJar()
			cookiejar = urllib2.HTTPCookieProcessor(cookiejar)
			opener = urllib2.build_opener(cookiejar)
			urllib2.install_opener(opener)
			data = urlencode(values)
			req = urllib2.Request(url, data, headers)
			try:
				response = urllib2.urlopen(req)
			except urllib2.HTTPError, e:
				print e.code
			except urllib2.URLError, e:
				print e.args
			else:
				link = response.read()
				if link:
					print "found embed data"
					embed = re.findall("get_file.php.stream=(.*?)'\,", link, re.S)
					if embed:
						req = urllib2.Request('http://www.%s.com/get_file.php?stream=%s' %(provider, embed[0]))
						req.add_header('User-Agent', user_agent)
						try:
							response = urllib2.urlopen(req)
						except urllib2.HTTPError, e:
							print e.code
						except urllib2.URLError, e:
							print e.args
						else:
							link = response.read()
							if link:
								stream_url = re.findall('<media:content url="(.*?)"', link, re.S)
								print stream_url[1].replace('&amp;','&')
								self._callback(stream_url[1].replace('&amp;','&'))
								return

			self.stream_not_found()

	def streamcloud(self, data):
		id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data)
		fname = re.findall('<input type="hidden" name="fname".*?alue="(.*?)">', data)
		hash = re.findall('<input type="hidden" name="hash" value="(.*?)">', data)
		if id and fname and hash:
			url = "http://streamcloud.eu/%s" % id[0]
			post_data = urllib.urlencode({'op': 'download2', 'usr_login': '', 'id': id[0], 'fname': fname[0], 'referer': '', 'hash': hash[0], 'imhuman':'Weiter+zum+Video'})
			getPage(url, method='POST', cookies=ck, postdata=post_data, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.streamcloud_data).addErrback(self.errorload)
		else:
			self.stream_not_found()

	def streamcloud_data(self, data):
		stream_url = re.findall('file: "(.*?)"', data)
		if stream_url:
			print stream_url
			self._callback(stream_url[0])
		elif re.search('This video is encoding now', data, re.S):
			self.session.open(MessageBoxExt, _("This video is encoding now. Please check back later."), MessageBoxExt.TYPE_INFO, timeout=10)
		else:
			self.stream_not_found()

	def xvidstage_post(self, data, url):
		op = re.findall('type="hidden" name="op".*?value="(.*?)"', data, re.S)
		id = re.findall('type="hidden" name="id".*?value="(.*?)"', data, re.S)
		fname = re.findall('type="hidden" name="fname".*?value="(.*?)"', data, re.S)
		referer = re.findall('type="hidden" name="referer".*?value="(.*?)"', data, re.S)
		if op and id and fname and referer:
			info = urlencode({
				'fname': fname[0],
				'id': id[0],
				'method_free': "Weiter zu Video / Stream Video",
				'op': "download1",
				'referer': "",
				'usr_login': ""})
			getPage(url, method='POST', postdata=info, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.xvidstage_data).addErrback(self.errorload)
		else:
#			self.stream_not_found()
			self.xvidstage_data(data)

	def xvidstage_data(self, data):
		print "drin"
		get_packedjava = re.findall("<script type=.text.javascript.>eval.function(.*?)</script>", data, re.S)
		if get_packedjava:
			print get_packedjava[1]
			sJavascript = get_packedjava[1]
			sUnpacked = cJsUnpacker().unpackByString(sJavascript)
			if sUnpacked:
				#print sUnpacked
				#stream_url = re.findall("'file','(.*?)'", sUnpacked)
				stream_url = re.search('type="video/divx"src="(.*?)"', sUnpacked)
				if not stream_url:
					stream_url = re.search("'file','(.*?)'", sUnpacked)
				if stream_url:
					print stream_url.group(1)
					self._callback(stream_url.group(1))
					return

		self.stream_not_found()

	def userporn_tv(self, link):
		#print "userporn: ",link
		fx = Userporn()
		stream_url = fx.get_media_url(link)
		if stream_url:
			self._callback(stream_url)
		else:
			self.stream_not_found()

	def check_istream_link(self, data):
		self.check_link(data, self._callback)

	def vidplay_readPostData(self, data, url):
		self.vidplay_url = url
		solvemedia = re.search('<iframe src="(http://api.solvemedia.com.+?)"', data)
		url2 = solvemedia.group(1)
		data2 = urllib.urlopen(url2).read()
		self.hugekey = re.search('id="adcopy_challenge" value="(.+?)">', data2).group(1)
		print self.hugekey
		burl = "http://api.solvemedia.com%s" % re.search('<img src="(.+?)"', data2).group(1)
		urllib.urlretrieve(burl, "/tmp/captcha.jpg")
		print "ok"
		self.data_p = {}
		r = re.findall('<input type="hidden".*?name="(.*?)".*?value="(.*?)"', data, re.S)
		if r:
			for name, value in r:
				self.data_p[name] = value
				print name, value
		print self.data_p
		self.session.openWithCallback(self.vidplay_captchaCallback, VirtualKeyBoardExt, title = (_("Captcha input:")), text = "", captcha = "/tmp/captcha.jpg", is_dialog=True)

	def vidplay_captchaCallback(self, callback = None, entry = None):
		if callback != None or callback != "":
			print callback
			self.data_p.update({'adcopy_challenge': self.hugekey,'adcopy_response': callback})
			print self.data_p
			print self.vidplay_url
			getPage(self.vidplay_url, method='POST', postdata=urlencode(self.data_p), headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.got_vidplay).addErrback(self.errorload)
		else:
			self.stream_not_found()

	def got_vidplay(self, data):
		print "data empfangen.."
		print data
		stream_url = re.search('id="downloadbutton".*?href="(.*?)"', data, re.S)
		if stream_url:
			print stream_url
			self._callback(stream_url.group(1))
		else:
			self.stream_not_found()