#!/usr/bin/python3
import sys
sys.modules["numpy"]=None
import json, os, re, collections, sys, pygame, tempfile, math, subprocess

def edit_file(name, contents, editor_cmd):
    try:
        with tempfile.NamedTemporaryFile(
                mode='w', suffix=".yarn.txt", prefix=name+"_", delete=False) as file_obj:
            file_obj.write(name+"\n")
            file_obj.write(contents)
            file_name=file_obj.name
        success=False
        fallback_editors= [["emacsclient", "-c"], ["subl", "-n", "-w"], ["code", "--wait"], ["gvim", "-f"]]
        if editor_cmd:
            fallback_editors= [editor_cmd]+fallback_editors
        for editor in fallback_editors:
            try:
                result=subprocess.run(editor+[file_obj.name])
                if result.returncode==0:
                    success=True
                    break
            except FileNotFoundError:
                success=False
        if success:
            with open(file_name, "r") as file_obj:
                name=file_obj.readline().strip()
                contents=file_obj.read()
        else:
            print("error return code")
    finally:
        os.unlink(file_name)
    return name, contents

def find_links(text):
    result=[]
    link_rgx = r"\[\[([^\|\[\]]*?)\|([\$\w]+)\]\]"
    for link in re.finditer(link_rgx, text):
        result.append(link[2])
    return result

def zoom_pt(pt, zoom, scroll):
    tx, ty=pt
    scroll_x, scroll_y=scroll
    tx-=scroll_x
    ty-=scroll_y
    if zoom > 0:
        tx/=zoom
        ty/=zoom
    return tx,ty

def zoom_inverse(pt, zoom, scroll):
    tx, ty=pt
    scroll_x, scroll_y=scroll
    tx*=zoom
    ty*=zoom
    tx+=scroll_x
    ty+=scroll_y
    return tx,ty

