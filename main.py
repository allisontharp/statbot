'''
# # To Do - Beckon and look at all of the bgg links, give average duration per player for each game
# # To Do - Ignore play duration where duration is 0.
# # To Do - Incorporate play quantity
'''
import praw, obot, re
from funcs_sql import *
from operator import itemgetter as ig


user_agent = ('Stat Guy 0.1')

while True:
    r = obot.login()
    subreddit = r.get_subreddit('statbot')
    all_comments = subreddit.get_comments()
    c, conn = initsql()
    
    comm_replied_to = []
    
    query = "SELECT commentid FROM comments"
    out = sql(c, query)
    comm_replied_to = [str(i[0]) for i in out]
    
    for comment in all_comments:
        if comment.id not in comm_replied_to: # and comment.author.name != 'stat-bot:
            body = comment.body
            body = body.replace('\n', ' ')
            body = re.sub('["]','',body)
            body = body.split(' ', 10000)
            body = [i for i in body if i != ''] # remove any spaces
            
            if '/u/stat-bot' in body:
               # print body

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
                        mindate = validate_date(mindate)
                    except ValueError:
                        error.append("- Start date format incorrect.  Expected YYYY-MM-DD, received '{md}'.".format(md = mindate))
                        
                    try:
                        maxdate = validate_date(maxdate)
                    except ValueError:
                        error.append("- End date format incorrect.  Expected YYYY-MM-DD, received '{md}'.".format(md = maxdate))    
                
                
                    if error == []:
                        isfail = 0
                        if kind == 'plays':     
                            out = playsmain(c, username, mindate = mindate, maxdate = maxdate)
                        elif kind == 'collection':
                            out = collectionmain(c, username, conn = conn)
                        else:
                            print "Someone mentioned /u/stat-bot, but didn't call it correctly"
                            out = "You didn't mention what kind of stats you want, or I am having trouble understanding you.  Right now, I only know plays.  Please use '/u/stat-bot help' if you need help."
                    else:
                        isfail = 1
                        out = "It looks like we've had one or more errors:\n\n"
                        out += '\n\n'.join(error)
                        out += "\n\nTo call me correctly, use the format:\n\nyour_username plays startdate enddate \n\nex: /u/stat-bot mad4hatter plays 2016-01-01 2016-06-30"
                    
                
                #print out
                comment.reply(out)
                print "Bot replied to : ", comment.body
                query = '''INSERT INTO comments (commentid, username, comment, isfail, bggusername) VALUES
("{cid}", "{usr}", "{cmt}", {isfail}, "{bgg}")'''.format(cid = comment.id, usr = comment.author, cmt = comment.body, isfail = isfail, bgg = username)
                
                conn.commit()
                time.sleep(30)
    
    time.sleep(900)
    
    

