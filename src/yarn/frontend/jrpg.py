# part of yarn.py, copyright © 2019 Robert Pfeiffer
import yarn
import pygame
import re

class Characters(object):
    pass

class Dialogue(object):
    def __init__(self, name, path, characters, box, font):
        self.characters={}
        chars_obj=Characters

        for char_name in characters:
            self.characters[char_name.lower()]=characters[char_name]
            setattr(chars_obj,char_name,characters[char_name])

        self.controller=yarn.YarnController(path, name, False, dict(chars=chars_obj))
        self.message=self.controller.message().split("\n")
        self.message_line=0
        self.box_template=box
        self.font=font
        self.options=self.controller.choices()
        self.selected=0
        self.finished=False

    def advance(self):
        if self.message_line < len(self.message):
            self.message_line+=1
        if (self.message_line == len(self.message)
            and self.controller.finished):
            self.finished=True

    def select_next(self):
        if (self.message_line == len(self.message) and
            self.selected < len(self.options)-1):
            self.selected+=1
            
    def select_prev(self):
        if (self.message_line == len(self.message) and
            self.selected > 0):
            self.selected-=1

    def choose_option(self):
        if self.finished:
            return
        if (self.message_line == len(self.message)):
            self.controller.transition(self.options[self.selected])
            self.message=self.controller.message().split("\n")
            self.message_line=0
            self.options=self.controller.choices()
            self.selected=0
            
    def draw(self, screen):
        if self.finished:
            return
        if self.message_line == len(self.message):
            message_content=self.message[-1]
        else:
            message_content=self.message[self.message_line]
        dialogue_line_portrait=r"(\w+)\((\w+)\)\:(.*)"
        dialogue_line_neutral=r"(\w+)\:(.*)"
        
        match_pt=re.match(dialogue_line_portrait, message_content)
        match_nt=re.match(dialogue_line_neutral, message_content)

        nchars=0
        cum_x=0
        cum_y=0
        screen_rect=screen.get_rect()
        for char in self.characters:
            char_x, char_y=self.characters[char].rect.center
            cum_x+=char_x
            cum_y+=char_y
            nchars+=1
        if nchars>0:
            avg_x=cum_x/nchars
            avg_y=cum_y/nchars
        else:
            avg_y=screen_rect.width//2

        h=screen_rect.height
        w=screen_rect.width
        target_rect=pygame.Rect(0, h-(h//5), w, h//5)
        content,_= self.box_template.blit(screen,target_rect)
 
        if match_pt or match_nt:
            match=match_pt or match_nt
            char = self.characters[match[1].lower()]
            char_x, char_y = char.rect.center
            if match_pt:
                emotion=match_pt[2]
                message_content=match_pt[3]
            else:
                emotion="neutral"
                message_content=match_nt[2]
            portrait = char.portraits[emotion]
            portrait_rect=portrait.get_rect()
            if char_x > avg_x:
                portrait_rect.right=content.right-5
            else:
                portrait_rect.left=content.left+5                
            portrait_rect.bottom=target_rect.top
        else:
            portrait=None
        if portrait:
            self.box_template.blit_content(screen, portrait_rect, portrait)

        text = self.font.render(message_content, 0, (0,0,0))
        screen.blit(text, content.topleft)
            
        if self.message_line == len(self.message):
            posx,posy=content.topleft
            posy+=text.get_height()+5
            posx+=5
            for option_i in range(len(self.options)):
                option_text=self.font.render(self.options[option_i], 0, (0,0,0))
                option_rect=option_text.get_rect()
                option_rect.topleft=posx,posy
                if option_rect.right>content.right:
                    posx=content.left
                    posy+=3+option_rect.height
                screen.blit(option_text, (posx, posy))
                if option_i==self.selected:
                    draw_rect=option_rect.copy()
                    draw_rect.topleft=posx-2,posy-2
                    draw_rect.w+=3
                    draw_rect.h+=3
                    pygame.draw.rect(screen, (200,0,0), draw_rect, 1)
                posx+=option_rect.width+5                
                
if __name__=="__main__":
    import ninepatch
    import sys
    import webm_recording
    
    pygame.init()
    screen=pygame.display.set_mode((320,240), pygame.SCALED)

    group=pygame.sprite.Group()
    triangle=pygame.sprite.Sprite()
    triangle.image=pygame.image.load("triangle_sprite.png").convert_alpha()
    triangle.rect=triangle.image.get_rect()
    triangle.rect.topleft=20,20
    triangle.portraits=dict(
    neutral=pygame.image.load("triangle_portrait_neutral.png").convert_alpha(),
    angry=pygame.image.load("triangle_portrait_angry.png").convert_alpha(),
    happy=pygame.image.load("triangle_portrait_happy.png").convert_alpha(),
    surprised=pygame.image.load("triangle_portrait_surprised.png").convert_alpha())
    
    square=pygame.sprite.Sprite()
    square.image=pygame.image.load("square_sprite.png").convert_alpha()
    square.rect=square.image.get_rect()
    square.rect.topleft=200,20
    square.portraits=dict(
    neutral=pygame.image.load("square_portrait_neutral.png").convert_alpha(),
    happy=pygame.image.load("square_portrait_happy.png").convert_alpha())
    group.add(square)
    group.add(triangle)

    ninpatch=pygame.image.load("ninpatch.png")
    template=ninepatch.NinePatchTemplate(ninpatch, pygame.Rect(12,12,5,5), pygame.Rect(8,7,18,19))
    font=pygame.font.SysFont("Arial", 11)
    dialogue=Dialogue(sys.argv[1], sys.argv[1], dict(square=square, triangle=triangle), template, font)

    clip_recorder=webm_recording.Recorder(screen, prefix="jrpg_dialogue")
    clip_recorder.start()
    
    clock=pygame.time.Clock()
    running=True
    while running:
        evs=pygame.event.get()
        for e in evs:
            if e.type==pygame.QUIT:
                running=False
            if e.type==pygame.KEYDOWN and e.key==pygame.K_SPACE:
                dialogue.advance()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_RIGHT:
                dialogue.select_next()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_LEFT:
                dialogue.select_prev()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN:
                dialogue.choose_option()

        screen.fill((255,255,255))
        group.draw(screen)
        dialogue.draw(screen)
        clip_recorder.record_maybe()
        pygame.display.flip()
        clock.tick(30)
    clip_recorder.finish()
    pygame.quit()
