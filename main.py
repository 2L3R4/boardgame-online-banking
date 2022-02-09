from flask import Flask, Response, send_file
from flask import flash, redirect, render_template, request, session, abort, send_from_directory
import os, json
from flask_table import Table, Col


app = Flask(__name__)

class Game(object):

    def __init__(self, gameid):
        self.gameid = gameid
        try:
            os.mkdir("data")
        except FileExistsError:
            pass
        self._loadconfig()
        self.config['settings']['gamename'] = self.config['settings']['gamename'] if 'gamename' in self.config['settings'] else None
        self.config['settings']['moneysymbol'] = self.config['settings']['moneysymbol'] if 'moneysymbol' in self.config['settings']  else "Geld"
        self.config['settings']['defaultmoney'] = self.config['settings']['defaultmoney'] if 'defaultmoney' in self.config['settings'] else 1500
        self.config['settings']['mittemoney'] = self.config['settings']['mittemoney'] if 'mittemoney' in self.config['settings'] else 50
        self._saveconfig()
        self.loadTransactions()
        print(self.config)
        print(self.gameid)
    
    def _loadconfig(self):
        print("loading config ...")
        print(self.gameid)
        try:
            with open(f'data/config-{self.gameid}.json', 'r') as f:
                print(f"loading from: {f.name}")
                config = json.load(f)
            self.config = config
        except FileNotFoundError:
            self.config = {'settings':{}, 'users': []}
            self._saveconfig()
    def _saveconfig(self):
        print("saving config ...")
        # print(str(self.config['users']))
        with open(f'data/config-{self.gameid}.json', 'w') as f:
            print(f"saving to: {f.name}")
            json.dump(self.config, f, indent=4)

        self._loadconfig()

    def _delete(confirm: bool = False):
        if confirm:
            # TODO: delete files
            ...
        else:
            return False

    def _handlepwd(self, password):
        # do some hashing or something (or not) ...
        return password
    
    #def load_users(self):
    #    print("loading users ...")
    #    try:
    #        with open(f'data/users-{self.gameid}.json', 'r') as f:
    #            users = json.load(f)
    #        self.users = users
    #    except FileNotFoundError:
    #        self.users = []
    #        self.save_users()
    
    #def save_users(self):
    #    print("saving users ...")
    #    # print(str(self.users))
    #    with open(f'data/users-{self.gameid}.json', 'w') as f:
    #        json.dump(self.users, f, indent=4)
    #    self.load_users()

    def add_user(self, name, password, money= None):
        if not money:
            money = self.config['settings']['defaultmoney']
        self.config['users'].append({"name": name, "password": self._handlepwd(password), "money": money})
        self._saveconfig()

    def statistik(self):
        # Declare your table

        class ItemTable(Table):
            name = Col('Name')
            description = Col(self.config['settings']['moneysymbol'])

        # Get some objects
        class Item(object):
            def __init__(self, name, description):
                self.name = name
                self.description = description

        
        items = []
        #users = load_users()
        for u in self.config['users']:
            items.append(Item(u["name"], u["money"]))
        return ItemTable(items)

    def checkpasswd(self, username, key):
        self._loadconfig()
        #print("users: " + str(self.config['users']))
        #print("data: " + str(username) + " " + str(key))
        if key == "":
            #print("password empty")
            return False
        for u in self.config['users']:
            if u["name"] == username:
                if u["password"] == str(key):
                    #print("key_correct")
                    return True
                else:
                    #print("key wrong")
                    return False
        #print("user not found")
        return False

    def loadTransactions(self):
        out = []
        try:
            with open(f"data/transactions-{self.gameid}.log", "r") as f:
                for line in f.readlines():
                    out.append(line.strip().split(","))
        except FileNotFoundError:
            #print("transactions.log not yet created")
            open(f"data/transactions-{self.gameid}.log","w").close()
        self.transactions = out

    def savetransactions(self):
        #print(self.transactions)
        with open(f"data/transactions-{self.gameid}.log", "w") as f:
            #from,to,amount
            out = ""
            for transaction in self.transactions:
                out += f"{transaction[0]},{transaction[1]},{transaction[2]}\n"
            f.write(out)

    def handleTransaction(self, sender, reciever, amount):
        sender["money"] = int(sender["money"]) - int(amount)
        reciever["money"] = int(reciever["money"]) + int(amount)
        #print(f"sender: {sender['name']}")
        #print(f"reciever: {reciever['name']}")
        if sender["name"] == "mitte" and int(sender["money"]) == 0:
            #print("mitte out of money")
            sender["money"] = 50
        self._saveconfig()
        # transaction successfull
        self.transactions.append([sender["name"],reciever["name"],amount])
        self.savetransactions()
        session["transaction"] = [amount,reciever["name"], 0]

    def _gettransactionlist(self, amount: int = 3):
        out = []
        #print(self.transactions)
        if self.transactions:
            for i in range(amount):
                try:
                    out.append([self.transactions[-(i+1)][0], self.transactions[-(i+1)][1], self.transactions[-(i+1)][2]])
                except IndexError:
                    pass
        return out


