import yarn
import pygame
import re

class Characters(object):
    pass

class Dialogue(object):
    def __init__(self, name, path, characters, main_character, speech, thought, n_bubbles, font):
        self.characters={}
        chars_obj=Characters

        for char_name in characters:
            self.characters[char_name.lower()]=characters[char_name]
            setattr(chars_obj,char_name,characters[char_name])

        nchars=0
        cum_x=0
        min_y=10000
        for char in self.characters:
            char_x = self.characters[char].rect.centerx
            char_y = self.characters[char].rect.top
            cum_x+=char_x
            min_y=min(min_y, char_y)
            nchars+=1
        assert(nchars>0)
        self.avg_x=cum_x/nchars
        self.min_y=min_y - 3

        self.controller=yarn.YarnController(path, name, False, dict(chars=chars_obj))
        self.message=self.controller.message().split("\n")
        self.message_line=0
        self.speech_template=speech
        self.thought_template=thought
        self.font=font
        self.options=self.controller.choices()
        self.selected=0
        self.finished=False
        self.n_bubbles=n_bubbles
        self.bubbles=[]
        self.thought_bubbles=[]
        self.bubbles_g=pygame.sprite.Group()
        self.main_character=main_character

    def init(self):
        if len(self.message)==0:
            return
        line=self.message[self.message_line]
        if self.message_line < len(self.message):
            new_bubble=self.draw_bubble(line)
            for other_bubble in self.bubbles:
                other_bubble.rect.top -= (new_bubble.rect.height + 3)
            self.bubbles.append(new_bubble)
            self.bubbles_g.add(new_bubble)

    def advance(self):
        if self.finished:
            for bubble in self.bubbles_g:
                bubble.kill()
            return
        if self.message_line < len(self.message):
            self.message_line+=1
        if self.message_line < len(self.message):
            line=self.message[self.message_line]
            if not line.isspace():
                if len(self.bubbles)>=self.n_bubbles:
                    self.bubbles[0].kill()
                    self.bubbles=self.bubbles[1:]
                self.init()
        if (self.message_line == len(self.message)
            and self.controller.finished):
            self.finished=True
            for bubble in self.bubbles_g:
                bubble.kill()
            return
        if (self.message_line == len(self.message)
            and self.options):
            if len(self.bubbles)>=self.n_bubbles:
                self.bubbles[0].kill()
                self.bubbles=self.bubbles[1:]
            self.thought_bubbles=self.draw_thought_bubbles()
            for tb in self.thought_bubbles:
                self.bubbles_g.add(tb)
                

    def select_next(self):
        if (self.message_line == len(self.message) and
            self.selected < len(self.options)-1):
            self.selected+=1

    def select_prev(self):
        if (self.message_line == len(self.message) and
            self.selected > 0):
            self.selected-=1

    def prepare_bubble(self, line, template, flipped):
        text = self.font.render(line, 0, (0,0,0))
        bubble_rect= template.calc_target_rect(text.get_rect())
        bubble_rect.topleft=(0,0)
        bubble_surf=pygame.Surface(bubble_rect.size).convert()
        bubble_surf.fill((255, 0, 255, 0))
        bubble_surf.set_colorkey((255, 0, 255))
        
        print(bubble_rect)
        print(line)
        content_rect,_=template.blit(bubble_surf, bubble_rect)
        if flipped:
            bubble_surf=pygame.transform.flip(bubble_surf, True, False)
            content_rect.left=bubble_rect.right-content_rect.right
        bubble_surf.blit(text, content_rect.topleft)
        return bubble_surf
            
    def draw_thought_bubble(self, line):
        character=self.main_character
        bubble_surf=self.prepare_bubble(
            line,
            self.thought_template,
            character.rect.centerx < self.avg_x)
        bubble_rect=bubble_surf.get_rect()
        bubble_sprite=pygame.sprite.Sprite()
        bubble_sprite.image=bubble_surf
        bubble_sprite.rect=bubble_rect
        bubble_sprite.text=line
        bubble_sprite.character=character
        if character.rect.centerx < self.avg_x:
            bubble_rect.right=character.rect.left
        else:
            bubble_rect.left=character.rect.right
        bubble_rect.bottom=self.min_y
        return bubble_sprite

    def draw_thought_bubbles(self):
        result=[]
        for option in self.options:
            sprite=self.draw_thought_bubble(option)
            for r in result:
                r.rect.top-= sprite.rect.height+3
            result.append(sprite)
        return result
            
    
    def draw_bubble(self, line):
        dialogue_line=r"(\w+)\:(.*)"
        match=re.match(dialogue_line, line)
        assert(match is not None)
        character=self.characters[match[1]]
        content=match[2].strip()
        bubble_surf=self.prepare_bubble(
            content,
            self.speech_template,
            character.rect.centerx > self.avg_x)
        bubble_rect=bubble_surf.get_rect()
        bubble_sprite=pygame.sprite.Sprite()
        bubble_sprite.image=bubble_surf
        bubble_sprite.rect=bubble_rect
        bubble_sprite.text=line
        bubble_sprite.character=character
        
        if character.rect.centerx < self.avg_x:
            bubble_rect.left=character.rect.right
        else:
            bubble_rect.right=character.rect.left
        bubble_rect.bottom=self.min_y
        return bubble_sprite

    def choose_option(self):
        if self.finished:
            return
        if (self.message_line == len(self.message)):
            self.controller.transition(self.options[self.selected])
            self.message=self.controller.message().split("\n")
            print(self.message)
            self.message_line=0
            self.options=self.controller.choices()
            self.selected=0
            for bubble in self.bubbles_g:
                bubble.kill()
            self.bubbles=[]
            self.thought_bubbles=[]
            self.init()
            

