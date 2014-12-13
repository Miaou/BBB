#!/usr/bin/python
# ;-)
# Conclusions : il n'est pas possible de faire du bon PWM...
#  On s'en doutait, j'esperais que ca passerait avec le random phase au pire, mais ... non.
# Les meilleurs résultats seront avec le random phase, mais on voit forcément apparaître des effets de synchronisations de phase puique c'est un TRIAC derrière.

from Adafruit_BBIO import GPIO, PWM
import time


PWM_OPTO = 'P9_14'


def testFreq(freq, duty=50):
    PWM.start(PWM_OPTO, duty, freq)
    time.sleep(5)
    PWM.cleanup()


