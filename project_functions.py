from datetime import datetime 
from typing import Callable
from beautifultable import BeautifulTable
def createTable(lst) -> BeautifulTable:
    '''
    Create a Beautifultable that displays lst in the format from project description.
    '''
    table = BeautifulTable()
    table.maxwidth = 120
    table.columns.header = ["Title", "Creation Date", "Score", "Answer Count"]
    for item in lst:
        table.rows.append([item.get("Title"), '{:10}'.format(item.get("Creation Date")), item.get("Score"), '{:<10}'.format(item.get("Answer Count"))])
    return table


def is_ascii(s:str):
    return len(s) == len(s.encode())

def format_check(s: str, l: int = 1, func: Callable = is_ascii, ignoreSpace: bool = True) -> bool:
    '''
    Check if the input string follows the given formats. Return True if the string passes.
    s: String to check.
    l: Length of the string. Default value 1.
    func: format checker function. Default checks if the string is ascii.
    ignoreSpace: If true, ignore spaces in the string.
    '''

    if len(s) < l:
        print('Input must be longer than ', str(l), 'characters! ')
        return False

    if ignoreSpace: 
        s = s.replace(' ', '')
        
    if not func(s):
        print('Input must follow ', func.__name__[2:], ' format.')
        return False
    return True

def getToday() -> str:
    '''
    Get today's date in the format of YYYY-MM-DD.
    '''
    return datetime.today().strftime("%Y-%m-%d")

def invalid_command(func: Callable=None):
    '''
    Tell user that the input is invalid, then call the given function.
    '''
    print('Please enter a valid command. ')
    if func: func()
    
def exit_program():
    '''
    Exit the program.
    '''

    print('Bye! :)')
    exit(0)