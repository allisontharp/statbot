'''
# # To Do - Put in database and compare to other users? Could also have a delta function
            (how many times/hours/games you've played since the last time you asked)
        

'''
import praw, obot, os, re
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

# for submission in subreddit.get_new(limit = 5):
for comment in all_comments:
    if comment.id not in posts_replied_to:
        body = comment.body
        # if re.search("/u/stat-bot", comment.body, re.IGNORECASE):
        if body[0:11] == '/u/stat-bot':
            mindate = ''
            maxdate = ''
            body = body.replace('/u/stat-bot ', '')
            split = body.split(' ',10)
            split = [i for i in split if i != ''] #remove any spaces
            username = split[0]
            kind = split[1] ## play or collection
            try: 
                mindate = split[2] ##
            except IndexError:
                mindate = ''      
            try:
                maxdate = split[3]
            except IndexError:
                maxdate = ''

            if kind == 'plays':     
                queryplay(username, mindate = mindate)
            
            
            #print out
            comment.reply(out)
            print "Bot replied to : ", comment.body
            posts_replied_to.append(comment.id)
            
with open("posts_replied_to.txt", "w") as f:
    for post_id in posts_replied_to:
        f.write(post_id + "\n")

    # time.sleep(1800)
    
    

# # 
# # 
# # 
# # # from decimal import Decimal as dec
# # # from funcs import *
# # # from operator import itemgetter as ig
# # 
# # # print "Username: "
# # # usr = raw_input()
# usr = 'mad4hatter'
# mindate = '2016-11-01'
# maxdate = '2016-11-10'
# 
# games = []
# plays, games = combine_plays(usr, games, mindate=mindate, maxdate=maxdate)
# #plays, games = combine_plays(usr, games)
# 
#  
# tot_time = sum([int(play.duration) for play in plays])
# numplays = sum([int(play.quantity) for play in plays])
# avg_time = tot_time*1.0/numplays
# totpoints = sum([float(play.totscore) for play in plays]) 
# [tot, avg] = userscore(usr, plays)
# 
# 
# data = [(game.name, game.quantity, round(game.totduration*1.0/game.quantity,2),
#          round(game.totscore*1.0/(game.totplayers),2) if game.totplayers != 0 else 0,
#          round(game.userscore*1.0/game.quantity))        
#         for game in games]
# # print ''
# # print 'Total Plays: ' + str(numplays)
# sdata = sorted(data, key=ig(1), reverse=True)
# head = ('Game', 'Total Plays', 'AVG Minutes', 'AVG Score', 'Your AVG')
# sdata = [head] + sdata
# # pprint(sdata, lim=10)
# # 
# # print '---'
# # print '---'
# 
# tbl = rtable(sdata, lim=5)
# 
# print tbl
# # 
