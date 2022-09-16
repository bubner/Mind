from flask import Flask, render_template, request, abort
import time
import pickle
import os
import datetime

# Initialise new Flask app
app = Flask(__name__)


class User:

    def __init__(self, name):
        self.name = name

        # If there is a file that matches the name, load it, otherwise, make a new one
        try:
            self.fload(self)
        except FileNotFoundError:
            self.unix = time.time()
            self.endings = []
            self.pagestate = ""
            self.variables = {}
            self.items = []
            self.lastsave = 0
            self.saved = False
            self.reset()

    @staticmethod
    def fload(self):
        with open('savestates/' + self.name + '.txt', 'rb') as file:
            self.__dict__ = pickle.load(file)

    @staticmethod
    def fsave(self):
        self.lastsave = time.time()
        with open('savestates/' + self.name + '.txt', 'wb') as file:
            file.write(pickle.dumps(self.__dict__))

    def changepagestate(self, currentstate):
        self.pagestate = currentstate
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

    def ci(self, item):
        return True if item in self.items else False

    def commituser(self):
        self.saved = True
        self.fsave(self)

    def addending(self, endingno):
        self.endings.append(endingno)
        self.fsave(self)

    def reset(self):
        self.variables = {
            'imRude': False,
            'Tired': False,
            'newGame': False,
            'tvSleep': False,
            'lateNightChips': False,

            'badTeeth1': False,
            'badTeeth2': False,
            'isEmail': False,
            'noAmbo': False,
            'noimmediateCare': False
        }
        self.items.clear()
        self.fsave(self)


@app.errorhandler(503)
def goback(e):
    return render_template('index.html')


