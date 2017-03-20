#!/bin/bash

cd "/home/homeassistant/.homeassistant" > /dev/null 2>&1
git fetch > /dev/null 2>&1
git rev-list --count master..origin/master
