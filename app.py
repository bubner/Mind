# Lucas Bubner, 2022

import datetime
import os
import pickle
import time
import hashlib

from flask import Flask, render_template, request, abort, redirect

# Initialise new Flask app
app = Flask(__name__)


class User:

    def __init__(self, name):
        self.name = name

        # If there is a file that matches the name, load it, otherwise, make a new one
        try:
            self.fload(self)
        except FileNotFoundError:
            print("New user was found. Info created for: " + self.name)
            self.unix = time.time()
            self.endings = []
            self.pagestate = ""
            self.variables = {}
            self.items = []
            self.lastsave = 0
            self.saved = False
            self.hash = None
            self.loggedin = False
            self.reset()

    # File management methods
    @staticmethod
    def fload(self):
        with open('savestates/' + self.name + '.pickle', 'rb') as file:
            self.__dict__ = pickle.load(file)

    @staticmethod
    def fsave(self):
        self.lastsave = time.time()
        with open('savestates/' + self.name + '.pickle', 'wb') as file:
            file.write(pickle.dumps(self.__dict__))

    # Set last page state to the last target
    def changepagestate(self):
        self.pagestate = target
        print(
            f"> autosaved pagestate of user: '{self.name}' with target: '{target}'"
        )
        self.fsave(self)

    # Set variable method
    def sv(self, variable, boolval):
        self.variables.update({variable: boolval})
        self.fsave(self)

    # Check variable method
    def cv(self, variable):
        return self.variables[variable]

    # Add or remove an item
    def toggleitem(self, item):
        if item in self.items:
            self.items.remove(item)
        else:
            self.items.append(item)
        self.fsave(self)

    # Check item method
    def ci(self, item):
        return item in self.items

    # Commit user as existing
    def commituser(self):
        self.saved = True
        self.fsave(self)

    # Add an ending to the total ending count
    def addending(self, endingname):
        if endingname not in self.endings:
            self.endings.append(endingname)
            self.fsave(self)
            return True
        return False

    # Set variables and list items back to default
    def reset(self):
        self.variables = {
            # xTV pathway
            'imRude': False,
            'Tired': False,
            'newGame': False,
            'tvSleep': False,
            'lateNightChips': False,

            # xC pathway
            'badTeeth1': False,
            'badTeeth2': False,
            'isEmail': False,
            'noAmbo': False,
            'noimmediateCare': False,
            'workerPaidDrink': False,
            'welderChips': False,
            'welderEarly': False,
            'eyeDmg': False
        }
        self.items.clear()
        self.fsave(self)


# Global requests
@app.errorhandler(503)
@app.errorhandler(500)
def goback(e):
    global target
    print(f"> error caught and redirected to index.html: {e}")
    target = 'index.html'
    return render_template(target)


# 404 request if a user exists
@app.errorhandler(404)
def notfound(e):
    global user
    print(f"> 404 request intercepted while user info was present: {e}")
    localtarget = '404.html'
    return render_template(localtarget, NAME=user)


@app.before_request
def checkuser():
    global user, save, target
    # Stop any requests that don't have a name/savefile attached to them
    if not request.path.startswith(
            '/static/'
    ) and not request.path == '/' and not request.path.startswith(
        '/story'
    ) and not request.path == '/pass' and (save is None or user is None):
        print(f"> stopped request of: {request.path} as user info was missing")
        target = 'index.html'
        return render_template(target)


@app.after_request
def autosave(r):
    global user, save, target
    # Update pagestate
    if save is not None and not request.path.startswith(
            '/static/') and target not in [
        "match.html", "index.html", "endings.html", "intro.html"
    ]:
        save.changepagestate()
        # Check if an ending was reached
        if 'ending' in target.lower():
            if save.addending(target):
                print(
                    f"> added new ending for user: {user}, ending '{target}'")
    return r


