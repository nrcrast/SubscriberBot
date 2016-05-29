import praw
import sqlite3
import pprint
import time
import logging
import sys
from subscriberbotbase import SubscriberBot


class Notifier(SubscriberBot):
    def __init__(self, config, CONSTANTS):

        super(Notifier, self).__init__(config, CONSTANTS)
        logging.info("Initialized Notifier")

    def getSubscribers(self, user):
        """Get subscribers from DB given a user

        Args:
            user: user to get subscribers for
        Returns:
            List (database rows) of subscribers
        """
        return self.db.execute("select * from subscribers where user = ?", [str(user)])

    def getUserData(self, user):
        """Get user information from users table

        Args:
            user: user to get information for
        Returns:
            User info (users table rows)
        """
        return self.db.execute("select * from users where user = ?", [str(user)]).fetchone()

    def getUsers(self):
        """Get list of all users subscribed to 

        Args:
            None
        Returns:
            List of usernames
        """
        return [user[0] for user in self.db.execute("select user from users")]

    def getNewSubmissions(self, user):
        """ Check for new submissions from user

        Args: 
            user: username to get new submissions of
        Returns: 
            list of post IDs of every new submission made by user (since last time this was called)
        """
        userData = self.getUserData(user)
        redditor = self.reddit.get_redditor(user)
        newPosts = []
        for post in redditor.get_submitted(sort='new', time='all', limit=10):

            # If the user deletes their post, don't want to send a bunch of notifications
            if post.id != userData[self.CONSTANTS["DATABASE_COLUMNS"]["users"]["lastSubmissionId"]] and (
                    post.created > userData[self.CONSTANTS["DATABASE_COLUMNS"]["users"]["lastSubmissionDate"]]):
                newPosts.append(post.id)
            else:
                break

        return newPosts

    def getNewComments(self, user):
        """ Check for new comments from user

        Args: 
            user: username to get new comments of
        Returns: 
            list of post IDs of every new comment made by user (since last time this was called)
        """
        userData = self.getUserData(user)
        redditor = self.reddit.get_redditor(user)
        newComments = []
        for post in redditor.get_comments(sort='new', time='all', limit=10):

            # If the user deletes their post, don't want to send a bunch of notifications
            if post.id != userData[self.CONSTANTS["DATABASE_COLUMNS"]["users"]["lastCommentId"]] and (
                    post.created > userData[self.CONSTANTS["DATABASE_COLUMNS"]["users"]["lastCommentDate"]]):
                newComments.append(post.id)
            else:
                break

        return newComments

    def notifyNewSubmission(self, post, user, subscriber):
        """ Notify subscriber of new submission

        Args:
            post: new post from user
            user: user who made new post
            subscriber: person to notify
        """
        logging.debug("Notifying user {} of new submission {}".format(user, post))

        # Try a few times
        for attempt in range(10):
            try:
                postInfo = self.reddit.get_submission(submission_id=str(post))
                postSubject = "New post from /u/{} - {}".format(user, postInfo.title)

                # Reddit has a max subject length of 100. Lame
                if (len(postSubject) > 100):
                    postSubject = "New post from /u/{}".format(user)

                postContent = "Hi! User /u/{} has posted a new submission: [{}]({})".format(user, postInfo.title,
                                                                                            postInfo.permalink)

                try:
                    self.reddit.send_message(subscriber[self.CONSTANTS["DATABASE_COLUMNS"]["subscriber"]["subscriber"]],
                                             postSubject, postContent)
                except:
                    logging.error("Unexpected error while sending msg: {}".format(sys.exc_info()[0]))
                else:
                    break
            except Exception, e:
                logging.error("Unexpected error while getting user's post: {}".format(str(e)))
            else:
                break
        else:
            logging.error("Failed to notify user after 10 tries")

    def notifyNewComment(self, comment, user, subscriber):
        """ Notify subscriber of new comment

        Args:
            post: new post from user
            user: user who made new post
            subscriber: person to notify
        """
        logging.debug("Notifying user {} of new comment {}".format(user, comment))

        # Try a few times
        for attempt in range(10):
            try:
                commentInfo = self.reddit.get_info(thing_id="t1_" + str(comment))
                parentInfo = self.reddit.get_info(thing_id=commentInfo.link_id)
                postSubject = "New comment from /u/{} on thread {}".format(user, parentInfo.title)

                # Reddit has a max subject length of 100. Lame
                if (len(postSubject) > 100):
                    postSubject = "New comment from /u/{}".format(user)

                postContent = "Hi! User /u/{} has posted a new [comment]({}) on thread: [{}]({})".format(
                    user, commentInfo.permalink, parentInfo.title, parentInfo.permalink)

                try:
                    self.reddit.send_message(subscriber[self.CONSTANTS["DATABASE_COLUMNS"]["subscriber"]["subscriber"]],
                                             postSubject, postContent)
                except:
                    logging.error("Unexpected error while sending msg: {}".format(sys.exc_info()[0]))
                else:
                    break
            except Exception, e:
                logging.error("Unexpected error while getting user's comment: {}".format(str(e)))
            else:
                break
        else:
            logging.error("Failed to notify user after 10 tries")

    def notifySubscribers(self):
        """ Notify subscribers of any new posts/comments
        """
        for user in self.getUsers():

            for attempt in range(10):
                try:
                    newSubmissions = self.getNewSubmissions(user)
                    newComments = self.getNewComments(user)

                    if newSubmissions or newComments:
                        self.updateLastPost(user)

                        # Notify subscribers
                        for subscriber in self.getSubscribers(user):
                            if subscriber[self.CONSTANTS["DATABASE_COLUMNS"]["subscriber"][
                                    "subscriptionType"]] & self.CONSTANTS["SUBSCRIPTION_TYPE"]["submissions"] > 0:
                                for post in newSubmissions:
                                    self.notifyNewSubmission(post, user, subscriber)
                            if subscriber[self.CONSTANTS["DATABASE_COLUMNS"]["subscriber"][
                                    "subscriptionType"]] & self.CONSTANTS["SUBSCRIPTION_TYPE"]["comments"] > 0:
                                for comment in newComments:
                                    self.notifyNewComment(comment, user, subscriber)
                except Exception, e:
                    logging.error("Unexpected error({}) getting new posts for user {}".format(str(e), user))
                else:
                    break
            else:
                logging.error("Failed ot get new posts for user {} after 10 tries".format(user))
