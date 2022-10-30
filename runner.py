import pygame
import sys
import random
import os


SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 600
CARD_SIZE = CARD_WIDTH, CARD_HEIGHT = 100, 100
background_color = (0, 127, 255)
face_images_path = 'photos/cards'
back_image_path = 'photos/covers/cover.jpg'

class Card(pygame.sprite.Sprite):

    def __init__(self, image):
        '''# every card has a face which is the given photo in parameter,
        back which is common photo (or numbers),
        and main surface which will vary between face and back'''
        super().__init__()
        self.image = image # save image to compere it with other cards
        self.face = pygame.image.load(image).convert() # load the given image to card face
        self.face = pygame.transform.scale(self.face, CARD_SIZE) # insure that the card in specified size
        self.back = pygame.image.load(back_image_path) # load the cover image to card back
        self.back = pygame.transform.scale(self.back, CARD_SIZE)
        self.surf = self.back # this is the main surface of the card and its initially will be the back
        self.rect = self.surf.get_rect()

    def __eq__(self, other):
        '''the tow card are equals if they have same image'''
        return self.image == other.image
    
    def flipped(self):
        '''check if the card surf shows the face'''
        return self.surf is self.face

    def show(self):
        '''flip the card to show its face'''
        self.surf = self.face

    def hide(self):
        '''flip the card back to its back'''
        self.surf = self.back



def upper_mid_factors(number):
    '''this methods is used to determine how many card should be in one line'''
    factors = []
    for i in range(2, number//2+1):
        if number % i == 0:
            factors. append(i)

    return factors[len(factors) // 2]


def all_opened(card_list):
    '''determine if all cards are opened (game finished)'''
    return all([card.flipped() for card in card_list])


def reset(card_list):
    '''flip back all the cards and shuffle them'''
    for card in card_list:
        card.hide()
    random.shuffle(card_list)




# initiate the game
pygame.init()

# set the screen to the specified size and color
screen = pygame.display.set_mode(SCREEN_SIZE)
screen.fill(background_color)

# creat a list for card and append the photos in photos folder to it
card_list = []

# loop in the files that in the photos folder
for filename in os.scandir(face_images_path):
    # appent two cards for each photo
    card_list.append(Card(filename.path))
    card_list.append(Card(filename.path))
# shuffle the cards
random.shuffle(card_list)

# creat list is for compare two cards when they flipped
to_compare = []

# creat custom event for keep last card flipped for sometime(specified in the game loop)
flip_timer = pygame.USEREVENT + 1

by_row = upper_mid_factors(len(card_list))



# GAME LOOP
while True:
    
    #CHECK FOR EVENTS:
    
    for event in pygame.event.get():
        # exit when user clicks close window botton
        if event.type == pygame.QUIT:
            sys.exit()

        # handle mouse click event
        if event.type == pygame.MOUSEBUTTONDOWN and len(to_compare) < 2: # will ignore clicks when to_compare list is full (has 2 cards)
            # get postion of mouse (tuple)
            mouse_pos = pygame.mouse.get_pos()
            # check which that is being clicked
            for card in card_list:
                # ignore flipped card
                if card.flipped():
                    continue
                # check if the card collides with mouse -> clicked one
                if card.rect.collidepoint(mouse_pos):
                    # flip the card and append to "to_compare" list to compere with the other card
                    card.show()
                    to_compare.append(card)
                    
                    # if there is another card in "to_compere" list then we compere them
                    if len(to_compare) == 2:
                        # compere the two cards
                        if card == to_compare[0]: # if they equal this mean the player got a point 
                            # clear "to_compere" list to use it with another tow cards
                            to_compare.clear() 
                        # if they are not equal then we set timer wait some of time before flipping the two cards back 
                        else: 
                            # after 1000 ms the "flip_timer will be true"
                            pygame.time.set_timer(flip_timer, 1000, loops=1)

                    break
        
        # flip the two flipped cards back and clear "to_compere" list when time is over
        if event.type == flip_timer:
            for card in to_compare:
                card.hide()
            to_compare.clear()

        # reset the game if finished and space key has been clicked
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if all_opened(card_list):
                reset(card_list)
                
                
    
    #DISPLAY CARDS:
    
    gap = 20 #gap between cards
    card_width = CARD_WIDTH
    card_height = CARD_HEIGHT
    # start point from left
    origin_left = (SCREEN_WIDTH - (by_row * (card_width + gap) - gap)) / 2
    # start point from top
    orgin_right = (SCREEN_HEIGHT - (len(card_list) / by_row * (card_height + gap) - gap)) / 2

    # put every card in position
    for i in range(len(card_list)):
        card = card_list[i]
        card.rect.left = origin_left + (card_width + gap) * (i % by_row)
        card.rect.top = orgin_right + \
            (card_height + gap) * (i // by_row)

        screen.blit(card.surf, card.rect)


    # update display in every loop
    pygame.display.update()
