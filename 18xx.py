import re
import logging
import copy

# create logger
log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

def getDollarValueInLine(line):
    m = re.search("\$([0-9]+)\s*", line)
    if m:
        money = int(m.group(1))
        return money
    log.error("couldn't find dollar value in line [{}]".format(line))
    return None

def playerExists(players, name):
    for p in players:
        if name == p["name"]: return True
    return False

def getPlayers(lines):
    start_money = 400
    # go through lines and find all uniques with "chooses a company"
    players = []
    for line in lines:
      if "chooses a company" in line:
          parts = line.split(" ")
          str = parts[0]
          p = str[7:]
          if playerExists(players, p):
              continue;
          players.append({"name":p, "money":start_money})
          #log.debug("found player {}".format(p))
    return players

def getCompanies(lines):
    companies = []
    #prev_line = ""
    for line in lines:
        if "pars" in line:
            parts=line.split(" ")
            company = {"name":parts[2], "owner":parts[0].split("]")[1], "money":0}
            companies.append(company)
        # company should still be valid because next line
        # this is done in getSpendForCompany() now
        #if "pars" in prev_line:
        #    if "share of" in line:
        #        company["money"] = getDollarValueInLine(line)
        #prev_line = line
    return companies;

def getSpendForCompany(companies, line):
    spend_terms = ["buys", "spends", "places a token", "pays out", "redeems"]
    for c in companies:
        if c["name"] in line:
            for s in spend_terms:
                invert = 1
                # sometimes a token gets placed for free
                if s == "places a token" and "for" not in line:
                    continue
                # if it contains "buys" and "share of" - it's a player buying a share - invert
                if s == "buys" and "share of" in line:
                    invert = -1
                if s in line:
                    payout_adjust = 0
                    # if it's "pays out", the company can also earn from payout
                    if s == "pays out":
                        brackets = line[line.find("(")+len("("):line.rfind(")")]
                        parts=brackets.split(",")
                        for r in parts:
                            if c["name"] in r:
                                payout_adjust = getDollarValueInLine(r)
                                #if payout_adjust > 0:
                                    #log.debug(r)

                    money = getDollarValueInLine(line)*invert
                    c["money"] -=  money + payout_adjust*-1
                    #log.debug("{} spent {} earns {} = {} [{}]".format(c["name"], money, payout_adjust, c["money"], line))
                    if c["money"] < 0:
                        log.error("{} spent {} earns {} = {} [{}]".format(c["name"], money, payout_adjust, c["money"], line))



def getEarnForCompany(companies, line):
    earn_terms = ["receives", "collects", "runs a"]
    for c in companies:
        if c["name"] in line:
            for e in earn_terms:
                if e in line:
                    money = getDollarValueInLine(line)
                    c["money"] +=  money
                    #log.debug("{} earns {} = {} [{}]".format(c["name"], money, c["money"], line))

def getSpendForPlayer(players, line):
    spend_terms = ["buys", "spends"]
    for p in players:
        if p["name"] in line:
            for s in spend_terms:
                if s in line:
                    invert = 1  # positive multipler
                    # but if it says 'buys' and 'from <player>'
                    # then it's a company buying from a player - so it's actually an earn
                    if s == "buys" and ("from "+p["name"]) in line:
                        invert = -1
                    money =  getDollarValueInLine(line)*invert
                    p["money"] -= money
                    #log.debug("{} spent {} = {} [{}]".format(p["name"], money, p["money"], line))

def getEarnForPlayer(players, line):
    earn_terms = ["collects", "receives", "pays out"]
    for e in earn_terms:
        if e in line:
            if e == "pays out":
                brackets = line[line.find("(")+len("("):line.rfind(")")]
                parts=brackets.split(",")
                for r in parts:
                    # multiple players can have earnings here
                    for p in players:
                        if p["name"] in r:
                            money = getDollarValueInLine(r)
                            p["money"] += money
                            #log.debug("{} earns {} = {} [{}]".format(p["name"], money, p["money"], line))
            else:
                for p in players:
                    if p["name"] in line:
                        money = getDollarValueInLine(line)
                        p["money"] += money
                        #log.debug("{} earns {} = {} [{}]".format(p["name"], money, p["money"], line))

def detectStage(line):
    # detect a change in stage so we can print out stuff
    stage = ["Phase", "Operating Round", "Stock Round"]
    for s in stage:
        if s in line:
            return str(re.findall("("+s+" *.*?) ", line))
    return None

def printMoney(players):
    str = ""
    for p in players:
        str = str + "{} {}, ".format(p["name"], p["money"])
    log.debug(str)

def printExcelTable(stages, players, companies):
    stageStr = "[Entity],"
    for s in stages:
        stageStr = stageStr + s["stage"] + ","
    log.debug(",{}".format(stageStr))

    pStr = ""
    for p in players:
        pStr = pStr + p["name"] + ","
        for s in stages:
            for sp in s["players"]:
                if sp["name"] == p["name"]:
                    pStr = pStr + str(sp["money"]) + ","
        log.debug(",{}".format(pStr))
        pStr = ""

    cStr = ""
    for c in companies:
        cStr = cStr + c["name"] + "-" + c["owner"] + ","
        for s in stages:
            for sc in s["companies"]:
                if sc["name"] == c["name"]:
                    cStr = cStr + str(sc["money"]) + ","
        log.debug(",{}".format(cStr))
        cStr = ""

# ===================================================================
# parse file

f = open("game1.txt", mode='r')
lines = f.readlines()
f.close()

players = getPlayers(lines)
log.debug(players)
companies = getCompanies(lines)
log.debug(companies)

stages = []
for line in lines:
    #log.debug(line.replace("\n", ""))
    getSpendForPlayer(players, line)
    getEarnForPlayer(players, line)
    getSpendForCompany(companies, line)
    getEarnForCompany(companies, line)

    stage = detectStage(line)
    if stage != None:
        stages.append({"stage":stage, "players": copy.deepcopy(players), "companies": copy.deepcopy(companies)})
        #log.debug({"stage":stage, "players": players.copy()})
        #printMoney(players)
printExcelTable(stages, players, companies)
