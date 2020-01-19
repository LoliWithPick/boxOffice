from colorama import init, Fore
init(autoreset=True)

color_dict = {
    'green': Fore.LIGHTGREEN_EX,
    'red': Fore.LIGHTRED_EX,
    'cyan': Fore.LIGHTCYAN_EX,
    'blue': Fore.LIGHTBLUE_EX,
    'yellow': Fore.LIGHTYELLOW_EX,
    'magenta': Fore.LIGHTMAGENTA_EX
}

def cprint(info, color='red'):
    print(color_dict[color] + str(info))
