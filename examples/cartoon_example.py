# part of yarn.py, copyright © 2019 Robert Pfeiffer
import pygame
import sys
from yarn.frontend import NinePatchTemplate
from yarn.frontend import Cartoon
    
pygame.init()
screen=pygame.display.set_mode((640,360), pygame.SCALED)

group=pygame.sprite.Group()
triangle=pygame.sprite.Sprite()
triangle.image=pygame.image.load("assets/sprites/triangle_sprite.png").convert_alpha()
triangle.rect=triangle.image.get_rect()
triangle.rect.topleft=400,200
    
square=pygame.sprite.Sprite()
square.image=pygame.image.load("assets/sprites/square_sprite.png").convert_alpha()
square.rect=square.image.get_rect()
square.rect.topleft=200,200

group.add(square)
group.add(triangle)

ninpatch=pygame.image.load("assets/cartoon/bubble3.png")
template_speech_bubble=NinePatchTemplate(ninpatch, pygame.Rect(11,11,8,4), pygame.Rect(6,6,20,15))
ninpatch=pygame.image.load("assets/cartoon/thought2.png").convert_alpha()
template_thought_bubble=NinePatchTemplate(ninpatch, pygame.Rect(24,24,8,8), pygame.Rect(14,14,35,26), True)
ninpatch=pygame.image.load("assets/cartoon/thought2.png").convert_alpha()
template_thought_bubble=NinePatchTemplate(ninpatch, pygame.Rect(24,24,12,12), pygame.Rect(14,14,35,26))
    
font=pygame.font.SysFont("Arial", 11)
dialogue=Cartoon("dialogue", "yarns/cartoon_dialogue.json", dict(square=square, triangle=triangle), triangle, template_speech_bubble, template_thought_bubble, 3, font)

dialogue.deliver_line()
    
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
    dialogue.run_stage_direction(screen.get_rect())
    dialogue.bubbles_g.draw(screen)
    if dialogue.thought_bubbles:
        sel_rect=dialogue.thought_bubbles[dialogue.selected] 
        pygame.draw.rect(screen, (200,0,0), sel_rect, 1)
    pygame.display.flip()
    clock.tick(30)
pygame.quit()
