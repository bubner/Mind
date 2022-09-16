from flask import Flask, render_template, request
import time
import pickle

# Initialise new Flask app
app = Flask(__name__)

# Set new user to user_error, to inform the user if the name was lost somewhere
user = "user_error"
usercap = "USER_ERROR"

# User management system
class User:
        
    def __init__(self, name):
        self.name = name
        
        # If there is a file that matches the name, load it, otherwise, make a new one
        try:
            self.load()
        except:
            self.unix = time.time()
            self.endings = []
            self.pagestate = ""
            self.variables = {}
            self.items = []
            self.lastsave = time.time()
            self.saved = False
            self.save()
        
    def load(self):
        with open('savestates/' + self.name + '.txt', 'rb') as file:
            self.__dict__ = pickle.load(file)
            
    def save(self):
        with open('savestates/' + self.name + '.txt', 'wb') as file:
            file.write(pickle.dumps(self.__dict__))
    
    def addending(self, endingno):
        self.endings.append(endingno)
        self.save()

    def changepagestate(self, currentstate):
        self.pagestate = currentstate
        self.save()

    def changevariables(self, newvariables):
        if newvariables in self.variables:
            self.variables.remove(newvariables)
        self.variables.append(newvariables)
        self.save()

    def changeitems(self, newitems):
        self.items.clear()
        self.items = newitems
        self.save()

    def updatesavetime(self):
        self.lastsave = time.time()
        self.save()

    @staticmethod
    def commituser(self):
        self.saved = True
        self.save()
        
savestate = None

# Create an empty list for the xC saga to indicate conditions and items held
items = []

# xChips saga boolean
imRude = Tired = newGame = tvSleep = lateNightChips = False

# xC saga boolean
badTeeth1 = badTeeth2 = isEmail = noAmbo = noimmediateCare = False

# Base route to home page
@app.route('/')
def home():
    return render_template('index.html')


# Initialise game with HTTP GET request for username
@app.route('/story', methods=["GET"])
def story():
    global user, usercap, savestate
    
    # Get player input for their username
    user = request.args.get("playername")

    # Capitalise the first letter of their user
    user = user.capitalize()    

    # Create a fullcaps varient
    usercap = user.upper()
    
    # Make a new user class for the person
    savestate = User(user)
    savestateinfo = str(savestate.saved)
    if savestate.saved:
        target = 'match.html'
    else:
        target = 'intro.html'

    return render_template(
        target,
        NAME=user,
        SAVEFILE=savestateinfo
    )

    
# Delete user request
@app.route('/userdel')
def userdel():
    global user, usercap
        
    # Return back to home page
    return render_template('index.html')


# Restart story method
@app.route('/storyrestart')
def storyrestart():
    global user, items, imRude, Tired, newGame, tvSleep, lateNightChips, badTeeth1, badTeeth2, isEmail, noAmbo, noimmediateCare

    # As the code has not been reloaded, we need to set every variable back to False
    imRude = Tired = newGame = tvSleep = lateNightChips = badTeeth1 = badTeeth2 = isEmail = noAmbo = noimmediateCare = False
    items.clear()

    return render_template(
        'intro.html',
        NAME=user
    )


@app.route('/startgame')
def startgame():
    global user, savestate
    # Base request
    target = 'xBase.html'
    
    # Handle new and old users to the game, directing them to the correct page with the correct variables
    if savestate.saved:
        pass
    else:
        savestate.commituser(savestate)
    
    return render_template(
        target,
        NAME=user
    )

    
# Endings page direct
@app.route('/endings')
def endings():
    return render_template('endings.html')


@app.route('/tv')
def tv():
    global user
    return render_template(
        'xTV.html',
        NAME=user
    )


@app.route('/mum')
def mum():
    global user, imRude
    imRude = False  # Resetting to False because of back key messing up variables
    return render_template(
        'xTV-Mum.html',
        NAME=user
    )


@app.route('/standforever')
def standforever():
    global user, lateNightChips

    if lateNightChips:
        target = 'ENDING-ChipFinder.html'
    else:
        target = 'ENDING-StandForever.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/standforevermum')
def standforevermum():
    global user
    return render_template(
        'ENDING-StandForeverMum.html',
        NAME=user
    )


@app.route('/berude')
def berude():
    global user, imRude
    imRude = True
    return render_template(
        'xTV-Ignore.html',
        NAME=user
    )


@app.route('/sleep')
def sleep():
    global user
    global Tired
    Tired = False

    return render_template(
        'xTV-Mum-Sleep.html',
        NAME=user
    )


@app.route('/chipstv')
def chipstv():
    global user, Tired, imRude, tvSleep
    tvSleep = True

    if imRude:
        Tired = True
        target = 'xTV-ChipsDecide.html'
    else:
        target = 'xTV-WatchTVChipsMum.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/gaming')
