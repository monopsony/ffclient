import pandas as pd
import clipboard, webbrowser

RECIPES_FILE = "Recipe.csv"
ITEMS_FILE = "Item.csv"
LISTS_DIR = "Lists"


def get_max_char_length(lst):
    a = 0
    for x in lst:
        a = max(a, len(x))

    return a


def copy(s):

    clipboard.copy(s)


def get_bool_opt_val(s):
    if s.isnumeric():
        if int(s) == 0:
            return False
        elif int(s) == 1:
            return True
        else:
            return None

    else:
        if s.lower() == "true":
            return True
        elif s.lower() == "false":
            return False
        else:
            return None


def open_browser_tab(s):
    b = webbrowser.get()
    b.open_new_tab(s)


def cols_remove_special_chars(df):

    df.columns = df.columns.str.replace("[#,@,&,{,},\[,\], ]", "")
    return df