from colorama import init, Fore
init(autoreset=True)

color_dict = {
    'green': Fore.GREEN,
    'red': Fore.RED,
    'cyan': Fore.CYAN,
    'blue': Fore.BLUE,
    'yellow': Fore.YELLOW
}

def cprint(info, color='red'):
    print(color_dict[color] + str(info))
