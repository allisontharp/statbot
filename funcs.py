import unicodedata
from xml.etree import ElementTree as ET
from math import ceil
import urllib2, time, datetime, sqlite3
from operator import itemgetter as ig




def strip_accents(s):
    s = unicode(s)
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

class Play(object):
    date = ''
    quantity = int
    duration = int
    location = ''
    game = ''
    player = []
    totscore = float
    avgscore = float
    
    def __init__(self, date, quantity, duration, location, game, player, totscore, avgscore):
        self.date = date
        self.quantity = quantity
        self.duration = duration
        self.location = location
        self.game = game
        self.player = player
        self.totscore = totscore
        self.avgscore = avgscore
    
    def __getitem__(self, key):
        return self.__getattribute__(key)
        

class Player(object):
    name = ""
    score = 0
    place = 0
    winner = 0
    new = 0
    username = ''
    
    def __init__(self, name, score, place, winner, new, username):
        self.name = name
        self.score = score
        self.place = place
        self.winner = winner
        self.new = new
        self.username = username
        

class Game(object):
    index = int
    name = ''
    quantity = int
    totduration = int
    avgduration = int
    totscore = float
    avgscore = float
    reqavgscore = float
    userscore = float
    totplayers = float

    
    def __init__(self, index, name, quantity, totduration, avgduration, totscore, avgscore, reqavgscore, userscore, totplayers):
        self.index = int(index)
        self.name = name
        self.quantity = int(quantity)
        self.totduration = int(totduration)
        self.avgduration = float(avgduration)
        self.totscore = float(totscore)
        self.avgscore = float(avgscore)
        self.reqavgscore = float(reqavgscore)
        self.userscore = float(userscore)
        self.totplayers = int(totplayers)
        
        

def combine_plays(c, user, games, **kwargs):
    url = 'https://www.boardgamegeek.com/xmlapi2/plays?username='+user
    if len(kwargs) > 0:
        if 'mindate' in kwargs:
            mindate = kwargs['mindate']
            url += '&mindate='+mindate
        if 'maxdate' in kwargs:
            maxdate = kwargs['maxdate']
            url += '&maxdate='+maxdate
    print url
    doc = ET.parse(urllib2.urlopen(url)).getroot()

    # Check that it is a valid url
    iserror = doc.get('class')

    if iserror is not None:
        print 'Error with URL: {url}'.format(url = url)
    else:
        numplays = doc.get('total')
        allplays = doc.findall('play')
        numpages = int(ceil(int(numplays)*1.0/100))
        
        
        for i in range(2,numpages+1):
            newurl = url + '&page=' + str(i)
            new = ET.parse(urllib2.urlopen(newurl)).getroot()
            new = new.findall('play')
            doc.extend(new)
    

        allplays = doc.findall('play')

        for play in allplays:
            plyrs = []
            totscore = 0
            userscore = 0
            
            loc = play.get('location')
            dur = play.get('length')
            quant = play.get('quantity')
            date = play.get('date')
            playid = int(play.get('id'))
            for item in play.findall('item'):
                game =  item.get('name')
                game = strip_accents(game)
                game = game.encode("ascii", "ignore")
                bggid = item.get('objectid')

            addgame(c, bggid)   # Add game to db
            requesterid = addplayerbyusername(c, user) # requester's playerid

            addplay(c, playid, requesterid, bggid, date, dur, loc) # add play to db
            
            for players in play.findall('players'): 
                for player in players.findall('player'):
                    
                    name = player.get('name')
                    score = player.get('score')
                    score = 0 if score == '' else score
                    new = player.get('new')
                    place = 15
                    winner = player.get('win')
                    username = player.get('username')
                    userid = player.get('userid')
                    name = player.get('name')
                    new = player.get('new')
        
                    if username == user:
                        userscore = score
                    
                    try:
                        totscore += int(score)
                    except ValueError:
                        totscore += 0

                    playerid = addplayerfull(c, name, username, userid, requesterid) # add player to db
                    playerplay(c, playid, playerid, userscore, winner, new) # link player to play indb
            


