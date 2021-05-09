#import asyncio
#import locale
import json
from beem.account import Account
from beem import Hive
from beem.comment import Comment
from beem.nodelist import NodeList
#from beem.blockchain import Blockchain
import datetime
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
def check_hive_reg(userlist, block_number_starting):
    account = Account("dach-support")
    result = []
    #block_number_current = chain.get_current_block_num()
    for user in userlist:
        user = list(user)
        discordid = user[0]
        discorduser = user[1]
        reguser = user[2]
        regtoken = user[3]
        # check all transactions and search for the user and token information, filter only by transfer
        for x in account.history(start=block_number_starting, only_ops=["transfer"]):
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
    return result

# Function to get and sort delegations out of the blockchain and send it back
def get_delegations():
    account = Account("dach-support")
    # max_op_count = account.virtual_op_count()
    delegator_list = []
    for row in account.history(start=52000000, use_block_num=True, only_ops=["delegate_vesting_shares"]):
        overwritten = 0
        if len(delegator_list) == 0:
            delegator_list.append({"delegator": row["delegator"], "vests":row["vesting_shares"]["amount"], "date":row["timestamp"]})
        else:
            for d in delegator_list:
                if d["delegator"] == row["delegator"]:
                    d["vests"] = row["vesting_shares"]["amount"]
                    overwritten = 1
            if overwritten == 0:
                delegator_list.append({"delegator": row["delegator"], "vests":row["vesting_shares"]["amount"], "date":row["timestamp"]})

    for item in delegator_list:
        item["vests"] = round(hive.vests_to_hp(float(item["vests"])*10**-6),2)
    
    sorted_delegator_list = sorted(delegator_list, key=lambda k: k['vests'], reverse=True)
    return sorted_delegator_list

# Function to claim rewards if existant // claimreward("dach-support")
def claimreward(account, password):
    account = Account(account)
    reward = account.balances["rewards"]
    if len(reward) == 3 and reward[0].amount + reward[1].amount + reward[2].amount == 0:
        return
    elif len(reward) == 2 and reward[0].amount + reward[1].amount:
        return

    hive.wallet.unlock(pwd=password)
    account.claim_reward_balance()
    hive.wallet.lock()
    return reward        


            
