'''
# # To Do - Put in database and compare to other users? Could also have a delta function
            (how many times/hours/games you've played since the last time you asked)
        

'''
import praw, obot, os
from funcs import *
from operator import itemgetter as ig


user_agent = ('Stat Guy 0.1')


# while True:
r = obot.login()
subreddit = r.get_subreddit('statbot')
all_comments = subreddit.get_comments()



if not os.path.isfile("posts_replied_to.txt"):
    posts_replied_to = []
else:
    with open("posts_replied_to.txt", "r") as f:
        posts_replied_to = f.read()
        posts_replied_to = posts_replied_to.split("\n")
        posts_replied_to = filter(None, posts_replied_to)

for comment in all_comments:
    if comment.id not in posts_replied_to:
        body = comment.body
        body = body.split(' ', 10000)
        body = [i for i in body if i != ''] # remove any spaces
        if '/u/stat-bot' in body:
            ind = body.index("/u/stat-bot")
            # Remove everything before the bot call:
            for i in xrange(ind+1):
                body.pop(0)
            
            username = body[0]
            kind = body[1] ## play or collection
            error = []
            try: 
                mindate = body[2] ##
            except IndexError:
                mindate = ''
                
            try:
                maxdate = body[3]
            except IndexError:
                maxdate = ''
            
            try:
                validate_date(mindate)
            except ValueError:
                error.append('- Start date format incorrect.  Expected YYYY-MM-DD, received "{md}".'.format(md = mindate))
                
            try:
                validate_date(maxdate)
            except ValueError:
                error.append('- End date format incorrect.  Expected YYYY-MM-DD, received "{md}".'.format(md = maxdate))    
            
            if error == []:
                if kind == 'plays':     
                    out = queryplay(username, mindate = mindate, maxdate = maxdate)
                else:
                    print "Someone mentioned /u/stat-bot, but didn't call it correctly"
            else:
                out = "It looks like we've had one or more errors:\n\n"
                out += '\n\n'.join(error)
                out += "\n\nTo call me correctly, use the format:\n\n/u/stat-bot your_username plays startdate enddate \n\nex: /u/stat-bot Octavian plays 2016-1-1 2016-06-30"
                
            
            
            #print out
            comment.reply(out)
            print "Bot replied to : ", comment.body
            posts_replied_to.append(comment.id)
        elif '/u/stat-bot' in body:
            out = ""
            print '/u/stat-bot was in a comment, but not the first word'
            
with open("posts_replied_to.txt", "w") as f:
    for post_id in posts_replied_to:
        f.write(post_id + "\n")

    # time.sleep(1800)
    
    

