import yaml
import pprint
import time
import logging
import sys
import inboxreader
import notifier

logging.basicConfig( filename='subscriberbot.log', level=logging.DEBUG, format='%(asctime)s [%(levelname)s]: %(message)s' )
config = yaml.load(file('config.yaml','r'))
reader = inboxreader.InboxReader(config)
notifier = notifier.Notifier(config)

while True:

    # TODO nick these could run in threads if you're feeling frisky
    reader.processInbox()
    notifier.notifySubscribers()
    time.sleep(1)
