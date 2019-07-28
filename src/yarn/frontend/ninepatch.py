import pygame
import math
def make_rect(x1,y1,x2,y2):
    return pygame.Rect(x1,y1,x2-x1, y2-y1)

def make_rect_alt(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    if x1>x2:
        x1, x2=x2, x1
    if y1>y2:
        y1, y2=y2, y1
        
    return pygame.Rect(x1,y1,x2-x1,y2-y1)

class NinePatchTemplate(object):
    def __init__(self, image, patch_rect, content_rect, tile=False):
        self.image=image
        self.fullrect=image.get_rect()
        self.content_rect=content_rect

        self.center=patch_rect
        self.topleft = make_rect(0, 0,
                                 patch_rect.left, patch_rect.top)
        self.topright= make_rect(patch_rect.right, 0,
                                 self.fullrect.right, patch_rect.top)
        self.bottomleft=make_rect(0, patch_rect.bottom,
                                  patch_rect.left,self.fullrect.bottom)
        self.bottomright=make_rect(patch_rect.right, patch_rect.bottom,
                                   self.fullrect.right, self.fullrect.bottom)
        self.top=make_rect(patch_rect.left, 0,
                           patch_rect.right, patch_rect.top)
        self.bottom=make_rect(patch_rect.left, patch_rect.bottom,
                              patch_rect.right, self.fullrect.bottom)
        self.left=make_rect(0, patch_rect.top,
                            patch_rect.left, patch_rect.bottom)
        self.right=make_rect(patch_rect.right, patch_rect.top,
                            self.fullrect.right, patch_rect.bottom)
        self.tile=tile

    def blit_content(self, target_surf, content_rect, content):
        target_rect=self.calc_target_rect(content_rect)
        res = self.blit(target_surf, target_rect)
        target_surf.blit(content, content_rect.topleft)
        return res

    def calc_target_rect(self, content_rect):
        target_rect=pygame.Rect(
            content_rect.left+(self.fullrect.left-
                                self.content_rect.left),
            content_rect.top+(self.fullrect.top-
                              self.content_rect.top),
            content_rect.width+(self.fullrect.width-
                                self.content_rect.width),
            content_rect.height+(self.fullrect.height-
                                  self.content_rect.height))
        if target_rect.width<self.fullrect.width-self.center.width:
            target_rect.width=self.fullrect.width-self.center.width
        if target_rect.height<self.fullrect.height-self.center.height:
            target_rect.height=self.fullrect.height-self.center.height
        if self.tile:
            cw=self.center.width
            ch=self.center.height
            dw=self.fullrect.width-cw
            dh=self.fullrect.height-ch
            tcw=target_rect.width-dw
            tch=target_rect.width-dh
            target_rect.w=math.ceil(tcw/cw)*cw+dw
            target_rect.h=math.ceil(tch/ch)*ch+dh            
        return target_rect

    def blit(self, target_surf, target_rect):
        assert(target_rect.width>=self.fullrect.width-self.center.width)
        assert(target_rect.height>=self.fullrect.height-self.center.height)
        
        patch_rect=self.center.move(target_rect.topleft)
        patch_rect.width=target_rect.width-(self.fullrect.width-
                                            patch_rect.width)
        patch_rect.height=target_rect.height-(self.fullrect.height-
                                              patch_rect.height)
        
        topleft=self.topleft.move(target_rect.topleft)
        topright=self.topright.copy()
        topright.topright=target_rect.topright
        bottomleft=self.bottomleft.copy()
        bottomleft.bottomleft=target_rect.bottomleft
        bottomright=self.bottomright.copy()
        bottomright.bottomright=target_rect.bottomright
        
        top=self.top.copy()
        top.width=patch_rect.width
        top.top=target_rect.top
        top.left=patch_rect.left

        #pygame.draw.rect(target, (0,255,255), top, 1)
        #pygame.draw.rect(target, (0,255,0), topleft, 1)

        right=self.right.copy()
        right.height=patch_rect.height
        right.topleft=patch_rect.topright
        
        bottom=self.bottom.copy()
        bottom.width=patch_rect.width
        bottom.topleft=patch_rect.bottomleft
        
        left=self.left.copy()
        left.height=patch_rect.height
        left.topright=patch_rect.topleft

        if self.tile:
            left1=self.left.copy()
            left1.topleft=left.topleft
            right1=self.right.copy()
            right1.topleft=right.topleft

            while left1.bottom<=bottomleft.top:
                target_surf.blit(self.image, left1, self.left)
                target_surf.blit(self.image, right1, self.right)
                left1.top+=left1.height
                right1.top=left1.top
                
            top1=self.top.move(target_rect.topleft)
            bottom1=self.bottom.copy()
            bottom1.top=bottom.top
            bottom1.left=top1.left

            while top1.right<=topright.left:
                target_surf.blit(self.image, bottom1, self.bottom)
                target_surf.blit(self.image, top1, self.top)
                top1.left+=top1.width
                bottom1.left=top1.left

                
        else:
            left_scaled=pygame.transform.scale(self.image.subsurface(self.left), left.size)
            right_scaled=pygame.transform.scale(self.image.subsurface(self.right), right.size)
            top_scaled=pygame.transform.scale(self.image.subsurface(self.top), top.size)
            bottom_scaled=pygame.transform.scale(self.image.subsurface(self.bottom), bottom.size)
        
            target_surf.blit(left_scaled, left)
            target_surf.blit(right_scaled, right)
            target_surf.blit(top_scaled, top)
            target_surf.blit(bottom_scaled, bottom)

        center_scaled=pygame.transform.scale(self.image.subsurface(self.center), patch_rect.size)
        target_surf.blit(center_scaled, patch_rect)

        target_surf.blit(self.image, topleft, self.topleft)
        target_surf.blit(self.image, topright, self.topright)
        target_surf.blit(self.image, bottomright, self.bottomright)
        target_surf.blit(self.image, bottomleft, self.bottomleft)

        content=self.content_rect.move(target_rect.topleft) 
        content.width=target_rect.width-(self.fullrect.width-content.width)
        content.height=target_rect.height-(self.fullrect.height-content.height)

        return content, patch_rect

    
if __name__=="__main__":
    
    pygame.init()
    target=pygame.Surface((256,256), 32)
    
    ninpatch=pygame.image.load("ninpatch.png")
    template=NinePatchTemplate(ninpatch, pygame.Rect(12,12,5,5), pygame.Rect(7,7,19,19))

    ninpatch=pygame.image.load("bubble2.png")
    template2=NinePatchTemplate(ninpatch, pygame.Rect(11,11,8,4), pygame.Rect(6,6,20,15))

    ninpatch=pygame.image.load("thought2.png")
    template3=NinePatchTemplate(ninpatch, pygame.Rect(24,24,8,8), pygame.Rect(14,14,35,26), True)

    content,pr=template3.blit(target,pygame.Rect(0,0,64,192))
    pygame.draw.rect(target, (255,0,0), content, 1)
    #pygame.draw.rect(target, (0,0,255), pr, 1)

    content,pr=template.blit(target,pygame.Rect(0,192,256,64))
    pygame.draw.rect(target, (255,0,0), content,1)
    #pygame.draw.rect(target, (0,0,255), pr, 1)

   
    content,pr=template2.blit(target,pygame.Rect(32,64,128,48))
    pygame.draw.rect(target, (255,0,0), content,1)
    #pygame.draw.rect(target, (0,0,255), pr, 1)

    
    content,pr=template3.blit(target,pygame.Rect(128,0,128,96))
    pygame.draw.rect(target, (255,0,0), content, 1)

    #pygame.draw.rect(target, (0,0,255), pr, 1)
    
    pygame.image.save(target, "ninpatch-saved.png")
