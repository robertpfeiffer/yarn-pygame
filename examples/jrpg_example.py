import pygame
import sys
from yarn.frontend import NinePatchTemplate
from yarn.frontend import JRPG

pygame.init()
screen=pygame.display.set_mode((320,240), pygame.SCALED)

group=pygame.sprite.Group()
triangle=pygame.sprite.Sprite()
triangle.image=pygame.image.load("assets/sprites/triangle_sprite.png").convert_alpha()
triangle.rect=triangle.image.get_rect()
triangle.rect.topleft=20,20
triangle.portraits=dict(
neutral=pygame.image.load("assets/portraits/triangle_portrait_neutral.png").convert_alpha(),
angry=pygame.image.load("assets/portraits/triangle_portrait_angry.png").convert_alpha(),
happy=pygame.image.load("assets/portraits/triangle_portrait_happy.png").convert_alpha(),
surprised=pygame.image.load("assets/portraits/triangle_portrait_surprised.png").convert_alpha())

square=pygame.sprite.Sprite()
square.image=pygame.image.load("assets/sprites/square_sprite.png").convert_alpha()
square.rect=square.image.get_rect()
square.rect.topleft=200,20
square.portraits=dict(
neutral=pygame.image.load("assets/portraits/square_portrait_neutral.png").convert_alpha(),
happy=pygame.image.load("assets/portraits/square_portrait_happy.png").convert_alpha())
group.add(square)
group.add(triangle)

ninpatch=pygame.image.load("assets/ui/ninpatch.png")
template=NinePatchTemplate(ninpatch, pygame.Rect(12,12,5,5), pygame.Rect(8,7,18,19))
font=pygame.font.SysFont("Arial", 11)
dialogue=JRPG("a heated exchange","yarns/JRPG_dialogue.json", dict(square=square, triangle=triangle), template, font)

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
    pygame.display.flip()
    clock.tick(30)
pygame.quit()
