installdir = $(pkglibdir)/python/Plugins/SystemPlugins

SUBDIRS = SoftwareManager PositionerSetup Satfinder \
	VideoTune Hotplug \
	CommonInterfaceAssignment \
	HdmiCEC VideoClippingSetup \
	VideoEnhancement WirelessLan NetworkWizard \
	SABnzbdSetup FastScan SatelliteEquipmentControl DiseqcTester LCNScanner NFRLedControl

if HAVE_LIBVUGLES2
SUBDIRS += AnimationSetup
endif

if VUSOLO2
SUBDIRS += CableScan
endif

if VUDUO2
SUBDIRS += CableScan
endif

if VUUNO
SUBDIRS += CableScan
endif

if VUULTIMO
SUBDIRS += CableScan
endif

install_PYTHON = __init__.py