def _darkmodeReal():
    wantsdark = None
    try:
        wantsdark = request.args.get("darkmode")
    finally:
        if wantsdark:
            #print(wantsdark)
            if wantsdark == "toggle":
                session["darkmode"] = not session["darkmode"]
            elif wantsdark == "true":
                session["darkmode"] = True
            elif wantsdark == "false":
                session["darkmode"] = False 
    try:
        darkmode = session["darkmode"]
    except KeyError:
        darkmode = False
        session["darkmode"] = darkmode
    #print(session, darkmode)
    if darkmode == True:
        darkmode = "darkmode"
    else:
        darkmode = "lightmode"
    #print(darkmode)
    return darkmode

def handleDarkMode(func):
    def wrapper(*args, **kwargs):
        
        return func(*args, darkmode=_darkmodeReal() **kwargs)
    return wrapper

games = {}
def _loadGames():
    try:
        with open("games.txt","r") as g:
            for l in g.readlines():
                try:
                    gameid = int(l.strip())
                    games[gameid].gameid
                except KeyError:
                    games[gameid] = Game(gameid)
            
    except FileNotFoundError:
        with open("games.txt", "w") as g:
            g.writelines(["0\n"])
            games[0] = Game(0)

def createGame(gameid: int):
    if not gameid in games:
        with open("games.txt","a+") as g:
            for l in g.readlines():
                if int(l.strip()) == gameid:
                    _loadGames()
                    return False
            g.writelines([f"{gameid}\n"])
        games[gameid] = Game(gameid)
        return True
    return False

def getGameID():
    #if 'gameid' in session:
    #    gameid = session['gameid']
    if 'gameid' in request.args:
        try:
            int(request.args["gameid"])
            gameid = session['gameid'] = request.args['gameid']
        except ValueError:
            gameid = session['gameid'] = request.args['gameid'][7:]
            
    elif 'gameid' in request.form:
        gameid = session['gameid'] = request.form['gameid']
    else:
        gameid = session['gameid'] = 0
    #print(gameid)
    return gameid
 
def getGame(gameid: int = None):
    if not gameid:
        gameid = getGameID()
        
        try:
            game = games[gameid]
        except KeyError:
            _loadGames()
            game = games[0]
    else:
        if gameid in games:
            game = games[gameid]
        else:
            createGame(0)
            game = games[0]
    return game


# app.route(...)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.route("/error/<error>")
def fail(error):
    if error.isnumeric():
        return abort(int(error))
    elif error == "nosetuid":
        return "<title> ERROR </title> <h2>You can't send money from somone else than you to you/someone</h2> <a href='/game'> return to ui </a>"
    elif error == "noself":
        return "<title> ERROR </title> <h2>You can't send money to yourself</h2>  <a href='/game'> return to ui </a>"
    elif error == "nosame":
        return "<title> ERROR </title> <h2>You can't send money to the sender</h2>  <a href='/game'> return to ui </a>"
    elif error == "user404":
        return "<title> ERROR </title> <h2>the account with this name was not found</h2>  <a href='/game'> return to ui </a>"
    elif error == "nonegative":
        return "<title> ERROR </title> <h2>You can't transfer a negatve amount</h2>  <a href='/game'> return to ui </a>"
    elif error == "notenough":
        return "<title> ERROR </title> <h2>You don't have enough money</h2>  <a href='/game'> return to ui </a>"
    elif error == "nonone":
        return "<title> ERROR </title> <h2>You can't send 'none' money</h2> <a href='/game'> return to ui </a>"
    return abort(Response(error))


@app.route("/logedin")
def accountpage():
    #print(request.args)
    #print(games.keys())
    darkmode = _darkmodeReal()
    gameid = getGameID()
    if 'logged_in' in session:
        if 'create' in request.args:
            if not request.args['gameid'] in games:
                createGame(request.args['gameid'])
                for user in games[0].config['users']:
                    if user['name'] == session['user']:
                        games[request.args['gameid']].config['users'].append(user)
                        del user
                        games[0]._saveconfig()
                session['gameid'] = gameid = request.args['gameid']
                return redirect(f"/setup?gameid={request.args['gameid']}")
            else: 
                return render_template("selector.html", darkmode=darkmode, nachricht="already exists")
        elif 'join' in request.args:
            if request.args['gameid'] in games:
                createGame(request.args['gameid'])
                session['gameid'] = gameid = request.args['gameid']
                return redirect(f"/game?gameid={request.args['gameid']}")
            else: 
                pass
            
        if not 'gameid' in session or 0 in [session['gameid'], gameid]:
            session['gameid'] = 0
            return render_template('selector.html', darkmode = darkmode)
        if gameid in games:
            return redirect(f"/game?gameid={gameid}")
        else:
            return redirect(f"?create&gameid={gameid}")
    else:
        return redirect("/login")

