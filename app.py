import os
from flask import Flask, render_template, request, redirect, flash, url_for, render_template_string, session
from deck import Deck
from game import *

app = Flask(__name__)
app.secret_key = os.urandom(24) # generate secret key randomly and safely


def reset_table(restart=False, increment_seq=False, increment_score=False):
    """ if the game was reset during the game then clear session, 
        otherwise just re-set the table and deal new cards to
        both player and house """
        
    if restart:
        session.clear()     # gets rid of the lingering data by clearing the session
    
    if increment_score:
        session["score"][ session["current_player"] ] += 1
    
    if increment_seq:
        session["seq"] += 1
    
    deck.reset()    # restores a full deck of cards
    session["houseHand"]  = []  # HOUSE starts with no cards since it has to wait for its turn
    session["playerHand"] = deck.deal(2)  # deal 2 new cards to player


def apply_verdict(verdict):
    """ APPLY points based on the passed verdict """

    if verdict == "PLAYER":
        # player has won - award a point, reset table and move to the next player
        reset_table(increment_seq=True, increment_score=True )
    else:
        # player has lost or PUSH has occured - reset table and move to the next player
        reset_table(increment_seq=True)
            

# defining globals
deck = Deck() # create deck initially with only 1 deck of cards


@app.route("/", methods=["POST","GET"])
def index():
    """ welcome view where players data is initially gathered """
    
    reset_table() # start fresh by clearing the session, resetting the deck
    
    if request.method == "POST":
        
        # with the use of a ".getlist()", the "ImmutableMultiDict" object is changed to a normal normal dictionary, allowing 
        # me to use the same input names (name = "John", name="Logan", ...) on my the form, which was impossible to do with an
        # "ImmutableMultiDict" object since it simply fetched the last value with the key "name" and ignored the rest.
        # all the values of the key "name" is stored as a list within the dictionary which was then stored in the session
        # using a key "username", {'username': [u'damian', u'yoni', u'michael', u'james'] }.
        for key in request.form.keys():
            
            # fetching the initital user data out of the from and putting it in a normal dictionary
            session[key] = request.form.getlist(key)
            
            if key == "decks":
                # comes in as a list with only ONE value - sets how many decks to use
                global deck
                deck = Deck(int(session[key][0]))
            
            if key == "username":
                # with the usernames stored as keys in a dictionary, it makes 
                # the data handling alot easier and the format easier to read.
                session["score"] = {username: 0 for username in session["username"]}
                session["score"]["house"] = 0
            
            if key == "rounds":
                # sets how many rounds a single session would last - will be used as an integer from this point onwards
                session["rounds"] = int(session["rounds"][0]) 
        
        # expanding on the uses data held in session
        session["seq"] = 0              # player turn tracker
        session["rounds_played"] = 0    # round tacker
        session["won"] = "TBC"          # winner(s) to be declared
        
        # by this point all the basic player data is now stored in the session.
        # print("session = ", session) # uncomment to check session data
        
        # DEFENSIVE - crude duplication check!
        if len(session["username"]) != len(set(session["username"])):
            flash("please use unique names")
            return render_template("index.html")
        
        # if POST then redirect to the first player in game view
        return redirect( url_for('game') )
        
    return render_template("index.html")
    


@app.route("/game", methods=["POST","GET"])
def game():
    
    # DEFENSIVE redirecting
    try:
        if not session["score"]:
            # there is session but no score has not been defined yet. 
            return redirect( url_for("game"))
    except KeyError:
        # no session - redirect back to index view
        return redirect( url_for("index"))    
    
        
    scores = session["score"]               # holds all the scores
    seq = session["seq"]                    # assigned to a variable only for readability purposes
    username = session["username"][seq]     # player whose turn it is to play
    session["current_player"]= username     # current player
    verdict = "UNDECIDED"    
    rounds = session["rounds"]               # is this really needed now? YES, if nothing's been posted we want UNDECIDED to be passed through to the template

    if request.method == "POST":
        
        if "reset" in request.form.keys():
            # reseting mechanism - triggered via the reset button
            reset_table(restart=True)   # clearing the session as well as resetting the table 
            return redirect( url_for("index")) 
        
        if "next" in request.form.keys(): 
            verdict = get_verdict(session["playerHand"], session["houseHand"])
            apply_verdict(verdict)

        if "hit" in request.form.keys():
            # deals one card to the player
            session["playerHand"].append(deck.deal())
        
        verdict = get_verdict(session["playerHand"], session["houseHand"])
        
        if "stand" in request.form.keys():
            # house gets cards until one of the below conditions is met.
            # BLACKJACK, BUST or hand value higher than player
            session["houseHand"] = deck.deal(2) # initialising house hand
            house_hand = house_plays(deck, session["playerHand"], session["houseHand"]) # simulate house play
            session["houseHand"] = house_hand
            
            verdict = get_verdict(session["playerHand"], session["houseHand"])

        # reseting mechanism - simulating a full cycle - each full cycle means 1 round
        if session["seq"] >= len( session["username"] ):
            session["seq"] = 0              # reset the sequence counter to cycle back to the first player
            session["rounds_played"] += 1   # when a cycle is complete, one found of game has been played by all the player!

            # game has eneded, declare the winner if there is one
            if session["rounds_played"] == session["rounds"]:
                
                # pick the winner
                session["won"] = pick_winner(scores,rounds)

                return redirect( url_for('winner') ) 

    # dictionaries will be easier to handle on the template and less variables are needed to be passed.
    player_dict = {"hand": convert_card_names( session["playerHand"] ), "value" : get_hand_value( session["playerHand"] ) }
    house_dict  = {"hand": convert_card_names( session["houseHand"] ), "value" : get_hand_value( session["houseHand"] ) }
    round_dict  = {"total": session["rounds"], "played": session["rounds_played"]+1}

    return render_template("game.html", usernames=session["username"], scores=scores, seq=session["seq"], 
        rounds=round_dict, player=player_dict, house=house_dict, verdict=verdict)
    
@app.route("/simulate",methods = ["POST","GET"])
def simulate():
    """ Simulate playing multiple games"""
    
@app.route("/winner", methods=["POST","GET"])
def winner():
    """ select the winner if there is any """
    
    # DEFENSIVE redirecting 
    try:
        if session["won"] == "TBC":
            # there is session but no winner has been appointed yet, meaning that the game 
            # is still in session, so redirect back to game view
            return redirect( url_for("game"))
    except KeyError:
        # no session (index view was skipped), so redirect back to index view
        return redirect( url_for("index"))
    
    
    if request.method == "POST":
    
        if "reset" in request.form.keys():
            # reseting mechanism - triggered via the reset button
            reset_table(restart=True)   # clearing the session as well as resetting the table 
            return redirect( url_for("index")) 

    # being passed in for the completeness of the 
    round_dict = {"total": session["rounds"], "played": session["rounds_played"]}
    
    return render_template("winner.html", usernames=session["username"], winner=session["won"], 
        scores=session["score"], rounds=round_dict)

if __name__ == "__main__":
    app.run(debug=True)