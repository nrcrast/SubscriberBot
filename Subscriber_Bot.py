import praw
import sqlite3
import yaml
import pprint
import time
import logging
import sys

class SubScriber:

    def __init__(self, config):

        self.reddit = praw.Reddit(user_agent='python:AutoSubscriber:v0.1 (by /u/elpantalla)')
        self.reddit.login(config['reddit']['username'], config['reddit']['password'], disable_warning=True)
        print("DB Path: {}".format(config['databasePath']))
        self.conn = sqlite3.connect(config['databasePath'])
        self.db = self.conn.cursor()
        logging.info("Initialized Subscriber")

    def getLastPost( self, user ):
        redditor = self.reddit.get_redditor( user )

        if redditor:
            for attempt in range(10):
                try:                
                    comment = redditor.get_submitted(sort='new', time='all', limit=1)
                    for c in comment:
                        return c.id
                except:
                    logging.error("Error getting last post for user {}".format(user))
                else:
                    break
            else:
                logging.error("Failed to get last post for user {} after 10 attempts".format(user))
        return None


    def processSubscribeCmd( self, author, user ):
        if not self.isAuthorAlreadySubscribed( user, author ):
            self.subscribe( user, author )
            self.updateLastPost( user )
            self.reddit.send_message(author, "Subscriber_Bot Subscription Confirmation - {}".format(user), 
                "Hi! You have been successfully subscribed to /u/{}".format(user)) 

    def processUnsubscribeCmd( self, author, user ):
        self.db.execute("delete from subscribers where user = ? and subscriber = ?", [str(user),str(author)] )
        self.conn.commit()
        self.reddit.send_message(author, "Subscriber_Bot Unsubscribe Confirmation - {}".format(user), 
                "Hi! You have been successfully unsubscribed from /u/{}".format(user)) 

    def updateLastPost( self, user ):
        self.db.execute("delete from users where user = ?", [str(user)] )
        
        if self.getLastPost( user ):
            self.db.execute("insert into users(user,lastpostid) values(?,?)", [str(user),str(self.getLastPost(user))] )
        else:
            self.db.execute("insert into users(user,lastpostid) values(?,'None')", [str(user),] )

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
        for attempt in range(10):
            try:
                for msg in self.reddit.get_unread( limit=None ):
                    # First token should be username
                    splitMsg = msg.body.split(" ")
                    msg.mark_as_read()

                    if splitMsg[0] == "/u/Subscriber_Bot":
                        splitMsg.remove("/u/Subscriber_Bot")

                    if splitMsg[0] == "subscribe":
                        logging.debug("Received subscribe cmd from {}".format(msg.author))
                        self.processSubscribeCmd( msg.author, splitMsg[1] )

                    elif splitMsg[0] == "unsubscribe":
                        logging.debug("Received unsubscribe cmd from {}".format(msg.author))
                        self.processUnsubscribeCmd( msg.author, splitMsg[1] )

                    elif splitMsg[0] == "help":
                        # Reply with help
                        logging.debug("Received help cmd from {}".format(msg.author))
                        self.reddit.send_message(msg.author, "Subscriber_Bot Help", 
                                """Hi! Glad you're interested in Subscriber_Bot. 

Subscriber_Bot is designed to allow you to be notified whenever a user of interest submits a new post.

How to interact with Subscriber_Bot:

1.) Subscribing to a user

   * Reply to any post with syntax /u/Subscriber_Bot subscribe [username]

   * Send PM to /u/Subscriber_Bot with same syntax (you can leave /u/Subscriber_Bot out of msg body or keep it in)

2.) Unsubscribing from a user

   * Same as subscribing, except replace 'subscribe' with 'unsubscribe'

3.) Help

   * Send PM to /u/Subscriber_Bot with 'help' as msg body

4.) Who am I subscribed to?
   
   * Send PM to /u/Subscriber_Bot with 'list' as msg body


                                """)

                    elif splitMsg[0] == "list":
                        # List subscriptions
                        logging.debug("Received list cmd from {}".format(msg.author))
                        subscriptions = """Subscriptions: 

        """
                        for sub in self.db.execute("select user from subscribers where subscriber = ?",[str(msg.author)]):
                            subscriptions += "/u/{}\n\n".format(sub[0])

                        self.reddit.send_message(msg.author, "Subscriber_Bot Subscriptions", subscriptions ) 
                    else:
                        logging.debug("Received erroneous cmd[{}] from {}".format(msg.body, msg.author))

            except:
                logging.error("Error processing inbox")
            else:
                break
        else:
            logging.error("Failed to process inbox after 10 tries")

class Notifier:

    def __init__(self, config):

        self.reddit = praw.Reddit(user_agent='python:AutoSubscriber:v0.1 (by /u/elpantalla)')
        self.reddit.login(config['reddit']['username'], config['reddit']['password'], disable_warning=True)
        self.conn = sqlite3.connect(config['databasePath'])
        self.db = self.conn.cursor()
        logging.info("Initialized Notifier")

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
            
            for attempt in range (10):
                try:
                    newPosts = self.getNewPosts( user )
                except:
                    logging.error("Unexpected error getting new posts for user {}".format(user))
                else:
                    break
            else:
                logging.error("Failed ot get new posts for user {} after 10 tries".format(user))

            if newPosts:
                # TODO nick make a common function class or something. Not currently organized very well.
                self.db.execute("delete from users where user = ?", [str(user)] )
                self.db.execute("insert into users(user,lastpostid) values(?,?)", [str(user),str(newPosts[0])])
                self.conn.commit()

                # Notify subscribers
                for subscriber in self.getSubscribers( user ):
                    for post in newPosts:
                        logging.debug("Notifying user {} of new post {}".format(user, post))
                        
                        # Try a few times
                        for attempt in range(10):
                            try:
                                postInfo = self.reddit.get_submission( submission_id = post )
                                postSubject = "New post from /u/{} - {}".format(user,postInfo.title)

                                # Reddit has a max subject length of 100. Lame
                                if( len(postInfo) > 100 ):
                                    postInfo = "New post from /u/{}".format(user)

                                postContent = "Hi! User /u/{} has posted a new submission: [{}]({})".format(user, postInfo.title, postInfo.permalink)
                                
                                try: 
                                    self.reddit.send_message(subscriber, postSubject, postContent )
                                except:
                                    logging.error("Unexpected error while sending msg: {}".format(sys.exc_info()[0]))
                                else:
                                    break
                            except:
                                logging.error("Unexpected error while getting user's post: {}".format(sys.exc_info()[0]))
                            else:
                                break
                        else:
                            logging.error("Failed to notify user after 10 tries")


logging.basicConfig( filename='subscriberbot.log', level=logging.DEBUG, format='%(asctime)s [%(levelname)s]: %(message)s' )
config = yaml.load(file('config.yaml','r'))
reader = SubScriber(config)
notifier = Notifier(config)

while True:

    # TODO nick these could run in threads if you're feeling frisky
    reader.processInbox()
    notifier.notifySubscribers()
    time.sleep(1)
