from Printer import Printer

command_help = {
    "recipe": {
        "short": "Show/update information of recipes",
        "args": {
            "update": [0, "Updates the Recipe.csv file to be up-to-date"],
            "info": [1, "Prints recipe information of item name/item id `arg1`"],
        },
    },
    "item": {
        "short": "Show/update information of recipes",
        "args": {
            "update": [0, "Updates the Item.csv file to be up-to-date"],
            "info": [1, "Prints item information of item name/item id `arg1`"],
        },
    },
    "mb": {
        "short": "Show/update information of the board listings",
        "args": {
            "hist": [
                1,
                "Puts mb history of item name/item id `arg1` into history.json",
            ],
            "list": [
                1,
                "Puts mb listings of item name/item id `arg1` into listing.json",
            ],
            "info": [1, "Prints general information of item name/item id `arg1`"],
        },
    },
    "macro": {
        "short": "Starts macro with name `arg1` (as found in Macros.py)",
        "args": 1,
    },
    "list": {
        "short": "Set/update/create craft lists",
        "args": {
            "update": [
                1,
                "Updates pre-made list of name `arg1`. Currently supports: CraftQuests",
            ],
            "custom": [
                0,
                "Create a new list with custom filters. Syntax equivalent to pandas .query method. Column names can be found in Item.csv or Recipe.csv, with '#' replaced by 'ItemId' and 'RecipeId' respectively, as well as all special characters removed.",
            ],
            "set": [
                1,
                "Sets currently active list to `arg1` (same name as seen in the Lists/ folder, minus .json). If multiple lists are given, active list will be a merge",
            ],
        },
    },
    "sell": {
        "short": "Shows basic mb info and crafting costs of item `arg1`. Optionally, 'hq' can be put before `arg1`. If `arg1` is 'list', this will apply to the entire currently selected list. Information can then be accessed using the 'sales' command.",
        "args": 1,
    },
    "sales": {
        "short": "Show/filter/craft sales, as created by 'sell list'",
        "args": {
            "sort": [
                1,
                "Sort sales by column `arg1`. Column names can be found using the 'sales cols' command",
            ],
            "show": [1, "Prints table of sales up to `arg1` items"],
            "copy": [1, "Copy item name of the `arg1`th column to the clipboard"],
            "cols": [0, "Show column names of the sales list"],
            "filter": [
                0,
                "Filters current sales list entries. Syntax equivalent to pandas .query method.",
            ],
            "craft": [
                1,
                "Craft the `arg1` first items of the current sales list. Opens a ffxivcrafting.com tab in your default browser.",
            ],
            "drop": [-1, "Remove all entries given (by index) from the sales list"],
        },
    },
    "clist": {
        "short": "Starts scanning clipboard for item names. Automatically puts every item into 'CurrentListings.txt'. All these items will then be ignored when generating sales lists. Press 'n' to stop scanning",
        "args": 0,
    },
    "debug": {
        "short": "Starts the debug shell. Enter 'continue' to resume client",
        "args": 0,
    },
}


