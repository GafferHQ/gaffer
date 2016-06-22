#! /bin/bash

set -e

gaffer screengrab scripts/groupFirst.gfr -image images/groupFirst.png -editor NodeGraph
gaffer screengrab scripts/groupSecond.gfr -image images/groupSecond.png -editor NodeGraph
gaffer screengrab scripts/performanceMonitor.gfr -image images/performanceMonitor.png -editor NodeEditor -selection StandardOptions -nodeEditor.reveal StandardOptions.options.performanceMonitor
