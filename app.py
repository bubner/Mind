"""
Mind of CEO
@author: Lucas Bubner, 2022
"""

from datetime import datetime
from os import path, remove, getcwd, environ, mkdir
from pickle import dumps, load, loads
from sqlite3 import connect
from waitress import serve
from time import time

from argon2 import PasswordHasher, exceptions
from flask import Flask, render_template, request, abort, redirect, session

# Override the Flask app to manually escape .jinja files, as they are not protected from XSS
class App(Flask):
    def select_jinja_autoescape(self, filename: str) -> bool:
        if filename is None:
            return True
        return filename.endswith((".html", ".htm", ".xml", ".xhtml", ".svg", ".jinja"))

# Initialise new Flask app
app = App(__name__)

if not environ.get("SECRET_KEY"):
    raise RuntimeError("SECRET_KEY not set as an environment variable.")

app.secret_key = environ.get("SECRET_KEY")

# Connect to SQL database for password info
sqlc = connect("auth.db", check_same_thread=False)
auth = sqlc.cursor()


# SQL execution for password authentication
def auth_addentry(username, password):
    # While salting with the username is not a great idea, it doesn't matter for the scope of this project
    # I am being held hostage in Dwyer's basement
    hpass = password + username
    usercombo = [
        username,
        PasswordHasher().hash(hpass)
    ]

    # Security measure, make sure there are no other user/pass entries in the database which match a
    # certain username, otherwise accounts which have not been committed will enforce an older password
    # that doesn't match the one that they entered, effectively losing their claim on creation
    auth.execute("DELETE FROM userlist WHERE user = ?", (username,))

    auth.execute("INSERT INTO userlist (user, pass) VALUES(?, ?)", usercombo)
    sqlc.commit()
    print(f"> added new user/pass entry into database with username: {username}")


def auth_removeentry(username):
    auth.execute("DELETE FROM userlist WHERE user = ?", (username,))
    sqlc.commit()
    print(f"> removed a user/pass entry from database with username: {username}")


def auth_check(username, password):
    hpass = password + username
    entry = auth.execute("SELECT pass FROM userlist WHERE user = ?", (username,)).fetchone()
    try:
        res = PasswordHasher().verify(entry[0], hpass)
    except (exceptions.VerifyMismatchError, TypeError):
        res = False
    return res


# Convenience function to render a template with all required metadata
def render(page, **kwargs):
    session["target"] = page
    try:
        currentsession = loads(session.get('save'))
    except TypeError:
        # In some cases, there will not be a save session and we can safely ignore this exception.
        # An actual savefile being missing will be caught by the check_user function per request
        # However, we still pass a NoneType to the passed keyword arguments so it doesn't complain
        currentsession = None
    return render_template(session.get("target"), SAVE=currentsession, NAME=session.get('user'), TOTAL=TOTALENDINGS, **kwargs)


# Ensures security when accessing save files on the server
def secure_path(name):
    basepath = path.join(getcwd(), "savestates")

    # Make sure the savefiles directory exists
    if not path.exists(basepath):
        mkdir(basepath)

    fullpath = path.normpath(path.join(basepath, name))
    if not fullpath.startswith(basepath):
        raise OSError("Security error. Attempted to access a path outside of the base directory.")

    return fullpath


class User:
    def __init__(self, name):
        self.name = name

        # If there is a file that matches the name, load it, otherwise, make a new one
        try:
            self.fload(self)
        except FileNotFoundError:
            print("> new user was found. Info created for: " + self.name)
            self.unix = time()
            self.endings = []
            self.pagestate = ""
            self.variables = {}
            self.items = []
            self.lastsave = 0
            self.saved = False
            self.loggedin = False
            self.reset()

    # File management methods
    @staticmethod
    def fload(self):
        with open(secure_path(self.name), 'rb') as file:
            self.__dict__ = load(file)

    @staticmethod
    def fsave(self):
        self.lastsave = time()
        session["save"] = dumps(self)
        with open(secure_path(self.name), 'wb') as file:
            file.write(dumps(self.__dict__))

    # Set last page state to the last target
    def changepagestate(self):
        self.pagestate = session["target"]
        print(f"> autosaved pagestate of user: '{self.name}' with target: '{session['target']}'")
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
        return endingname in self.endings

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
    print(f"> error caught and redirected to base index: {e}")
    return render("index.html.jinja", MSG="Something went wrong on our end processing your request. Sorry!")


