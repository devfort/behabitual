#!/bin/sh

set -e
sleep 2

cd ${SCREENGRAB_DIR:=${HOME}/Desktop/screengrabs}
webkit2png                      \
    --width 1024                \
    --height 1600               \
    --fullsize                  \
    --filename "`date +%s`"     \
    --dir ${SCREENGRAB_DIR}     \
        ${URL_TO_CAPTURE:=http://localhost:8000/}