def userscore(user, plays):
    totscore = 0
    totplays = 0
    for play in plays:
        totplays += 1
        for i in xrange(len(play.player)):
            if play.player[i].username.lower() == user.lower():
                try:
                    totscore += float(play.player[i].score)
                except ValueError:
                    totscore += 0
    return round(totscore,2), round(totscore*1/totplays,2)

def findind(games, game):
    ind = [s.index for s in games if s.name == game][0]
    return ind

def pprint(out, **kwargs):
    numCol = len(out[0])-1
    s = "{:<75} "
    
    for col in xrange(numCol):
        s += "{: <15} "
        
    if len(kwargs) > 0:
        if 'lim' in kwargs:
            i = 0
            lim = kwargs['lim']
            for row in out:
                if i <= lim:
                    print (s.format(*row))
                    i += 1
    else: 
        for row in out:
            print(s.format(*row))
            
def rtable(data, **kwargs):
    tbl = ''
    
    numCol = len(data[0])
    align = 'c'
    
    for col in xrange(numCol):
        tbl += str(data[0][col])
        if col != numCol-1:
            tbl += '|'

            
    tbl += '\n'
    data.pop(0)
    for col in xrange(numCol):
        tbl += ':--'
        if col != numCol-1:
            tbl+= '|'

    tbl += '\n'
    if len(kwargs) > 0:
        if 'lim' in kwargs:
            i = 0
            lim = kwargs['lim']
            for row in data:
                if i <= lim:
                    for col in xrange(len(row)):
                        tbl += str(row[col])
                        if col != numCol-1 :
                            tbl += '|'
                        else:
                            tbl += '\n'
                    i += 1
    else:
        for row in data:
            for col in xrange(len(row)):
                tbl += str(row[col])
                if col != numCol-1 :
                    tbl += '|'
                else:
                    tbl += '\n'
    
    return tbl

def playsmain(c, username, **kwargs):
    games = []
    mindate2 = ''
    maxdate2 = ''

    if 'mindate' in kwargs:
        mindate = kwargs['mindate']
        if mindate != '':
            mindate2 = "AND p.date >= '{mindate}'".format(mindate = mindate)
    if 'maxdate' in kwargs:
        maxdate = kwargs['maxdate']
        if maxdate != '':
            maxdate2 = "AND p.date <= '{maxdate}'".format(maxdate = maxdate)
    combine_plays(c, username, games, mindate=mindate, maxdate=maxdate)
    requestid = findplayerbyusername(c, username)
    
    
    query = '''
SELECT g.name, count(p.playid) as tot, round(sum(playdur.duration)*1.0/count(playdur.playid),2), round(sum(pp.score)*1.0/count(p.playid),2), round(sum(rpp.score)*1.0/count(p.playid),2)
FROM plays p
LEFT JOIN games g ON g.bggid = p.bggid
LEFT JOIN plays playdur ON playdur.playid = p.playid AND playdur.duration > 0
LEFT JOIN playerplay pp ON pp.playid = p.playid
LEFT JOIN playerplay rpp ON rpp.playid = p.playid AND rpp.playerid = {reqid}
WHERE p.playerid = {reqid} {mindate} {maxdate}
GROUP BY g.bggid ORDER BY tot desc limit 10
    '''.format(reqid = requestid, mindate = mindate2, maxdate = maxdate2)
    
    out = sql(c, query)

    head = ('Game', 'Total Plays', 'AVG Minutes', 'AVG Score For Your Logged Plays', 'Your AVG Score')
    out = [head] + out
    
    tbl = rtable(out, lim=10)

    query = '''
SELECT count(p.playid), sum(p.duration)
FROM plays p
WHERE p.playerid = {reqid} {mindate} {maxdate}
    '''.format(reqid = requestid, mindate = mindate2, maxdate = maxdate2)
    
    summary = sql(c,query)

    numplays = summary[0][0]
    try:
        tot_time = summary[0][1]
        hour = tot_time*1.0/60
    except TypeError:
        tot_time = 0
        hour = 0

    if numplays > 0:
        out = '''{un}'s play summary from {d}:\n
**Total Plays:** {totplay}\n
**Total Time:** {mn} min ({hr} hours)\n\n
        '''.format(un = username, d = mindate, totplay = numplays, mn = tot_time, hr = round(hour,2) )
        out += tbl
    else:
        out = "{usr} has 0 recorded plays on BGG for the requested date range ({mindate} - {maxdate}).".format(usr = username, mindate = mindate, maxdate = maxdate)
    
    
    return out

