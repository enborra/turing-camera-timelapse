from datetime import datetime
import calendar
import time


while True:
    now = datetime.utcnow()
    unixtime = calendar.timegm(now.utctimetuple())
    minstamp = unixtime - (now.second)

    print('Current timestamp:               %s' % unixtime)
    print('Current timestamp on the minute: %s' % minstamp)
    print('---')

    time.sleep(1)
