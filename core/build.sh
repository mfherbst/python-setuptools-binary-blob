#!/bin/sh

if [ ! -f core/build.sh -o ! -f head/__init__.py -o ! -f extension/ExportCore.cc ]; then
	echo "Please run this script from the adcc directory." >&2
	exit 1
fi

if [ ! -d core/build ]; then
	mkdir core/build
	cd core/build
	git submodule update --init --recursive
	cmake -DCMAKE_INSTALL_PREFIX="${PWD}/../../extension/core" ..
else
	if [ ! -f core/build/Makefile ]; then
		echo "Something went wrong setting up cmake" >&2
		echo "Please delete ./core/build/ and try again" >&2
		exit 1
	fi
	cd core/build
	git submodule update --recursive
fi

make $@ install
