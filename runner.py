import pygame
import random
import os
from enum import Enum

pygame.init()

SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 600
CARD_SIZE = CARD_WIDTH, CARD_HEIGHT = 100, 100
background_color = (0, 127, 255)
face_images_path = 'photos/cards'
back_image_path = 'photos/covers/cover.jpg'
font = pygame.font.SysFont('arial', 20)
font_large = pygame.font.SysFont('arial', 30)

class Card(pygame.sprite.Sprite):

    def __init__(self, image):
        '''# every card has a face which is the given photo in parameter,
        back which is common photo (or numbers),
        and main surface which will vary between face and back'''
        super().__init__()
        self.image = image # save image to compere it with other cards
        self.face = pygame.image.load(image).convert() # load the given image to card face
        self.face = pygame.transform.scale(self.face, CARD_SIZE) # insure that the card in specified size
        self.back = pygame.image.load(back_image_path).convert() # load the cover image to card back
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


class Button(pygame.sprite.Sprite):
    def __init__(self, text, size, background_color=(255, 255, 255), text_color=(0, 0, 0), font=pygame.font.SysFont('arial', 20), flag=None):
        super().__init__()
        self.flag = flag
        self.surf = pygame.Surface(size)
        self.surf.fill(background_color)
        self.text = font.render(text, True, text_color)
        self.surf.blit(self.text, (self.surf.get_width()/2 - self.text.get_width()/2, self.surf.get_height()/2 - self.text.get_height()/2))



class Page(Enum):
    start = 1
    choose_level = 2
    game = 3
    result = 4


class Mode(Enum):
    online = 1
    local = 2


class Level(Enum):
    easy = 8
    medium = 16
    hard = 20


class Player(Enum):
    player1 = 'player 1'
    player2 = 'player 2'

