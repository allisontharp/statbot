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
        
        
def make_play(date, quantity, duration, location, game, player, totscore, avgscore):
    play = Play(date, quantity, duration, location, game, player, totscore, avgscore)
    return play

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
        
def make_player(name, score, place, winner, new, username):
    player = Player(name, score, place, winner, new, username)
    return player

class Game(object):
    index = int
    name = ''
    quantity = int
    totduration = int
    totscore = float
    userscore = float
    totplayers = float
    plays = []
    
    def __init__(self, index, name, quantity, totduration, totscore, userscore, totplayers, plays):
        self.index = int(index)
        self.name = name
        self.quantity = int(quantity)
        self.totduration = int(totduration)
        self.totscore = float(totscore)
        self.userscore = float(userscore)
        self.totplayers = int(totplayers)
        self.plays = plays
        
def make_game(index, name, quantity, totduration, totscore, userscore, totplayers, plays):
    game = Game(index, name, quantity, totduration, totscore, userscore, totplayers, plays)
    return game

def combine_plays(c, user, games, **kwargs):
    url = 'https://www.boardgamegeek.com/xmlapi2/plays?username='+user
    if len(kwargs) > 0:
        if 'mindate' in kwargs:
            mindate = kwargs['mindate']
            url += '&mindate='+mindate
        if 'maxdate' in kwargs:
            maxdate = kwargs['maxdate']
            url += '&maxdate='+maxdate
    doc = ET.parse(urllib2.urlopen(url)).getroot()

    # Check that it is a valid url
    iserror = doc.get('class')

    if iserror is not None:
        plays = []
        games = []
        print 'Error with URL: {url}'.format(url = url)
    else:
        numplays = doc.get('total')
        allplays = doc.findall('play')
        numpages = int(ceil(int(numplays)*1.0/100))
        
        # print 'NumPlays: ' + str(numplays)
        # print 'NumPages: ' + str(numpages)
        
        for i in range(2,numpages+1):
            newurl = url + '&page=' + str(i)
            new = ET.parse(urllib2.urlopen(newurl)).getroot()
            new = new.findall('play')
            doc.extend(new)
    
        
        
        allplays = doc.findall('play')
        
        cnt = 0
        
        plays = []
        for play in allplays:
            cnt += 1
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
                
            addgame(c, bggid)
            requesterid = addplayerbyusername(c, user) # requester's playerid
            addplay(c, playid, requesterid, bggid, date, dur, loc)
            for players in play.findall('players'): 
                for player in players.findall('player'):
                    
                    name = player.get('name')
                    score = player.get('score')
                    new = player.get('new')
                    place = 15
                    winner = player.get('win')
                    username = player.get('username')
                    userid = player.get('userid')
                    name = player.get('name')
                    new = player.get('new')
        
                    if username == user:
                        userscore = score
                    
                    plyr = make_player(name, score, place, winner, new, username)
                    
                    plyrs.append(plyr)
                    try:
                        totscore += int(score)
                    except ValueError:
                        totscore += 0
                    
                    playerid = addplayerfull(c, name, username, userid)
                    playerplay(c, playid, playerid, userscore, winner, new)
            try:
                avgscore = totscore*1.0/len(plyrs)
            except ZeroDivisionError:
                avgscore = 0
        
    
            ply = make_play(date, quant, dur, loc, game, plyrs, totscore, avgscore)
            
            plays.append(ply)
    
            if [s.index for s in games if s.name == game] == []: # the game is not in the games list 
                try:
                    ind = max([s.index for s in games]) + 1
                except ValueError, TypeError: # first game
                    ind = 0
                
                games.append(make_game(ind, game, quant, dur, totscore, userscore, len(plyrs), [ply]))
                
            else: # the game is in the games list
                
                ind = [s.index for s in games if s.name == game][0]
                games[ind].quantity += int(quant)
                games[ind].totduration += int(dur)
                games[ind].totscore += float(totscore)
                games[ind].totplayers += int(len(plyrs))
                games[ind].plays.append(ply)
                games[ind].userscore += float(userscore)

            
            
        
    return plays, games

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