@app.route("/logout")
def logout():
    session.clear()
    return Response('<p>Logged out</p><p><a href="/">return</a></p>')

# debug: returns current session
@app.route('/session')
def show_session():
    return str(session)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    gameid = getGameID()
    darkmode = _darkmodeReal()
    if request.method == "POST":
        name = request.form['username']
        key1 = request.form['password']
        key2 = request.form['password2']
        gameid = request.form['gameid'] if 'gameid' in request.form else 0
        game = games[gameid] if gameid in games else games[0]
        if key1 == key2 and key1 != "":
            for u in game.config['users']:
                if u["name"].lower() == name.lower():
                    return render_template('signup.html', darkmode=darkmode, gameid = gameid, nachricht="username already exists!")

            game.add_user(name, key1)
            return render_template('login.html', darkmode=darkmode, gameid = gameid, nachricht="login now to see if it worked!")
        else:
            return render_template('signup.html', darkmode=darkmode, gameid = gameid, nachricht="both passwords must be identical and not empty")
    # else
    return render_template("signup.html", darkmode=darkmode, gameid=gameid)


@app.route("/login", methods=["GET", "POST"])
def login():
    darkmode = _darkmodeReal()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        gameid = request.form['gameid'] if 'gameid' in request.form else 0
        game = games[gameid] if gameid in games else games[0]
        if game.checkpasswd(username, password):
            session["user"] = username
            session["logged_in"] = True
            return redirect(f"/logedin?gameid={gameid}")
        else:
            return render_template('login.html', darkmode=darkmode, nachricht="username or password is not correct!")
    return render_template('login.html', darkmode=darkmode)


@app.route('/')
def main():
    darkmode = _darkmodeReal()
    return render_template('main.html', darkmode=darkmode)


@app.route("/init")
def init():
    gameid = getGameID()
    if not gameid in games:
        createGame(gameid)
    game = getGame(gameid)
    if game.config['users'] == []:
        game.add_user('bank', '', 10000)
        game.add_user('mitte', '', 50)
        return '<title>init</title>initialized game'
    return '<title>init</title>already initialized'


@app.route("/givebank/<int:amount>")
def givebank(amount):
    game = getGame(getGameID())
    # users=load_users()
    c = amount
    if len(game.config['users']) == 0:
        game.add_user("bank", "", amount)
        #    users = load_users()
        return f"created user 'bank' with password '' and set money to {amount}"
    for i in range(0, len(game.config['users'])):
        #print(game.config['users'][i])
        if game.config['users'][i]["name"] == "bank":
            game.config['users'][i]["money"] = str(int(game.config['users'][i]["money"]) + int(amount))
            c = game.config['users'][i]["money"]
            break
    game.save_users()
    return f"added {amount} to 'bank'. 'bank' now has  {c}"

@app.route("/setup", methods=["GET","POST"])
def setup():
    def _getnachrichtfromsession():
        return "" 
    gameid = getGameID()
    game = getGame(gameid)
    print(f"gameid: {gameid}\ngame.gameid {game.gameid}")
    darkmode = _darkmodeReal()
    if 'logged_in' in session:
        if request.method == "POST":
            #print(f"setup-data: {str(request.form)}")
            if request.form["gameid"] != f"gameid: {gameid}":
                ...
            if 'gamename' in request.form:
                game.config['settings']['gamename'] = request.form["gamename"]
            if 'moneysymbol' in request.form:
                game.config['settings']['moneysymbol'] = request.form["moneysymbol"]
            if 'defaultmoney' in request.form:
                game.config['settings']['defaultmoney'] = request.form["defaultmoney"]


            game._saveconfig()
            return redirect(f"setup?gameid={gameid}")
        return render_template('setup.html', nachricht=_getnachrichtfromsession(), game=game, darkmode=darkmode, name=str(session["user"]))
    return redirect("login")


