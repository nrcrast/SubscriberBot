import praw
import sqlite3

class SubScriber:

    def __init__(self):

        self.reddit = praw.Reddit(user_agent='python:AutoSubscriber:v0.1 (by /u/elpantalla)')
        self.reddit.login('Subscriber_Bot', 'password', disable_warning=True)
        self.conn = sqlite3.connect('C:\\Users\\nrcra\\subscriptions.db')
        self.db = self.conn.cursor()


    def getLastPost( self, user ):
        redditor = self.reddit.get_redditor( user )
        comment = redditor.get_submitted(sort='new', time='all', limit=1)
        for c in comment:
            return c.id

        return None


    def processMention( self, author, msgBody ):
        user = msgBody.split(" ")[1]

        # Get last post of user
        lastPost = self.getLastPost( user )

        # Is user in database
        print("In DB: {}".format(self.isUserInDb(user)))
        print("Subscribed: {}".format(self.isAuthorAlreadySubscribed(user,author)))
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

    def checkForMentions( self ):
    	for msg in self.reddit.get_mentions( limit=None ):
    		print("Found mention by {}: {}".format(msg.author, msg.body))
    		self.processMention( msg.author, msg.body )



class Notifier:

    def __init__(self):

        self.reddit = praw.Reddit(user_agent='python:AutoSubscriber:v0.1 (by /u/elpantalla)')
        self.reddit.login('Subscriber_Bot', 'password', disable_warning=True)
        self.conn = sqlite3.connect('C:\\Users\\nrcra\\subscriptions.db')
        self.db = self.conn.cursor()

    def getSubscribers( self, user ):
    	return [sub[0] for sub in self.db.execute("select subscriber from subscribers where user = ?",[str(user)])]

    def getLastSavedPost( self, user ):
    	return self.db.execute("select lastpostid from users where user = ?",[str(user)])[0]

    def getUsers( self ):
    	return [user[0] for user in self.db.execute("select user from users")]

    def getNewPosts( self, user ):
    	lastSavedPost = self.getLastSavedPost( user )

    	redditor = self.reddit.get_redditor( user )
    	newPosts = []
        for post in redditor.get_submitted(sort='new', time='all', limit=50):
        	if post.id != lastSavedPost:
        		newPosts.append( post.id )

    def notifySubscribers( self ):
        for user in self.getUsers():
        	newPosts = self.getNewPosts( user )

        	if newPosts:
        		# Save the first new post
        		# TODO nick make a common function class or something. Not currently organized very well.
        		self.db.execute("delete from users where user = ?", [str(user)] )
    		    self.db.execute("insert into users(user,lastpostid) values(?,?)", [str(user),str(newPosts[0]] )
    		    self.conn.commit();

    		    # Notify subscribers
    		    for subscriber in self.getSubscribers( user ):
    		    	for post in newPosts:

    		    	 r.send_message(subsriber, "New post from /u/{}".format(user), 
    		    	 	"Hi! User /u/{} has posted a new submission: {}".format(user, r.get_submission(submission_id = post ).permalink))




# r = praw.Reddit(user_agent='python:AutoSubscriber:v0.1 (by /u/elpantalla)')

# r.login('Subscriber_Bot', 'Reptar1!', disable_warning=True)

# for msg in r.get_mentions( limit=None ):
#       processMention( r, msg.author, msg.body )

bot = SubScriber()
#print(bot.checkForMentions())
notifier = Notifier()
print(notifier.getSubscribers('elpantalla'))