#!/bin/bash

cd "/home/homeassistant/.homeassistant" > /dev/null
git fetch > /dev/null
git rev-list --count master..origin/master