def validate_date(txt):
    if len(txt) > 0:
        try:
            tmp = datetime.datetime.strptime(txt, '%Y-%m-%d')
            out = tmp.strftime('%Y-%m-%d')
            
            
        except ValueError:
            raise ValueError('Incorrect data format, should be YYYY-MM-DD')
    else:
        out = ''
    
    return out
             
def sql(c, query):
    c.execute(query)
    
    out =  c.fetchall()
    return out
             
def initsql():
    db_loc = 'sqlbot.sqlite'
    conn = sqlite3.connect(db_loc)
    c = conn.cursor()
    
    c.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'games'")
    if not c.fetchall(): # if the games table doesn't exist, create it
        print "Creating games Table"
        c.execute("CREATE TABLE games(bggid INTEGER PRIMARY KEY, name VARCHAR(50) NOT NULL, year INTEGER, minplayers INTEGER, maxplayers INTEGER, isexapansion INTEGER(1,0))")
        
    c.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'plays'")
    if not c.fetchall(): # if the games table doesn't exist, create it
        print "Creating plays Table"
        c.execute("CREATE TABLE plays(playid INTEGER PRIMARY KEY, playerid INTEGER NOT NULL, bggid INTEGER NOT NULL,date DATETIME NOT NULL,\
duration INTEGER,location varchar(200), datecreated DATETIME DEFAULT current_date)")
        
    c.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'player'")
    if not c.fetchall(): # if the games table doesn't exist, create it
        print "Creating player Table"
        c.execute("CREATE TABLE player(playerid INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(200),  \
username VARCHAR(200), userid INT, requesterid INT)")
        
    c.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'playerplay'")
    if not c.fetchall(): # if the games table doesn't exist, create it
        print "Creating playerplay Table"
        c.execute("CREATE TABLE playerplay(playid INTEGER NOT NULL, playerid INTEGER NOT NULL, score INTEGER, winner INTEGER(0,1), new INTEGER(0,1), PRIMARY KEY (playid, playerid))")
        
    c.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'comments'")
    if not c.fetchall(): # if the games table doesn't exist, create it
        print "Creating comments Table"
        c.execute("CREATE TABLE comments(commentid VARCHAR(100) PRIMARY KEY, username VARCHAR(200), date DATETIME DEFAULT current_timestamp, comment varchar(10000), isfail INTEGER(0,1), bggusername varchar(200))")

    
        
    return c, conn


def addgame(c, bggid):
    # Check if game is in db:
    try:
        query = "SELECT bggid FROM games WHERE bggid = {bid}".format(bid = bggid)
        out = sql(c, query)

        if len(out) == 0: # game does not exist
            url  ='https://www.boardgamegeek.com/xmlapi2/thing?stats=1&type=boardgame,boardgameexpansion&id={bid}'.format(bid = bggid)
            doc = ET.parse(urllib2.urlopen(url)).getroot()
            item = doc.findall('item')


            bgcheck = item[0].get('type')

            if bgcheck == 'boardgame':
                isexpansion = 0
            else:
                isexpansion = 1
            
            minplayer = item[0].findall('minplayers')[0].get('value')
            maxplayer = item[0].findall('maxplayers')[0].get('value')
            year = item[0].findall('yearpublished')[0].get('value')
            
            allnames = item[0].findall('name')
            name = [i.get('value') for i in allnames if i.get('type') == 'primary']
            name = name[0]

            
            query = 'INSERT INTO games VALUES ({bid}, "{nm}", {yr}, {mn}, {mx}, {isx})'.format(bid = bggid, nm = name, yr = year, mn = minplayer, mx = maxplayer, isx = isexpansion)

            sql(c, query)
    except:
        print "Error occurred with adding bgg id {bid} to the db (Video game/RPG?).".format(bid = bggid)
        


