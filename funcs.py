import unicodedata
from xml.etree import ElementTree as ET
from math import ceil
import urllib2
import time

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
        
    # def __repr__(self):
    #     return '{}: {} {} {} {} {}'.format(self.__class__.__name__,
    #             self.date,
    #             self.quantity,
    #             self.duration,
    #             self.game,
    #             self.totscore,
    #             self.avgscore)
    # 
    # def __cmp__(self, other):
    #     if hasattr(other, 'avgscore'):
    #         return self.avgscore.__cmp__(other.avgscore)
        
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

def combine_plays(user, games, **kwargs):
    url = 'https://www.boardgamegeek.com/xmlapi2/plays?username='+user
    newurl = ''
    if len(kwargs) > 0:
        if 'mindate' in kwargs:
            mindate = kwargs['mindate']
            url += '&mindate='+mindate
        if 'maxdate' in kwargs:
            maxdate = kwargs['maxdate']
            url += '&maxdate='+maxdate
    doc = ET.parse(urllib2.urlopen(url)).getroot()

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
        for item in play.findall('item'):
            game =  item.get('name')
            game = strip_accents(game)
            game = game.encode("ascii", "ignore")
        for players in play.findall('players'): 
            for player in players.findall('player'):
                
                name = player.get('name')
                score = player.get('score')
                new = player.get('new')
                place = 15
                winner = player.get('win')
                username = player.get('username')
                
                if username == user:
                    userscore = score
                
                plyr = make_player(name, score, place, winner, new, username)
                
                plyrs.append(plyr)
                try:
                    totscore += int(score)
                except ValueError:
                    totscore += 0
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
            print 'limit'
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

def queryplay(username, **kwargs):
    games = []
    plays, games = combine_plays(username, games, mindate=mindate)
    
    tot_time = sum([int(play.duration) for play in plays])
    numplays = sum([int(play.quantity) for play in plays])
    hour = round(tot_time*1.0/60,2)
    # 
    # out = '''Congratulations {us}!  You have played a total of {tm} minutes ({hr} hrs) and {num} games since {dt}            
    # '''.format(us = username, tm = tot_time, num=numplays, dt = mindate )
    
    data = [(game.name, game.quantity, round(game.totduration*1.0/game.quantity,2),
            round(game.totscore*1.0/(game.totplayers),2) if game.totplayers != 0 else 0,
            round(game.userscore*1.0/game.quantity))        
           for game in games]
    
    sdata = sorted(data, key=ig(1), reverse=True)
    head = ('Game', 'Total Plays', 'AVG Minutes', 'AVG Score', 'Your AVG')
    sdata = [head] + sdata
    
    
    tbl = rtable(sdata, lim=10)
    
    out = '''{un}'s play summary from {d}:\n
**Total Plays:** {totplay} \n
**Total Time:** {mn} min ({hr} hours) \n\n
    '''.format(un = username, d = mindate, totplay = numplays, mn = tot_time, hr = hour )
    out += tbl

    return out