def queryplay(c, username, **kwargs):
    games = []
    mindate = ''
    maxdate = ''
    if 'mindate' in kwargs:
        mindate = kwargs['mindate']
    if 'maxdate' in kwargs:
        maxdate = kwargs['maxdate']
    plays, games = combine_plays(c, username, games, mindate=mindate, maxdate=maxdate)
    
    if len(plays) > 0 and len(games) > 0:
    
        tot_time = sum([int(play.duration) for play in plays])
        numplays = sum([int(play.quantity) for play in plays])
        hour = round(tot_time*1.0/60,2)
        
        data = [(game.name, game.quantity, round(game.totduration*1.0/game.quantity,2),
                round(game.totscore*1.0/(game.totplayers),2) if game.totplayers != 0 else 0,
                round(game.userscore*1.0/game.quantity))        
               for game in games]
        
        sdata = sorted(data, key=ig(1), reverse=True)
        head = ('Game', 'Total Plays', 'AVG Minutes', 'AVG Score For Your Logged Plays', 'Your AVG Score')
        sdata = [head] + sdata
        
        
        tbl = rtable(sdata, lim=10)
        
        out = '''{un}'s play summary from {d}:\n
**Total Plays:** {totplay}\n
**Total Time:** {mn} min ({hr} hours)\n\n
    '''.format(un = username, d = mindate, totplay = numplays, mn = tot_time, hr = hour )
        out += tbl
    
    else:
        out = "Oops! I seem to have an error.  Check that the username ({un}) is valid and that it have plays within the date range ({mind} - {maxd}).".format(un = username, mind = mindate, maxd=maxdate)
    return out

def validate_date(txt):
    if len(txt) > 0:
        try:
            datetime.datetime.strptime(txt, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Incorrect data format, should be YYYY-MM-DD')
             
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
                  username VARCHAR(200), userid INT)")
        
    c.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'playerplay'")
    if not c.fetchall(): # if the games table doesn't exist, create it
        print "Creating playerplay Table"
        c.execute("CREATE TABLE playerplay(playid INTEGER NOT NULL, playerid INTEGER NOT NULL, score INTEGER, winner INTEGER(0,1), new INTEGER(0,1), PRIMARY KEY (playid, playerid))")
        
    c.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'comments'")
    if not c.fetchall(): # if the games table doesn't exist, create it
        print "Creating comments Table"
        c.execute("CREATE TABLE comments(commentid VARCHAR(100) PRIMARY KEY, username VARCHAR(200), date DATETIME DEFAULT current_timestamp, comment varchar(10000))")
        
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

            
            query = "INSERT INTO games VALUES ({bid}, '{nm}', {yr}, {mn}, {mx}, {isx})".format(bid = bggid, nm = name, yr = year, mn = minplayer, mx = maxplayer, isx = isexpansion)

            sql(c, query)
    except:
        print "Error occurred with adding bgg id {bid} to the db.".format(bid = bggid)
        


def addplayerfull(c, name, username, userid):
    try:
        playerid = findplayerfull(c, name, userid)
        if playerid == []: # player doesn't exist
            query = "INSERT INTO player (name, username, userid) VALUES ('{nm}', '{un}', {uid})".format(nm=name, un=username, uid = userid)
            sql(c,query)
            query  = "SELECT max(playerid) FROM player"
            playerid = sql(c, query)[0][0]

        return playerid
    except:
        print "Error adding player to player table.  Name: '{nm}'".format(nm = name)

def findplayerfull(c, name, userid):
    try:
        query = "SELECT playerid FROM player WHERE name = '{nm}' AND userid = {uid}".format(nm = name, uid = userid)
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
        query = "SELECT playerid FROM player WHERE username = '{usr}'".format(usr = username)
        playerid = sql(c, query)
        
    except:
        print "Error finding player (username: '{usr}').".format(usr = username)
        playerid = 0
    return playerid


def addplayerbyusername(c, username):
    try:
        playerid = findplayerbyusername(c, username)
        if playerid == []: # user not in database
            url = 'https://www.boardgamegeek.com/xmlapi2/user?name={usr}'.format(usr = username)
            doc = ET.parse(urllib2.urlopen(url)).getroot()
            firstname = doc.find('firstname').get('value')
            lastname = doc.find('lastname').get('value')

            name = firstname + ' ' + lastname
            userid = doc.get('id')
            
            query = "INSERT INTO player (name, username, userid) VALUES ('{nm}', '{un}', {uid})".format(nm = name, un = username, uid = userid)
            sql(c, query)
            playerid = sql(c, "SELECT max(playerid) FROM player")
        return playerid[0][0]
    except:
        print "Error adding user to database (username: '{usr}').".format(usr = username)








