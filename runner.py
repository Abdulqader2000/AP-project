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
        self.animation = {'status': 'stopped', 'current_side': self.back}

    def same_image(self, other):
        '''the tow card are equals if they have same image'''
        return self.image == other.image
    
    def openned(self):
        '''check if the card surf shows the face'''
        return self.surf is self.face
    
    def closed(self):
        '''check if the card surf shows the back'''
        return self.surf is self.back
    
    def animation_running(self):
        return self.animation['status'] != 'stopped'

    def open(self):
        '''flip the card to show its face'''
        self.animation['status'] = 'showing'

    def close(self):
        '''flip the card back to its back'''
        self.animation['status'] = 'hiding'
        
    
    def update(self):
        current_width = self.surf.get_width()

        if self.animation['status'] == 'showing':
            
            if self.animation['current_side'] is self.back:
                if current_width > 0:
                    self.surf = pygame.transform.scale(self.back, (current_width-1, CARD_HEIGHT))
                else:
                    self.animation['current_side'] = self.face
                    
            else:
                if current_width < CARD_WIDTH:
                    self.surf = pygame.transform.scale(self.face, (current_width+1, CARD_HEIGHT))
                else:
                    self.surf = self.face
                    self.animation['status'] = 'stopped'
        
        elif self.animation['status'] == 'hiding':
            if self.animation['current_side'] is self.face:
                if current_width > 0:
                    self.surf = pygame.transform.scale(self.face, (current_width-1, CARD_HEIGHT))
                else:
                    self.animation['current_side'] = self.back
                    
            else:
                if current_width < CARD_WIDTH:
                    self.surf = pygame.transform.scale(self.back, (current_width+1, CARD_HEIGHT))
                else:
                    self.surf = self.back
                    self.animation['status'] = 'stopped'




def upper_mid_factors(number):
    '''this methods is used to determine how many card should be in one line'''
    factors = []
    for i in range(2, number//2+1):
        if number % i == 0:
            factors. append(i)

    return factors[len(factors) // 2]


def all_opened(card_list):
    '''determine if all cards are opened (game finished)'''
    return all([card.openned() for card in card_list])


def reset(card_list):
    '''flip back all the cards and shuffle them'''
    for card in card_list:
        card.close()
    random.shuffle(card_list)
    
def animation_stopped(card_list):
    return all(not card.animation_running() for card in card_list)




# initiate the game
pygame.init()

# set the screen to the specified size and color
screen = pygame.display.set_mode(SCREEN_SIZE)

# creat a list for card and append the photos in photos folder to it
card_list = []

# loop in the files that in the photos folder
for filename in os.scandir(face_images_path):
    # appent two cards for each photo
    card_list.append(Card(filename.path))
    card_list.append(Card(filename.path))
# shuffle the cards
random.shuffle(card_list)

# this list is for compare two cards when they openned
to_compare = []

# creat custom event for keep last card openned for sometime(specified in the game loop)
flip_timer = pygame.USEREVENT + 1

by_row = upper_mid_factors(len(card_list))

clock = pygame.time.Clock()

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
            # check which cardN that is being clicked
            for card in card_list:
                # ignore openned card
                if card.openned():
                    continue
                # check if the card collides with mouse -> clicked one
                if card.rect.collidepoint(mouse_pos):
                    # flip the card and append to "to_compare" list to compere with the other card
                    card.open()
                    to_compare.append(card)
                    break
        
        # flip the two openned cards back and clear "to_compere" list when time is over
        if event.type == flip_timer:
            for card in to_compare[:2]:
                card.close()
            to_compare.clear()

        # reset the game if finished and space key has been clicked
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if all_opened(card_list):
                reset(card_list)


    if len(to_compare) == 2 and animation_stopped(to_compare):
        if to_compare[0].same_image(to_compare[1]):
            to_compare.clear()
        else:
            to_compare.append('this to make the condition above false (~˘▾˘)~')
            pygame.time.set_timer(flip_timer, 1000, 1)
                
    #DISPLAY CARDS:
    screen.fill(background_color)
    
    gap = 20 #gap between cards
    # center start point from left
    origin_left = (SCREEN_WIDTH - (by_row * (CARD_WIDTH + gap) - gap)) / 2 + CARD_WIDTH / 2
    # center start point from top
    orgin_right = (SCREEN_HEIGHT - (len(card_list) / by_row * (CARD_HEIGHT + gap) - gap)) / 2  + CARD_HEIGHT / 2

    # put every card in position
    for i, card in enumerate(card_list):
        x = origin_left + (CARD_WIDTH + gap) * (i % by_row)
        y = orgin_right + \
            (CARD_HEIGHT + gap) * (i // by_row)
            
        card.rect = card.surf.get_rect(center=(x, y))

        screen.blit(card.surf, card.rect)


    # update display in every loop
    # TODO decide which best to contain the cards (list or group)
    pygame.sprite.Group(*card_list).update()
    pygame.display.update()
    clock.tick(1000)