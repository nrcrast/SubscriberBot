import praw
import sqlite3
import pprint
import time
import logging
import sys

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

