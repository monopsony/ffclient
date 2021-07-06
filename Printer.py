import sys, json, re
from termcolor import colored, cprint
import Utils as utils
import pprint


class Printer:

    smallSpace = 5
    mediumSpace = 10
    longSpace = 20

    labels = {}
    properties = {
        "errorLabel": ["white", "on_red"],
        "error": ["red"],
        "infoLabel": ["white", "on_blue"],
        "info": [],
        "waitLabel": ["grey", "on_yellow"],
        "wait": [],
        "doneLabel": ["grey", "on_green"],
        "done": [],
        "inputLabel": ["grey", "on_white"],
        "input": [],
        "macroLabel": ["grey", "on_white"],
        "macro": [],
        "title": ["white"],
        "commandLabel": ["grey", "on_white"],
        "command": ["white"],
        "sub": ["white"],
    }

    def __init__(self):

        self.initialize()
        self.pp = pprint.PrettyPrinter(indent=2)

    def initialize(self):

        p = self.properties
        l = self.labels

        l["info"] = colored(f"{' INFO':<{self.mediumSpace}}", *p["infoLabel"])
        l["error"] = colored(f"{' ERROR':<{self.mediumSpace}}", *p["errorLabel"])
        l["wait"] = colored(f"{' WAIT':<{self.mediumSpace}}", *p["waitLabel"])
        l["done"] = colored(f"{' DONE':<{self.mediumSpace}}", *p["doneLabel"])
        l["input"] = colored(f"{' INPUT':<{self.mediumSpace}}", *p["inputLabel"])
        l["macro"] = colored(f"{' MACRO':<{self.mediumSpace}}", *p["macroLabel"])
        l["command"] = colored(f"{' CMD':<{self.smallSpace}}", *p["commandLabel"])
        l["sub"] = colored(f"{' SUB':<{self.smallSpace}}", *p["commandLabel"])

    def parseString(self, s):

        if s is None:
            return ""

        return str(s)

    def print(self, label, s=None, end=None):

        s = colored(self.parseString(s), *self.properties[label])
        print(f"{self.labels[label]} {s}", end=end)

    def input(self, s=None, quiet=False):

        label = "input"
        if quiet:
            r = input(": ")
        else:
            s = colored(self.parseString(s), *self.properties[label])
            r = input(f"{self.labels[label]} {s}: ")

        return r

    def printTitle(self, s=None):

        s = colored(self.parseString(s), *self.properties["title"], attrs=["underline"])
        print(f"{s}\n")

    def testPrint(self):

        self.print("info", "This is an info message")
        self.print("error", "This is an error message")
        self.print("wait", "Task is in progress")
        self.print("done", "Task is done")

    def loadingCount(self, s, step, max, done=False):

        if done:
            self.print("done", f"{step}/{max} -- {s}        ")

        else:
            self.print("wait", f"{step}/{max} -- {s}        ", end="\r")

    def printGraphQL(self, s):

        print(s)

    def printJSON(self, s):

        if type(s) == "string":

            try:
                s = json.load(s)
            except:
                print(s)
                return

        print(json.dumps(s, indent=2))

    def pprint(self, s):
        self.pp.pprint(s)

    def printDFItem(self, info):
        cols = list(info.keys())
        n_char = utils.get_max_char_length(cols) + 5

        for col in cols:
            print(f"{col:<{n_char}}{info[col]}")

    def printSeparator(self):
        print("—" * 50)


if __name__ == "__main__":
    p = Printer()
    p.testPrint()

    # render('snail.jpg')