def editor():
    try:
        file_name=sys.argv[1]
    except:
        print("usage: python3 editor.py filename.json [texteditor [params]]")
        print("eg: python3 editor.py filename.json gedit")

    editor_program=None
    if len(sys.argv) > 2:
        editor_program=sys.argv[2:]
        
    if os.path.exists(file_name):
        with open(file_name) as thefile:
            json_content=json.load(thefile)
    else:
        json_content=[
            dict(tags=[],
                 title="Start",
                 position=dict(
                     x=100,
                     y=100),
                 colorID=0,
                 body="Empty Text")]

    pygame.init()
    SCREEN_SIZE=800,600
    screen=pygame.display.set_mode(SCREEN_SIZE)
    font1=pygame.font.SysFont("Arial", 16)
    font2=pygame.font.SysFont("ubuntumono", 11)
    font3=pygame.font.SysFont("Arial", 48)

    clock=pygame.time.Clock()
    running=True
    clicked=None
    doubleclick_time=-1

    named_nodes={}

    zoom=1
    scroll_x=0
    scroll_y=0

    for arect in json_content:
        pos=(arect["position"]["x"],arect["position"]["y"])
        arect["rect"]=pygame.Rect(pos, (200,100))
        arect["links"]=find_links(arect["body"])
        named_nodes[arect["title"]]=arect

    if "Start" in named_nodes:
        scroll_x=named_nodes["Start"]["position"]["x"]-20
        scroll_y=named_nodes["Start"]["position"]["y"]-20

    while running:
        evs=pygame.event.get()
        keys=pygame.key.get_pressed()
        mouse=pygame.mouse.get_pressed()
        mpx,mpy=pygame.mouse.get_pos()
        mx,my=zoom_inverse((mpx,mpy), zoom, (scroll_x, scroll_y))

        for e in evs:
            if e.type==pygame.QUIT:
                for arect in json_content:
                    del arect["rect"]
                    del arect["links"]
                with open(file_name, "w") as thefile:
                    json.dump(json_content, thefile, indent=3, sort_keys=True, )
                running=False
                return
            if e.type==pygame.MOUSEMOTION:
                doubleclick_time=-1
                buttons=e.buttons
                rx,ry=e.rel
                rx*=zoom
                ry*=zoom
                if buttons[0] and clicked:
                    margin=100
                    hit_margin=False
                    if mpx<margin:
                        hit_margin=True
                        mpx=margin
                        scroll_x-=rx
                        pygame.mouse.set_pos(mpx, mpy)
                        pygame.event.pump()
                    if mpx>SCREEN_SIZE[0]-margin:
                        hit_margin=True
                        scroll_x-=rx
                        mpx=SCREEN_SIZE[0]-margin
                        pygame.mouse.set_pos(mpx, mpy)
                        pygame.event.pump()
                    if mpy<margin:
                        hit_margin=True
                        mpy=margin
                        scroll_y-=ry
                        pygame.mouse.set_pos(mpx, mpy)
                        pygame.event.pump()
                    if mpy>SCREEN_SIZE[1]-margin:
                        hit_margin=True
                        mpy=SCREEN_SIZE[1]-margin
                        scroll_y-=ry
                        pygame.mouse.set_pos(mpx, mpy)
                        pygame.event.pump()

                    if hit_margin:
                        clicked["rect"].center=mx, my
                    else:
                        clicked["rect"]=clicked["rect"].move(rx, ry)
                    clicked["position"]["x"]=clicked["rect"].left
                    clicked["position"]["y"]=clicked["rect"].top
                elif buttons[0]:
                    scroll_x-=rx
                    scroll_y-=ry
            if e.type==pygame.MOUSEBUTTONUP:
                pass
            if e.type==pygame.MOUSEBUTTONDOWN:
                if e.button==5:
                    if zoom<6:
                        zoom+=1
                    scroll_x,scroll_y=mx-mpx*zoom, my-mpy*zoom

                if e.button==4:
                    scroll_x, scroll_y=mx, my
                    if zoom>1:
                        zoom-=1
                    scroll_x,scroll_y=mx-mpx*zoom, my-mpy*zoom

                if e.button==2:
                    clicked=None
                    doubleclick_time=-1
                    for arect in json_content:
                        if arect["rect"].collidepoint(mx,my):
                            clicked=arect
                    if clicked:
                        off=0
                        for link in clicked["links"]:
                            if link in named_nodes:
                                pass
                            else:
                                newrect=dict(tags=[],
                                             title=link,
                                             position=dict(
                                                 x=mx+off,
                                                 y=my+off),
                                             colorID=0,
                                             body="Empty Text")
                                newrect["rect"]=pygame.Rect((mx, my), (200,100))
                                newrect["links"]=[]
                                named_nodes[link]=newrect
                                json_content.append(newrect)
                                off+=20
                if e.button==1:
                    if doubleclick_time>0:
                        doubleclick_time=-1
                        if clicked:
                            #doubleclicked
                            name=clicked["title"]
                            contents=clicked["body"]
                            del clicked["links"]
                            del named_nodes[name]
                            screen.blit(font3.render("WAITING FOR EDITOR", 0, (200,0,0)),
                                        (100,100))
                            pygame.display.flip()
                            name,contents=edit_file(name, contents, editor_program)
                            pygame.event.pump()
                            clicked["title"]=name
                            clicked["body"]=contents
                            named_nodes[name]=clicked
                            clicked["links"]=find_links(contents)
                    else:
                        clicked=None
                        for arect in json_content:
                            if arect["rect"].collidepoint(mx,my):
                                clicked=arect
                                doubleclick_time=15
        if doubleclick_time>0:
            doubleclick_time-=1
            if doubleclick_time<=0:
                clicked=None

        screen.fill((255,255,255))
        for arect in json_content:
            tx,ty=arect["rect"].topleft
            tx,ty=zoom_pt((tx,ty), zoom, (scroll_x, scroll_y))
            ty_top=ty
            pygame.draw.rect(screen, (0,0,200), (tx, ty, arect["rect"].w/zoom, arect["rect"].h/zoom), 1)
            tx+=2
            if zoom > 4:
                screen.blit(font2.render(arect["title"], 0, (0,0,0)),(tx, ty))

            else:
                screen.blit(font1.render(arect["title"], 0, (0,0,0)),(tx, ty))
            ty+=9

            #if zoom==1:
            line_len=32/zoom
            for line in arect["body"].split("\n"):
                ty+=11
                if ty > ty_top+arect["rect"].height/zoom - 12:
                    break
                line_len=32//zoom
                if len(line)> line_len:
                    line=line[:(line_len-1)]+".."
                screen.blit(font2.render(line, 0, (0,0,0)), (tx, ty))



        for arect in json_content:
            for link in arect["links"]:
                if link in named_nodes:
                    srcx,srcy=arect["rect"].midbottom
                    trgx,trgy=named_nodes[link]["rect"].midtop

                    if zoom>2:
                        if named_nodes[link]["rect"].top < arect["rect"].bottom:
                            srcy = arect["rect"].top
                            trgy=named_nodes[link]["rect"].bottom
                        if named_nodes[link]["rect"].left>arect["rect"].right:
                            srcx = arect["rect"].right
                            trgx=named_nodes[link]["rect"].left
                        if named_nodes[link]["rect"].right<arect["rect"].left:
                            srcx = arect["rect"].left
                            trgx=named_nodes[link]["rect"].right


                    diff1=trgx-srcx
                    srcx+=diff1*0.05
                    trgx-=diff1*0.2
                    if srcx<arect["rect"].left:
                        srcx=arect["rect"].left
                    if srcx>arect["rect"].right:
                        srcx=arect["rect"].right
                    if trgx<named_nodes[link]["rect"].left:
                        trgx=named_nodes[link]["rect"].left
                    if trgx>named_nodes[link]["rect"].right:
                        trgx=named_nodes[link]["rect"].right

                    srcx,srcy=zoom_pt((srcx,srcy), zoom, (scroll_x, scroll_y))
                    trgx,trgy=zoom_pt((trgx,trgy), zoom, (scroll_x, scroll_y))
                    diff=trgx-srcx

                    if zoom>2 or srcy < trgy:
                        pygame.draw.line(screen, (0,200,0), (srcx, srcy),
                                         (trgx, trgy), 1)
                    else:
                        gap=arect["rect"].width/2
                        if abs(diff1) < arect["rect"].width and diff1 >= 0:
                            p1 = (srcx+diff*0.05-60/zoom, srcy+(35+abs(diff)*0.1)/zoom)
                            p2 = (srcx-(diff+10)*0.2-gap/zoom, srcy+(15+abs(diff)*0.05)/zoom)
                            p3 = (srcx-diff*0.1-gap/zoom, trgy-(15+abs(diff)*0.05)/zoom)
                            p4 = (trgx+diff*0.05-60/zoom, trgy-(35+abs(diff)*0.1)/zoom)
                        elif abs(diff1) < arect["rect"].width and diff1 < 0:
                            p1 = (srcx+diff*0.05+60/zoom, srcy+(35+abs(diff)*0.1)/zoom)
                            p2 = (srcx-(diff-10)*0.2+gap/zoom, srcy+(15+abs(diff)*0.05)/zoom)
                            p3 = (srcx-diff*0.1+gap/zoom, trgy-(15+abs(diff)*0.05)/zoom)
                            p4 = (trgx+diff*0.05+60/zoom, trgy-(35+abs(diff)*0.1)/zoom)
                        else:
                            dx=math.copysign(gap, diff)
                            p1 = (srcx+diff*0.05+(dx/2)/zoom, srcy+(35+abs(diff)*0.1)/zoom)
                            p2 = (srcx+diff*0.08+dx/zoom,     srcy+(15+abs(diff)*0.05)/zoom)
                            p3 = (trgx-diff*0.08-dx/zoom,     trgy-(15+abs(diff)*0.05)/zoom)
                            p4 = (trgx-diff*0.05-(dx/2)/zoom, trgy-(35+abs(diff)*0.1)/zoom)

                        pygame.draw.line(screen, (0,200,0),
                                         (srcx, srcy),p1, 1)
                        pygame.draw.line(screen, (0,200,0),p1, p2, 1)
                        pygame.draw.line(screen, (0,200,0),p2, p3, 1)
                        pygame.draw.line(screen, (0,200,0),p3, p4, 1)
                        pygame.draw.line(screen, (0,200,0), p4, (trgx, trgy), 1)
                        srcx, srcy=p4

                    angle=math.atan2(trgy-srcy, trgx-srcx)
                    angle1=angle+0.3
                    angle2=angle-0.3
                    trgx1=trgx-10*math.cos(angle1)
                    trgy1=trgy-10*math.sin(angle1)

                    trgx2=trgx-10*math.cos(angle2)
                    trgy2=trgy-10*math.sin(angle2)

                    pygame.draw.line(screen, (0,200,0), (trgx1, trgy1),
                                     (trgx, trgy), 2)
                    pygame.draw.line(screen, (0,200,0), (trgx2, trgy2),
                                     (trgx, trgy), 2)
                else:
                    screen.blit(font2.render("[["+link+"]]", 0, (200,0,0)), arect["rect"].bottomleft)

        pygame.display.flip()
        clock.tick(30)

if __name__=="__main__":
    editor()