# Direct any requests that have AttributeErrors back to the index, incase a user attempts manual navigation
try:
    # Set global variables
    TOTALENDINGS = 33
    user = None
    target = '/'

    # User management system for variables and conditions
    save = None


    # Stop any requests that don't have a name attached to them
    @app.before_request
    def checkuser():
        if not request.path.startswith('/static/') and not request.path == '/' and not request.path.startswith(
                '/story') and user is None:
            return render_template('index.html')


    # Base route to home page
    @app.route('/')
    def home():
        global user, save, target
        user = usercap = ""
        return render_template('index.html')


    # Initialise game with HTTP GET request for username
    @app.route('/story', methods=["GET"])
    def story():
        global TOTALENDINGS, user, save, target

        # Get player input for their username
        user = request.args.get("playername")

        # Capitalise the first letter of their username
        user = user.capitalize()

        # Make a new user class for the person
        save = User(user)

        # If the user had previously existed, take them to the management page and show them info
        saveinfo = vars(save)

        # Pretty formatting for the end-user
        savefileformat = "Username: " + str(save.name).upper() + " <br> Endings found: " + str(
            len(save.endings)) + "/" + str(TOTALENDINGS) + " <br> Last page state: " + (
                             str(save.pagestate) if str(
                                 save.pagestate) != "" else "NONE") + "<br> User creation date: " + str(
            datetime.datetime.fromtimestamp(save.unix)) + " <br> Last save time: " + str(
            datetime.datetime.fromtimestamp(save.lastsave))

        if save.saved:
            target = 'match.html'
        else:
            target = 'intro.html'

        return render_template(
            target,
            NAME=user,
            SAVEFILERAW=saveinfo,
            SAVEFILE=savefileformat
        )


    # Delete user request
    @app.route('/userdel/<string:n>', methods=['POST'])
    def userdel(n):
        global user, save, target

        # POST request to delete a user in question, so people can't go around running /userdel/
        try:
            os.remove('savestates/' + n + '.txt')
        except OSError:
            print(f"ERROR DELETING SAVEFILE: {n}")
        else:
            print(f"SUCCESS DELETING SAVEFILE: {n}")

        # Return to home page
        return render_template('index.html')


    # Restart story method
    @app.route('/storyrestart')
    def storyrestart():
        # Variables and conditions are based per object now
        try:
            save.reset()
        except AttributeError:
            abort(503)

        return render_template(
            'intro.html',
            NAME=user
        )


    @app.route('/startgame')
    def startgame():
        global user, save, target
        # Base request
        target = 'xBase.html'

        # Handle new and old users to the game, directing them to the correct page with the correct variables
        try:
            if not save.saved:
                save.commituser()
        except AttributeError:
            abort(503)

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
        global user, save, target
        return render_template(
            'xTV.html',
            NAME=user
        )


    @app.route('/mum')
    def mum():
        global user, save, target
        imRude = False  # Resetting to False because of back key messing up variables
        return render_template(
            'xTV-Mum.html',
            NAME=user
        )


    @app.route('/standforever')
    def standforever():
        global user, save, target

        if save.cv("lateNightChips"):
            target = 'ENDING-ChipFinder.html'
        else:
            target = 'ENDING-StandForever.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/standforevermum')
    def standforevermum():
        global user, save, target
        return render_template(
            'ENDING-StandForeverMum.html',
            NAME=user
        )


    @app.route('/berude')
    def berude():
        global user, save, target
        save.sv("imRude", True)
        return render_template(
            'xTV-Ignore.html',
            NAME=user
        )


    @app.route('/sleep')
    def sleep():
        global user, save, target
        save.sv("Tired", True)

        return render_template(
            'xTV-Mum-Sleep.html',
            NAME=user
        )


    @app.route('/chipstv')
    def chipstv():
        global user, save, target
        save.sv('tvSleep', True)

        if save.cv("imRude"):
            save.sv('Tired', True)
            target = 'xTV-ChipsDecide.html'
        else:
            target = 'xTV-WatchTVChipsMum.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/gaming')
    def gaming():
        global user, save, target

        if save.cv("imRude"):
            save.sv('Tired', True)

        return render_template(
            'xTV-GamingBridge.html',
            NAME=user
        )


    @app.route('/takeoutchips')
    def takeoutchips():
        global user, save, target

        if save.cv("Tired"):
            target = 'ENDING-TiredTakeOutChips.html'
        else:
            target = 'ENDING-NotTiredTakeOutChips.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/bringoutchips')
    def bringoutchips():
        global user, save, target
        return render_template(
            'ENDING-EnthusiasticTakeOutChips.html',
            NAME=user
        )


    @app.route('/gamedontknow')
    def gamedontknow():
        global user, save, target

        if save.cv("imRude"):
            target = 'xTV-PlayOGameFallAsleep.html'
        else:
            target = 'xTV-PlayOGameMum.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/newgame')
    def newgame():
        global user, save, target
        save.sv("newGame", True)

        if save.cv("imRude"):
            target = 'xTV-PlayNGameFallAsleep.html'
        else:
            target = 'xTV-PlayNGameMum.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/lie')
    def lie():
        global user, save, target

        if save.cv("tvSleep") and save.cv("lateNightChips"):
            target = 'xTV-Mum-RushTVAte.html'
        else:
            target = 'xTV-Mum-RushTV.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/truth')
    def truth():
        global user, save, target
        return render_template(
            'ENDING-MadMum.html',
            NAME=user
        )


    @app.route('/givechipseveryone')
    def givechipseveryone():
        global user, save, target
        return render_template(
            'ENDING-ChipsGenocide.html',
            NAME=user
        )


    @app.route('/dietician')
    def dietician():
        global user, save, target
        save.sv("tvSleep", True)

        if save.cv("imRude"):
            target = 'xTV-WatchTVChipsFallAsleep.html'
        else:
            target = 'xTV-WatchTVChipsMum.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/fatty')
    def fatty():
        global user, save, target
        save.sv('lateNightChips', True)
        save.sv('tvSleep', True)

        if save.cv("imRude"):
            target = 'xTV-WatchTVChipsFallAsleepAte.html'
        else:
            target = 'xTV-WatchTVChipsMum.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/taketime')
    def taketime():
        global user, save, target
        return render_template(
            'ENDING-MadMumDeliquent.html',
            NAME=user
        )


    @app.route('/rush')
    def rush():
        global user, save, target
        return render_template(
            'xTV-DoAnythingFallAsleepBridge.html',
            NAME=user
        )


    @app.route('/newgametalk')
    def newgametalk():
        global user, save, target

        if save.cv("Tired"):
            target = 'ENDING-FSNewGame.html'
        else:
            target = 'ENDING-MumNewGame.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/oldgametalk')
    def oldgametalk():
        global user, save, target

        if save.cv("Tired"):
            target = 'ENDING-FSOldGame.html'
        else:
            target = 'ENDING-MumOldGame.html'

        return render_template(
            target,
            NAME=user,
            NAMECAP=user.upper()
        )


    @app.route('/takeoutdrone')
    def takeoutdrone():
        global user, save, target
        return render_template(
            'ENDING-TakeOutDrone.html',
            NAME=user
        )


    @app.route('/computerinvestigate')
    def computerinvestigate():
        global user, save, target
        return render_template(
            'ENDING-VistaMum.html',
            NAME=user
        )


    @app.route('/chips')
    def chips():
        global user, save, target
        return render_template(
            'xC.html',
            NAME=user
        )


    @app.route('/bed')
    def bed():
        global user, save, target
        save.sv('badTeeth1', True)
        return render_template(
            'xC-Bed.html',
            NAME=user
        )


    @app.route('/cleanteeth')
    def cleanteeth():
        global user, save, target
        save.sv('badTeeth1', False)
        return render_template(
            'xC-Teeth.html',
            NAME=user
        )


    @app.route('/gowork')
    def gowork():
        global user, save, target
        return render_template(
            'xC-Work.html',
            NAME=user
        )


    @app.route('/callfriend')
    def callfriend():
        global user, save, target
        return render_template(
            'xC-Friend.html',
            NAME=user
        )


    @app.route('/friendconvo')
    def friendconvo():
        global user, save, target
        return render_template(
            'ENDING-FriendConvo.html',
            NAME=user
        )


    @app.route('/eatchips')
    def eatchips():
        global user, save, target

        if save.ci("chips"):
            target = 'ENDING-HomeChips.html'
        else:
            target = 'xC-NoChips.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/vanish')
    def vanish():
        global user, save, target
        return render_template(
            'ENDING-Vanish.html',
            NAME=user
        )


    @app.route('/turnoncomputer')
    def turnoncomputer():
        global user, save, target
        return render_template(
            'xC-TurnOnPC.html',
            NAME=user
        )


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

        return render_template(
            target,
            NAME=user
        )


    @app.route('/checkemails')
    def checkemails():
        global user, save, target
        return render_template(
            'xC-TurnOnPC.html',
            NAME=user
        )


    @app.route('/eatchipshome')
    def eatchipshome():
        global user, save, target

        if save.cv('badTeeth1') and save.cv('badTeeth2'):
            target = 'ENDING-ChipOverload.html'
        else:
            target = 'xC-EatChips.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/embracecheese')
    def embracecheese():
        global user, save, target
        return render_template(
            'ENDING-EmbraceCheese.html',
            NAME=user
        )


    @app.route('/runcheese')
    def runcheese():
        global user, save, target
        return render_template(
            'ENDING-RunCheese.html',
            NAME=user
        )


    @app.route('/cheesesim')
    def cheesesim():
        global user, save, target
        return render_template(
            'xC-CheeseSim.html',
            NAME=user
        )


    @app.route('/emails')
    def emails():
        global user, save, target

        if save.cv('isEmail'):
            target = '/'  # Page not yet created due to missing prerequisites
        else:
            target = 'xC-NoEmails.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/doomsupereternal')
    def doomsupereternal():
        global user, save, target
        return render_template(
            'ENDING-Doom.html',
            NAME=user
        )


    @app.route('/closeemails')
    def closeemails():
        global user, save, target
        return render_template(
            'xC-CloseEmails.html',
            NAME=user
        )


    @app.route('/minecraft')
    def minecraft():
        global user, save, target
        return render_template(
            'ENDING-Minecraft.html',
            NAME=user
        )


    @app.route('/fortnite')
    def fortnite():
        global user, save, target
        return render_template(
            'ENDING-Fortnite.html',
            NAME=user
        )


    @app.route('/cheesesimchips')
    def cheesesimchips():
        global user, save, target
        return render_template(
            'ENDING-CheeseSimChips.html',
            NAME=user
        )


    @app.route('/it')
    def it():
        global user, save, target

        if save.cv('badTeeth1') and save.cv('badTeeth2'):
            target = 'ENDING-BadTeethIT.html'
        elif save.ci("chips"):
            target = 'xC-WorkITChips.html'
        else:
            target = 'xC-WorkITNoChips.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/weld')
    def weld():
        global user, save, target

        if save.cv('badTeeth1') and save.cv('badTeeth2'):
            target = 'ENDING-BadTeethWeld.html'
        else:
            target = 'xC-WorkWeld.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/gohome')
    def gohome():
        global user, save, target
        return render_template(
            'xC-HomeBridge02.html',
            NAME=user
        )


    @app.route('/itworkhelp')
    def itworkhelp():
        global user, save, target
        return render_template(
            'xC-WorkITHelp.html',
            NAME=user
        )


    @app.route('/noambo')
    def noambo():
        global user, save, target
        save.sv('noAmbo', True)
        return render_template(
            'xC-HomeBridge01.html',
            NAME=user
        )


    @app.route('/ambo')
    def ambo():
        global user, save, target
        save.sv('noAmbo', True)
        return render_template(
            'xC-WorkITGCAmboDe.html',
            NAME=user
        )


    @app.route('/itleave')
    def itleave():
        global user, save, target
        save.sv('noimmediateCare', True)
        return render_template(
            'xC-WorkITGCAmboDeLeave.html',
            NAME=user
        )


    @app.route('/subinneed')
    def subinneed():
        global user, save, target

        if save.cv("noimmediateCare"):
            target = 'ENDING-SubInNeedLa.html'
        else:
            target = 'ENDING-SubInNeedIm.html'

        return render_template(
            target,
            NAME=user
        )


    @app.route('/weirdwall')
    def weirdwall():
        global user, save, target
        return render_template(
            'ENDING-Backrooms.html',
            NAME=user
        )


    @app.route('/itignorerun')
    def itignorerun():
        global user, save, target
        return render_template(
            'xC-WorkITGCAmboDeLeaveCall.html',
            NAME=user
        )


    @app.route('/itringout')
    def itringout():
        global user, save, target
        return render_template(
            'ENDING-ITRingout.html',
            NAME=user
        )


    @app.route('/itaccept')
    def itaccept():
        global user, save, target
        return render_template(
            'xC-WorkITGCCallAccept.html',
            NAME=user
        )


    @app.route('/itdeny')
    def itdeny():
        global user, save, target
        return render_template(
            'xC-WorkITGCCallDeny.html',
            NAME=user
        )


    @app.route('/itnocare')
    def itnocare():
        global user, save, target
        return render_template(
            'ENDING-21KO.html',
            NAME=user
        )


    @app.route('/itremainsilent')
    def itremainsilent():
        global user, save, target
        return render_template(
            'ENDING-ITRemainSilent.html',
            NAME=user
        )


    @app.route('/givechips')
    def givechips():
        global user, save, target

        if save.ci("chips"):
            save.toggleitem("chips")

        return render_template(
            'xC-WorkITGC.html',
            NAME=user
        )
except AttributeError:
    abort(503)

if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)

# if __name__ == "__main__":
#    from waitress import serve
#    serve(app, host="0.0.0.0")
