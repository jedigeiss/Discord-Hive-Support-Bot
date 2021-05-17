#import asyncio
#import locale
import json
from beem.account import Account
from beem import Hive
from beem.comment import Comment
from beem.nodelist import NodeList
#from beem.blockchain import Blockchain
import datetime
import time

from pytz import timezone
from pycoingecko import CoinGeckoAPI
import db_connection as db

from beem.exceptions import AccountDoesNotExistsException


nodelist = NodeList()
nodelist.update_nodes()

hive = Hive(node=nodelist.get_hive_nodes())
#chain = Blockchain(blockchain_instance=hive)
cg = CoinGeckoAPI()



# get the recharge time of the bot and send it back 
def get_recharge_time():
    account= Account("dach-support")
    recharge_timedelta = account.get_recharge_timedelta(starting_voting_power=account.vp)
    recharge_vp = datetime.datetime.now() + recharge_timedelta
    recharge_vp = recharge_vp.astimezone(timezone("Europe/Berlin"))
    
    return recharge_timedelta

# get informations out of the Hive Blockchain about accounts and send it back
def basic_info(account_name, level):
    return_data = {}

    today = datetime.datetime.today()
    try:
        account = Account(account_name)
    except AccountDoesNotExistsException:
        return_data["error"] = 1
        return return_data

    balances = account.balances
    hivelink = "https://hive.blog/@"+ account_name
    profile_data = account.profile
    data = account.json()

    if "profile_image" in profile_data.keys():
        pic_url = profile_data["profile_image"]
    else:
        picdata = data["posting_json_metadata"]
        if len(picdata) > 0:
            newpicdata = json.loads(picdata)
            pic_url = newpicdata["profile"]["profile_image"]
        else:
            pic_url="https://i.ibb.co/t2ThhD2/blank.png"

    
    created = data["created"]
    created = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%S")
    since = today - created

    # start of caluclation of actual voting power, need to go some strange ways
    votetime = data["last_vote_time"] 
    votetime = datetime.datetime.strptime(votetime, "%Y-%m-%dT%H:%M:%S")

    # start of caluclation of last activity information
    time_comment = data["last_post"] 
    time_comment = datetime.datetime.strptime(time_comment, "%Y-%m-%dT%H:%M:%S")
    time_post = data["last_root_post"]
    time_post = datetime.datetime.strptime(time_post, "%Y-%m-%dT%H:%M:%S")
    latestactivity = max((votetime,time_comment,time_post))
    latestactivity = latestactivity.replace(tzinfo=timezone('UTC'))
    latestactivity_cet = latestactivity.astimezone(timezone('Europe/Berlin'))

    #start of calculation of additional informations
    recharge_timedelta = account.get_recharge_timedelta(starting_voting_power=account.vp)
    recharge_vp = datetime.datetime.now() + recharge_timedelta
    recharge_vp = recharge_vp.astimezone(timezone("Europe/Berlin"))
    own_sp = account.get_steem_power(onlyOwnSP=True)
    hive_amount = account.balances["total"][0].amount
    hbd_amount = account.balances["total"][1].amount
    hive_price = cg.get_price(ids="hive", vs_currencies="EUR")
    hive_price = hive_price["hive"]["eur"]
    hbd_price = cg.get_price(ids="hive_dollar", vs_currencies="EUR")
    hbd_price = hbd_price["hive_dollar"]["eur"]
    vote_value = round(account.get_voting_value(),2)

    #calculation of account worth in Euro for the Hive account
    acc_worth = round(own_sp * hive_price,2) + round(hive_amount * hive_price,2) + round(hbd_amount * hbd_price,2)

    
    if level == "short":
        return_data["error"] = 0
        return_data["pic_url"] = pic_url
        return_data["hivelink"] = hivelink
        return_data["created"] = created
        return_data["since"] = since.days
        return_data["latestactivity"] = latestactivity_cet
        return_data["sp"] = round(account.sp, 2)
        return_data["vp"] = round(account.vp, 2)
        return_data["rep"] = round(account.rep, 2)
        return_data["votetime"] = votetime
        return_data["recharge_vp"] = recharge_vp
        return_data["worth"] = round(acc_worth,2)
        return_data["hive_price"] = hive_price
        return_data["vote_value"] = vote_value

        return return_data
    else:
        #own_sp = hive.vests_to_hp(own_sp) / 1000000
        delegated_sp = data["delegated_vesting_shares"]["amount"]
        delegated_sp = hive.vests_to_hp(delegated_sp) / 1000000
        received_sp = data["received_vesting_shares"]["amount"]
        received_sp = hive.vests_to_hp(received_sp) / 1000000

        return_data["error"] = 0
        return_data["pic_url"] = pic_url
        return_data["hivelink"] = hivelink
        return_data["created"] = created
        return_data["since"] = since.days
        return_data["latestactivity"] = latestactivity_cet
        return_data["sp"] = round(account.sp, 2)
        return_data["vp"] = round(account.vp, 2)
        return_data["rep"] = round(account.rep, 2)
        return_data["votetime"] = votetime
        return_data["recharge_vp"] = recharge_vp
        return_data["own_sp"] = round(own_sp, 2)
        return_data["delegated_sp"] = round(int(delegated_sp), 2)
        return_data["received_sp"] = round(int(received_sp), 2)
        return_data["worth"] = round(acc_worth,2)
        return_data["hive_price"] = hive_price
        return_data["vote_value"] = vote_value
        
        return return_data

