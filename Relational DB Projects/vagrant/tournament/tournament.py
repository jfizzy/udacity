#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    DB = connect()
    c = DB.cursor()
    query = "DELETE FROM Matches;"
    c.execute(query)
    query = "UPDATE Players SET matches='0',wins='0'"
    c.execute(query)
    DB.commit()
    DB.close()

def deletePlayers():
    """Remove all the player records from the database."""
    DB = connect()
    c = DB.cursor()
    query = "DELETE FROM Players;"
    c.execute(query)
    DB.commit()
    DB.close()

def countPlayers():
    """Returns the number of players currently registered."""
    DB = connect()
    c = DB.cursor()
    query = "SELECT count(*) FROM Players;"
    c.execute(query)
    rows = c.fetchall() #need to figure out how to get this to return the value properly
    result = ''
    for row in rows:
        result = row[0]
    DB.close()
    if not result:
        return 0
    else:
        return result

def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    DB = connect()
    c = DB.cursor()
    query = "INSERT INTO Players (name) VALUES (%s);"
    c.execute(query, (name,))
    DB.commit()
    DB.close()

def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    DB = connect()
    c = DB.cursor()
    query = "SELECT * FROM Players ORDER BY wins DESC"
    c.execute(query)
    rows = c.fetchall()
    DB.close()
    return rows

def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    DB = connect()
    c = DB.cursor()
    # insert match
    query = "INSERT INTO Matches (winner,loser) VALUES ((%s),(%s));"
    c.execute(query, (winner,loser))
    # get winner wins
    query = "SELECT wins,matches FROM Players WHERE id=(%s);"
    c.execute(query, (winner,))
    wws = c.fetchall()
    ww = ''
    wm = ''
    for row in wws:
        ww = row[0]
        wm = row[1]
    ww = int(ww) + 1
    wm = int(wm) + 1
    # update winner
    query = "UPDATE Players SET wins=(%s),matches=(%s) WHERE id=(%s);"
    c.execute(query, (str(ww),str(wm),winner)) # update the winner's wins and matches
    # get loser matches
    query = "SELECT matches FROM Players WHERE id=(%s);"
    c.execute(query, (loser,))
    lms = c.fetchall()
    lm = ''
    for row in lms:
        lm = row[0]
    lm = int(lm) + 1
    # update loser
    query = "UPDATE Players SET matches=(%s) WHERE id=(%s);"
    c.execute(query, (str(lm),loser)) # update the loser's matches

    DB.commit() # commits all the update and insert queries to the DB

    DB.close()
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    DB = connect()
    c = DB.cursor()
    query = "SELECT p.id,p.name FROM Players as p LEFT JOIN Matches as m ON p.id = m.winner ORDER BY wins DESC;"
    c.execute(query)
    players = c.fetchall()
    if len(players) % 2 == 1:
        bye = players.pop()
    # need to update the popee
    returnList = []
    for p1,p2 in zip(players[0::2], players[1::2]): # this is a way of making a list of pairs
        returnList.append((p1[0], p1[1], p2[0], p2[1]))
    return returnList
    DB.close()

