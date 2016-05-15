import praw
import sqlite3
import yaml
import pprint
import time

class SubScriber:

    def __init__(self, config):

        self.reddit = praw.Reddit(user_agent='python:AutoSubscriber:v0.1 (by /u/elpantalla)')
        self.reddit.login(config['reddit']['username'], config['reddit']['password'], disable_warning=True)
        print("DB Path: {}".format(config['databasePath']))
        self.conn = sqlite3.connect(config['databasePath'])
        self.db = self.conn.cursor()


    def getLastPost( self, user ):
        redditor = self.reddit.get_redditor( user )
        comment = redditor.get_submitted(sort='new', time='all', limit=1)
        for c in comment:
            return c.id

        return None


    def processMention( self, author, msgBody ):
        user = msgBody.split(" ")[1]

        if not self.isAuthorAlreadySubscribed( user, author ):
            print("Subscribing to {}".format(user))
            self.subscribe( user, author )
            self.updateLastPost( user )

    def updateLastPost( self, user ):
        if self.getLastPost( user ) != None:
            self.db.execute("delete from users where user = ?", [str(user)] )
            self.db.execute("insert into users(user,lastpostid) values(?,?)", [str(user),str(self.getLastPost(user))] )
            self.conn.commit();

    def subscribe( self, user, author ):
        self.db.execute("insert into subscribers(user, subscriber) values(?, ?)", [str(user), str(author)] )
        self.conn.commit()

    def isAuthorAlreadySubscribed( self, user, author ):
        users = self.db.execute("select * from subscribers where user = ? and subscriber = ?", [str(user),str(author)] )
        return users.fetchone() != None

    def isUserInDb( self, user ):
        users = self.db.execute( "select distinct user from subscribers")

        for u in users:
            if user == u[0]:
                return True

        return False

    def processInbox( self ):
        for msg in self.reddit.get_unread( limit=None ):
            # First token should be username
            splitMsg = msg.body.split(" ")
            msg.mark_as_read()

            if splitMsg[0] == "/u/Subscriber_Bot":
                print("Found mention by {}: {}".format(msg.author, msg.body))
                self.processMention( msg.author, msg.body )

            elif splitMsg[0] == "help":
                # Reply with help
                print("Sending help to {}".format(msg.author))
                self.reddit.send_message(msg.author, "Subscriber_Bot Help", 
                        """Hi! Glad you're interested in Subscriber_Bot. 

Subscriber_Bot is designed to allow you to be notified whenever a user of interest submits a new post.

How to interact with Subscriber_Bot:

1.) Reply to any post with the phrase: '/u/Subscriber_Bot [user to subscribe to]' (eg. /u/Subscriber_Bot elpantalla to subscribe to elpantalla's posts)

2.) Send /u/Subscriber_Bot a personal message with the same syntax

3.) Send 'help' to Subscriber_Bot to receive this message

                        """)

            elif splitMsg[0] == "list":
                # List subscriptions
                subscriptions = """Subscriptions: 

"""
                for sub in self.db.execute("select subscriber from subscribers where user = ?",[str(msg.author)]):
                    subscriptions += "/u/{}\n\n".format(sub[0])

                self.reddit.send_message(msg.author, "Subscriber_Bot Subscriptions", subscriptions ) 

class Notifier:

    def __init__(self, config):

        self.reddit = praw.Reddit(user_agent='python:AutoSubscriber:v0.1 (by /u/elpantalla)')
        self.reddit.login(config['reddit']['username'], config['reddit']['password'], disable_warning=True)
        self.conn = sqlite3.connect(config['databasePath'])
        self.db = self.conn.cursor()

    def getSubscribers( self, user ):
        return [sub[0] for sub in self.db.execute("select subscriber from subscribers where user = ?",[str(user)])]

    def getLastSavedPost( self, user ):
        return self.db.execute("select lastpostid from users where user = ?",[str(user)]).fetchone()[0]

    def getUsers( self ):
        return [user[0] for user in self.db.execute("select user from users")]

    def getNewPosts( self, user ):
        lastSavedPost = self.getLastSavedPost( user )
        redditor = self.reddit.get_redditor( user )
        newPosts = []
        for post in redditor.get_submitted(sort='new', time='all', limit=10):
            if post.id != lastSavedPost:
                newPosts.append( post.id )
            else:
                break

        return newPosts

    def notifySubscribers( self ):
        for user in self.getUsers():
            newPosts = self.getNewPosts( user )

            if newPosts:
                # TODO nick make a common function class or something. Not currently organized very well.
                self.db.execute("delete from users where user = ?", [str(user)] )
                self.db.execute("insert into users(user,lastpostid) values(?,?)", [str(user),str(newPosts[0])])
                self.conn.commit()

                # Notify subscribers
                for subscriber in self.getSubscribers( user ):
                    print("Notifying: {}".format(subscriber))
                    for post in newPosts:
                        postInfo = self.reddit.get_submission(submission_id = post )
                        self.reddit.send_message(subscriber, "New post from /u/{} - {}".format(user,postInfo.title), 
                        "Hi! User /u/{} has posted a new submission: [{}]({})".format(user, postInfo.title, postInfo.permalink))

config = yaml.load(file('config.yaml','r'))
reader = SubScriber(config)
notifier = Notifier(config)

while True:

    # TODO nick these could run in threads if you're feeling frisky
    reader.processInbox()
    notifier.notifySubscribers()
    time.sleep(5)