@app.route("/game", methods=["GET", "POST"])
def game():
    def _getnachrichtfromsession():
        try:
            if session["transaction"]:
                amount = session["transaction"][0]
                reciever = session["transaction"][1]
                #print(session["transaction"])
                session["transaction"] = None
                return f"Überweisung von {amount} Geld an {reciever} erfolgreich"
        except KeyError:
            pass
        finally:
            return ""
    
    gameid = getGameID()
    game = getGame(gameid)
    #print(f"gameid: {gameid}")
    darkmode = _darkmodeReal()
    if 'logged_in' in session:
        if request.method == "POST":
            #print("game-data: " + str(request.form))
            user = session["user"]
            sender = request.form["sender"]
            reciever = request.form["reciever"]
            amount = request.form["amount"]
            if amount == "":
                return render_template('game.html', nachricht = "You can't send 'none' money",  gameid = gameid, darkmode=darkmode, name=str(session["user"]))
                return redirect("/error/nonone")
            if sender == "":
                sender = user
            if int(amount) < 0:
                return render_template('game.html', nachricht = "You can't send a negative amount of money",  gameid = gameid, darkmode=darkmode, name=str(session["user"]))
                return redirect("/error/nonegative")
            if user.lower() != "bank":
                if sender.lower() != user.lower():
                    return render_template('game.html', nachricht = "You can't send money from someone else to you/someone",  gameid = gameid, darkmode=darkmode, name=str(session["user"]))
                    return redirect("/error/nosetuid")
                elif reciever.lower() == user.lower():
                    return render_template('game.html', nachricht = "You can't send money to yourself",  gameid = gameid, darkmode=darkmode, name=str(session["user"]))
                    return redirect("/error/noself")
                elif reciever.lower() == sender.lower():
                    return render_template('game.html', nachricht = "You can't send money to the sender",  gameid = gameid, darkmode=darkmode, name=str(session["user"]))
                    return redirect("/error/nosame")

            elif user.lower() == "bank":
                if reciever.lower() == sender.lower():
                    return redirect("/error/nosame")
            Sender = senderindex = sender
            Reciever = recieverindex = reciever
            #print(str(game.config['users']))
            for i in range(0, len(game.config['users'])):
                if game.config['users'][i]["name"] == sender:
                    senderindex = i
                elif game.config['users'][i]["name"] == reciever:
                    recieverindex = i
            if Sender == senderindex or Reciever == recieverindex:
                return render_template('game.html', darkmode=darkmode, game = game, nachricht = f"recipient not found please verify",  gameid = gameid, name=str(session["user"]))
                return redirect("/error/user404")
            if int(game.config['users'][senderindex]["money"]) - int(amount) < 0:
                return render_template('game.html', darkmode=darkmode, game = game, nachricht = f"You don't have enough money", gameid = gameid, name=str(session["user"]))

                return redirect("/error/notenough")
            game.handleTransaction(game.config['users'][senderindex], game.config['users'][recieverindex], amount)
            
            return redirect("game")
            return render_template('game.html', darkmode=darkmode, nachricht = f"Überweisung von {amount} Geld an {Reciever} erfolgreich ", name=str(session["user"]), gameid = gameid)
            return str(request.form)
        return render_template('game.html', nachricht=_getnachrichtfromsession(), game=game, gameid = gameid, darkmode=darkmode, name=str(session["user"]))
    return redirect('/login')

def api_test_transactions ():
    transactions = []
    with open("api_test_transactions.log","r") as transaction_log:
        for line in transaction_log.readlines ():
            transactions.append(line.split(","))
    return transactions
@app.route("/api/<string:topic>/<int:request_gameid>/<path:action>", methods=["GET", "POST"])
def api(topic, request_gameid, action):
    if topic == "game":
        if action == "transactions":
            if request.method == "GET":
                print(request.args.get)
                amount = request.args.get("amount", default=3, type = int)
                client_local_count = request.args.get("local_count", default = 0 , type = int)
                
                transactions = api_test_transactions()

                wanted_transactions = transactions[client_local_count:][-(amount):]
                return {"count": len(transactions), "transactions": wanted_transactions}

@app.route('/setuid/<user>')
def setuid(user):
    session["user"] = str(user)
    return "set user to: " + str(user)


@app.route('/<path:path>')
def Else(path):
    global users
    if path.startswith("request"):
        try:
            return render_template(path[8:])
        except:
            return "request: " + path[8:]
    elif path == "users":
        #print(users)
        return str(users)
    elif path == "darkmode":
        _darkmodeReal()
        return "<script>window.location.replace(document.referrer);</script><h1>press the back button to refresh</h1>"
    elif path == "load":
        users = load_users()
        return "(re)loaded users"
    elif path == "save":
        save_users()
        return "saved users to disk"
    elif path == "debugger":
        raise
    else:
        return path


print("start")
app.secret_key = "key"
if __name__ == '__main__':
    _loadGames()
    app.run(host="0.0.0.0", port=8001, debug=True, threaded=True)
