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

NAME = ranger
VERSION = $(shell grep -m 1 -o '[0-9][0-9.]\+' README)
SNAPSHOT_NAME ?= $(NAME)-$(VERSION)-$(shell git rev-parse HEAD | cut -b 1-8).tar.gz
# Find suitable python version (need python >= 2.6 or 3.1):
PYTHON ?= $(shell python -c 'import sys; sys.exit(sys.version < "2.6")' && \
	which python || which python3.1 || which python3 || which python2.6)
SETUPOPTS ?= '--record=install_log.txt'
DOCDIR ?= doc/pydoc
DESTDIR ?= /
PYOPTIMIZE ?= 1
BMCOUNT ?= 5  # how often to run the benchmarks?

CWD = $(shell pwd)

default: compile
	@echo 'Run `make options` for a list of all options'

options: help
	@echo
	@echo 'Options:'
	@echo 'PYTHON = $(PYTHON)'
	@echo 'PYOPTIMIZE = $(PYOPTIMIZE)'
	@echo 'DOCDIR = $(DOCDIR)'

help:
	@echo 'make install: Install $(NAME)'
	@echo 'make doc: Create the pydoc documentation'
	@echo 'make clean: Remove the compiled files (*.pyc, *.pyo)'
	@echo 'make cleandoc: Remove the pydoc documentation'
	@echo 'make snapshot: Create a tar.gz of the current git revision'
	@echo 'make test: Run all unittests.'

install:
	$(PYTHON) setup.py install $(SETUPOPTS) \
		'--root=$(DESTDIR)' --optimize=$(PYOPTIMIZE)

compile: clean
	PYTHONOPTIMIZE=$(PYOPTIMIZE) $(PYTHON) -m compileall -q ranger

clean:
	find . -regex .\*.py[co]\$$ -exec rm -f -- {} \;

doc: cleandoc
	mkdir -p $(DOCDIR)
	cd $(DOCDIR); \
		$(PYTHON) -c 'import pydoc, sys; \
		sys.path[0] = "$(CWD)"; \
		pydoc.writedocs("$(CWD)")'
	find . -name \*.html -exec sed -i 's|'$(CWD)'|../..|g' -- {} \;

cleandoc:
	test -d $(DOCDIR) && rm -f -- $(DOCDIR)/*.html || true

test:
	@$(PYTHON) test/all_tests.py 1

bm:
	@$(PYTHON) test/all_benchmarks.py $(BMCOUNT)

snapshot:
	git archive --prefix='$(NAME)-$(VERSION)/' --format=tar HEAD | gzip > $(SNAPSHOT_NAME)

.PHONY: default options compile clean doc cleandoc test bm snapshot install