# 404 request if a user exists, otherwise checkuser will redirect them back to the index
@app.errorhandler(404)
def notfound(e):
    print(f"> 404 request intercepted while info for {session['user']} was present")
    return render('404.html.jinja')


@app.before_request
def checkuser():
    # Stop any requests that don't have a name/savefile attached to them
    # This is to prevent blank names entering the story, and also can prevent against some manual navigation exploits
    # Not all manual navigation exploits can be stopped, but those that crash the game can be
    if not request.path.startswith(('/static/', '/story', '/', '/pass')) or not all(k in session for k in ('save', 'user')):
        print(f"> stopped request of: {request.path} as user info was missing")
        return render("index.html.jinja", MSG="We had a problem with your savefile. Please try again.")


@app.after_request
def autosave(r):
    # Update pagestate if appropriate to
    if not request.path.startswith(
            '/static/'
    ) and session.get("target") not in [
        "match.html.jinja", "index.html.jinja", "endings.html.jinja", "intro.html.jinja", "auth.html.jinja", "404.html.jinja"
    ] and session.get("save") is not None:
        save = loads(session["save"])
        save.changepagestate()
        # Check if an ending was reached
        if 'ending' in session["target"].lower():
            if save.addending(session["target"]):
                print(
                    f"> reached ending for user: {session['user']}, ending '{session['target']}'")
        session["save"] = dumps(save)
    return r


# Set number of total endings for display on all templates
TOTALENDINGS = 68


# Base route to home page, resetting all local data
@app.route('/')
def home():
    session.clear()
    session['save'] = None
    session['user'] = None
    session['target'] = None
    session.modified = True
    return render("index.html.jinja")


@app.route('/pass', methods=["POST", "GET"])
def authenticate():
    # Get player input for their username
    if not session.get("user"):
        if not (playername := request.args.get("playername")):
            return render("index.html.jinja", MSG="Username is missing.")

        if len(playername) > 16:
            return render("index.html.jinja", MSG="Username too long. 16 characters limit.")

        session['user'] = playername
        session['user'] = session["user"].capitalize()

    # Make a new user object for the person
    save = User(session["user"])

    if request.method == 'POST':
        if not (password := request.form.get("password")):
            abort(503)

        if not save.saved:
            auth_addentry(session["user"], password)
        else:
            if not auth_check(session["user"], password):
                return render("auth.html.jinja", FAILED=True)

        save.loggedin = True
        session["save"] = dumps(save)
        return redirect("/story")
    else:
        session["save"] = dumps(save)
        return render("auth.html.jinja", FAILED=False)


# Manual endpage navigation if unlocked
@app.route('/e/<string:page>')
def ending(page):
    save = loads(session["save"])
    # Uses a local target to not trigger autosave
    if page in save.endings:
        localtarget = page
    else:
        print(f"> stopped manual navigation to: {page}")
        localtarget = 'index.html.jinja'

    return render_template(localtarget, NAME=session["user"], NAMECAP=session["user"].upper(), TOTAL=TOTALENDINGS)


# Initialise game and grab username field arguments
@app.route('/story', methods=["GET"])
def story():
    # If the user had previously existed, take them to the management page and show them this info
    save = loads(session["save"])
    saveinfo = vars(save)

    # Pretty formatting for the end-user
    savefileformat = f"""
                        Username: { str(save.name).upper() } <br>
                        Endings found: { str(len(save.endings)) }/{ str(TOTALENDINGS) } <br>
                        Last page state: { (str(save.pagestate) if str(save.pagestate) != "" else "NONE") } <br>
                        User creation time: { str(datetime.fromtimestamp(round(save.unix))) } UTC <br>
                        Last save time: { str(datetime.fromtimestamp(round(save.lastsave))) } UTC
                      """

    # Checks if the savefile had been started previously
    if save.saved:
        page = 'match.html.jinja'
    else:
        page = 'intro.html.jinja'

    return render(page,
                  SAVEFILERAW=saveinfo,
                  SAVEFILE=savefileformat)


