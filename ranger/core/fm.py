# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
The File Manager, putting the pieces together
"""

from time import time
from collections import deque

import ranger
from ranger.core.signal import SignalContainer
from ranger.core.actions import Actions
from ranger.container import Bookmarks
from ranger.core.runner import Runner
from ranger import relpath_conf
from ranger.ext.get_executables import get_executables
from ranger import __version__
from ranger.fsobject import Loader

CTRL_C = 3
TICKS_BEFORE_COLLECTING_GARBAGE = 100

class FM(Actions):
	input_blocked = False
	input_blocked_until = 0
	stderr_to_out = False
	def __init__(self, ui=None, bookmarks=None, tags=None):
		"""Initialize FM."""
		Actions.__init__(self)
		self.ui = ui
		self.log = deque(maxlen=20)
		self.bookmarks = bookmarks
		self.tags = tags
		self.loader = Loader()
		self.signals = SignalContainer()
		self._executables = None
		self.apps = self.settings.apps.CustomApplications()

		@self.signals.register('throbber')
		def throbber_function(signal):
			if hasattr(signal.fm.ui, 'throbber'):
				if signal.fm.loader.has_work():
					signal.fm.ui.throbber(signal.fm.loader.status)
				else:
					signal.fm.ui.throbber(remove=True)

		def mylogfunc(text):
			self.notify(text, bad=True)
		self.run = Runner(ui=self.ui, apps=self.apps,
				logfunc=mylogfunc)

		from ranger.shared import FileManagerAware
		FileManagerAware.fm = self
	
	def emit(self, name):
		self.signals.emit(name, fm=self)

	@property
	def executables(self):
		if self._executables is None:
			self._executables = sorted(get_executables())
		return self._executables

	def initialize(self):
		"""If ui/bookmarks are None, they will be initialized here."""
		from ranger.fsobject.directory import Directory

		if self.bookmarks is None:
			if ranger.arg.clean:
				bookmarkfile = None
			else:
				bookmarkfile = relpath_conf('bookmarks')
			self.bookmarks = Bookmarks(
					bookmarkfile=bookmarkfile,
					bookmarktype=Directory,
					autosave=self.settings.autosave_bookmarks)
			self.bookmarks.load()

		else:
			self.bookmarks = bookmarks

		from ranger.container.tags import Tags
		if not ranger.arg.clean and self.tags is None:
			self.tags = Tags(relpath_conf('tagged'))

		if self.ui is None:
			from ranger.gui.defaultui import DefaultUI
			self.ui = DefaultUI()
			self.ui.initialize()

	def block_input(self, sec=0):
		self.input_blocked = sec != 0
		self.input_blocked_until = time() + sec

	def loop(self):
		"""
		The main loop consists of:
		1. reloading bookmarks if outdated
		2. letting the loader work
		3. drawing and finalizing ui
		4. reading and handling user input
		5. after X loops: collecting unused directory objects
		"""

		self.env.enter_dir(self.env.path)

		gc_tick = 0

		# for faster lookup:
		ui = self.ui
		throbber = ui.throbber
		bookmarks = self.bookmarks
		loader = self.loader
		env = self.env
		has_throbber = hasattr(ui, 'throbber')

		try:
			while True:
				bookmarks.update_if_outdated()
				loader.work()
				self.emit('throbber')

				ui.redraw()

				ui.set_load_mode(loader.has_work())

				key = ui.get_next_key()

				if key > 0:
					if self.input_blocked and \
							time() > self.input_blocked_until:
						self.input_blocked = False
					if not self.input_blocked:
						ui.handle_key(key)

				gc_tick += 1
				if gc_tick > TICKS_BEFORE_COLLECTING_GARBAGE:
					gc_tick = 0
					env.garbage_collect()

		finally:
			bookmarks.remember(env.cwd)
			bookmarks.save()
