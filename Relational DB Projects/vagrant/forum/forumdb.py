#
# Database access functions for the web forum.
# 
import psycopg2
import time

## Get posts from database.
def GetAllPosts():
    DB = psycopg2.connect("dbname=forum")
    c = DB.cursor()
    c.execute("UPDATE posts SET content = 'Cheese' WHERE content LIKE '%Spam, spam, spam, spam%Wonderful spam, glorious spam!%'")
    c.execute("DELETE FROM posts WHERE content LIKE '%Cheese%'")
    c.execute("SELECT time,content FROM posts ORDER BY time DESC")
    posts = ({'content': str(row[1]), 'time': str(row[0])}
             for row in c.fetchall())
    DB.close()
    return posts

## Add a post to the database.
def AddPost(content):
    DB = psycopg2.connect("dbname=forum")
    c = DB.cursor()
    data = (content,)
    c.execute("INSERT INTO posts (content) VALUES (%s)", data) # getting the comma to replace the % was issue
    DB.commit()
    DB.close()
