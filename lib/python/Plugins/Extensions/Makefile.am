installdir = $(pkglibdir)/python/Plugins/Extensions

SUBDIRS = TuxboxPlugins CutListEditor PicturePlayer MediaScanner MediaPlayer SocketMMI DVDBurn Modem Infopanel MenuSort CustomSubservices bmediacenter MediaPortal MainMenu2 e2speedtest

if SPARK
SUBDIRS +=  NFR4XBoot-sh4
else
SUBDIRS +=  NFR4XBoot
endif

if HAVE_LIBDDVD
SUBDIRS += DVDPlayer
endif

install_PYTHON = __init__.py
