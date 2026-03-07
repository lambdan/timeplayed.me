#!/bin/sh
set -e
black "$@" conftest.py tpbackend