# Delete user request
@app.route('/userdel', methods=['POST'])
def userdel():
    if not (n := request.form.get("user")):
        return redirect("/")

    # Prevent deleting a user that isn't logged in as said user
    if n != session["user"]:
        print(
            f"> stopped delete request for user '{n}' by user '{session['user']}'")
        return redirect("/")

    try:
        remove(secure_path(n))
        auth_removeentry(session["user"])
    except OSError:
        print(f"> error deleting savefile of name: {n}")
    else:
        print(f"> successfully deleted savefile of name: {n}")

    # Return to home page
    return redirect("/")


# Restart story method
@app.route('/storyrestart')
def storyrestart():
    save = loads(session["save"])
    # Variables and conditions are based per object
    # Method only resets variables and lists, keeps endings
    if save is not None:
        save.reset()
    else:
        abort(503)

    return render('xBase.html.jinja')


@app.route('/startgame')
def startgame():
    save = loads(session["save"])
    # Base request if a savefile didn't previously exist
    page = 'xBase.html.jinja'

    try:
        # Handle new and old users to the game, directing them to the correct page in autosave
        if not save.saved:
            # Commits information to savefile that this user now exists and should not be replaced
            save.commituser()
        else:
            # Otherwise if we actually have data on this player, set their target page to the last saved one
            page = save.pagestate
    except AttributeError:
        abort(503)

    # If the start game request came from an ending, redirect to the start and clear their variables for a new game
    if 'ending' in page.lower():
        page = 'xBase.html.jinja'
        save.reset()

    return render(page)


# Endings page direct
@app.route('/endings')
def endings():
    save = loads(session["save"])
    return render('endings.html.jinja',
                  UNLOCKED=save.endings,
                  NAMECAP=session["user"].upper())


# HomeBridge01 junction direct
@app.route('/homebridge')
def homebridge():
    save = loads(session["save"])
    if save.cv("noAmbo"):
        page = 'xC-WorkITPhoneBridge.html.jinja'
    elif save.cv("welderEarly"):
        if save.ci("chips"):
            page = 'xC-HBEarly.html.jinja'
        else:
            page = 'xC-HBEarlyNoChips.html.jinja'
    else:
        # There may be a possibility that a variable is not saved and this would cause problems. For now, and this may
        # be a permanent solution, report 404 and redirect away. It shouldn't be the case that someone gets to this
        # route (perhaps via manual navigation) and doesn't have one of the variables unlocked, but it can be possible.
        abort(404)

    return render(page)


# Story subroutes and logic redirections
@app.route('/tv')
def tv():
    return render("xTV.html.jinja")


@app.route('/mum')
def mum():
    return render("xTV-Mum.html.jinja")


@app.route('/standforever')
def standforever():
    save = loads(session["save"])
    if save.cv("lateNightChips"):
        page = 'ENDING-ChipFinder.html.jinja'
    else:
        page = 'ENDING-StandForever.html.jinja'
    return render(page)


@app.route('/standforevermum')
def standforevermum():
    return render('ENDING-StandForeverMum.html.jinja')


@app.route('/berude')
def berude():
    save = loads(session["save"])
    save.sv("imRude", True)
    return render('xTV-Ignore.html.jinja')


@app.route('/sleep')
def sleep():
    save = loads(session["save"])
    save.sv("Tired", True)
    return render('xTV-Mum-Sleep.html.jinja')


@app.route('/chipstv')
def chipstv():
    save = loads(session["save"])
    save.sv('tvSleep', True)
    if save.cv("imRude"):
        save.sv('Tired', True)
        page = 'xTV-ChipsDecide.html.jinja'
    else:
        page = 'xTV-WatchTVChipsMum.html.jinja'
    return render(page)


@app.route('/gaming')
def gaming():
    save = loads(session["save"])
    if save.cv("imRude"):
        save.sv('Tired', True)
    return render('xTV-GamingBridge.html.jinja')


