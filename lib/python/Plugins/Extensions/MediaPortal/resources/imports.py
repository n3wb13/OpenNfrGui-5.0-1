# -*- coding: utf-8 -*-
from enigma import gFont, addFont, eTimer, eConsoleAppContainer, ePicLoad, loadPNG, getDesktop, eServiceReference, iPlayableService, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, eListbox, gPixmapPtr, getPrevAsciiCode, eBackgroundFileEraser

from Plugins.Plugin import PluginDescriptor

from twisted.internet import reactor, defer
from twisted.web.client import downloadPage, getPage, error
from twisted.web import client, error as weberror
from twisted.web.http_headers import Headers
from twisted.web.client import Agent, ProxyAgent, CookieAgent, PartialDownloadError
from twisted.web._newclient import ResponseDone
from twisted.internet.defer import Deferred, succeed
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import Protocol
from twisted.web.iweb import IBodyProducer
from twisted.web import http

from cookielib import CookieJar

from zope.interface import implements

from Components.ActionMap import NumberActionMap, ActionMap, HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.Button import Button
from Components.config import config, ConfigInteger, ConfigSelection, getConfigListEntry, ConfigText, ConfigDirectory, ConfigYesNo, configfile, ConfigSelection, ConfigSubsection, ConfigPIN, NoSave, ConfigNothing, ConfigIP
try:
	from Components.config import ConfigPassword
except ImportError:
	ConfigPassword = ConfigText
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend
from Components.Pixmap import Pixmap, MovingPixmap
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.Boolean import Boolean
from Components.Input import Input

from Screens.InfoBar import MoviePlayer, InfoBar
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarNotifications
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog
from Screens.HelpMenu import HelpableScreen

from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN, SCOPE_CURRENT_SKIN, createDir
from Tools.LoadPixmap import LoadPixmap
from Tools.NumericalTextInput import NumericalTextInput

import re, httplib, urllib, urllib2, os, cookielib, socket, sha, shutil, datetime, math, hashlib, random, json, md5, string, xml.etree.cElementTree, StringIO, Queue, threading, sys

from urllib2 import Request, URLError, urlopen as urlopen2
from socket import gaierror, error
from urllib import quote, unquote_plus, unquote, urlencode
from httplib import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException
from binascii import unhexlify, hexlify
from urlparse import parse_qs
from time import time, localtime, strftime, mktime

# MediaPortal Imports
import mp_globals
from mp_globals import std_headers
from debuglog import printlog as printl
from streams import isSupportedHoster, get_stream_link
from simpleplayer import SimplePlayer
from coverhelper import CoverHelper
from mpscreen import MPScreen
from showAsThumb import ThumbsHelper
from messageboxext import MessageBoxExt

def registerFont(file, name, scale, replacement):
		try:
				addFont(file, name, scale, replacement)
		except Exception, ex: #probably just openpli
				addFont(file, name, scale, replacement, 0)

def getUserAgent():
	userAgents = [
		"Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
		"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; de) Presto/2.9.168 Version/11.52",
		"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20120101 Firefox/35.0",
	    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0",
	    "Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0",
	    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
	    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)",
	    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
	    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
	    "Mozilla/5.0 (compatible; Konqueror/4.5; FreeBSD) KHTML/4.5.4 (like Gecko)",
	    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",
	]
	return random.choice(userAgents)

def testWebConnection():
	conn = httplib.HTTPConnection("www.google.com", timeout=15)
	try:
		conn.request("GET", "/")
		data = conn.getresponse()
		conn.close()
		return True
	except:
		conn.close()
	return False

