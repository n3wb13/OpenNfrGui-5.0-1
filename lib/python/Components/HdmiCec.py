import struct
import os
from sys import maxint

from enigma import eHdmiCEC, eActionMap
from enigma import eTimer

from config import config, ConfigSelection, ConfigYesNo, ConfigSubsection, ConfigText
from Tools.StbHardware import getFPWasTimerWakeup

config.hdmicec = ConfigSubsection()
config.hdmicec.enabled = ConfigYesNo(default = False)
config.hdmicec.control_tv_standby = ConfigYesNo(default = True)
config.hdmicec.control_tv_wakeup = ConfigYesNo(default = True)
config.hdmicec.report_active_source = ConfigYesNo(default = True)
config.hdmicec.report_active_menu = ConfigYesNo(default = True)
config.hdmicec.handle_tv_standby = ConfigYesNo(default = True)
config.hdmicec.handle_tv_wakeup = ConfigYesNo(default = True)
config.hdmicec.tv_wakeup_detection = ConfigSelection(
	choices = {
	"wakeup": _("Wakeup"),
	"tvreportphysicaladdress": _("TV physical address report"),
	"sourcerequest": _("Source request"),
	"streamrequest": _("Stream request"),
	"osdnamerequest": _("OSD name request"),
	"activity": _("Any activity"),
	},
	default = "streamrequest")
config.hdmicec.fixed_physical_address = ConfigText(default = "0.0.0.0")
config.hdmicec.volume_forwarding = ConfigYesNo(default = False)
config.hdmicec.control_receiver_wakeup = ConfigYesNo(default = False)
config.hdmicec.control_receiver_standby = ConfigYesNo(default = False)
config.hdmicec.handle_deepstandby_events = ConfigYesNo(default = False)
config.hdmicec.preemphasis = ConfigYesNo(default = False)	
choicelist = []
for i in (10, 50, 100, 150, 250):
	choicelist.append(("%d" % i, "%d ms" % i))
config.hdmicec.minimum_send_interval = ConfigSelection(default = "0", choices = [("0", _("Disabled"))] + choicelist)

class HdmiCec:
	instance = None

	def __init__(self):
		if config.hdmicec.enabled.getValue():
			assert not HdmiCec.instance, "only one HdmiCec instance is allowed!"
			HdmiCec.instance = self

			self.wait = eTimer()
			self.wait.timeout.get().append(self.sendCmd)
			self.queue = []

			eHdmiCEC.getInstance().messageReceived.get().append(self.messageReceived)
			config.misc.standbyCounter.addNotifier(self.onEnterStandby, initial_call = False)
			config.misc.DeepStandby.addNotifier(self.onEnterDeepStandby, initial_call = False)
			self.setFixedPhysicalAddress(config.hdmicec.fixed_physical_address.getValue())

			self.volumeForwardingEnabled = False
			self.volumeForwardingDestination = 0
			eActionMap.getInstance().bindAction('', -maxint - 1, self.keyEvent)
			config.hdmicec.volume_forwarding.addNotifier(self.configVolumeForwarding)
			config.hdmicec.enabled.addNotifier(self.configVolumeForwarding)
			if config.hdmicec.handle_deepstandby_events.getValue():
				if not getFPWasTimerWakeup():
					self.wakeupMessages()
