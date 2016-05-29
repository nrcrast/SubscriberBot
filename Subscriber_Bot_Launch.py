import yaml
import pprint
import time
import logging
import sys
import inboxreader
import notifier
import sqlite3
import praw

def createDatabase( dbPath ):
    conn = sqlite3.connect( dbPath );
    c = conn.cursor()
    c.execute("create table if not exists subscribers ( id integer primary key autoincrement, user char(256) not null, subscriber char(256) not null, subscriptionType integer not null );")
    c.execute("create table if not exists users ( id integer primary key autoincrement, user char(256) not null, lastsubmissionid char(256) not null, lastsubmissiondate integer not null, lastcommentid char(256) not null, lastcommentdate integer not null );")

# Bitmap for subscription type
SUBSCRIPTION_TYPE = { "comments" : 1, "submissions" : 2}

# Constants to make code more readable
DATABASE_COLUMNS = { "subscriber": { "id" : 0, "user" : 1, "subscriber" : 2, "subscriptionType" : 3}, "users" : { "id" : 0, "user" : 1, "lastSubmissionId" : 2, "lastSubmissionDate" : 3, "lastCommentId" : 4 ,
"lastCommentDate" : 5}}

CONSTANTS = { "DATABASE_COLUMNS" : DATABASE_COLUMNS, "SUBSCRIPTION_TYPE" : SUBSCRIPTION_TYPE }

logging.basicConfig( filename='subscriberbot.log', level=logging.DEBUG, format='%(asctime)s [%(levelname)s]: %(message)s' )
config = yaml.load(file('config.yaml','r'))
createDatabase(config["databasePath"])
reader = inboxreader.InboxReader(config, CONSTANTS)
notifier = notifier.Notifier(config, CONSTANTS)

# pp = pprint.PrettyPrinter(indent=4)
# reddit = praw.Reddit(user_agent='python:AutoSubscriber:v0.1 (by /u/elpantalla)')
# pp.pprint( reddit.get_info( thing_id = "t3_4l1jkj" ).title )
while True:

    # TODO nick these could run in threads if you're feeling frisky
    reader.processInbox()
    notifier.notifySubscribers()
    time.sleep(.1)
