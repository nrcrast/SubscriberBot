import praw
import sqlite3
import pprint
import time
import logging
import sys

class SubscriberBot(object):
    """Base class contaning some common functionality between Notifier and InboxReader
    """
    def __init__(self, config, CONSTANTS ):
        self.CONSTANTS = CONSTANTS
        self.reddit = praw.Reddit(user_agent='python:AutoSubscriber:v0.1 (by /u/elpantalla)')
        self.reddit.login(config['reddit']['username'], config['reddit']['password'], disable_warning=True)
        self.conn = sqlite3.connect(config['databasePath'])
        self.db = self.conn.cursor()

    def getLastComment( self, user ):
        """Get the last comment by a user

        Args:
            user: The user to get comments of
        Returns:
            The ID of the user's last comment
        """
        redditor = self.reddit.get_redditor( user )

        if redditor:
            for attempt in range(10):
                try:                
                    comment = redditor.get_comments(sort='new', time='all', limit=1)
                    for c in comment:
                        return c
                except:
                    logging.error("Error getting last comment for user {}".format(user))
                else:
                    break
            else:
                logging.error("Failed to get last comment for user {} after 10 attempts".format(user))
        return None

    def getLastPost( self, user ):
        """Get the last submission by a user

        Args:
            user: The user to get submissions of
        Returns:
            The ID of the user's last submission
        """

        redditor = self.reddit.get_redditor( user )

        if redditor:
            for attempt in range(10):
                try:                
                    comment = redditor.get_submitted(sort='new', time='all', limit=1)
                    for c in comment:
                        return c
                except:
                    logging.error("Error getting last post for user {}".format(user))
                else:
                    break
            else:
                logging.error("Failed to get last post for user {} after 10 attempts".format(user))
        return None

    # TODO this shouldn't be just copied and pasted in both classes...
    def updateLastPost( self, user ):
        """Update the database with the last post from a user

        Args:
            user: The user whose database entry is to be updated
        Returns:
            None
        """
        self.db.execute("delete from users where user = ?", [str(user)] )
        lastPost = self.getLastPost(user)
        lastComment = self.getLastComment(user)

        self.db.execute("insert into users(user,lastsubmissionid, lastsubmissiondate, lastcommentid, lastcommentdate) values(?,?,?,?,?)", [ 
            str(user),
            str(lastPost.id) if lastPost else 'None', 
            int(lastPost.created) if lastPost else 0,
            str(lastComment.id) if lastComment else 'None',
            int(lastComment.created) if lastComment else 0,
            ])


        self.conn.commit();