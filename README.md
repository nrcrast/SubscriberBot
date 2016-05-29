# SubscriberBot

# Overview
SubscriberBot is a Reddit bot designed to allow users to subscribe to other users. When a user makes a new post, all users that have subscribed to that user are sent a personal message with a link and title of the new post. 

# Dependencies
* Python 2.7.x
* PyYaml
* Praw
* Sqlite3

# Configuration
SubscriberBot expects a configuration file called config.yaml. See configtemplate.yaml for the format.

# Usage
SubscriberBot can be interacted with via PM or by summoning it in a comment. 

## Subscribing to a user

   * Reply to any post with syntax /u/Subscriber_Bot subscribe [username] [subscriptiontype] where [submissiontype] can be any combination of the words "submissions" and "comments"
   	
   	#eg. 

	  * /u/Subscriber_Bot subscribe elpantalla submissions => subscribes to new submissions by elpantalla
  
	  * /u/Subscriber_Bot subscribe elpantalla => subscribes to new submissions by elpantalla

	  * /u/Subscriber_Bot subscribe elpantalla comments => subscribes to new comments by elpantalla

	  * /u/Subscriber_Bot subscribe elpantalla comments submissions => subscribes to new comments and submissions by elpantalla

   * Send PM to /u/Subscriber_Bot with same syntax (you can leave /u/Subscriber_Bot out of msg body or keep it in)

## Unsubscribing from a user

   * Same as subscribing, except replace 'subscribe' with 'unsubscribe'

## Help

   * Send PM to /u/Subscriber_Bot with 'help' as msg body (subject can be anything)

## Who am I subscribed to?
   
   * Send PM to /u/Subscriber_Bot with 'list' as msg body (subject can be anything)
