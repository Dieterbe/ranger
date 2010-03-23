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

__license__ = 'GPL3'
__version__ = '1.0.4'
__credits__ = 'Roman Zimbelmann'
__author__ = 'Roman Zimbelmann'
__maintainer__ = 'Roman Zimbelmann'
__email__ = 'romanz@lavabit.com'

from ranger import log
from ranger.container import Bookmarks
from ranger import relpath_conf
from ranger.fsobject.directory import Directory
from ranger.gui.widgets.browserview import BrowserView

def __install__(fm):
	@fm.signals.register
	def loop_start(signal):
		signal.fm.bookmarks.update_if_outdated()

	@fm.signals.register
	def terminate(signal):
		signal.fm.bookmarks.remember(signal.fm.env.cwd)
		signal.fm.bookmarks.save()

	@fm.signals.register
	def initialize(signal):
		if signal.arg.clean:
			bookmarkfile = None
		else:
			bookmarkfile = relpath_conf('bookmarks')
		bm = Bookmarks(
				bookmarkfile=bookmarkfile,
				bookmarktype=Directory,
				autosave=signal.fm.settings.autosave_bookmarks)
		bm.load()
		signal.fm.bookmarks = bm

	@fm.signals.register
	def draw(sig):
		try:
			sig.fm.env.cmd.show_obj.draw_bookmarks
		except AttributeError:
			return

		sig.stop_propagation()

		self = sig.target
		self.need_clear = True

		sorted_bookmarks = sorted(item for item in self.fm.bookmarks \
				if '/.' not in item[1].path)

		def generator():
			return zip(range(self.hei), sorted_bookmarks)

		try:
			maxlen = max(len(item[1].path) for i, item in generator())
		except ValueError:
			return
		maxlen = min(maxlen + 5, self.wid)

		for line, items in generator():
			key, mark = items
			string = " " + key + ": " + mark.path
			self.addnstr(line, 0, string.ljust(maxlen), self.wid)

	@fm.lib.register
	def enter_bookmark(fm, key):
		try:
			destination = fm.bookmarks[key]
			cwd = fm.env.cwd
			if destination.path != cwd.path:
				fm.bookmarks.enter(key)
				fm.bookmarks.remember(cwd)
		except KeyError:
			pass

	@fm.lib.register
	def set_bookmark(fm, key):
		"""Set the bookmark with the name <key> to the current directory"""
		log(fm.bookmarks.dct.keys())
		log(key)
		fm.bookmarks[key] = fm.env.cwd
		log(fm.bookmarks.dct.keys())

	@fm.lib.register
	def unset_bookmark(fm, key):
		"""Delete the bookmark with the name <key>"""
		fm.bookmarks.delete(key)