@app.route('/takeoutchips')
def takeoutchips():
    save = loads(session["save"])
    if save.cv("Tired"):
        page = 'ENDING-TiredTakeOutChips.html.jinja'
    else:
        page = 'ENDING-NotTiredTakeOutChips.html.jinja'
    return render(page)


@app.route('/bringoutchips')
def bringoutchips():
    return render('ENDING-EnthusiasticTakeOutChips.html.jinja')


@app.route('/gamedontknow')
def gamedontknow():
    save = loads(session["save"])
    if save.cv("imRude"):
        page = 'xTV-PlayOGameFallAsleep.html.jinja'
    else:
        page = 'xTV-PlayOGameMum.html.jinja'
    return render(page)


@app.route('/newgame')
def newgame():
    save = loads(session["save"])
    save.sv("newGame", True)
    if save.cv("imRude"):
        page = 'xTV-PlayNGameFallAsleep.html.jinja'
    else:
        page = 'xTV-PlayNGameMum.html.jinja'
    return render(page)


@app.route('/lie')
def lie():
    save = loads(session["save"])
    if save.cv("tvSleep") and save.cv("lateNightChips"):
        page = 'xTV-Mum-RushTVAte.html.jinja'
    else:
        page = 'xTV-Mum-RushTV.html.jinja'
    return render(page)


@app.route('/truth')
def truth():
    return render('ENDING-MadMum.html.jinja')


@app.route('/givechipseveryone')
def givechipseveryone():
    return render('ENDING-ChipsGenocide.html.jinja')


@app.route('/dietician')
def dietician():
    save = loads(session["save"])
    save.sv("tvSleep", True)
    if save.cv("imRude"):
        page = 'xTV-WatchTVChipsFallAsleep.html.jinja'
    else:
        page = 'xTV-WatchTVChipsMum.html.jinja'
    return render(page)


@app.route('/fatty')
def fatty():
    save = loads(session["save"])
    save.sv('lateNightChips', True)
    save.sv('tvSleep', True)
    if save.cv("imRude"):
        page = 'xTV-WatchTVChipsFallAsleepAte.html.jinja'
    else:
        page = 'xTV-WatchTVChipsMum.html.jinja'
    return render(page)


@app.route('/taketime')
def taketime():
    return render('ENDING-MadMumDeliquent.html.jinja')


@app.route('/rush')
def rush():
    return render('xTV-DoAnythingFallAsleepBridge.html.jinja')


@app.route('/newgametalk')
def newgametalk():
    save = loads(session["save"])
    if save.cv("Tired"):
        page = 'ENDING-FSNewGame.html.jinja'
    else:
        page = 'ENDING-MumNewGame.html.jinja'
    return render(page)


@app.route('/oldgametalk')
def oldgametalk():
    save = loads(session["save"])
    if save.cv("Tired"):
        page = 'ENDING-FSOldGame.html.jinja'
    else:
        page = 'ENDING-MumOldGame.html.jinja'
    return render(page, NAMECAP=session['user'].upper())


@app.route('/takeoutdrone')
def takeoutdrone():
    return render('ENDING-TakeOutDrone.html.jinja')


@app.route('/computerinvestigate')
def computerinvestigate():
    return render('ENDING-VistaMum.html.jinja')


@app.route('/chips')
def chips():
    return render('xC.html.jinja')


@app.route('/bed')
def bed():
    save = loads(session["save"])
    save.sv('badTeeth1', True)
    return render('xC-Bed.html.jinja')


@app.route('/cleanteeth')
def cleanteeth():
    save = loads(session["save"])
    save.sv('badTeeth1', False)
    return render('xC-Teeth.html.jinja')


@app.route('/gowork')
def gowork():
    return render('xC-Work.html.jinja')


@app.route('/callfriend')
def callfriend():
    return render('xC-Friend.html.jinja')


@app.route('/friendconvo')
def friendconvo():
    return render('ENDING-FriendConvo.html.jinja')


@app.route('/eatchips')
def eatchips():
    save = loads(session["save"])
    if save.ci("chips"):
        page = 'ENDING-HomeChips.html.jinja'
    else:
        page = 'xC-NoChips.html.jinja'
    return render(page)