# Check post given to Bot and send back information
def check_post(post_url):
    return_data = {}
    try:
        article = Comment(post_url)
        return_data["age"] = article.time_elapsed()
        return_data["main_post"] = article.is_main_post()
        return_data["category"] = article.category
        return_data["error"] = 0
        return_data["author"] = article.author
        return_data["title"] = article.title
        return_data["tags"] = article.json_metadata["tags"]
    except:
        return_data["error"] = -1
    return return_data

# Check the registrations to the bot and send back infos
def check_hive_reg(userlist):
    account = Account("dach-support")
    result = []
    max_op_count = account.virtual_op_count()
    op_count = db.get_op_count("registration")["ops"]
    if max_op_count > op_count:

        for user in userlist:
            user = list(user)
            discordid = user[0]
            discorduser = user[1]
            reguser = user[2]
            regtoken = user[3]
            # check all transactions and search for the user and token information, filter only by transfer
            for x in account.history(start=op_count, stop=max_op_count, only_ops=["transfer"], use_block_num=False):
                hiveuser = x["from"]
                hivetoken = x["memo"]
                if reguser == hiveuser and regtoken == hivetoken:
                    data = db.validate_user(discorduser)
                    if data == 0:
                        listuser = [discorduser, reguser, "validated", discordid]
                        result.append(listuser)
                    else: 
                        listuser = [discorduser, reguser, "db not changed", discordid]
                        result.append(listuser)
            else:
                result.append(-1)
        db.set_op_count("registration", max_op_count)
    else: 
        result.append(0)
    return result

# Function to get and sort delegations out of the blockchain and send it back
def get_delegations():
    account = Account("dach-support")
    max_op_count = account.virtual_op_count()
    op_count = db.get_op_count("delegation")["ops"]
    if max_op_count > op_count:
        delegator_list = []
        for row in account.history(start=op_count, stop=max_op_count, use_block_num=False, only_ops=["delegate_vesting_shares"]):
            overwritten = 0
            if len(delegator_list) == 0:
                delegator_list.append({"delegator": row["delegator"], "vests":row["vesting_shares"]["amount"], "from":row["timestamp"], "to":""})
            else:
                for d in delegator_list:
                    if d["delegator"] == row["delegator"]:
                        d["vests"] = row["vesting_shares"]["amount"]
                        d["from"] = row["timestamp"]
                        overwritten = 1
                if overwritten == 0:
                    delegator_list.append({"delegator": row["delegator"], "vests":row["vesting_shares"]["amount"], "from":row["timestamp"], "to":""})

        print(delegator_list)
        db.delegations_update(delegator_list)
        db.set_op_count("delegation", max_op_count)
    
    data = db.get_delegators()

    for item in data:
        item["vests"] = round(hive.vests_to_hp(float(item["vests"])*10**-6),2)
    
    #sorted_delegator_list = sorted(delegator_list, key=lambda k: k['vests'], reverse=True)
    return data

# Function to claim rewards if existant // claimreward("dach-support")
def claimreward(account, password):
    return_data = {}
    account = Account(account,blockchain_instance=hive)
    reward = account.balances["rewards"]
    if len(reward) == 3 and reward[0].amount + reward[1].amount + reward[2].amount == 0:
        return_data["status"] = 0
        
    elif len(reward) == 2 and reward[0].amount + reward[1].amount:
        return_data["status"] = 0
    else:
        hive.wallet.unlock(pwd=password)
        account.claim_reward_balance()
        hive.wallet.lock()
        return_data["status"] = 1
        return_data["Hive"] = reward[0].amount
        return_data["HBD"] = reward[1].amount
        return_data["HivePower"] = round(hive.vests_to_hp(reward[2].amount),2)
    
    return return_data