def gaming():
    global user, imRude, Tired

    if imRude:
        Tired = True

    return render_template(
        'xTV-GamingBridge.html',
        NAME=user
    )


@app.route('/takeoutchips')
def takeoutchips():
    global user, Tired

    if Tired:
        target = 'ENDING-TiredTakeOutChips.html'
    else:
        target = 'ENDING-NotTiredTakeOutChips.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/bringoutchips')
def bringoutchips():
    global user
    return render_template(
        'ENDING-EnthusiasticTakeOutChips.html',
        NAME=user
    )


@app.route('/gamedontknow')
def gamedontknow():
    global user, imRude

    if imRude:
        target = 'xTV-PlayOGameFallAsleep.html'
    else:
        target = 'xTV-PlayOGameMum.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/newgame')
def newgame():
    global user, imRude, newGame
    newGame = True

    if imRude:
        target = 'xTV-PlayNGameFallAsleep.html'
    else:
        target = 'xTV-PlayNGameMum.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/lie')
def lie():
    global user, tvSleep, lateNightChips

    if tvSleep and lateNightChips:
        target = 'xTV-Mum-RushTVAte.html'
    else:
        target = 'xTV-Mum-RushTV.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/truth')
def truth():
    global user
    return render_template(
        'ENDING-MadMum.html',
        NAME=user
    )


@app.route('/givechipseveryone')
def givechipseveryone():
    global user
    return render_template(
        'ENDING-ChipsGenocide.html',
        NAME=user
    )


@app.route('/dietician')
def dietician():
    global user
    global tvSleep
    global imRude
    tvSleep = True

    if imRude:
        target = 'xTV-WatchTVChipsFallAsleep.html'
    else:
        target = 'xTV-WatchTVChipsMum.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/fatty')
def fatty():
    global user
    global lateNightChips
    global imRude
    global tvSleep
    lateNightChips = True
    tvSleep = True

    if imRude:
        target = 'xTV-WatchTVChipsFallAsleepAte.html'
    else:
        target = 'xTV-WatchTVChipsMum.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/taketime')
def taketime():
    global user
    return render_template(
        'ENDING-MadMumDeliquent.html',
        NAME=user
    )


@app.route('/rush')
def rush():
    global user
    return render_template(
        'xTV-DoAnythingFallAsleepBridge.html',
        NAME=user
    )


@app.route('/newgametalk')
def newgametalk():
    global user
    global Tired

    if Tired:
        target = 'ENDING-FSNewGame.html'
    else:
        target = 'ENDING-MumNewGame.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/oldgametalk')
def oldgametalk():
    global user
    global Tired
    global usercap

    if Tired:
        target = 'ENDING-FSOldGame.html'
    else:
        target = 'ENDING-MumOldGame.html'

    return render_template(
        target,
        NAME=user,
        NAMECAP=usercap
    )


@app.route('/takeoutdrone')
def takeoutdrone():
    global user
    return render_template(
        'ENDING-TakeOutDrone.html',
        NAME=user
    )


@app.route('/computerinvestigate')
def computerinvestigate():
    global user
    return render_template(
        'ENDING-VistaMum.html',
        NAME=user
    )


@app.route('/chips')
def chips():
    global user
    return render_template(
        'xC.html',
        NAME=user
    )


@app.route('/bed')
def bed():
    global user
    global badTeeth1
    badTeeth1 = True
    return render_template(
        'xC-Bed.html',
        NAME=user
    )


@app.route('/cleanteeth')
def cleanteeth():
    global user
    global badTeeth1
    badTeeth1 = False
    return render_template(
        'xC-Teeth.html',
        NAME=user
    )


@app.route('/gowork')
def gowork():
    global user
    return render_template(
        'xC-Work.html',
        NAME=user
    )


@app.route('/callfriend')
def callfriend():
    global user
    return render_template(
        'xC-Friend.html',
        NAME=user
    )


@app.route('/friendconvo')
def friendconvo():
    global user
    return render_template(
        'ENDING-FriendConvo.html',
        NAME=user
    )


@app.route('/eatchips')
def eatchips():
    global user
    global items

    if "chips" in items:
        target = 'ENDING-HomeChips.html'
    else:
        target = 'xC-NoChips.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/vanish')
def vanish():
    global user
    return render_template(
        'ENDING-Vanish.html',
        NAME=user
    )


@app.route('/turnoncomputer')
def turnoncomputer():
    global user
    return render_template(
        'xC-TurnOnPC.html',
        NAME=user
    )


@app.route('/eatmorechips')
def eatmorechips():
    global user
    global badTeeth1
    global badTeeth2
    global items

    if badTeeth1:
        target = 'xC-EatExtraChips.html'
        badTeeth2 = True
    else:
        target = 'xC-EatMoreChips.html'
        badTeeth1 = False
        items.append("chips")

    return render_template(
        target,
        NAME=user
    )