@app.route('/vanish')
def vanish():
    return render('ENDING-Vanish.html.jinja')


@app.route('/turnoncomputer')
def turnoncomputer():
    return render('xC-TurnOnPC.html.jinja')


@app.route('/eatmorechips')
def eatmorechips():
    save = loads(session["save"])
    if save.cv('badTeeth1'):
        page = 'xC-EatExtraChips.html.jinja'
        save.sv('badTeeth2', True)
    else:
        page = 'xC-EatMoreChips.html.jinja'
        save.sv('badTeeth1', False)
        save.toggleitem("chips")
    return render(page)


@app.route('/checkemails')
def checkemails():
    return render('xC-TurnOnPC.html.jinja')


@app.route('/eatchipshome')
def eatchipshome():
    save = loads(session["save"])
    if save.cv('badTeeth1') and save.cv('badTeeth2'):
        page = 'ENDING-ChipOverload.html.jinja'
    else:
        page = 'xC-EatChips.html.jinja'
    return render(page)


@app.route('/embracecheese')
def embracecheese():
    return render('ENDING-EmbraceCheese.html.jinja')


@app.route('/runcheese')
def runcheese():
    return render('ENDING-RunCheese.html.jinja')


@app.route('/cheesesim')
def cheesesim():
    return render('xC-CheeseSim.html.jinja')


@app.route('/emails')
def emails():
    save = loads(session["save"])
    if save.cv('isEmail'):
        page = 'xC-EmailBridge.html.jinja'
    else:
        page = 'xC-NoEmails.html.jinja'
    return render(page)


@app.route('/doomsupereternal')
def doomsupereternal():
    return render('ENDING-Doom.html.jinja')


@app.route('/closeemails')
def closeemails():
    return render('xC-CloseEmails.html.jinja')


@app.route('/minecraft')
def minecraft():
    return render('ENDING-Minecraft.html.jinja')


@app.route('/fortnite')
def fortnite():
    return render('ENDING-Fortnite.html.jinja')


@app.route('/cheesesimchips')
def cheesesimchips():
    return render('ENDING-CheeseSimChips.html.jinja')


@app.route('/it')
def it():
    save = loads(session["save"])
    if save.cv('badTeeth1') and save.cv('badTeeth2'):
        page = 'ENDING-BadTeethIT.html.jinja'
    elif save.ci("chips"):
        page = 'xC-WorkITChips.html.jinja'
    else:
        page = 'xC-WorkITNoChips.html.jinja'
    return render(page)


@app.route('/weld')
def weld():
    save = loads(session["save"])
    if save.cv('badTeeth1') and save.cv('badTeeth2'):
        page = 'ENDING-BadTeethWeld.html.jinja'
    elif save.ci("chips"):
        page = 'xC-WorkWeldChips.html.jinja'
    else:
        page = 'xC-WorkWeldNoChips.html.jinja'
    return render(page)


@app.route('/gohome')
def gohome():
    return render('xC-HomeBridge02.html.jinja')


@app.route('/itworkhelp')
def itworkhelp():
    return render('xC-WorkITHelp.html.jinja')


@app.route('/noambo')
def noambo():
    save = loads(session["save"])
    save.sv('noAmbo', True)
    return render('xC-HomeBridge01.html.jinja')


@app.route('/ambo')
def ambo():
    save = loads(session["save"])
    save.sv('noAmbo', True)
    return render('xC-WorkITGCAmboDe.html.jinja')


@app.route('/itleave')
def itleave():
    save = loads(session["save"])
    save.sv('noimmediateCare', True)
    return render('xC-WorkITGCAmboDeLeave.html.jinja')


@app.route('/subinneed')
def subinneed():
    save = loads(session["save"])
    if save.cv("noimmediateCare"):
        page = 'ENDING-SubInNeedLa.html.jinja'
    else:
        page = 'ENDING-SubInNeedIm.html.jinja'
    return render(page)


@app.route('/weirdwall')
def weirdwall():
    return render('ENDING-Backrooms.html.jinja')