#			if fileExists("/proc/stb/hdmi/preemphasis"):		
#				self.sethdmipreemphasis()

	def getPhysicalAddress(self):
		physicaladdress = eHdmiCEC.getInstance().getPhysicalAddress()
		hexstring = '%04x' % physicaladdress
		return hexstring[0] + '.' + hexstring[1] + '.' + hexstring[2] + '.' + hexstring[3]

	def setFixedPhysicalAddress(self, address):
		if address != config.hdmicec.fixed_physical_address.getValue():
			config.hdmicec.fixed_physical_address.value = address
			config.hdmicec.fixed_physical_address.save()
		hexstring = address[0] + address[2] + address[4] + address[6]
		eHdmiCEC.getInstance().setFixedPhysicalAddress(int(float.fromhex(hexstring)))

	def sendMessage(self, address, message):
		if config.hdmicec.enabled.getValue():
			cmd = 0
			data = ''
			if message == "wakeup":
				cmd = 0x04
			elif message == "sourceactive":
				address = 0x0f # use broadcast for active source command
				cmd = 0x82
				physicaladdress = eHdmiCEC.getInstance().getPhysicalAddress()
				data = str(struct.pack('BB', int(physicaladdress/256), int(physicaladdress%256)))
			elif message == "standby":
				cmd = 0x36
			elif message == "sourceinactive":
				physicaladdress = eHdmiCEC.getInstance().getPhysicalAddress()
				cmd = 0x9d
				data = str(struct.pack('BB', int(physicaladdress/256), int(physicaladdress%256)))
			elif message == "menuactive":
				cmd = 0x8e
				data = str(struct.pack('B', 0x00))
			elif message == "menuinactive":
				cmd = 0x8e
				data = str(struct.pack('B', 0x01))
			elif message == "givesystemaudiostatus":
				cmd = 0x7d
				address = 0x05
			elif message == "setsystemaudiomode":
				cmd = 0x70
				address = 0x05
				physicaladdress = eHdmiCEC.getInstance().getPhysicalAddress()
				data = str(struct.pack('BB', int(physicaladdress/256), int(physicaladdress%256)))
			elif message == "osdname":
				cmd = 0x47
				data = os.uname()[1]
				data = data[:14]
			elif message == "poweractive":
				cmd = 0x90
				data = str(struct.pack('B', 0x00))
			elif message == "powerinactive":
				cmd = 0x90
				data = str(struct.pack('B', 0x01))
			elif message == "reportaddress":
				address = 0x0f # use broadcast address
				cmd = 0x84
				physicaladdress = eHdmiCEC.getInstance().getPhysicalAddress()
				devicetype = eHdmiCEC.getInstance().getDeviceType()
				data = str(struct.pack('BBB', int(physicaladdress/256), int(physicaladdress%256), devicetype))
			elif message == "vendorid":
				cmd = 0x87
				data = '\x00\x00\x00'
			elif message == "keypoweron":
				cmd = 0x44
				data = str(struct.pack('B', 0x6d))
			elif message == "keypoweroff":
				cmd = 0x44
				data = str(struct.pack('B', 0x6c))
			if cmd:
				if config.hdmicec.minimum_send_interval.getValue() != "0" and message != "standby": # Use no interval time when message is standby. usefull for Panasonic TV
					self.queue.append((address, cmd, data))
					if not self.wait.isActive():
						self.wait.start(int(config.hdmicec.minimum_send_interval.getValue()), True)
				else:
					eHdmiCEC.getInstance().sendMessage(address, cmd, data, len(data))

	def sendCmd(self):
		if len(self.queue):
			(address, cmd, data) = self.queue.pop(0)
			eHdmiCEC.getInstance().sendMessage(address, cmd, data, len(data))
			self.wait.start(int(config.hdmicec.minimum_send_interval.getValue()), True)

	def sendMessages(self, address, messages):
		for message in messages:
			self.sendMessage(address, message)

	def wakeupMessages(self):
		if config.hdmicec.enabled.getValue():
			messages = []
			if config.hdmicec.control_tv_wakeup.getValue():
				messages.append("wakeup")
			if config.hdmicec.report_active_source.getValue():
				messages.append("sourceactive")
			if config.hdmicec.report_active_menu.getValue():
				messages.append("menuactive")
			if messages:
				self.sendMessages(0, messages)

			if config.hdmicec.control_receiver_wakeup.getValue():
				self.sendMessage(5, "keypoweron")
				self.sendMessage(5, "setsystemaudiomode")

	def standbyMessages(self):
		if config.hdmicec.enabled.getValue():
			messages = []
			if config.hdmicec.control_tv_standby.getValue():
				messages.append("standby")
			else:
				if config.hdmicec.report_active_source.getValue():
					messages.append("sourceinactive")
				if config.hdmicec.report_active_menu.getValue():
					messages.append("menuinactive")
			if messages:
				self.sendMessages(0, messages)

			if config.hdmicec.control_receiver_standby.getValue():
				self.sendMessage(5, "keypoweroff")
				self.sendMessage(5, "standby")

	def onLeaveStandby(self):
		self.wakeupMessages()

	def onEnterStandby(self, configElement):
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.onLeaveStandby)
		self.standbyMessages()

	def onEnterDeepStandby(self, configElement):
		if config.hdmicec.handle_deepstandby_events.getValue():
			self.standbyMessages()

	def standby(self):
		from Screens.Standby import Standby, inStandby
		if not inStandby:
			from Tools import Notifications
			Notifications.AddNotification(Standby)

	def wakeup(self):
		from Screens.Standby import inStandby
		if inStandby:
			inStandby.Power()

	def messageReceived(self, message):
		if config.hdmicec.enabled.getValue():
			from Screens.Standby import inStandby
			cmd = message.getCommand()
			data = 16 * '\x00'
			length = message.getData(data, len(data))
			if cmd == 0x00: # feature abort
				if data[0] == '\x44':
					print 'eHdmiCec: volume forwarding not supported by device %02x'%(message.getAddress())
					self.volumeForwardingEnabled = False
			elif cmd == 0x46: # request name
				self.sendMessage(message.getAddress(), 'osdname')
			elif cmd == 0x7e or cmd == 0x72: # system audio mode status
				if data[0] == '\x01':
					self.volumeForwardingDestination = 5 # on: send volume keys to receiver
				else:
					self.volumeForwardingDestination = 0 # off: send volume keys to tv
				if config.hdmicec.volume_forwarding.getValue():
					print 'eHdmiCec: volume forwarding to device %02x enabled'% self.volumeForwardingDestination
					self.volumeForwardingEnabled = True
			elif cmd == 0x8f: # request power status
				if inStandby:
					self.sendMessage(message.getAddress(), 'powerinactive')
				else:
					self.sendMessage(message.getAddress(), 'poweractive')
			elif cmd == 0x83: # request address
				self.sendMessage(message.getAddress(), 'reportaddress')
			elif cmd == 0x86: # request streaming path
				physicaladdress = ord(data[0]) * 256 + ord(data[1])
				ouraddress = eHdmiCEC.getInstance().getPhysicalAddress()
				if physicaladdress == ouraddress:
					if not inStandby:
						if config.hdmicec.report_active_source.getValue():
							self.sendMessage(message.getAddress(), 'sourceactive')
			elif cmd == 0x85: # request active source
				if not inStandby:
					if config.hdmicec.report_active_source.getValue():
						self.sendMessage(message.getAddress(), 'sourceactive')
			elif cmd == 0x8c: # request vendor id
				self.sendMessage(message.getAddress(), 'vendorid')
			elif cmd == 0x8d: # menu request
				requesttype = ord(data[0])
				if requesttype == 2: # query
					if inStandby:
						self.sendMessage(message.getAddress(), 'menuinactive')
					else:
						self.sendMessage(message.getAddress(), 'menuactive')

			# handle standby request from the tv
			if cmd == 0x36 and config.hdmicec.handle_tv_standby.getValue():
				self.standby()

			# handle wakeup requests from the tv
			if config.hdmicec.handle_tv_wakeup.getValue():
				if cmd == 0x04 and config.hdmicec.tv_wakeup_detection.getValue() == "wakeup":
					self.wakeup()
				elif cmd == 0x84 and config.hdmicec.tv_wakeup_detection.getValue() == "tvreportphysicaladdress":
					if (ord(data[0]) * 256 + ord(data[1])) == 0 and ord(data[2]) == 0:
						self.wakeup()
				elif cmd == 0x85 and config.hdmicec.tv_wakeup_detection.getValue() == "sourcerequest":
					self.wakeup()
				elif cmd == 0x86 and config.hdmicec.tv_wakeup_detection.getValue() == "streamrequest":
					physicaladdress = ord(data[0]) * 256 + ord(data[1])
					ouraddress = eHdmiCEC.getInstance().getPhysicalAddress()
					if physicaladdress == ouraddress:
						self.wakeup()
				elif cmd == 0x46 and config.hdmicec.tv_wakeup_detection.getValue() == "osdnamerequest":
					self.wakeup()
				elif cmd != 0x36 and config.hdmicec.tv_wakeup_detection.getValue() == "activity":
					self.wakeup()

	def configVolumeForwarding(self, configElement):
		if config.hdmicec.enabled.getValue() and config.hdmicec.volume_forwarding.getValue():
			self.volumeForwardingEnabled = True
			self.sendMessage(0x05, 'givesystemaudiostatus')
		else:
			self.volumeForwardingEnabled = False

	def keyEvent(self, keyCode, keyEvent):
		if not self.volumeForwardingEnabled: return
		cmd = 0
		data = ''
		if keyEvent == 0:
			if keyCode == 115:
				cmd = 0x44
				data = str(struct.pack('B', 0x41))
			if keyCode == 114:
				cmd = 0x44
				data = str(struct.pack('B', 0x42))
			if keyCode == 113:
				cmd = 0x44
				data = str(struct.pack('B', 0x43))
		if keyEvent == 2:
			if keyCode == 115:
				cmd = 0x44
				data = str(struct.pack('B', 0x41))
			if keyCode == 114:
				cmd = 0x44
				data = str(struct.pack('B', 0x42))
			if keyCode == 113:
				cmd = 0x44
				data = str(struct.pack('B', 0x43))
		if keyEvent == 1:
			if keyCode == 115 or keyCode == 114 or keyCode == 113:
				cmd = 0x45
		if cmd:
			eHdmiCEC.getInstance().sendMessage(self.volumeForwardingDestination, cmd, data, len(data))
			return 1
		else:
			return 0
			
	def sethdmipreemphasis(self):
		try:
			if config.hdmicec.preemphasis.getValue() == True:
				file = open("/proc/stb/hdmi/preemphasis", "w")
				file.write('on')
				file.close()
			else:
				file = open("/proc/stb/hdmi/preemphasis", "w")
				file.write('off')
				file.close()
		except:
			return

hdmi_cec = HdmiCec()