@app.route('/checkemails')
def checkemails():
    global user
    return render_template(
        'xC-TurnOnPC.html',
        NAME=user
    )


@app.route('/eatchipshome')
def eatchipshome():
    global user
    global badTeeth1
    global badTeeth2

    if badTeeth1 and badTeeth2:
        target = 'ENDING-ChipOverload.html'
    else:
        target = 'xC-EatChips.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/embracecheese')
def embracecheese():
    global user
    return render_template(
        'ENDING-EmbraceCheese.html',
        NAME=user
    )


@app.route('/runcheese')
def runcheese():
    global user
    return render_template(
        'ENDING-RunCheese.html',
        NAME=user
    )


@app.route('/cheesesim')
def cheesesim():
    global user
    return render_template(
        'xC-CheeseSim.html',
        NAME=user
    )


@app.route('/emails')
def emails():
    global user
    global isEmail

    if isEmail:
        target = '/'  # Page not yet created due to missing prerequisites
    else:
        target = 'xC-NoEmails.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/doomsupereternal')
def doomsupereternal():
    global user
    return render_template(
        'ENDING-Doom.html',
        NAME=user
    )


@app.route('/closeemails')
def closeemails():
    global user
    return render_template(
        'xC-CloseEmails.html',
        NAME=user
    )


@app.route('/minecraft')
def minecraft():
    global user
    return render_template(
        'ENDING-Minecraft.html',
        NAME=user
    )


@app.route('/fortnite')
def fortnite():
    global user
    return render_template(
        'ENDING-Fortnite.html',
        NAME=user
    )


@app.route('/cheesesimchips')
def cheesesimchips():
    global user
    return render_template(
        'ENDING-CheeseSimChips.html',
        NAME=user
    )


@app.route('/it')
def it():
    global user, items
    global badTeeth1, badTeeth2

    if badTeeth1 and badTeeth2:
        target = 'ENDING-BadTeethIT.html'
    elif "chips" in items:
        target = 'xC-WorkITChips.html'
    else:
        target = 'xC-WorkITNoChips.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/weld')
def weld():
    global user
    global badTeeth1, badTeeth2

    if badTeeth1 and badTeeth2 is True:
        target = 'ENDING-BadTeethWeld.html'
    else:
        target = 'xC-WorkWeld.html'

    return render_template(
        target,
        NAME=user
    )


@app.route('/gohome')
def gohome():
    global user
    return render_template(
        'xC-HomeBridge02.html',
        NAME=user
    )


@app.route('/itworkhelp')
def itworkhelp():
    global user
    return render_template(
        'xC-WorkITHelp.html',
        NAME=user
    )


@app.route('/noambo')
def noambo():
    global user
    global noAmbo
    noAmbo = True
    return render_template(
        'xC-HomeBridge01.html',
        NAME=user
    )


@app.route('/ambo')
def ambo():
    global user
    global noAmbo
    noAmbo = True
    return render_template(
        'xC-WorkITGCAmboDe.html',
        NAME=user
    )


@app.route('/itleave')
def itleave():
    global user
    global noimmediateCare
    
    noimmediateCare = True
        
    return render_template(
        'xC-WorkITGCAmboDeLeave.html',
        NAME=user
    )


@app.route('/subinneed')
def subinneed():
    global user
    global noimmediateCare
    
    if noimmediateCare:
        target = 'ENDING-SubInNeedLa.html'
    else:
        target = 'ENDING-SubInNeedIm.html'
        
    return render_template(
        target,
        NAME=user
    )


@app.route('/weirdwall')
def weirdwall():
    global user
    return render_template(
        'ENDING-Backrooms.html',
        NAME=user
    )


@app.route('/itignorerun')
def itignorerun():
    global user
    return render_template(
        'xC-WorkITGCAmboDeLeaveCall.html',
        NAME=user
    )


@app.route('/itringout')
def itringout():
    global user
    return render_template(
        'ENDING-ITRingout.html',
        NAME=user
    )


@app.route('/itaccept')
def itaccept():
    global user
    return render_template(
        'xC-WorkITGCCallAccept.html',
        NAME=user
    )


@app.route('/itdeny')
def itdeny():
    global user
    return render_template(
        'xC-WorkITGCCallDeny.html',
        NAME=user
    )

@app.route('/itnocare')
def itnocare():
    global user
    return render_template(
        'ENDING-21KO.html',
        NAME=user
    )

@app.route('/itremainsilent')
def itremainsilent():
    global user
    return render_template(
        'ENDING-ITRemainSilent.html',
        NAME=user
    )

@app.route('/givechips')
def givechips():
    global user
    global items
    
    # Prevent crashing if the user decides to backtrack
    if "chips" in items:
        items.remove("chips")

    return render_template(
        'xC-WorkITGC.html',
        NAME=user
    )

if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)

# if __name__ == "__main__":
#    from waitress import serve
#    serve(app, host="0.0.0.0")