@app.route('/itignorerun')
def itignorerun():
    return render('xC-WorkITGCAmboDeLeaveCall.html.jinja')


@app.route('/itringout')
def itringout():
    return render('ENDING-ITRingout.html.jinja')


@app.route('/itaccept')
def itaccept():
    return render('xC-WorkITGCCallAccept.html.jinja')


@app.route('/itdeny')
def itdeny():
    return render('xC-WorkITGCCallDeny.html.jinja')


@app.route('/itnocare')
def itnocare():
    return render('ENDING-21KO.html.jinja')


@app.route('/itremainsilent')
def itremainsilent():
    return render('ENDING-ITRemainSilent.html.jinja')


@app.route('/givechips')
def givechips():
    save = loads(session["save"])
    if save.ci("chips"):
        save.toggleitem("chips")
    return render('xC-WorkITGC.html.jinja')


@app.route('/codejava')
def codejava():
    return render('xC-WorkITHelpJava.html.jinja')


@app.route('/serverrooms')
def serverrooms():
    return render('xC-WorkITHelpServer.html.jinja')


@app.route('/javapsv')
def javapsv():
    return render('xC-WorkITHelpJavaDe.html.jinja')


@app.route('/javapvs')
def javapvs():
    return render('ENDING-JavaError.html.jinja')


@app.route('/pirwindows')
def pirwindows():
    return render('ENDING-PirWindows.html.jinja')


@app.route('/insarch')
def insarch():
    return render('ENDING-ArchBtw.html.jinja')


@app.route('/payrise')
def payrise():
    return render('xC-WorkITHelpServerPay.html.jinja')


@app.route('/drink')
def drink():
    return render('xC-WorkITHelpServerDrink.html.jinja')


@app.route('/mepay')
def mepay():
    save = loads(session["save"])
    save.sv('workerPaidDrink', False)
    return render('xC-WorkITBarAttack.html.jinja')


@app.route('/youpay')
def youpay():
    save = loads(session["save"])
    save.sv('workerPaidDrink', True)
    return render('xC-WorkITBarAttack.html.jinja')


@app.route('/itfight')
def itfight():
    save = loads(session["save"])
    if save.cv('workerPaidDrink'):
        page = 'ENDING-WorkerNotFighter.html.jinja'
    else:
        page = 'ENDING-ImmoIT.html.jinja'
    return render(page)


@app.route('/itretreat')
def itretreat():
    return render('ENDING-SocietyInter.html.jinja')


@app.route('/strangechips')
def strangechips():
    return render('ENDING-StrangeChips.html.jinja')


@app.route('/wgohome')
def wgohome():
    save = loads(session["save"])
    save.sv('welderEarly', True)
    return render('xC-HomeBridge01.html.jinja')


@app.route('/wgivechips')
def wgivechips():
    save = loads(session["save"])
    if save.ci("chips"):
        save.toggleitem("chips")
    save.sv("welderChips", True)
    return render('xC-WorkWeldGiveChips.html.jinja')


@app.route('/disobeynarrator')
def dnarr():
    return render('ENDING-DisobeyedNarrator.html.jinja')


@app.route('/wdisregard')
def wdisregard():
    return render('xC-WorkWeldNCDe.html.jinja')


@app.route('/weldhelp')
def weldhelp():
    return render('xC-WorkWeldMachine.html.jinja')


@app.route('/wweld')
def wweld():
    save = loads(session["save"])
    save.sv("eyeDmg", True)
    return render('xC-WorkWeldMachineWeld.html.jinja')


@app.route('/wmach')
def wmach():
    return render('xC-WorkWeldMachineMach.html.jinja')


@app.route('/wtakechip')
def wtakechip():
    return render('ENDING-ChipTakeGone.html.jinja')


@app.route('/wmed')
def wmed():
    return render('ENDING-SmallStepWelder.html.jinja')


@app.route('/cbridge')
def stayhome():
    save = loads(session["save"])
    if save.cv("welderChips"):
        page = 'xC-WorkWeldCallBridge.html.jinja'
    else:
        page = 'ENDING-CEOWithoutVision.html.jinja'
    return render(page)


