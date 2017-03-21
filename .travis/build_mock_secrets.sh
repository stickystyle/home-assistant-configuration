#!/bin/sh

find $PWD -name "*.yaml" | xargs grep "\!secret"| awk '{print $4": 25"}'