def decodeHtml(text):
	text = text.replace('&auml;','ä')
	text = text.replace('\u00e4','ä')
	text = text.replace('&#228;','ä')

	text = text.replace('&Auml;','Ä')
	text = text.replace('\u00c4','Ä')
	text = text.replace('&#196;','Ä')

	text = text.replace('&ouml;','ö')
	text = text.replace('\u00f6','ö')
	text = text.replace('&#246;','ö')

	text = text.replace('&ouml;','Ö')
	text = text.replace('&Ouml;','Ö')
	text = text.replace('\u00d6','Ö')
	text = text.replace('&#214;','Ö')

	text = text.replace('&uuml;','ü')
	text = text.replace('\u00fc','ü')
	text = text.replace('&#252;','ü')

	text = text.replace('&Uuml;','Ü')
	text = text.replace('\u00dc','Ü')
	text = text.replace('&#220;','Ü')

	text = text.replace('&szlig;','ß')
	text = text.replace('\u00df','ß')
	text = text.replace('&#223;','ß')

	text = text.replace('&copy;','©')
	text = text.replace('&pound;','£')
	text = text.replace('&fnof;','ƒ')
	text = text.replace('&Atilde;','Ã')
	text = text.replace('&atilde;','ã')
	text = text.replace('&Egrave;','È')
	text = text.replace('&egrave;','è')
	text = text.replace('&Yacute;','Ý')
	text = text.replace('&yacute;','ý')
	text = text.replace('&amp;','&')
	text = text.replace('&quot;','\"')
	text = text.replace('&gt;','>')
	text = text.replace('&apos;',"'")
	text = text.replace('&acute;','\'')
	text = text.replace('&ndash;','-')
	text = text.replace('&bdquo;','"')
	text = text.replace('&rdquo;','"')
	text = text.replace('&ldquo;','"')
	text = text.replace('&lsquo;','\'')
	text = text.replace('&rsquo;','\'')
	text = text.replace('&#034;','"')
	text = text.replace('&#34;','"')
	text = text.replace('&#038;','&')
	text = text.replace('&#039;','\'')
	text = text.replace('&#39;','\'')
	text = text.replace('&#160;',' ')
	text = text.replace('\u00a0',' ')
	text = text.replace('\u00b4','\'')
	text = text.replace('\u003d','=')
	text = text.replace('\u0026','&')
	text = text.replace('&#174;','')
	text = text.replace('&#225;','a')
	text = text.replace('&#233;','e')
	text = text.replace('&#243;','o')
	text = text.replace('&#8211;',"-")
	text = text.replace('&#8212;',"—")
	text = text.replace('&mdash;','—')
	text = text.replace('\u2013',"–")
	text = text.replace('&#8216;',"'")
	text = text.replace('&#8217;',"'")
	text = text.replace('&#8220;',"'")
	text = text.replace('&#8221;','"')
	text = text.replace('&#8222;',',')
	text = text.replace('&#124;','|')
	text = text.replace('\u014d','ō')
	text = text.replace('\u016b','ū')
	text = text.replace('\u201a','\"')
	text = text.replace('\u2018','\"')
	text = text.replace('\u201e','\"')
	text = text.replace('\u201c','\"')
	text = text.replace('\u201d','\'')
	text = text.replace('\u2019','’')
	text = text.replace('\u2019s','’')
	text = text.replace('\u00e0','à')
	text = text.replace('\u00e7','ç')
	text = text.replace('\u00e8','é')
	text = text.replace('\u00e9','é')
	text = text.replace('\u00c1','Á')
	text = text.replace('\u00c6','Æ')
	text = text.replace('\u00e1','á')
	text = text.replace('\u00b0','°')
	text = text.replace('\u00e6','æ')

	text = text.replace('&#xC4;','Ä')
	text = text.replace('&#xD6;','Ö')
	text = text.replace('&#xDC;','Ü')
	text = text.replace('&#xE4;','ä')
	text = text.replace('&#xF6;','ö')
	text = text.replace('&#xFC;','ü')
	text = text.replace('&#xDF;','ß')
	text = text.replace('&#xE9;','é')
	text = text.replace('&#xB7;','·')
	text = text.replace("&#x27;","'")
	text = text.replace("&#x26;","&")
	text = text.replace("&#xFB;","û")
	text = text.replace("&#xF8;","ø")
	text = text.replace("&#x21;","!")
	text = text.replace("&#x3f;","?")

	text = text.replace('&#8230;','...')
	text = text.replace('\u2026','...')
	text = text.replace('&hellip;','...')

	text = text.replace('&#8234;','')
	text = text.replace('&nbsp;','')
	return text

def iso8859_Decode(txt):
	txt = txt.replace('\xe4','ä').replace('\xf6','ö').replace('\xfc','ü').replace('\xdf','ß')
	txt = txt.replace('\xc4','Ä').replace('\xd6','Ö').replace('\xdc','Ü')
	return txt

def decodeHtml2(txt):
	txt = iso8859_Decode(txt)
	txt = decodeHtml(txt).strip()
	return txt

def stripAllTags(html):
	cleanr =re.compile('<.*?>')
	cleantext = re.sub(cleanr,'', html)
	return cleantext

def getMac():
	try:
		from Components.Network import iNetwork
		BoxID = iNetwork.getAdapterAttribute("eth0", "mac")
	except:
		try:
			from Components.Network import iNetworkInfo
			ifaces = iNetworkInfo.getConfiguredInterfaces()
			iface = ifaces["eth0"]
			BoxID = iface.ethernet.mac
		except:
			BoxID = "N/A"

	return BoxID

def getInfo():
	try:
		from Tools.HardwareInfoVu import HardwareInfoVu
		DeviceName = HardwareInfoVu().get_device_name()
	except:
		try:
			from Tools.HardwareInfo import HardwareInfo
			DeviceName = HardwareInfo().get_device_name()
		except:
			try:
				file = open("/proc/stb/info/model", "r")
				DeviceName = file.readline().strip()
				file.close()
			except:
				DeviceName = "unknown"

	BoxID = getMac()

	try:
		from Components.About import about
		EnigmaVersion = about.getEnigmaVersionString()
		ImageVersion = about.getVersionString()
	except:
		EnigmaVersion = "unknown"
		ImageVersion = "unknown"

	Hash = hashlib.sha512(BoxID.lower()).hexdigest().lower()
	OUI = BoxID[0:8]

	return [DeviceName, Hash, OUI, EnigmaVersion, ImageVersion]