if __name__=="__main__":
    from ninepatch import NinePatchTemplate
    import webm_recording
    
    pygame.init()
    screen=pygame.display.set_mode((640,360), pygame.SCALED)

    group=pygame.sprite.Group()
    triangle=pygame.sprite.Sprite()
    triangle.image=pygame.image.load("triangle_sprite.png").convert_alpha()
    triangle.rect=triangle.image.get_rect()
    triangle.rect.topleft=400,200
    
    square=pygame.sprite.Sprite()
    square.image=pygame.image.load("square_sprite.png").convert_alpha()
    square.rect=square.image.get_rect()
    square.rect.topleft=200,200

    group.add(square)
    group.add(triangle)

    ninpatch=pygame.image.load("bubble3.png")
    template_speech_bubble=NinePatchTemplate(ninpatch, pygame.Rect(11,11,8,4), pygame.Rect(6,6,20,15))
    ninpatch=pygame.image.load("thought2.png").convert_alpha()
    template_thought_bubble=NinePatchTemplate(ninpatch, pygame.Rect(24,24,8,8), pygame.Rect(14,14,35,26), True)
    ninpatch=pygame.image.load("thought2.png").convert_alpha()
    template_thought_bubble=NinePatchTemplate(ninpatch, pygame.Rect(24,24,12,12), pygame.Rect(14,14,35,26))
    
    font=pygame.font.SysFont("Arial", 11)
    dialogue=Dialogue("dialogue", "dialogue2.json", dict(square=square, triangle=triangle), triangle, template_speech_bubble, template_thought_bubble, 3, font)

    clip_recorder=webm_recording.Recorder(screen, prefix="cartoon_dialogue")
    clip_recorder.start()

    dialogue.init()
    
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
        dialogue.bubbles_g.draw(screen)
        if dialogue.thought_bubbles:
            sel_rect=dialogue.thought_bubbles[dialogue.selected] 
            pygame.draw.rect(screen, (200,0,0), sel_rect, 1)
        clip_recorder.record_maybe()
        pygame.display.flip()
        clock.tick(30)
    clip_recorder.finish()
    pygame.quit()
