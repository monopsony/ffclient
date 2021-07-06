from Printer import Printer
from Connector import Connector
from Parser import Parser
from ListCreator import ListCreator
import os

if not os.path.exists("Macros.py"):
    fil = open("Macros.py", "w+")
    fil.close()

import Macros as macros
import Utils as utils
from Utils import RECIPES_FILE, ITEMS_FILE, LISTS_DIR

import datetime, sys, pickle, json, time, glob
import pandas as pd
import numpy as np
import pdb
import threading, queue, clipboard, keyboard

from Connector import THROTTLES


# USER-PARAMETERS
N_QUERY_THREADS = 4


class Client(Parser, ListCreator):
    def __init__(self):

        super().__init__()

        self.load_default_parameters()

        self.printer = Printer()
        self.connector = Connector(self.printer)

        self.connector.connect(self)

        self.load_recipes()
        self.load_items()
        self.load_lists()

        self.loadCurrentListings()

        self.printer.print("done", "Client ready to go!")
        # self.generateEncounters() # toad, readd? With command maybe?

    def load_default_parameters(self):
        from Para import defaults

        self.para = defaults

    def loadCurrentListings(self):
        lst = []
        if not os.path.exists("CurrentListings.txt"):
            fil = open("CurrentListings.txt", "w+")
            fil.close()

        with open("CurrentListings.txt", "r") as f:
            s = f.read()

        lst = [x.strip().title() for x in s.split("\n")]

        self.current_listings = list(filter(lambda item: item.strip() != "", lst))

        self.printer.print(
            "info", f"Found {len(self.current_listings)} items in current listings"
        )

    # def query(self, query, source, **kwargs):
    #     return self.connector.query(query, source, **kwargs)

    killed = False

    def run(self):

        # first one is not quiet
        inp = self.printer.input("Awaiting Input\n")
        self.parseExecute(inp)

        while not self.killed:

            if self.executingMacro:
                self.nextMacroLine()

            else:
                inp = self.printer.input("Awaiting Input\n", quiet=True)
                self.parseExecute(inp)

        self.printer.print("done", "Exited without error")

    #####
    ## RECIPES
    #####

    recipes = None

    def load_recipes(self):
        r = pd.read_csv(RECIPES_FILE)
        self.recipes = r[r["Item{Result}"] > 0]
        self.printer.print("info", f"Loaded a total of {len(self.recipes)} recipes")

    def print_recipes(self):
        self.printer.print("info", "Loaded recipes extract:")
        print(self.recipes)

    def update_recipes(self):

        r = self.query(
            "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/Recipe.csv",
            "GITHUB",
            raw=True,
        )

        lines = r.split("\n")
        lines.pop(2)
        lines.pop(0)

        s = "\n".join(lines)

        with open(RECIPES_FILE, "w", encoding="utf-8") as f:
            f.write(s)

        self.load_recipes()

    def get_recipe(self, id=None, name=None):
        df = self.recipes

        if id is not None:
            recipe = df.loc[df["Item{Result}"] == id]
        elif name is not None:
            item = self.get_item(name=name)
            if item is None:
                self.printer.print("error", f"No item found under name {name}")
                return
            recipe = df.loc[df["Item{Result}"] == int(item["#"])]
        else:
            self.printer.print("warn", f"Get recipe called but no id or name given")

        if len(recipe) == 0:
            return None
        elif len(recipe) == 1:
            return recipe.iloc[0]
        else:
            if self.current_cmd == "recipe":
                self.printer.print(
                    "info",
                    f"More than one recipe found under id/name {id}/{name}, using first found",
                )
                print(recipe)
            return recipe.iloc[0]

    def print_recipe_info(self, *inp):
        item = self.to_item_input(inp)

        if item is None:
            self.printer.print("error", f"No item found under id/name '{inp}'.")
            return

        info = self.get_recipe(id=item["#"])

        if info is None:
            self.printer.print(
                "error", f"No recipe found under id/name '{item['Name']}'."
            )
            return

        self.printer.print("info", f"Recipe found under id/name {item['Name']}:")
        self.printer.printDFItem(info)

    def get_comp(self, id):
        rec = self.get_recipe(id=id)

        if rec is None:
            return []

        lst = []
        for i in range(6):
            ing_id = int(rec["Item{Ingredient}[" + str(i) + "]"])
            if ing_id == 0:
                break

            lst += [ing_id] + self.get_comp(ing_id)

        return lst

    def get_comp_list(self, id_list):
        lst = []
        for id in id_list:
            lst += self.get_comp(id)

        lst = list(set(lst))
        return lst

    #####
    ## ITEMS
    #####

    def to_item_input(self, inp):
        inp = " ".join(inp)
        if inp.isnumeric():
            info = self.get_item(id=int(inp))
        else:
            info = self.get_item(name=inp)

        return info

    def load_items(self):
        r = pd.read_csv(ITEMS_FILE)

        # change all Names to titlecase for consistency
        r["Name"] = r["Name"].astype(str).str.title()

        self.items = r
        self.printer.print("info", f"Loaded a total of {len(self.items)} items")

    def print_items(self):
        self.printer.print("info", "Loaded items extract:")
        print(self.items)

    def update_items(self):

        r = self.query(
            "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/Item.csv",
            "GITHUB",
            raw=True,
        )

        lines = r.split("\n")
        lines.pop(2)
        lines.pop(0)

        s = "\n".join(lines)

        with open(ITEMS_FILE, "w", encoding="utf-8") as f:
            f.write(s)

        self.load_items()

    def get_item(self, id=None, name=None):
        df = self.items

        if id is not None:
            item = df.loc[df["#"] == id]
        elif name is not None:
            item = df.loc[df["Name"] == name.title()]
        else:
            self.printer.print("warn", f"Get item called but no id or name given")

        if len(item) == 0:
            return None
        elif len(item) == 1:
            return item.iloc[0]
        else:
            self.printer.print(
                "want",
                f"More than one item found under id/name {id}/{name}, using first found",
            )
            print(item)
            return item

    def print_item_info(self, *inp):
        info = self.to_item_input(inp)

        if info is None:
            self.printer.print("error", f"No item found under id/name '{inp}'.")
            return

        self.printer.print("info", f"{len(info)} item(s) found under id/name {inp}:")
        self.printer.printDFItem(info)

    #####
    ## Market board
    #####
    def print_mb_listing(self, *inp, out=False):
        info = self.to_item_input(inp)
        if info is None:
            self.printer.print("error", f"No item found under id/name '{inp}'.")
            return

        self.printer.print(
            "info",
            f'Looking up market board listings for item {info["Name"]}(id: {info["#"]})',
        )

        d = self.get_mb_listing(info["#"])

        with open("listing.json", "w") as f:
            json.dump(d, f)

        self.printer.print(
            "info", f'Market board listings for {info["Name"]} saved in "listing.json"'
        )

    mb_listings = {}

    def get_mb_listing(self, item):
        d = self.uv_query(self.para["world"], item)
        self.mb_listings[item] = d
        return d

    def print_mb_history(self, *inp):
        info = self.to_item_input(inp)
        if info is None:
            self.printer.print("error", f"No item found under id/name '{inp}'.")
            return
        self.printer.print(
            "info",
            f'Looking up market board history for item {info["Name"]}(id: {info["#"]})',
        )

        d = self.get_mb_history(info["#"])
        # self.printer.pprint(d)

        with open("history.json", "w") as f:
            json.dump(d, f)

        self.printer.print(
            "info", f'Market board history for {info["Name"]} saved in "history.json"'
        )

    def get_mb_history(self, item):
        d = self.uv_query("history", self.para["world"], item)
        return d

    def print_mb_info(self, *inp):
        info = self.to_item_input(inp)
        if info is None:
            self.printer.print("error", f"No item found under id/name '{inp}'.")
            return
        self.printer.print(
            "info",
            f'Looking up market board infos for item {info["Name"]}(id: {info["#"]})',
        )

        d = self.get_mb_info(item=info["#"])
        self.printer.printDFItem(d)

    mb_info = {}

    def get_mb_info(self, item=None, listing=None):
        if item in self.mb_info:
            return self.mb_info[item]

        if listing is None:
            d = self.get_mb_listing(item)
        else:
            d = listing

        if d is None:
            self.mb_info[item] = None
            return None

        # calculate sales per day
        times = [(time.time() - x["timestamp"]) / 86400 for x in d["recentHistory"]]
        if np.max(times) > 7:
            h_tot = np.max(times)
            sales_tot = np.sum([x["quantity"] for x in d["recentHistory"]])
            sph = sales_tot / h_tot

            sales_tot_hq = np.sum(
                [x["quantity"] for x in d["recentHistory"] if x["hq"] == True]
            )
            sph_hq = sales_tot_hq / h_tot

        else:
            sph = d["regularSaleVelocity"]
            sph_hq = d["hqSaleVelocity"]

        i = {
            "itemID": d["itemID"],
            "averagePrice": d["averagePrice"],
            "averagePriceNQ": d["averagePriceNQ"],
            "averagePriceHQ": d["averagePriceHQ"],
            "minPrice": d["minPrice"],
            "minPriceNQ": d["minPriceNQ"],
            "minPriceHQ": d["minPriceHQ"],
            "salesPerDay": sph,
            "salesPerDayHQ": sph_hq,
            "salesPerDayNQ": (sph - sph_hq),
        }

        for k in i.keys():
            if i[k] is None:
                i[k] = 99999999

        self.mb_info[item] = i

        return i

    #####
    ## LISTS
    #####
    lists = {}

    def load_lists(self):
        if not os.path.exists(LISTS_DIR):
            os.mkdir(LISTS_DIR)

        for s in glob.glob(os.path.join(LISTS_DIR, "*.json")):
            self.load_list(s)

        self.printer.print(
            "info",
            f"Loaded a total of {len(self.lists.keys())} lists from {LISTS_DIR} directory",
        )

    def load_list(self, name):
        with open(name, "r") as f:
            d = json.load(f)

        name = os.path.basename(name).replace(".json", "")
        self.lists[name] = d

    def list_update(self, s_list):
        if s_list == "CraftQuests":
            d = self.connector.get_craft_quests()
            path = os.path.join(LISTS_DIR, "CraftQuests.json")
            with open(path, "w+") as f:
                json.dump(d, f)

            self.printer.print("info", f"Updated list {path}")

        else:
            self.printer.print("error", f"No default list found under name {s_list}")
            return

    active_list = None

    def set_active_list(self, s):
        if type(s) == str:
            if not (s in self.lists):
                self.printer.print("error", f"No list found under the name {s}")
                return

            self.active_list = s

            self.printer.print(
                "info",
                f"Active list set to {s}, total of {len(self.lists[self.active_list])} items",
            )

        elif hasattr(s, "__len__"):
            lst = []
            ids = []
            for key in s:
                if not (key in self.lists):
                    self.printer.print(
                        "error", f"No list found under the name {s}, ignored"
                    )
                else:
                    lst += self.lists[key]
                    ids.append(key)

            id = "+".join(ids)
            self.lists[id] = lst
            self.set_active_list(id)

        else:
            self.printer.print(
                "error", f"Invalid argument to set_active_list: {s}, {type(s)}"
            )

    #####
    ## SELL
    #####
    prices = {}

    def get_craft_price(self, item_id):
        item_name = self.get_item(item_id)

        if item_id in self.prices:
            return self.prices[item_id]

        mb_info = self.get_mb_info(item_id)

        if mb_info is None:
            d = {
                "price": 0,
                "craftPrice": 0,
                "buyPrice": 0,
            }
            self.prices[item_id] = d
            return d

        recipe = self.get_recipe(id=item_id)

        if recipe is None:
            d = {
                "price": mb_info["minPrice"],
                "craftPrice": 0,
                "buyPrice": mb_info["minPrice"],
            }
            self.prices[item_id] = d
            return d

        price = 0
        N = 10 if self.para["crystalsCraftPrice"] else 6
        for i in range(N):
            ing = int(recipe["Item{Ingredient}[" + f"{i}]"])
            if ing == 0:
                continue

            n = int(recipe["Amount{Ingredient}[" + f"{i}]"])
            if n == 0:
                continue

            price += self.get_craft_price(ing)["price"] * n
        price /= recipe["Amount{Result}"]

        d = {
            "price": min(price, mb_info["minPrice"]),
            "craftPrice": price,
            "buyPrice": mb_info["minPrice"],
        }
        self.prices[item_id] = d
        return d

    sales = None

    def _sell_current_list_helper(self, q):
        while not q.empty():
            el = q.get()
            item = self.get_item(name=el["name"])
            sale = self.sell_item(item, hq=el.get("hq", False), ignore_bl=False)
            if sale is None:
                q.task_done()
                continue

            sale["quantity"] = el.get("quantity", 0)
            self.sales_list.append(sale)
            self.printer.loadingCount(
                self.sales_list_message, len(self.sales_list), self.sales_list_N
            )
            q.task_done()

    def sell_current_list(self):
        self.sales_list = []
        sales_list = self.sales_list

        if self.active_list is None:
            self.printer.print("error", "No active current list set")
            return

        alist = self.active_list
        N = len(self.lists[alist])

        # get number of components
        id_list = []
        for el in self.lists[alist]:
            item = self.get_item(name=el["name"])
            id_list.append(item["#"])
        comps = self.get_comp_list(id_list)
        n_calls = len(comps) + N

        # ask user for confirmation
        app_time = n_calls * THROTTLES["UNIVERSALIS"]
        if not self.wait_confirm(
            f"Are you sure you want to sell {N} items from list: {alist}? Max market board calls: {n_calls}. Approximate time: {app_time//60:.0f}min {app_time%60:.0f}s."
        ):
            return

        t0 = time.time()
        i = 0
        self.sales_list_message = "Collecting data and calculating prices"
        self.sales_list_N = N
        active_list = self.lists[alist]

        q = queue.Queue()
        for el in active_list:
            q.put(el)

        threads = []
        for i in range(N_QUERY_THREADS):
            t = threading.Thread(
                target=self._sell_current_list_helper, daemon=True, args=(q,)
            )
            t.start()
            threads.append(t)

        while True:
            time.sleep(0.5)
            alive = False
            for t in threads:
                alive = alive or t.is_alive()

            if not alive:
                break

        # "useless blocking call"
        # https://stackoverflow.com/questions/1635080/terminate-a-multi-thread-python-program
        # for t in threads:
        #     t.join()

        # for el in active_list:
        # self.printer.loadingCount(s, i, N)
        # item = self.get_item(name=el["name"])
        # sale = self.sell_item(item, hq=el.get("hq", False), ignore_bl=False)
        # if sale is None:
        #     continue
        # sale["quantity"] = el.get("quantity", 0)
        # sales_list.append(sale)
        # i += 1

        self.printer.loadingCount(
            self.sales_list_message, len(sales_list), N, done=True
        )
        t = time.time() - t0
        self.printer.print(
            "info",
            f"Took {t//60:.0f}min {t%60:.0f}s, for a total of {len(self.mb_info)} market board queries.",
        )

        sales_list = pd.DataFrame(sales_list)

        self.sales = sales_list

    def print_sell_item(self, *inp, hq=False):
        item = self.to_item_input(inp)
        if item is None:
            self.printer.print("error", f"No item found under id/name '{inp}'.")
            return None

        d = self.sell_item(item, hq=hq)

        self.printer.print("info", f"Looking to sell {item['Name']}")
        tag = "HQ" if hq else "NQ"
        l = [
            "itemID",
            "averagePrice" + tag,
            "minPrice" + tag,
            "salesPerDay" + tag,
            "craftPrice",
            "maxProfitPerDay",
            "expProfitPerDay",
        ]
        self.printer.printDFItem({k: d[k] for k in l})

        self.printer.print("info", f"Expected  profit: {d['expProfit']}")
        self.printer.print("info", f"Potential profit: {d['maxProfit']}")

    def sell_item(self, item, hq=False, ignore_bl=True):
        item_id = item["#"]
        mb_info = self.get_mb_info(item=item_id)

        if mb_info is None:
            self.printer.print(
                "error", f"No mb info found for {item['Name']}, skipping"
            )
            return

        mb_list = self.mb_listings[item_id]
        if (not ignore_bl) and (self.check_listing_retainer_bl(mb_list) is not None):
            retainer = self.check_listing_retainer_bl(mb_list)
            self.printer.print(
                "info",
                f'Ignored {item["Name"]} due to retainer {retainer} being in blacklist',
            )
            return None

        if (
            (not ignore_bl)
            and (self.para["blCurrentListings"])
            and (item["Name"] in self.current_listings)
        ):
            self.printer.print(
                "info",
                f'Ignored {item["Name"]} due to item being in current listings',
            )
            return None

        craft_price = self.get_craft_price(item_id)

        d = mb_info.copy()
        d["craftPrice"] = craft_price["craftPrice"]
        d["hq"] = hq

        tag = "HQ" if hq else "NQ"
        d["expProfit"] = (
            min(d["minPrice" + tag], d["averagePrice" + tag]) * 0.95 - d["craftPrice"]
        )
        d["maxProfit"] = (
            max(d["minPrice" + tag], d["averagePrice" + tag]) * 0.95 - d["craftPrice"]
        )
        d["expProfitPerDay"] = d["expProfit"] * d["salesPerDay" + tag]
        d["maxProfitPerDay"] = d["maxProfit"] * d["salesPerDay" + tag]

        return d

    def sales_list_sort(self, s):

        if self.sales is None:
            self.printer.print(
                "error",
                "No sales generated yet. Use `sell list` to generate a sales list.",
            )
            return

        sales = self.sales
        cols = list(sales.columns)
        if not (s in cols):
            self.printer.print(
                "error",
                f"Unable to sort by {s}: not a column title. Column titles are:\n{cols}",
            )
            return

        self.sales.sort_values(s, ascending=False, inplace=True, ignore_index=True)

    def sales_list_show(self, N):
        if self.sales is None:
            self.printer.print(
                "error",
                "No sales generated yet. Use `sell list` to generate a sales list.",
            )
            return

        if not N.isnumeric():
            self.printer.print("error", "Argument {N} is not a number")
            return
        N = int(N)

        sales = self.sales[:N]

        self.printer.print("info", f"Show top {N} sales out of {len(sales)}")

        header = f"{'':<4}{'Name':<30}{'hq':<6}{'N':<6}{'avg price':<12}{'curr price':<12}{'spd':<6}{'expProfit':<12}{'maxProfit':<12}{'expPPD':<12}{'maxPPD':<12}"
        print(header)

        for index, row in sales.iterrows():
            item = self.get_item(id=row["itemID"])
            tag = "HQ" if row["hq"] else "NQ"
            s = f"{index:<4}{item['Name'][:28]:<28}  {row['hq']:<6}{row['quantity']:<4}  {row['averagePrice'+tag]:<10.0f}  {row['minPrice'+tag]:<10.0f}  {row['salesPerDay'+tag]:<4.1f}  "
            s += f"{row['expProfit']:<10.0f}  {row['maxProfit']:<10.0f}  {row['expProfitPerDay']:<10.0f}  {row['maxProfitPerDay']:<10.0f}  "
            print(s)

        print(
            f"Total // expProfit: {sales['expProfit'].to_numpy().sum():.0f}   expProfitPerDay: {sales['expProfitPerDay'].to_numpy().sum():.0f}"
        )

    def sales_list_print_columns(self):
        if self.sales is None:
            self.printer.print(
                "error",
                "No sales generated yet. Use `sell list` to generate a sales list.",
            )
            return

        self.printer.print("info", "Printing sales columns")
        self.printer.pprint(list(self.sales.columns))

    def sales_list_copy(self, N):

        if self.sales is None:
            self.printer.print(
                "error",
                "No sales generated yet. Use `sell list` to generate a sales list.",
            )
            return

        if not N.isnumeric():
            self.printer.print("error", "Argument {N} is not a number")
            return
        N = int(N)

        if N < 0 or N >= len(self.sales):
            self.printer.print(
                "error",
                f"Index {N} too low/large for sales list with {len(self.sales)} elements",
            )
            return

        sale = self.sales.iloc[N]

        item = self.get_item(id=sale["itemID"])
        name = item["Name"]

        utils.copy(name)
        self.printer.print("info", f"Copied `{name}` to clipboard")

    def sales_list_craft(self, N):

        if self.sales is None:
            self.printer.print(
                "error",
                "No sales generated yet. Use `sell list` to generate a sales list.",
            )
            return

        if not N.isnumeric():
            self.printer.print("error", "Argument {N} is not a number")
            return
        N = int(N)

        sales = self.sales[:N]
        self.printer.print("info", f"Preparing top {N} sales out of {len(sales)}")

        url = "https://ffxivcrafting.com/list/saved/"
        crafts = []
        for index, row in sales.iterrows():
            tag = "HQ" if row["hq"] else "NQ"
            n_crafts = max(
                row["salesPerDay" + tag] // max(row["quantity"], 1),
                max(row["quantity"], 1),
            )
            recipe = self.get_recipe(row["itemID"])
            n_crafts = n_crafts // int(recipe["Amount{Result}"])
            crafts.append(f"{row['itemID']},{n_crafts:.0f}")

        url = url + ":".join(crafts)

        self.printer.print("info", f"Opening `{url}` in browser")
        utils.open_browser_tab(url)

        # look at which items to buy vs craft
        lenience = self.para["buyCraftLenience"]
        buys = []
        sales_id = list(sales["itemID"])
        comp_ids = self.get_comp_list(sales_id)
        for id in comp_ids:

            if not (id in self.prices):
                continue

            reagent = self.prices[id]
            item = self.get_item(id=id)
            name = item["Name"]
            if (
                (reagent["craftPrice"] > 0)
                and (reagent["buyPrice"] < reagent["craftPrice"] + lenience)
                and (
                    id not in sales_id
                )  # gotta ignore the items we're trying to sell ofc
            ):
                buys.append({**reagent, "name": name})

        self.printer.print(
            "info",
            f"Found {len(buys)} components to buy instead of craft. Confirm to copy next item name to clipboard, (n) to stop looping",
        )
        for buy in buys:
            s = f'Copy {buy["name"]} to clipboard?'
            if self.wait_confirm(s):
                utils.copy(buy["name"])
                print(
                    f'{buy["name"]} // craft: {buy["craftPrice"]:.0f}    buy: {buy["buyPrice"]:.0f}'
                )
            else:
                break

    def sales_list_drop(self, idxs):
        idxs = [int(x) for x in idxs if x.isnumeric()]
        self.printer.print("info", f"Dropping sale indices {idxs}.")
        self.sales.drop(idxs, inplace=True)

    def sales_list_filter(self, query=None):

        if self.sales is None:
            self.printer.print(
                "error",
                "No sales generated yet. Use `sell list` to generate a sales list.",
            )
            return

        if query is None:
            s = self.printer.input(f"Set filters:\n")
        else:
            s = query

        N = len(self.sales)
        try:
            filtered = self.sales.query(s)
            self.sales = filtered
            self.printer.print(
                "info",
                f"Filters applied, sales list contains {len(self.sales)} items down from {N}",
            )
        except Exception as e:
            self.printer.print("error", e)
            self.printer.print("info", "No filters applied")
            return

    #####
    ## MACROS
    #####

    currentMacro = None
    executingMacro = False

    def nextMacroLine(self):

        if (self.currentMacro is None) or len(self.currentMacro) == 0:
            self.executingMacro = False
            return

        s = self.currentMacro.pop(0)
        self.printer.print("macro", f"Executing line '{s}'")
        self.parseExecute(s)

    def startMacro(self, macroName):

        macroString = getattr(macros, macroName, None)
        if macroString is None:
            self.printer.print("error", f"No macro found under the name {macroString}.")
            return

        self.executingMacro = True
        self.currentMacro = macroString.splitlines()

    #####
    ## UTILS
    #####

    def test_run(self):
        r = self.query("http://xivapi.com/Item/1675", "XIVAPI")

        self.printer.pprint(r)

        self.printer.print("done", "Test run complete")

    def wait_confirm(self, s):
        inp = self.printer.input(s=s + " (y/n)")
        if inp == "y":
            return True
        elif inp == "n":
            return False
        else:
            return self.wait_confirm(s)

    def start_inter_shell(self):
        self.printer.print(
            "info", "Starting interactive shell. Type `continue` to escape."
        )
        pdb.set_trace()

    def check_listing_retainer_bl(self, mb_list):
        bl = self.para["retainerBL"]
        for listing in mb_list["listings"]:
            if listing["retainerName"] in bl:
                return listing["retainerName"]

        return None

    def get_thread_ranges(self, N):

        if N < N_QUERY_THREADS:
            return [(i, i + 1) for i in range(N)]
        else:
            nPerThread = N // N_QUERY_THREADS
            nPers = np.array([nPerThread] * N_QUERY_THREADS)
            nPers[: N % N_QUERY_THREADS] += 1
            nPers = [0] + np.cumsum(nPers).tolist()
            return [(nPers[i - 1], nPers[i]) for i in range(len(nPers))]

    def detect_clipboard_listings(self, replace=False):
        self.printer.print(
            "info",
            "Checking clipboard for listings. Press `n` at any time to stop scanning.",
        )
        recent_value = ""
        clipboard.copy("")
        lst = []
        while True:
            value = clipboard.paste()
            if value != recent_value:
                recent_value = value
                print(recent_value)
                lst.append(recent_value)

            if keyboard.read_key() == "n":
                break

            time.sleep(0.05)

        typ = "w" if replace else "a"
        with open("CurrentListings.txt", typ) as fil:
            fil.write("\n" + "\n".join(lst))

        if replace:
            self.printer.print(
                "info", f"Wrote {len(lst)} items into CurrentListings.txt"
            )
        else:
            self.printer.print("info", f"Added {len(lst)} items to CurrentListings.txt")

        self.loadCurrentListings()


if __name__ == "__main__":

    c = Client()
    c.run()
    # c.generateBossList()
