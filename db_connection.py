import sqlite3
import secrets
import datetime
from sqlite3.dbapi2 import Cursor

# initializing the db that will hold the articles to be voted
#db = sqlite3.connect("articles.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) 
db = sqlite3.connect("articles.db") 

# get a Chuck Norris joke out of the db and send it back
def get_chuck():
    c = db.cursor()
    c.execute("SELECT text from chuck ORDER BY RANDOM() LIMIT 1")
    data = c.fetchall()
    c.close()
    gag = data[0][0]
    return gag

# register a new user in the db of the bot
def db_register(discord_ID, discord_user, hive_user):
    return_data = {}
    # Check if the discord or the steem user has already been registered
    c = db.cursor()
    c.execute("SELECT * FROM users where discordname = ? OR hivename = ?", (discord_user, hive_user))
    result = c.fetchall()
    if len(result) == 0:
        return_data["error"] = 0
        return_data["token"] = secrets.token_hex(32)
        #print (token)
        today = datetime.datetime.today()
        datarow=(discord_ID, discord_user, hive_user, return_data["token"], "pending hive", today, 0)
        c.execute ("INSERT INTO users VALUES(?,?,?,?,?,?,?)", datarow )
        db.commit()
        c.close()
        #logger.info("Registrierung gestartet für User %s mit Token %s", message.author.name, token)
        return return_data
    else:
        return_data["error"] = -1
        c.close()
        return return_data

# gets user information out of the database of the bot
def get_users(username):
    c = db.cursor()
    result = []
    if username == "all":
        c.execute("SELECT count(status) FROM users where status = ?", ("registered",))
        test = c.fetchone()
        result.append(test[0])
        c.execute("SELECT count(status) FROM users where status = ?", ("pending hive",))
        test = c.fetchone()
        result.append(test[0])
    else:
        c.execute("Select * FROM users where discordname = ? or hivename =?", (username, username))
        result = c.fetchall()
        
    c.close()
    return result

# gets users that are in status "hive pending" in the database of the bot
def get_users_reg():
    c = db.cursor()
    result = []
    c.execute("SELECT discordid, discordname, hivename, token FROM users where status = ?", ("pending hive",))
    result = c.fetchall()
    if len(result) == 0:
        c.close()
        return -1
    c.close()   
    return list(result)

# updates the status of the users to registerred
def validate_user(username):
    c = db.cursor()
    c.execute("UPDATE users SET status = ? WHERE discordname = ?", ("registered", username))
    db.commit()
    c.close()
    return 0

# deletes a user out of the database
def delete_user(username):
    c = db.cursor()
    c.execute("DELETE FROM users WHERE hivename = ?", (username,))
    db.commit()
    return_value = c.rowcount
    c.close()
    return return_value


# inserts a post into the list to be voted in the database of the bot
def insert_article_db(discord_name, post, title, author):
    print(discord_name)
    c = db.cursor()
    datarow =(discord_name,post,1,"No",title,author)
    c.execute("INSERT INTO articles (kurator, permlink, votes, voted, title, author) VALUES(?,?,?,?,?,?)", datarow)
    db.commit()
    c.close()
    return 0 

# increases votes to a given post by 1 
def increase_article_votes(post):
    c = db.cursor()
    c.execute("UPDATE articles SET votes = votes + 1 WHERE permlink= ?",(post, ))
    db.commit()
    c.close()    
        
    
# gets information about the no of votes a user has used
def get_voter_info(discord_id):
    c = db.cursor()
    return_data = {}
    c.execute("SELECT has_voted FROM users where discordid = ?", (discord_id,))
    result = c.fetchone()
    c.close()
    return_data["votes"] = int(result[0])
    return return_data
     
# increse votes done by a user in the user table by 1
def increase_votes(curator):
    c = db.cursor()
    c.execute("UPDATE users SET has_voted = has_voted + 1 WHERE discordname = ?",(curator, ))
    db.commit()
    c.close()    

