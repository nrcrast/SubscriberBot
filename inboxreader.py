import pprint
import time
import logging
import sys
import sqlite3
import praw
from subscriberbotbase import SubscriberBot

class InboxReader(SubscriberBot):

    def __init__(self, config, CONSTANTS):
        super( InboxReader, self ).__init__(config, CONSTANTS)
        logging.info("Initialized Subscriber")


    def getCurrentSubscriptionType( self, user, author ):
        subscription = self.db.execute("select subscriptionType from subscribers where user = ? and subscriber = ?", [str(user),str(author)] )
        return subscription.fetchone()

    def subscriptionTypeToInt( self, subscriptionType ):
        """Convert subscription type string to bitmapped integer

        Bit 0 => Comments
        Bit 1 => Submissions
        """
        subscriptionType = subscriptionType.lower()
        typeInt = 0

        if "comments" in subscriptionType:
            typeInt |= self.CONSTANTS["SUBSCRIPTION_TYPE"]["comments"]
        if "submissions" in subscriptionType:
            typeInt |= self.CONSTANTS["SUBSCRIPTION_TYPE"]["submissions"]

        return typeInt

    def processSubscribeCmd( self, author, user, subscriptionType ):
        """Subscribe to a user's posts

        Args:
            author: The user who sent the request
            user: The user whose posts the author wants to subscribe to
        Returns:
            None
        """

        # If the user is not subscribed or the subscription type is changing
        if (not self.isAuthorAlreadySubscribed( user, author )) or (self.subscriptionTypeToInt(subscriptionType) != getCurrentSubscriptionType( user, author )):
            self.subscribe( user, author, self.subscriptionTypeToInt(subscriptionType) )
            self.updateLastPost( user )
            self.reddit.send_message(author, "Subscriber_Bot Subscription Confirmation - {}".format(user), 
                "Hi! You have been successfully subscribed to /u/{}".format(user)) 

    def processUnsubscribeCmd( self, author, user ):
        """Unsubscribe from a user's posts

        Args:
            author: The user who sent the request
            user: The user the author wants to unsubscribe from
        Returns:
            None
        """
        self.db.execute("delete from subscribers where user = ? and subscriber = ?", [str(user),str(author)] )
        self.conn.commit()
        self.reddit.send_message(author, "Subscriber_Bot Unsubscribe Confirmation - {}".format(user), 
                "Hi! You have been successfully unsubscribed from /u/{}".format(user)) 

    def subscribe( self, user, author, subscriptionType ):
        """Add entry to subscribers database

        Args:
            author: The user who sent the request
            user: The user to subscribe to
        Returns:
            None
        """
        self.db.execute("insert into subscribers(user, subscriber, subscriptionType ) values(?, ?, ?)", [str(user), str(author), subscriptionType ] )
        self.conn.commit()

    def isAuthorAlreadySubscribed( self, user, author ):
        """Is the author already subscribed to this user?

        Args:
            author: The user who sent the request
            user: The user to subscribe to
        Returns:
            True => Author is already subscribed    False => Author is not already subscribed
        """
        users = self.db.execute("select * from subscribers where user = ? and subscriber = ?", [str(user),str(author)] )
        return users.fetchone() != None

    def isUserInDb( self, user ):
        """Does this user already have a database entry?

        Args:
            user: user to check
        Returns:
            True => User is already in the database     False => User is not already in the database
        """
        users = self.db.execute( "select distinct user from subscribers")

        for u in users:
            if user == u[0]:
                return True

        return False

    def processInbox( self ):
        """Process the bot's inbox, respond to any requests that it receives:
    
        Requests:
            subscribe - Subscribe to user
            unsubscribe - Unsubscribe from user
            list - list current subscriptions for user
            help - send help text
        """
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
                        subscriptionType = "submissions"

                        if( len(splitMsg) >= 4 ):
                            subscriptionType = splitMsg[2].lower() + splitMsg[3].lower()
                        elif( len(splitMsg) >= 3 ):
                            subscriptionType = splitMsg[2].lower()

                        self.processSubscribeCmd( msg.author, splitMsg[1], subscriptionType )

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

            except Exception, e:
                logging.error("Error processing inbox: {}".format(str(e)))
            else:
                break
        else:
            logging.error("Failed to process inbox after 10 tries")