def addplayerfull(c, name, username, userid, requesterid):
    try:
        playerid = findplayerfull(c, name, userid, requesterid)
        if playerid == 0 or playerid == []: # player doesn't exist
            query = 'INSERT INTO player (name, username, userid, requesterid) VALUES ("{nm}", "{un}", {uid}, {rid})'.format(nm=name, un=username, uid = userid, rid = requesterid)
            sql(c,query)
            query  = "SELECT max(playerid) FROM player"
            playerid = sql(c, query)[0][0]

        return playerid
    except:
        print "Error adding player to player table.  Name: '{nm}'".format(nm = name)

def findplayeruserid(c, userid):
    try:
        query = 'SELECT playerid FROM player WHERE userid = {uid}'.format(nm = name, uid = userid)
        playerid = sql(c, query)
        if playerid != 0:
            playerid = playerid[0][0]
        else:
            playerid = 0
        return playerid
    except:
        print "Error finding player (name: '{nm}', userid: {uid})".format(nm = name, uid = userid)

def findplayerfull(c, name, userid, requesterid):

    try: 
        query = 'SELECT playerid FROM player WHERE userid = {uid}'.format(nm = name, uid = userid)
        playerid = sql(c, query)
        if playerid != []:
            playerid = playerid[0][0]
        else:
            query = 'SELECT playerid FROM player WHERE name = "{nm}" AND requesterid = {uid}'.format(nm = name, uid = requesterid)
            playerid = sql(c, query)
            if playerid != []:
                playerid = playerid[0][0]
            else:
                playerid = []
        return playerid
        
        
        
        
        
        

    except:
        print "Error finding player (name: '{nm}', userid: {uid})".format(nm = name, uid = userid)
    

def addplay(c, playid, playerid, bggid, date, duration, location):
    try:
        query = "SELECT * FROM plays WHERE playid = {play}".format(play = playid)
        out = sql(c, query)
        if out == []:
            query = 'INSERT INTO plays (playid, playerid, bggid, date, duration, location) VALUES ({playid}, {playerid}, {bid}, "{dt}", {dur}, "{loc}")'.format(playid = playid, playerid = playerid, bid = bggid, dt = date, dur = duration, loc = location)
            sql(c, query)
            playid = "SELECT max(playid) FROM plays"
    except:
        print "Error adding play to play table (playid: {playid} ).".format(playid = playid)
        playid = 0
    return playid


def playerplay(c, playid, playerid, score, win, new):
    try:
        query = "SELECT playid, playerid FROM playerplay WHERE playid = {play} AND playerid = {player}".format(play = playid, player = playerid)
        out = sql(c, query)
        if out == []:
            query = "INSERT INTO playerplay VALUES ({play}, {player}, {score}, {win}, {new})".format(play = playid, player=playerid, score = score, win = win, new = new)
            sql(c, query)
    except:
        print "Error adding playerplay entry.  Playid: {play}, Playerid: {player}".format(play = playid, player = playerid)

def findplayerbyusername(c, username):
    try:
        query = 'SELECT playerid FROM player WHERE username = "{usr}"'.format(usr = username)
        playerid = sql(c, query)[0][0]
        
    except IndexError: #username not in the database
        playerid = 0
    return playerid


def addplayerbyusername(c, username):
    try:
        playerid = findplayerbyusername(c, username)
        if playerid == 0: # user not in database
            url = 'https://www.boardgamegeek.com/xmlapi2/user?name={usr}'.format(usr = username)
            doc = ET.parse(urllib2.urlopen(url)).getroot()
            firstname = doc.find('firstname').get('value')
            lastname = doc.find('lastname').get('value')

            name = firstname + ' ' + lastname
            userid = doc.get('id')
            
            playerid = addplayerfull(c, name, username, userid, userid)
        return playerid
    except:
        print "Error adding user to database (username: '{usr}').".format(usr = username)