def upper_mid_factors(number):
    '''this methods is used to determine how many card should be in one line'''
    factors = []
    for i in range(1, number+1):
        if number % i == 0:
            factors. append(i)

    return factors[len(factors) // 2]


def all_opened(card_list):
    '''determine if all cards are opened (game finished)'''
    return all([card.openned() for card in card_list])


# def reset():
#     '''flip back all the cards and shuffle them'''
#     for card in card_list:
#         card.close()
#     random.shuffle(card_list)


def animation_stopped(card_list):
    return all(not card.animation_running() for card in card_list)


def display_surfaces(surfaces_list):
    #gap between cards
    gap = 20
    by_row =  upper_mid_factors(len(surfaces_list))
    surf_width = surfaces_list[0].surf.get_width() if type(surfaces_list[0]) != Card else CARD_WIDTH
    surf_height = surfaces_list[0].surf.get_height()
    # center start point from left
    origin_left = (SCREEN_WIDTH - (by_row * (surf_width + gap) - gap)) / 2 + surf_width / 2
    # center start point from top
    origin_top = (SCREEN_HEIGHT - (len(surfaces_list) / by_row * (surf_height + gap) - gap)) / 2  + surf_height / 2

    # put every card in position
    for i, card in enumerate(surfaces_list):
        x = origin_left + (surf_width + gap) * (i % by_row)
        y = origin_top + \
            (surf_height + gap) * (i // by_row)
            
        card.rect = card.surf.get_rect(center=(x, y))

        screen.blit(card.surf, card.rect)
        
    if page is Page.game:
        score1_text = font.render(f'{Player.player1.value}: {player1_score}', True, (0, 255, 0) if turn is Player.player1 else (255, 255, 255))
        text1_rect = score1_text.get_rect()
        score2_text = font.render(f'{Player.player2.value}: {player2_score}', True, (0, 255, 0) if turn is Player.player2 else (255, 255, 255))
        text2_rect = score2_text.get_rect()
        
        text1_rect.left = origin_left
        text2_rect.right = SCREEN_WIDTH - origin_left
        text1_rect.bottom = text2_rect.bottom = origin_top - 70
        
        screen.blit(score1_text, text1_rect)
        screen.blit(score2_text, text2_rect)


def prepare_cards():
    #TODO : adding numbers
    # loop in the files that in the photos folder
    for filename in list(os.scandir(face_images_path))[:level.value//2]:
        # appent two cards for each photo
        card_list.append(Card(filename.path))
        card_list.append(Card(filename.path))
    # shuffle the cards
    random.shuffle(card_list)


def initiate_game():
    global card_list
    global to_compare
    global page
    global level
    global mode
    global turn
    global result
    global player1_score
    global player2_score
    
    # creat a list for card and append the photos in photos folder to it
    card_list = []

    # this list is for compare two cards when they openned
    to_compare = []

    # flags
    page = Page.start
    level = None
    mode = None
    turn = Player.player1
    result = None

    player1_score = 0
    player2_score = 0



# set the screen to the specified size and color
screen = pygame.display.set_mode(SCREEN_SIZE)

# creat custom event for keep last card openned for sometime(specified in the game loop)
flip_timer = pygame.USEREVENT + 1

clock = pygame.time.Clock()

# start page buttons
start_page_buttons = []
start_page_buttons.append(Button('Play Online', (200, 100), flag=Mode.online))
start_page_buttons.append(Button('Play local', (200, 100), flag=Mode.local))

# choose level page buttons
level_page_buttons = []
level_page_buttons.append(Button('easy', (100, 100), flag=Level.easy))
level_page_buttons.append(Button('medium', (100, 100), flag=Level.medium))
level_page_buttons.append(Button('hard', (100, 100), flag=Level.hard))

exit_button = Button('Exit', (50, 30))
exit_button_rect = exit_button.surf.get_rect(center=(30, 30))

initiate_game()


# GAME LOOP
while True:
    
    #CHECK FOR EVENTS:
    
    for event in pygame.event.get():
        # exit when user clicks close window botton
        if event.type == pygame.QUIT:
            exit()
            

        # handle mouse click event
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            if exit_button_rect.collidepoint(mouse_pos):
                initiate_game()
            
            elif page is Page.start:
                for button in start_page_buttons:
                    if button.rect.collidepoint(mouse_pos):
                        mode = button.flag
                        page = Page.choose_level
            
            
            elif page is Page.choose_level:
                for button in level_page_buttons:
                    if button.rect.collidepoint(mouse_pos):
                        level = button.flag
                        page = Page.game
                        prepare_cards()
                        
            
            
            elif page is Page.game and len(to_compare) < 2: # will ignore clicks when to_compare list is full (has 2 cards)
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
            turn = Player.player2 if turn is Player.player1 else Player.player1 
            

        # # reset the game if finished and space key has been clicked
        # if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
        #     if all_opened(card_list):
        #         reset(card_list)


    # DISPLAY CONTENT

    if page is Page.start:
        screen.fill(background_color)
        display_surfaces(start_page_buttons)
        
    
    elif page is Page.choose_level:
        screen.fill(background_color)
        screen.blit(exit_button.surf, exit_button_rect)
        display_surfaces(level_page_buttons)
        
    elif page is Page.game:
        screen.fill(background_color)
        screen.blit(exit_button.surf, exit_button_rect)
        display_surfaces(card_list)
        if result:
            result_surf = font_large.render(result, True, (255, 255, 255))
            result_rect = result_surf.get_rect(center=(SCREEN_WIDTH/2, 40))
            screen.blit(result_surf, result_rect)
            


    # update display in every loop
    # TODO decide which best to contain the cards (list or group)
    pygame.sprite.Group(*card_list).update()
    pygame.display.update()
    clock.tick(1000)


    if len(to_compare) == 2 and animation_stopped(to_compare) and not result:
        if to_compare[0].same_image(to_compare[1]):
            if turn is Player.player1:
                player1_score += 1
            else: 
                player2_score += 1
            
            if all_opened(card_list):
                if player1_score > player2_score:
                    result = f'{Player.player1.value} won'
                elif player1_score < player2_score:
                    result = f'{Player.player2.value} won'
                else:
                    result = 'tie!'
            else:
                turn = Player.player2 if turn is Player.player1 else Player.player1 
            to_compare.clear()
        else:
            to_compare.append('this to make the condition above false (~˘▾˘)~')
            pygame.time.set_timer(flip_timer, 1000, 1)