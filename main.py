'''
# # To Do - Beckon and look at all of the bgg links, give average duration per player for each game

'''
import praw, obot, os, re
from funcs import *
from operator import itemgetter as ig


user_agent = ('Stat Guy 0.1')

while True:
    r = obot.login()
    subreddit = r.get_subreddit('statbot')
    all_comments = subreddit.get_comments()
    c, conn = initsql()
    
    
    
    if not os.path.isfile("posts_replied_to.txt"):
        posts_replied_to = []
    else:
        with open("posts_replied_to.txt", "r") as f:
            posts_replied_to = f.read()
            posts_replied_to = posts_replied_to.split("\n")
            posts_replied_to = filter(None, posts_replied_to)
    
    for comment in all_comments:
        if comment.id not in posts_replied_to: # and comment.author.name != 'stat-bot:
            body = comment.body
            body = re.sub('["]','',body)
            body = body.split(' ', 10000)
            body = [i for i in body if i != ''] # remove any spaces
            
            
            if '/u/stat-bot' in body:
                
                condensed = ' '.join(body)
                query = 'INSERT INTO comments (commentid, username, comment) VALUES ("{cid}","{usr}", "{cmt}")'.format(cid = comment.id, usr = comment.author, cmt = condensed)
                sql(c, query)
                
                ind = body.index("/u/stat-bot")
                # Remove everything before the bot call:
                for i in xrange(ind+1):
                    body.pop(0)
                
                username = body[0]
                kind = ''
                if username == 'about':
                    out = '''Hello!  I am a bot that grabs play data for plays logged on board game geek for a specific user.
\n\nTo call me correctly, use the format:\n\n/u/stat-bot your_username plays startdate enddate \n\nex: /u/stat-bot Octavian plays 2016-1-1 2016-06-30
\n\nMy code is available [here](https://github.com/allisontharp/statbot).
\n\nI am always interested in suggestions for improvement.  If you have any suggestions, please message me!'''
                elif username == 'help':
                    out = 'To call me correctly, use the format:\n\n/u/stat-bot your_username plays startdate enddate \n\nex: /u/stat-bot Octavian plays 2016-1-1 2016-06-30'
                else:
                    error = []
                    try:
                        kind = body[1] ## play or collection
                    except IndexError:
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
                        error.append("- Start date format incorrect.  Expected YYYY-MM-DD, received '{md}'.".format(md = mindate))
                        
                    try:
                        validate_date(maxdate)
                    except ValueError:
                        error.append("- End date format incorrect.  Expected YYYY-MM-DD, received '{md}'.".format(md = maxdate))    
                
                
                    if error == []:
                        if kind == 'plays':     
                            out = queryplay(c, username, mindate = mindate, maxdate = maxdate)
                        else:
                            print "Someone mentioned /u/stat-bot, but didn't call it correctly"
                            out = "You didn't mention what kind of stats you want, or I am having trouble understanding you.  Right now, I only know plays.  Please use '/u/stat-bot help' if you need help."
                    else:
                        out = "It looks like we've had one or more errors:\n\n"
                        out += '\n\n'.join(error)
                        out += "\n\nTo call me correctly, use the format:\n\n/u/stat-bot your_username plays startdate enddate \n\nex: /u/stat-bot Octavian plays 2016-1-1 2016-06-30"
                    
                
                
                comment.reply(out)
                print "Bot replied to : ", comment.body
                posts_replied_to.append(comment.id)
                conn.commit()
  
                
                with open("posts_replied_to.txt", "w") as f:
                    for post_id in posts_replied_to:
                        f.write(post_id + "\n")

    time.sleep(900)
    
    