@app.route('/wdecline')
def wdecline():
    return render('xC-W.html.jinja')


@app.route('/waccept')
def waccept():
    save = loads(session["save"])
    if not save.cv("welderChips"):
        page = 'ENDING-MistakesWorkplaceWelder.html.jinja'
    else:
        page = 'xC-FinalBridgeW.html.jinja'
    return render(page)


@app.route('/wapologise')
def wapologise():
    return render('ENDING-CheeseBad.html.jinja')


@app.route('/itfdeny')
def itfdeny():
    return render('ENDING-ITOverthrow.html.jinja')


@app.route('/itfaccept')
def itfaccept():
    return render('ENDING-MistakesWorkplaceIT.html.jinja')


@app.route('/hbpc')
def hbpc():
    return render('xC-PcOn.html.jinja')


@app.route('/hbchips')
def hbchips():
    return render('ENDING-PoisonAgain.html.jinja')


@app.route('/wvideogames')
def wgaming():
    return render('ENDING-JobForget.html.jinja')


@app.route('/repllie')
def repllie():
    return render('ENDING-Manipulator.html.jinja')


@app.route('/replhon')
def replhon():
    return render('ENDING-CorrectiveMeasures.html.jinja')


@app.route("/wamb")
def wamb():
    save = loads(session["save"])
    if save.ci("chips"):
        page = 'xC-WeldDayEndAmboChips.html.jinja'
    else:
        page = 'xC-WeldDayEndAmboNoChips.html.jinja'
    return render(page)


@app.route("/wnamb")
def wnamb():
    return render('xC-WeldDayEndNoAmbo.html.jinja')


@app.route("/wheatchips")
def wheatchips():
    return render('ENDING-ChipsClutch.html.jinja')


@app.route("/whsleep")
def whsleep():
    return render('xC-WeldFoodFinal.html.jinja')


@app.route("/foodbuy")
def foodbuy():
    return render('ENDING-FoodBuy.html.jinja')


@app.route("/foodignore")
def foodignore():
    return render('ENDING-FoodIgnore.html.jinja')


@app.route("/wafight")
def wafight():
    return render('xC-WFight.html.jinja')


@app.route("/wkill")
def wkill():
    return render('ENDING-Murderer.html.jinja')


@app.route("/wko")
def wko():
    save = loads(session["save"])
    if not save.cv("eyeDmg"):
        page = 'xC-WTakeDownSuccess.html.jinja'
    else:
        page = 'ENDING-Weakling.html.jinja'
    return render(page)


@app.route("/wleave")
def wleave():
    return render('ENDING-BusinessContinue.html.jinja')


@app.route("/wpipe")
def wpipe():
    return render('ENDING-Bomber.html.jinja')


@app.route("/wphone")
def wphone():
    return render('ENDING-CrimeCrime.html.jinja')


@app.route("/wacops")
def wacops():
    return render('xC-WCops.html.jinja')


@app.route("/wcont")
def wcont():
    save = loads(session["save"])
    if save.cv("eyeDmg"):
        page = 'ENDING-CantDial.html.jinja'
    else:
        page = 'ENDING-ArrestedWelder.html.jinja'
    return render(page)


@app.route("/wstop")
def wstop():
    return render('xC-WLifeBridge.html.jinja')


@app.route("/wgoogle")
def wgoogle():
    return render('ENDING-GooglePowered.html.jinja')


@app.route("/wask")
def wask():
    return render('xC-WFinalBridge.html.jinja')


@app.route("/wceo")
def wceo():
    return render('ENDING-CEOless.html.jinja')


@app.route("/wsil")
def wsil():
    return render('ENDING-ManiacWelder.html.jinja')


@app.route("/wpry")
def wpry():
    return render('ENDING-QuestionableForces.html.jinja')


@app.route("/grass")
def grass():
    return render("ENDING-GrassToucher.html.jinja")


@app.route("/hbeat")
def hbeat():
    return render("ENDING-ChipCrusader.html.jinja")


if __name__ == "__main__":
    print("> APP INIT | running on http://127.0.0.1:8080/")
    serve(app, host="0.0.0.0", port=8080)
