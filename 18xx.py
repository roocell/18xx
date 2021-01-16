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


f = open("game1.txt", mode='r')
lines = f.readlines()
f.close()

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
                    m = re.search("\$([0-9]+)\s*", line)
                    if m:
                        money = int(m.group(1))*invert
                        p["money"] -= int(money)
                        #log.debug("{} spent {} = {}".format(p["name"], money, p["money"]))

def getEarnForPlayer(players, line):
    earn_terms = ["collects", "receives", "pays out"]
    for e in earn_terms:
        if e in line:
            if e == "pays out":
                brackets = line[line.find("(")+len("("):line.rfind(")")]
                parts=line.split(",")
                for r in parts:
                    # multiple players can have earnings here
                    for p in players:
                        if p["name"] in r:
                            m = re.search("\$([0-9]+)\s*", r)
                            if m:
                                money = m.group(1)
                                p["money"] += int(money)
                                #log.debug("{} earns {} = {}".format(p["name"], money, p["money"]))
            else:
                for p in players:
                    if p["name"] in line:
                        m = re.search("\$([0-9]+)\s*", line)
                        if m:
                            money = m.group(1)
                            p["money"] += int(money)
                            #log.debug("{} earns {} = {}".format(p["name"], money, p["money"]))

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

players = getPlayers(lines)
log.debug(players)

# track player money
stages = []
for line in lines:
    #log.debug(line.replace("\n", ""))
    getSpendForPlayer(players, line)
    getEarnForPlayer(players, line)
    stage = detectStage(line)
    if stage != None:
        stages.append({"stage":stage, "players": copy.deepcopy(players)})
        #log.debug({"stage":stage, "players": players.copy()})
        #printMoney(players)

stageStr = "[Player],"
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
