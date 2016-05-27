import yaml
import pprint
import time
import logging
import sys
import inboxreader
import notifier
import sqlite3

def createDatabase( dbPath ):
    conn = sqlite3.connect( dbPath );
    c = conn.cursor()
    c.execute("create table if not exists subscribers ( id integer primary key autoincrement, user char(256) not null, subscriber char(256) not null );")
    c.execute("create table if not exists users ( id integer primary key autoincrement, user char(256) not null, lastpostid char(256) not null );")

logging.basicConfig( filename='subscriberbot.log', level=logging.DEBUG, format='%(asctime)s [%(levelname)s]: %(message)s' )
config = yaml.load(file('config.yaml','r'))
createDatabase(config["databasePath"])
reader = inboxreader.InboxReader(config)
notifier = notifier.Notifier(config)

while True:

    # TODO nick these could run in threads if you're feeling frisky
    reader.processInbox()
    notifier.notifySubscribers()
    time.sleep(1)
