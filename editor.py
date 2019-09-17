#!/usr/bin/python3
# -*- mode: python; coding: utf-8; indent-tabs-mode: nil;  -*-

"""
minimal Yarn dialogue editor
copyright © 2019 Robert Pfeiffer

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


The standard Yarn editor is based on node-webkit, eats ram, and isn't emacs.
This one is based on pygame, runs on a potato, and calls emacs for text editing.

You probably won't find it super useful if your main development machine is a
Macbook Pro.
"""


import sys
sys.modules["numpy"]=None
import json, os, re, collections, sys, pygame, tempfile, math, subprocess

colorids=[(255,255,255), (0x6E, 0xA5, 0xE0), (0x9E, 0xDE, 0x74),
          (0xFF, 0xE3, 0x74), (0xF7, 0xA6, 0x66), (0xC4, 0x78, 0x62)]

def edit_file(name, attrs, contents, editor_cmd):
    attrs_new={}
    try:
        with tempfile.NamedTemporaryFile(
                mode='w', suffix=".yarn.txt", prefix=name+"_", delete=False) as file_obj:
            file_obj.write("title: "+name+"\n")
            for key in attrs:
                value=attrs[key]
                if key in ("title", "links", "includes", "rect",
                           "body", "position"):
                    pass
                elif key=="tags":
                    file_obj.write("tags: "+", ".join(value)+"\n")
                elif key=="colorID":
                    file_obj.write("colorID: "+str(value)+"\n")
                elif type(value)==str:
                    file_obj.write(key + ": "+value+"\n")

            file_obj.write("---\n")
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
                name_line=file_obj.readline().strip()
                if not re.match("^title:\s*(\\w+)\s*$", name_line):
                    return "", {}, ""
                name=name_line[6:].strip()
                attrs_new={}
                next_line=file_obj.readline().strip()
                while (next_line
                       and next_line!="---"):
                    if next_line.isspace():
                        next_line=file_obj.readline().strip()
                        continue
                    else:
                        match=re.match("^(\\w+):(.*)$", next_line)
                        key=match[1].strip()
                        value=match[2].strip()
                        if key in ("title", "links", "includes", "rect",
                                   "body", "position"):
                            pass
                        elif key=="tags":
                            if value:
                                tags=[tag.strip() for tag in value.split(",")]
                                attrs_new["tags"]=tags
                            else:
                                attrs_new["tags"]=[]
                        elif key=="colorID":
                            attrs_new["colorID"]=int(value)
                        elif key=="color":
                            try:
                                pygame.color.Color(value)
                                attrs_new["color"]=value
                            except:
                                print("could not parse color", value)
                                pass
                        else:
                            attrs_new[key] = value
                    next_line=file_obj.readline().strip()
                contents=file_obj.read()
        else:
            print("error return code")
    finally:
        os.unlink(file_name)
    return name, attrs_new, contents

def find_links(text):
    result=[]
    link_rgx = r"\[\[(?:(?:(?!\]\]).)+?\|)?(?P<link>\w+)\]\]"
    for link in re.finditer(link_rgx, text):
        if not link in result:
            result.append(link["link"])
    return result