def badge_main(password):
    stime = 4

    #USED ACCS
    account = Account("dach-support", blockchain_instance=hive)
    badge10 = Account("badge-413801", blockchain_instance=hive)
    badge100 = Account("badge-413802", blockchain_instance=hive)
    badge500 = Account("badge-413803", blockchain_instance=hive)
    badge2500 = Account("badge-413804", blockchain_instance=hive)
    badge10000 = Account("badge-413805", blockchain_instance=hive)
    
    
    #GET FOLLOWING ACCOUNTS
    following10 = badge10.get_following()
    following100 = badge100.get_following()
    following500 = badge500.get_following()
    following2500 = badge2500.get_following()
    following10000 = badge10000.get_following()
    
    #BADGES URLS
    url10 = "https://files.peakd.com/file/peakd-hive/badge-413801/dach_dele_10_FINAL.png"
    url100 = "https://files.peakd.com/file/peakd-hive/badge-413802/dach_dele_100_FINAL.png"
    url500 = "https://files.peakd.com/file/peakd-hive/badge-413803/dach_dele_500_FINAL.png"
    url2500 = "https://files.peakd.com/file/peakd-hive/badge-413804/dach_dele_2500_FINAL.png"
    url10000 = "https://files.peakd.com/file/peakd-hive/badge-413805/dach_dele_10000_FINAL.png"
    
    #GET DELEGATED LIST
    ops = []
    delegated_list_hp = dict()
    for op in account.history(only_ops=["delegate_vesting_shares"]):
        ops.append(op)
    acc_info = AccountSnapshot(account, account_history=ops, steem_instance=hive)
    acc_info.build()
    data = acc_info.get_data()
    delegated_vests_in = data["delegated_vests_in"]

    # FOLLOW LOOP
    return_data = {}
    for user,vests in delegated_vests_in.items():
        hp = f"{hive.vests_to_hp(vests):.0f}"
        delegated_list_hp[user] = hp
        #10000+
        if (float(hp) >= 10000):        
            if user not in following10000:  
                hive.wallet.unlock(pwd=password)
                badge10000.follow(user)
                hive.wallet.lock()
                time.sleep(stime)
                return_data[user] = [float(hp), url10000]
            else:
                following10000.remove(user)
        #2500+
        elif (float(hp) >= 2500):        
            if user not in following2500:
                hive.wallet.unlock(pwd=password)
                badge2500.follow(user)
                hive.wallet.lock()
                time.sleep(stime)
                return_data[user] = [float(hp), url2500]
            else:
                following2500.remove(user)
        #500+
        elif (float(hp) >= 500):
            if user not in following500:
                hive.wallet.unlock(pwd=password)
                badge500.follow(user)
                hive.wallet.lock()
                time.sleep(stime)
                return_data[user] = [float(hp), url500]
            else:
                following500.remove(user)
        #100+
        elif (float(hp) >= 100):
            if user not in following100:
                hive.wallet.unlock(pwd=password)
                badge100.follow(user)
                hive.wallet.lock()
                time.sleep(stime)
                return_data[user] = [float(hp), url100]
            else:
                following100.remove(user)
        #10+
        elif (float(hp) >= 10):
            if user not in following10:
                hive.wallet.unlock(pwd=password)
                badge10.follow(user)
                hive.wallet.lock()
                time.sleep(stime)
                return_data[user] = [float(hp), url10]
            else:
                following10.remove(user)

    # FILTER LOOP
    bagdes_filter = ['dach-support']
    for user in bagdes_filter:
        if user in following10000:
            following10000.remove(user)
        if user in following2500:
            following2500.remove(user)
        if user in following500:
            following500.remove(user)
        if user in following100:
            following100.remove(user)
        if user in following10:
            following10.remove(user)
                       
    # UNFOLLOW LOOP
    for user in following10000:
        hive.wallet.unlock(pwd=password)
        badge10000.unfollow(user)
        hive.wallet.lock()
    for user in following2500:
        hive.wallet.unlock(pwd=password)
        badge2500.unfollow(user)
        hive.wallet.lock()
    for user in following500:
        hive.wallet.unlock(pwd=password)
        badge500.unfollow(user)
        hive.wallet.lock()
    for user in following100:
        hive.wallet.unlock(pwd=password)
        badge100.unfollow(user)
        hive.wallet.lock()
    for user in following10:
        hive.wallet.unlock(pwd=password)
        badge10.unfollow(user)
        hive.wallet.lock()

    return return_data
