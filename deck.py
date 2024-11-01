import random 
import itertools


class Deck:
    """ Deck of playing cards """

    def __init__(self, number_of_decks=1):
        
        self.suits = ["spades", "clubs", "hearts", "diamonds"]
        self.ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.number_of_decks = number_of_decks
        self.deck = list(itertools.product(self.suits, self.ranks)) * self.number_of_decks
        random.shuffle(self.deck)


    def deal(self, num=1):
        """ deal a card and remove that card from the deck, 
            this will also serve as a HIT function 
            num:    number of cards being drawn
        """
            
        if num == 1:
            return self.deck.pop() # since the deck is already shuffled we can just use pop
        else:
            return list( self.deck.pop() for x in range(num) )


    def __str__(self):
        return "Deck of cards"
    
    
    def reset(self):
        """ restore the deck to its original state "52" cards """        
        
        self.deck = list(itertools.product(self.suits, self.ranks)) * self.number_of_decks
        random.shuffle(self.deck)