# Direct any requests that raise AttributeError back to the index, incase a user attempts manual navigation
try:
    # Set global variables
    TOTALENDINGS = 48
    user = None
    target = '/'

    # User management system for variables and conditions
    save = None

    # Base route to home page
    @app.route('/')
    def home():
        global user, save, target, TOTALENDINGS
        user = ""
        target = 'index.html'
        return render_template(target, ENDINGNO=TOTALENDINGS)


    @app.route('/pass', methods=["POST", "GET"])
    def authenticate():
        global user, save
        # Get player input for their username
        if not user:
            if request.args.get("playername") == "":
                return redirect("/")
            user = request.args.get("playername")
            user = user.capitalize()

        # Make a new user object for the person
        save = User(user)

        if request.method == 'POST':
            if not (password := request.form.get("password")):
                abort(503)
            if not save.saved:
                save.hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            else:
                if not (save.hash == hashlib.sha256(password.encode('utf-8')).hexdigest()):
                    return render_template('auth.html', NAME=user, save=save)
            save.loggedin = True
            return redirect("/story")
        else:
            return render_template('auth.html', NAME=user, save=save)


    # Manual endpage navigation if unlocked
    @app.route('/e/<string:page>')
    def ending(page):
        global user, save
        # Uses a local target to not trigger autosave

        if page in save.endings:
            localtarget = page
        else:
            print(f"> stopped manual navigation to: {page}")
            localtarget = 'index.html'

        return render_template(localtarget, NAME=user, NAMECAP=user.upper())


    # Initialise game and grab username field arguments
    @app.route('/story', methods=["GET"])
    def story():
        global TOTALENDINGS, user, save, target

        # If the user had previously existed, take them to the management page and show them this info
        saveinfo = vars(save)
        # Pretty formatting for the end-user
        savefileformat = "Username: " + str(
            save.name).upper() + " <br> Endings found: " + str(
            len(save.endings)
        ) + "/" + str(TOTALENDINGS) + " <br> Last page state: " + (
                             str(save.pagestate) if str(save.pagestate) != "" else
                             "NONE") + "<br> User creation time: " + str(
            datetime.datetime.fromtimestamp(
                save.unix)) + " UTC" + " <br> Last save time: " + str(
            datetime.datetime.fromtimestamp(
                save.lastsave)) + " UTC"

        # Checks if the savefile had been started previously
        if save.saved:
            target = 'match.html'
        else:
            target = 'intro.html'

        return render_template(target,
                               NAME=user,
                               SAVEFILERAW=saveinfo,
                               SAVEFILE=savefileformat)


    # Delete user request
    @app.route('/userdel/<string:n>', methods=['POST'])
    def userdel(n):
        global user, save, target

        # POST request to delete a user in question, so people can't go around running /userdel/
        try:
            os.remove('savestates/' + n + '.txt')
        except OSError:
            print(f"> error deleting savefile of name: {n}")
        else:
            print(f"> successfully deleted savefile of name: {n}")

        # Return to home page
        target = 'index.html'
        return render_template(target)


    # Restart story method
    @app.route('/storyrestart')
    def storyrestart():
        global user, save, target

        # Variables and conditions are based per object
        # Method only resets variables and lists, keeps endings
        if save is not None:
            save.reset()
        else:
            abort(503)

        target = 'xBase.html'
        return render_template(target, NAME=user)


    @app.route('/startgame')
    def startgame():
        global user, save, target

        # Base request if a savefile didn't previously exist
        target = 'xBase.html'

        try:
            # Handle new and old users to the game, directing them to the correct page in autosave
            if not save.saved:
                # Commits information to savefile that this user now exists and should not be replaced
                save.commituser()
            else:
                target = save.pagestate
                user = save.name
        except AttributeError:
            abort(503)

        # If the start game request came from an ending, redirect to the start and clear their variables for a new game
        if 'ending' in target.lower():
            target = 'xBase.html'
            save.reset()

        return render_template(target, NAME=user)


    # Endings page direct
    @app.route('/endings')
    def endings():
        global user, save, target, TOTALENDINGS
        endingsinfo = save.endings
        target = 'endings.html'
        return render_template(target,
                               UNLOCKED=endingsinfo,
                               TOTAL=TOTALENDINGS,
                               NAME=user,
                               NAMECAP=user.upper())


    # HomeBridge01 junction direct
    @app.route('/homebridge')
    def homebridge():
        global user, save, target

        if save.cv("noAmbo"):
            target = 'xC-WorkITPhoneBridge.html'
        elif save.cv("welderEarly"):
            target = 'xC-HBEarly.html'
        else:
            target = 'xC-.html'
        return render_template(target, NAME=user)


    # Story subroutes and logic redirections
    @app.route('/tv')
    def tv():
        global user, save, target
        target = 'xTV.html'
        return render_template(target, NAME=user)


    @app.route('/mum')
    def mum():
        global user, save, target
        target = 'xTV-Mum.html'
        return render_template(target, NAME=user)


    @app.route('/standforever')
    def standforever():
        global user, save, target, TOTALENDINGS

        if save.cv("lateNightChips"):
            target = 'ENDING-ChipFinder.html'
        else:
            target = 'ENDING-StandForever.html'

        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/standforevermum')
    def standforevermum():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-StandForeverMum.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/berude')
    def berude():
        global user, save, target
        save.sv("imRude", True)
        target = 'xTV-Ignore.html'
        return render_template(target, NAME=user)


    @app.route('/sleep')
    def sleep():
        global user, save, target
        save.sv("Tired", True)
        target = 'xTV-Mum-Sleep.html'
        return render_template(target, NAME=user)


    @app.route('/chipstv')
    def chipstv():
        global user, save, target
        save.sv('tvSleep', True)

        if save.cv("imRude"):
            save.sv('Tired', True)
            target = 'xTV-ChipsDecide.html'
        else:
            target = 'xTV-WatchTVChipsMum.html'

        return render_template(target, NAME=user)


    @app.route('/gaming')
    def gaming():
        global user, save, target

        if save.cv("imRude"):
            save.sv('Tired', True)

        target = 'xTV-GamingBridge.html'
        return render_template(target, NAME=user)


    @app.route('/takeoutchips')
    def takeoutchips():
        global user, save, target, TOTALENDINGS

        if save.cv("Tired"):
            target = 'ENDING-TiredTakeOutChips.html'
        else:
            target = 'ENDING-NotTiredTakeOutChips.html'

        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/bringoutchips')
    def bringoutchips():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-EnthusiasticTakeOutChips.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/gamedontknow')
    def gamedontknow():
        global user, save, target

        if save.cv("imRude"):
            target = 'xTV-PlayOGameFallAsleep.html'
        else:
            target = 'xTV-PlayOGameMum.html'

        return render_template(target, NAME=user)


    @app.route('/newgame')
    def newgame():
        global user, save, target
        save.sv("newGame", True)

        if save.cv("imRude"):
            target = 'xTV-PlayNGameFallAsleep.html'
        else:
            target = 'xTV-PlayNGameMum.html'

        return render_template(target, NAME=user)


    @app.route('/lie')
    def lie():
        global user, save, target

        if save.cv("tvSleep") and save.cv("lateNightChips"):
            target = 'xTV-Mum-RushTVAte.html'
        else:
            target = 'xTV-Mum-RushTV.html'

        return render_template(target, NAME=user)


    @app.route('/truth')
    def truth():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-MadMum.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/givechipseveryone')
    def givechipseveryone():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-ChipsGenocide.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/dietician')
    def dietician():
        global user, save, target
        save.sv("tvSleep", True)

        if save.cv("imRude"):
            target = 'xTV-WatchTVChipsFallAsleep.html'
        else:
            target = 'xTV-WatchTVChipsMum.html'

        return render_template(target, NAME=user)


    @app.route('/fatty')
    def fatty():
        global user, save, target
        save.sv('lateNightChips', True)
        save.sv('tvSleep', True)

        if save.cv("imRude"):
            target = 'xTV-WatchTVChipsFallAsleepAte.html'
        else:
            target = 'xTV-WatchTVChipsMum.html'

        return render_template(target, NAME=user)


    @app.route('/taketime')
    def taketime():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-MadMumDeliquent.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/rush')
    def rush():
        global user, save, target
        target = 'xTV-DoAnythingFallAsleepBridge.html'
        return render_template(target, NAME=user)


    @app.route('/newgametalk')
    def newgametalk():
        global user, save, target, TOTALENDINGS

        if save.cv("Tired"):
            target = 'ENDING-FSNewGame.html'
        else:
            target = 'ENDING-MumNewGame.html'

        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/oldgametalk')
    def oldgametalk():
        global user, save, target, TOTALENDINGS

        if save.cv("Tired"):
            target = 'ENDING-FSOldGame.html'
        else:
            target = 'ENDING-MumOldGame.html'

        return render_template(target, NAME=user, NAMECAP=user.upper(), TOTAL=TOTALENDINGS)


    @app.route('/takeoutdrone')
    def takeoutdrone():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-TakeOutDrone.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/computerinvestigate')
    def computerinvestigate():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-VistaMum.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/chips')
    def chips():
        global user, save, target
        target = 'xC.html'
        return render_template(target, NAME=user)


    @app.route('/bed')
    def bed():
        global user, save, target
        save.sv('badTeeth1', True)
        target = 'xC-Bed.html'
        return render_template(target, NAME=user)


    @app.route('/cleanteeth')
    def cleanteeth():
        global user, save, target
        save.sv('badTeeth1', False)
        target = 'xC-Teeth.html'
        return render_template(target, NAME=user)


    @app.route('/gowork')
    def gowork():
        global user, save, target
        target = 'xC-Work.html'
        return render_template(target, NAME=user)


    @app.route('/callfriend')
    def callfriend():
        global user, save, target
        target = 'xC-Friend.html'
        return render_template(target, NAME=user)


    @app.route('/friendconvo')
    def friendconvo():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-FriendConvo.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/eatchips')
    def eatchips():
        global user, save, target, TOTALENDINGS

        if save.ci("chips"):
            target = 'ENDING-HomeChips.html'
        else:
            target = 'xC-NoChips.html'

        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/vanish')
    def vanish():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-Vanish.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/turnoncomputer')
    def turnoncomputer():
        global user, save, target
        target = 'xC-TurnOnPC.html'
        return render_template(target, NAME=user)


    @app.route('/eatmorechips')
    def eatmorechips():
        global user, save, target

        if save.cv('badTeeth1'):
            target = 'xC-EatExtraChips.html'
            save.sv('badTeeth2', True)
        else:
            target = 'xC-EatMoreChips.html'
            save.sv('badTeeth1', False)
            save.toggleitem("chips")

        return render_template(target, NAME=user)


    @app.route('/checkemails')
    def checkemails():
        global user, save, target
        target = 'xC-TurnOnPC.html'
        return render_template(target, NAME=user)


    @app.route('/eatchipshome')
    def eatchipshome():
        global user, save, target, TOTALENDINGS

        if save.cv('badTeeth1') and save.cv('badTeeth2'):
            target = 'ENDING-ChipOverload.html'
        else:
            target = 'xC-EatChips.html'

        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/embracecheese')
    def embracecheese():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-EmbraceCheese.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/runcheese')
    def runcheese():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-RunCheese.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/cheesesim')
    def cheesesim():
        global user, save, target
        target = 'xC-CheeseSim.html'
        return render_template(target, NAME=user)


    @app.route('/emails')
    def emails():
        global user, save, target

        if save.cv('isEmail'):
            target = '/'  # Page not yet created due to missing prerequisites
        else:
            target = 'xC-NoEmails.html'

        return render_template(target, NAME=user)


    @app.route('/doomsupereternal')
    def doomsupereternal():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-Doom.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/closeemails')
    def closeemails():
        global user, save, target
        target = 'xC-CloseEmails.html'
        return render_template(target, NAME=user)


    @app.route('/minecraft')
    def minecraft():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-Minecraft.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/fortnite')
    def fortnite():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-Fortnite.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/cheesesimchips')
    def cheesesimchips():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-CheeseSimChips.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/it')
    def it():
        global user, save, target, TOTALENDINGS

        if save.cv('badTeeth1') and save.cv('badTeeth2'):
            target = 'ENDING-BadTeethIT.html'
        elif save.ci("chips"):
            target = 'xC-WorkITChips.html'
        else:
            target = 'xC-WorkITNoChips.html'

        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/weld')
    def weld():
        global user, save, target, TOTALENDINGS

        if save.cv('badTeeth1') and save.cv('badTeeth2'):
            target = 'ENDING-BadTeethWeld.html'
        elif save.ci("chips"):
            target = 'xC-WorkWeldChips.html'
        else:
            target = 'xC-WorkWeldNoChips.html'

        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/gohome')
    def gohome():
        global user, save, target
        target = 'xC-HomeBridge02.html'
        return render_template(target, NAME=user)


    @app.route('/itworkhelp')
    def itworkhelp():
        global user, save, target
        target = 'xC-WorkITHelp.html'
        return render_template(target, NAME=user)


    @app.route('/noambo')
    def noambo():
        global user, save, target
        # Easter egg!
        save.sv('noAmbo', True)
        target = 'xC-HomeBridge01.html'
        return render_template(target, NAME=user)


    @app.route('/ambo')
    def ambo():
        global user, save, target
        save.sv('noAmbo', True)
        target = 'xC-WorkITGCAmboDe.html'
        return render_template(target, NAME=user)


    @app.route('/itleave')
    def itleave():
        global user, save, target
        save.sv('noimmediateCare', True)
        target = 'xC-WorkITGCAmboDeLeave.html'
        return render_template(target, NAME=user)


    @app.route('/subinneed')
    def subinneed():
        global user, save, target, TOTALENDINGS

        if save.cv("noimmediateCare"):
            target = 'ENDING-SubInNeedLa.html'
        else:
            target = 'ENDING-SubInNeedIm.html'

        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/weirdwall')
    def weirdwall():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-Backrooms.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/itignorerun')
    def itignorerun():
        global user, save, target
        target = 'xC-WorkITGCAmboDeLeaveCall.html'
        return render_template(target, NAME=user)


    @app.route('/itringout')
    def itringout():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-ITRingout.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/itaccept')
    def itaccept():
        global user, save, target
        target = 'xC-WorkITGCCallAccept.html'
        return render_template(target, NAME=user)


    @app.route('/itdeny')
    def itdeny():
        global user, save, target
        target = 'xC-WorkITGCCallDeny.html'
        return render_template(target, NAME=user)


    @app.route('/itnocare')
    def itnocare():
        global user, save, target
        target = 'ENDING-21KO.html'
        return render_template(target, NAME=user)


    @app.route('/itremainsilent')
    def itremainsilent():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-ITRemainSilent.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/givechips')
    def givechips():
        global user, save, target

        if save.ci("chips"):
            save.toggleitem("chips")

        target = 'xC-WorkITGC.html'
        return render_template(target, NAME=user)


    @app.route('/codejava')
    def codejava():
        global user, save, target
        target = 'xC-WorkITHelpJava.html'
        return render_template(target, NAME=user)


    @app.route('/serverrooms')
    def serverrooms():
        global user, save, target
        target = 'xC-WorkITHelpServer.html'
        return render_template(target, NAME=user)


    @app.route('/javapsv')
    def javapsv():
        global user, save, target
        target = 'xC-WorkITHelpJavaDe.html'
        return render_template(target, NAME=user)


    @app.route('/javapvs')
    def javapvs():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-JavaError.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/pirwindows')
    def pirwindows():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-PirWindows.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/insarch')
    def insarch():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-ArchBtw.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/payrise')
    def payrise():
        global user, save, target
        target = 'xC-WorkITHelpServerPay.html'
        return render_template(target, NAME=user)


    @app.route('/drink')
    def drink():
        global user, save, target
        target = 'xC-WorkITHelpServerDrink.html'
        return render_template(target, NAME=user)


    @app.route('/mepay')
    def mepay():
        global user, save, target
        save.sv('workerPaidDrink', False)
        target = 'xC-WorkITBarAttack.html'
        return render_template(target, NAME=user)


    @app.route('/youpay')
    def youpay():
        global user, save, target
        save.sv('workerPaidDrink', True)
        target = 'xC-WorkITBarAttack.html'
        return render_template(target, NAME=user)


    @app.route('/itfight')
    def itfight():
        global user, save, target, TOTALENDINGS

        if save.cv('workerPaidDrink'):
            target = 'ENDING-WorkerNotFighter.html'
        else:
            target = 'ENDING-ImmoIT.html'

        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/itretreat')
    def itretreat():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-SocietyInter.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/strangechips')
    def strangechips():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-StrangeChips.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/wgohome')
    def wgohome():
        global user, save, target

        save.sv('welderEarly', True)

        target = 'xC-HomeBridge01.html'
        return render_template(target, NAME=user)


    @app.route('/wgivechips')
    def wgivechips():
        global user, save, target

        if save.ci("chips"):
            save.toggleitem("chips")

        save.sv("welderChips", True)

        target = 'xC-WorkWeldGiveChips.html'
        return render_template(target, NAME=user)


    @app.route('/disobeynarrator')
    def dnarr():
        global user, save, target
        target = 'ENDING-DisobeyedNarrator.html'
        return render_template(target, NAME=user)


    @app.route('/wdisregard')
    def wdisregard():
        global user, save, target
        target = 'xC-WorkWeldNCDe.html'
        return render_template(target, NAME=user)


    @app.route('/weldhelp')
    def weldhelp():
        global user, save, target
        target = 'xC-WorkWeldMachine.html'
        return render_template(target, NAME=user)


    @app.route('/wweld')
    def wweld():
        global user, save, target
        save.sv("eyeDmg", True)
        target = 'xC-WorkWeldMachineWeld.html'
        return render_template(target, NAME=user)


    @app.route('/wmach')
    def wmach():
        global user, save, target
        target = 'xC-WorkWeldMachineMach.html'
        return render_template(target, NAME=user)


    @app.route('/wtakechip')
    def wtakechip():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-ChipTakeGone.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/wmed')
    def wmed():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-SmallStepWelder.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/cbridge')
    def stayhome():
        global user, save, target, TOTALENDINGS

        if save.cv("welderChips"):
            target = 'xC-WorkWeldCallBridge.html'
        else:
            target = 'ENDING-CEOWithoutVision.html'

        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/wdecline')
    def wdecline():
        global user, save, target
        target = 'xC-W.html'
        return render_template(target, NAME=user)


    @app.route('/waccept')
    def waccept():
        global user, save, target, TOTALENDINGS
        if not save.cv("welderChips"):
            target = 'ENDING-MistakesWorkplaceWelder.html'
        else:
            target = 'xC-FinalBridgeW.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/wapologise')
    def wapologise():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-CheeseBad.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/itfdeny')
    def itfdeny():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-ITOverthrow.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)


    @app.route('/itfaccept')
    def itfaccept():
        global user, save, target, TOTALENDINGS
        target = 'ENDING-MistakesWorkplaceIT.html'
        return render_template(target, NAME=user, TOTAL=TOTALENDINGS)

except AttributeError:
    abort(503)

if __name__ == "__main__":
    # from waitress import serve

    print("> APP INIT | running on http://127.0.0.1:8080/")
    app.run("0.0.0.0", debug=True)
    # serve(app, host="0.0.0.0", port=8080)