class Parser:
    def __init__(self, printer=Printer()):

        self.printer = printer

    def argumentCheck(self, cmds, N):
        if len(cmds) < N + 1:
            self.printer.print(
                "error", f"Command {' '.join(cmds[:N])} requires {N} argument(s)"
            )
            return False

        return True

    def bad_subcmd(self, cmds):
        self.printer.print("error", f"Unrecognised subcommand {cmds[1]}")

    def parseExecute(self, s=""):

        s = s.strip()
        if len(s) == 0:
            return

        cmds = list(s.split(" "))

        if len(cmds) < 1:
            return

        main = cmds[0]

        self.current_cmd = main

        if (len(cmds) > 1) and (cmds[0] in command_help) and (cmds[1] == "help"):
            self.helpCommand(cmds[0])
            return

        if (main == "exit") or (main == "quit"):
            self.killed = True
            return

        elif main.startswith("#"):
            return

        elif main == "test":

            self.test_run()

        elif main == "recipe":

            if not self.argumentCheck(cmds, 1):
                return

            if cmds[1] == "update":
                self.update_recipes()

            elif cmds[1] == "print":
                self.print_recipes()

            elif cmds[1] == "info":
                if not self.argumentCheck(cmds, 2):
                    return
                self.print_recipe_info(*cmds[2:])

            else:
                self.bad_subcmd(cmds)

        elif main == "item":
            if not self.argumentCheck(cmds, 1):
                return

            if cmds[1] == "update":
                self.update_items()

            elif cmds[1] == "print":
                self.print_items()

            elif cmds[1] == "info":
                if not self.argumentCheck(cmds, 2):
                    return
                self.print_item_info(*cmds[2:])

            else:
                self.bad_subcmd(cmds)

        elif main == "mb":
            if not self.argumentCheck(cmds, 1):
                return

            elif cmds[1] == "hist":
                if not self.argumentCheck(cmds, 2):
                    return

                self.print_mb_history(*cmds[2:])

            elif cmds[1] == "list":
                if not self.argumentCheck(cmds, 2):
                    return

                self.print_mb_listing(*cmds[2:])

            elif cmds[1] == "info":
                if not self.argumentCheck(cmds, 2):
                    return

                self.print_mb_info(*cmds[2:])

            else:
                self.bad_subcmd(cmds)

        elif main == "macro":

            if not self.argumentCheck(cmds, 1):
                return

            self.startMacro(cmds[1])

        elif main == "list":

            if not self.argumentCheck(cmds, 1):
                return

            if cmds[1] == "update":
                if not self.argumentCheck(cmds, 2):
                    return

                self.list_update(cmds[2])

            elif cmds[1] == "custom":

                self.create_custom()

            elif cmds[1] == "set":
                if not self.argumentCheck(cmds, 2):
                    return

                self.set_active_list(cmds[2:])

            else:
                self.bad_subcmd(cmds)

        elif main == "sell":
            if not self.argumentCheck(cmds, 1):
                return

            if cmds[1] == "hq":
                hq = True
                del cmds[1]
            else:
                hq = False

            if cmds[1] == "list":
                self.sell_current_list()

            else:
                self.print_sell_item(*cmds[1:], hq=hq)

        elif main == "sales":
            if not self.argumentCheck(cmds, 1):
                return

            if cmds[1] == "sort":
                if not self.argumentCheck(cmds, 2):
                    return

                self.sales_list_sort(cmds[2])

            elif cmds[1] == "show":
                if not self.argumentCheck(cmds, 2):
                    return

                self.sales_list_show(cmds[2])

            elif cmds[1] == "copy":
                if not self.argumentCheck(cmds, 2):
                    return

                self.sales_list_copy(cmds[2])

            elif cmds[1] == "cols" or cmds[1] == "columns":
                self.sales_list_print_columns()

            elif cmds[1] == "filter":
                if len(cmds) > 2:
                    self.sales_list_filter(query=" ".join(cmds[2:]))
                else:
                    self.sales_list_filter()

            elif cmds[1] == "craft":
                if not self.argumentCheck(cmds, 2):
                    return

                self.sales_list_craft(cmds[2])

            elif cmds[1] == "drop":
                if not self.argumentCheck(cmds, 2):
                    return

                self.sales_list_drop(cmds[2:])

            else:
                self.bad_subcmd(cmds)

        elif main == "clist":

            boo = False
            if (len(cmds) > 1) and (cmds[1] == "r" or cmds[1] == "replace"):
                boo = True
            self.detect_clipboard_listings(replace=boo)

        elif main == "debug":

            self.start_inter_shell()

        elif main == "help":
            self.helpPrint()

        else:
            self.printer.print(
                "error",
                f"Command '{main}' not recognised. Type 'help' to get a list of all commands.",
            )

    ## HELP FUNCTIONS
    def helpPrint(self):

        self.printer.print("info", "List of commands:")
        cmds = list(command_help.keys())
        cmds.sort()
        print(", ".join(cmds))

        self.printer.printSeparator()
        self.printer.print("info", "Command descriptions:")
        for k, v in command_help.items():
            if type(v["args"]) == int:
                if v["args"] < 0:
                    s = f"{k} `*args`"
                else:
                    lst = [f"`arg{i+1}`" for i in range(v["args"])]
                    s = f'{k} {" ".join(lst)}'

            else:
                s = f"{k} `subcmd`"

            self.printer.print("command", f"{s}")
            print(v["short"])
            self.printer.printSeparator()

    def helpCommand(self, cmd):
        args = command_help[cmd]["args"]

        if type(args) == int:
            if args < 0:
                s = f"{cmd} `*args`"
            else:
                lst = [f"`arg{i+1}`" for i in range(args)]
                s = f'{cmd} {" ".join(lst)}'

            self.printer.print("command", f"{s}")
            print(command_help[cmd]["short"])
            return

        self.printer.print("info", "List of subcommands:")
        subs = list(args.keys())
        subs.sort()
        print(", ".join(subs))

        self.printer.printSeparator()
        self.printer.print("info", "Subcommand descriptions:")

        for k in subs:
            v = args[k]
            arg = v[0]

            if type(arg) == int:
                if arg < 0:
                    s = f"{k} `*args`"
                else:
                    lst = [f"`arg{i+1}`" for i in range(arg)]
                    s = f'{k} {" ".join(lst)}'

            self.printer.print("sub", f"{s}")
            print(v[1])
            self.printer.printSeparator()