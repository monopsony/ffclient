import Utils as utils
from Utils import RECIPES_FILE, ITEMS_FILE, LISTS_DIR
import json, os


class ListCreator:
    def __init__(self, printer):
        pass

    recipe_filter = ""

    def create_custom(self, ignore_untradeable=False):

        # recipe filter
        s = self.printer.input(f"Recipe filters:\n")
        self.set_recipe_filter(s, apply=True)

        # item filter
        s = self.printer.input(f"Item filters:\n")
        self.set_item_filter(s, apply=True)

        self.combine_recipe_item_filters()

        if self.para["removeUntradeableReagents"]:
            self.custom_remove_untradeable_reagents()

        save = self.wait_confirm(
            f"Fully filtered recipe list contains {len(self.filtered_list)} items. Do you want to save it?"
        )
        if save:
            name = self.printer.input("Name your list")

            self.save_filtered_list(name)

    def set_recipe_filter(self, s, apply=False):

        self.recipe_filter = s
        if apply:
            self.filter_recipes()

    filtered_recipes = None

    def filter_recipes(self):
        rec = self.recipes.rename(
            columns={"#": "RecipeId"}
        )  # hashtag is a special character for queries and theres no escape
        rec = utils.cols_remove_special_chars(rec)
        try:
            self.filtered_recipes = rec.query(self.recipe_filter)
        except Exception as e:
            self.printer.print("error", e)
            self.printer.print("info", "No filters applied")
            self.filtered_recipes = rec

    item_filter = ""

    def set_item_filter(self, s, apply=False):

        self.item_filter = s
        if apply:
            self.filter_items()

    filtered_items = None

    def filter_items(self):
        items = self.items.rename(
            columns={"#": "ItemId"}
        )  # hashtag is a special character for queries and theres no escape
        items = utils.cols_remove_special_chars(items)
        try:
            self.filtered_items = items.query(self.item_filter)
        except Exception as e:
            self.printer.print("error", e)
            self.printer.print("info", "No filters applied")
            self.filtered_items = items

    filtered_list = None

    def combine_recipe_item_filters(self):
        item_ids = list(self.filtered_items["ItemId"])

        self.filtered_list = self.filtered_recipes[
            self.filtered_recipes["ItemResult"].isin(item_ids)
        ]

    def custom_remove_untradeable_reagents(self):
        item_ids = list(self.filtered_list["ItemResult"])
        N = len(item_ids)
        to_remove = []

        s = "Removing items with untradeable base components"
        for i in range(len(item_ids)):

            self.printer.loadingCount(s, i, N)

            id = item_ids[i]
            comp = self.get_comp(id)
            untradeable = False
            for comp_id in comp:
                item = self.get_item(id=comp_id)
                main_item = self.get_item(id=id)
                if item["IsUntradable"] and (self.get_recipe(id=comp_id) is None):
                    self.printer.print(
                        "info",
                        f"Removing `{main_item['Name']}` because {item['Name']} is untradeable",
                    )
                    to_remove.append(id)
                    break
        self.printer.loadingCount(s, N, N, done=True)

        self.filtered_list = self.filtered_list[
            ~self.filtered_list["ItemResult"].isin(to_remove)
        ]
        self.printer.print(
            "info",
            f"Removed a total of {N - len(self.filtered_list)} because of untradability",
        )

    def save_filtered_list(self, name):
        lst = []
        for index, row in self.filtered_list.iterrows():
            item = self.get_item(id=row["ItemResult"])
            lst.append({"quantity": 1, "hq": False, "name": item["Name"]})

        path = os.path.join(LISTS_DIR, f"{name}.json")
        with open(path, "w+") as f:
            json.dump(lst, f)

        self.printer.print("info", f"Saved list in {path}")
        self.load_list(path)