def find_includes(text):
    result=[]
    link_rgx = r"<<(include|goto) (\w+)>>"
    for link in re.finditer(link_rgx, text):
        if not link in result:
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
        try:
            from tkinter import filedialog
            file_name=filedialog.askopenfilename()
        except:
            print("usage: python3 editor.py filename.json [texteditor [params]]")
            print("eg: python3 editor.py filename.json gedit")

    editor_program=None
    if len(sys.argv) > 2:
        editor_program=sys.argv[2:]

    if os.path.exists(file_name):
        with open(file_name) as thefile:
            json_content=json.load(thefile)
            for arect in thefile:
                if type(arect["tags"])==str:
                   arect["tags"]=arect["tags"].split()
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
    screen=pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption("yarnpy editor: "+file_name)
    font1=pygame.font.SysFont("Arial", 16)
    font2=pygame.font.SysFont("ubuntumono", 11)
    font3=pygame.font.SysFont("Arial", 48)

    clock=pygame.time.Clock()
    running=True
    clicked=None
    show_help=True
    doubleclick_time=-1

    named_nodes={}

    zoom=1
    scroll_x=0
    scroll_y=0

    for arect in json_content:
        pos=(arect["position"]["x"],arect["position"]["y"])
        arect["rect"]=pygame.Rect(pos, (200,100))
        arect["links"]=find_links(arect["body"])
        arect["includes"]=find_includes(arect["body"])
        named_nodes[arect["title"]]=arect

    if "Start" in named_nodes:
        scroll_x=named_nodes["Start"]["position"]["x"]-20
        scroll_y=named_nodes["Start"]["position"]["y"]-20

    resizing=False
    resizing_this_frame=False
    last_resize=None

    while running:
        evs=pygame.event.get()
        keys=pygame.key.get_pressed()
        mouse=pygame.mouse.get_pressed()
        mpx,mpy=pygame.mouse.get_pos()
        mx,my=zoom_inverse((mpx,mpy), zoom, (scroll_x, scroll_y))
        assert(len(json_content)==len(named_nodes))

        resizing_this_frame=False

        for e in evs:
            if e.type==pygame.QUIT:
                do_save=True
                try:
                    # import tkinter
                    pygame.display.quit()
                    from tkinter import messagebox
                    do_save=messagebox.askyesno("Yarn Ed",
                      f"Would you like to save \"{file_name}\" before quitting?")
                except:
                    pass
                if do_save:
                    for arect in json_content:
                        del arect["rect"]
                        del arect["links"]
                        del arect["includes"]
                        if type(arect["tags"])==list:
                            arect["tags"]=" ".join(arect["tags"])
                    with open(file_name, "w") as thefile:
                        json.dump(json_content, thefile,
                                  indent=3, sort_keys=True)
                running=False
                return
            elif e.type==pygame.VIDEORESIZE:
                resizing=True
                resizing_this_frame=True
                last_resize=e.w, e.h
            elif e.type==pygame.KEYDOWN and e.key==pygame.K_h:
                show_help = not show_help
            elif e.type==pygame.KEYDOWN and e.key==pygame.K_s:
                try:
                    from tkinter import filedialog
                    res=filedialog.asksaveasfilename()
                    if res:
                        file_name=res
                    pygame.display.set_caption("yarnpy editor: "+file_name)
                except:
                    pass

                content_copy=[r.copy() for r in json_content]
                for arect in content_copy:
                    del arect["rect"]
                    del arect["links"]
                    del arect["includes"]
                with open(file_name, "w") as thefile:
                    json.dump(content_copy, thefile,
                              indent=3, sort_keys=True)
            elif e.type==pygame.KEYDOWN and e.key==pygame.K_SPACE:
                scroll_x=named_nodes["Start"]["position"]["x"]-20
                scroll_y=named_nodes["Start"]["position"]["y"]-20
                zoom=1
            elif e.type==pygame.MOUSEMOTION:
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
            elif e.type==pygame.MOUSEBUTTONUP:
                pass
            elif e.type==pygame.MOUSEBUTTONDOWN:
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
                        title=clicked["title"]
                        # inbound_links=False
                        # if title=="Start":
                        #     inbound_links=True
                        # for node in named_nodes:
                        #     if (node != title and
                        #         title in named_nodes[node]["links"]
                        #                + named_nodes[node]["includes"]):
                        #         inbound_links=True
                        #         break
                        # if not inbound_links and clicked["body"].isspace():
                        #     del named_nodes[title]
                        #     json_content.remove(cicked)
                        #     clicked=None

                        for link in (clicked["links"] + clicked["includes"]):
                            if link in named_nodes:
                                pass
                            else:
                                newrect=dict(tags=[],
                                             title=link,
                                             position=dict(
                                                 x=clicked["position"]["x"]+off,
                                                 y=clicked["position"]["y"]+120),
                                             colorID=0,
                                             links=[],
                                             includes=[],
                                             body="Empty Text")
                                newrect["rect"]=pygame.Rect((newrect["position"]["x"],newrect["position"]["y"]), (200,100))
                                named_nodes[link]=newrect
                                json_content.append(newrect)
                                off+=250
                if e.button==1:
                    if doubleclick_time>0:
                        doubleclick_time=-1
                        if clicked:
                            #doubleclicked
                            title=name=clicked["title"]
                            contents=clicked["body"]

                            keep_keys=['position', 'rect', 'tags', 'colorID', 'title', 'body']
                            del_keys=['position', 'rect', 'title', 'body', "links", "includes"]

                            attrs=clicked.copy()
                            for key in del_keys:
                                del attrs[key]

                            dict_keys=list(clicked.keys())
                            for key in dict_keys:
                                if not key in keep_keys: del clicked[key]

                            del named_nodes[title]
                            screen.blit(font3.render("WAITING FOR EDITOR", 0, (200,0,0)),
                                        (100,100))
                            pygame.display.flip()
                            pygame.event.pump()
                            name, attrs, contents=edit_file(title, attrs, contents, editor_program)
                            pygame.event.pump()

                            if title=="Start":
                                name="Start"
                            if name in named_nodes:
                                name=title

                            if name=="":
                                title=clicked["title"]
                                json_content.remove(clicked)
                                clicked=None
                            else:
                                clicked["title"]=name
                                clicked["body"]=contents
                                named_nodes[name]=clicked
                                print(clicked)
                                print(attrs)

                                for key in attrs:
                                    clicked[key]=attrs[key]

                                clicked["links"]=find_links(contents)
                                clicked["includes"]=find_includes(contents)
                    else:
                        clicked=None
                        for arect in json_content:
                            if arect["rect"].collidepoint(mx,my):
                                clicked=arect
                                doubleclick_time=15
        if resizing and not resizing_this_frame:
            SCREEN_SIZE=last_resize
            screen=pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
            resizing=False
            resizing_this_frame=False
            last_resize=None


        if doubleclick_time>0:
            doubleclick_time-=1
            #if doubleclick_time<=0:
            #    clicked=None

        screen.fill((255,255,255))

        for arect in json_content:
            tx,ty=arect["rect"].topleft
            tx,ty=zoom_pt((tx,ty), zoom, (scroll_x, scroll_y))
            ty_top=ty
            bgcol=colorids[arect["colorID"]]
            if "color" in arect:
                try:
                    bgcol=pygame.color.Color(arect["color"])
                except:
                    pass

            if arect["colorID"]>0:
                pygame.draw.rect(screen, bgcol, (tx, ty, arect["rect"].w/zoom, arect["rect"].h/zoom))
            else:
                pygame.draw.rect(screen, (0,0,200), (tx, ty, arect["rect"].w/zoom, arect["rect"].h/zoom), 1)
            tx+=2

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
            ni=0

            for link in arect["includes"]:
                if link in named_nodes:
                    srcx,srcy=arect["rect"].midbottom
                    trgx,trgy=named_nodes[link]["rect"].midtop
                    if clicked == named_nodes[link] or clicked == arect:
                        line_width=3
                    else:
                        line_width=1

                    if named_nodes[link]["rect"].top < arect["rect"].bottom:
                        srcy = arect["rect"].top
                        trgy=named_nodes[link]["rect"].bottom
                    if named_nodes[link]["rect"].left>arect["rect"].right:
                        srcx = arect["rect"].right
                        trgx=named_nodes[link]["rect"].left
                    if named_nodes[link]["rect"].right<arect["rect"].left:
                        srcx = arect["rect"].left
                        trgx=named_nodes[link]["rect"].right

                    srcx,srcy=zoom_pt((srcx,srcy), zoom, (scroll_x, scroll_y))
                    trgx,trgy=zoom_pt((trgx,trgy), zoom, (scroll_x, scroll_y))

                    pygame.draw.line(screen, (200,0,0), (srcx, srcy),
                                         (trgx, trgy), line_width)
                    pygame.draw.circle(screen, (200,0,0), (trgx, trgy), 3, line_width)


            for link in arect["links"]:
                if link in named_nodes:
                    srcx,srcy=arect["rect"].midbottom
                    trgx,trgy=named_nodes[link]["rect"].midtop
                    if clicked == named_nodes[link] or clicked == arect:
                        line_width=3
                    else:
                        line_width=1


                    if zoom>2 and arect["title"]==link:
                        continue

                    if zoom>2 or (arect["title"]!=link and arect["title"] in named_nodes[link]["links"]):
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


                    if arect["title"]==link:
                        pygame.draw.circle(screen, (0,200,0), (trgx, trgy-10),
                                         10, line_width)

                        srcx,srcy=trgx-10, trgy-7
                    elif srcy < trgy or zoom>2 or arect["title"] in named_nodes[link]["links"]:
                        pygame.draw.line(screen, (0,200,0), (srcx, srcy),
                                         (trgx, trgy), line_width)
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
                                         (srcx, srcy),p1, line_width)
                        pygame.draw.line(screen, (0,200,0),p1, p2, line_width)
                        pygame.draw.line(screen, (0,200,0),p2, p3, line_width)
                        pygame.draw.line(screen, (0,200,0),p3, p4, line_width)
                        pygame.draw.line(screen, (0,200,0), p4, (trgx, trgy), line_width)
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
                    blx, bly = zoom_pt(arect["rect"].bottomleft, zoom, (scroll_x, scroll_y))
                    bly+=12*ni
                    ni+=1
                    screen.blit(font2.render("[["+link+"]]", 0, (200,0,0)),(blx, bly))

        if show_help:
            pygame.draw.rect(screen, (20,20,20), (SCREEN_SIZE[0]-260, 10, 250, 150))
            screen.blit(font1.render("HELP:", 0, (200,200,200)),(SCREEN_SIZE[0]-255, 15))
            screen.blit(font2.render("click & drag to move nodes", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 35))
            screen.blit(font2.render("drag background to move view ", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 45))
            screen.blit(font2.render("double click to edit nodes", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 55))
            screen.blit(font2.render("broken links show up red below nodes", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 65))
            screen.blit(font2.render(" middle click to create these nodes", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 75))
            screen.blit(font2.render("delete all text in editor to delete node", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 85))
            screen.blit(font2.render("'Start' cannot be renamed or deleted", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 95))
            screen.blit(font2.render("SPACE to center on 'Start' node", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 105))
            screen.blit(font2.render("S to save", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 115))
            screen.blit(font2.render("H to toggle this help", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 125))
            screen.blit(font2.render("mouse wheel to zoom", 0, (200,200,200)), (SCREEN_SIZE[0]-255, 135))

        pygame.display.flip()
        clock.tick(30)

if __name__=="__main__":
    editor()