# gets the post out of the db that is going to be voted next
def get_next_vote():
    return_data = {}
    c = db.cursor()
    c.execute("SELECT title, author, votes, permlink from articles WHERE voted = ?", ("No",))
    data = c.fetchone()
    c.close()
    if data is None:
        return_data["status"] = 0
    else:
        return_data["status"] = 1   
        return_data["title"] = data[0]
        return_data["author"] = data[1]
        return_data["votes"] = data[2]  
        return_data["permlink"] = data[3]
    return return_data



def get_article(url):
    c = db.cursor()
    return_data = {}
    c.execute("SELECT votes, voted FROM articles where permlink = ?", (url,))
    result = c.fetchone()
    if result is None:
        return_data["code"] = 0
        return_data["voted"] = "No"

    else:
        return_data["code"] = 1
        return_data["votes"] = result[0]
        return_data["voted"] = result[1]
        
    c.close()
    return return_data

def get_all_articles():
    c = db.cursor()
    return_data = {}
    c.execute("SELECT * FROM articles where voted =?",("No",))
    result = c.fetchall()
    if len(result) == 0:
        c.close()
        data = []
        data.append(-1)
        return data
    c.close()
    return result

def get_voted_articles():
    c = db.cursor()
    #return_data = {}
    c.execute("SELECT * FROM articles where voted !=? ORDER by ID desc LIMIT 5",("No",))
    result = c.fetchall()
    #print(result)
    if len(result) == 0:
        c.close()
        result[0] = -1
        return result
    c.close()
    return result

def get_op_count(reason):
    c = db.cursor()
    return_data = {}
    if reason == "registration":
        c.execute("SELECT virtualops FROM config")
    elif reason == "delegation":
        c.execute("SELECT deleops FROM config")
    result = c.fetchone()
    if result is None:
        return_data["status"] = 0
    else:
        return_data["status"] = 1
    c.close()
    return_data["ops"] = result[0]
    return return_data

def set_op_count(reason, op_count):
    c = db.cursor()
    if reason == "registration":
        c.execute("UPDATE config SET virtualops = ?",(op_count, ))
    if reason == "delegation":
        c.execute("UPDATE config SET deleops = ?",(op_count, ))
    db.commit()
    c.close()    

def delegations_update(delegator_list):
    c = db.cursor()
    db_delegations = []
    c.execute("SELECT delegator, vests, time, until FROM delegations WHERE until = ''")
    result = c.fetchall()
    for item in result:
        db_delegations.append(item[0])
    if len(db_delegations) != 0:
        for row in delegator_list:
            if row["delegator"] in db_delegations:
                c.execute("UPDATE delegations SET until = ? WHERE delegator = ?",(row["from"],row["delegator"]))
                datarow = (row["delegator"],row["vests"],row["from"], row["to"])
                c.execute("INSERT INTO delegations (delegator, vests, time, until) VALUES(?,?,?,?)", datarow)
                db.commit()
            else:
                datarow = (row["delegator"],row["vests"],row["from"], row["to"])
                c.execute("INSERT INTO delegations (delegator, vests, time, until) VALUES(?,?,?,?)", datarow)
                db.commit() 
        
    else:
        for row in delegator_list:
            datarow = (row["delegator"],row["vests"],row["from"],row["to"])
            c.execute("INSERT INTO delegations (delegator, vests, time,until) VALUES(?,?,?,?)", datarow)
            db.commit()
    c.close()

def get_delegators():
    c = db.cursor()
    return_data = []
    c.execute("SELECT delegator, vests from delegations WHERE vests != 0 AND until = 0 ORDER BY vests DESC")
    result = c.fetchall()
    for item in result:
        transform = {}
        transform["delegator"] = item[0]
        transform["vests"] = item[1]
        return_data.append(transform)
        
    c.close()
    return return_data

def get_delegators_bydate(date):
    c = db.cursor()
    return_data = []
    #select valid delegators that have an end date set
    c.execute("SELECT delegator, vests from delegations WHERE vests > 0 AND time < ? AND until > ? ", (date,date))
    result = c.fetchall()
    for row in result:
        #payload = [row[0], row[1]]
        return_data.append(list(row))
    #select valid delegators that have an indefinite end date set
    c.execute("SELECT delegator, vests from delegations WHERE vests > 0 AND time < ? AND until = 0 ", (date,))
    result = c.fetchall()
    for row in result:
        return_data.append(list(row))
    return return_data

