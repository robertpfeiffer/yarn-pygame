import yarn


def run_in_console(controller):
    while not controller.finished:
        print(controller.message())
        print("")
        for i, choice in enumerate(controller.choices()):
            i+=1
            print(f"{i:<3}- {choice}")
        print("q  - Quit")
        try:
            choice = input("> ").strip()
        except EOFError:
            choice="q"
        if choice=="q":
            print("exiting...")
            return
        try:
            choice_text=controller.choices()[int(choice)-1]
        except:
            print("could not parse input")
            continue
        controller.transition(choice_text)
        print("\n")
    print(controller.message())
    print("The End")
            
if __name__=="__main__":
    import sys
    path=sys.argv[1]
    controller=yarn.YarnController(path, "console", False)
    run_in_console(controller)
