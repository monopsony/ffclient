import sys, webbrowser, json, os, time, re, datetime, requests, time, csv, clipboard
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup

# https://stackoverflow.com/questions/48767143/how-to-suppress-warnings-about-lack-of-cert-verification-in-a-requests-https-cal
# API call had no verified certificate so the requests library wasnt happy and threw wwarnings
# whenver I used verify = False, which was needed to get any response at all
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

THROTTLES = {
    "XIVAPI": 1.0 / 7,  # 8 requests per second, down to 7 for safety
    "GITHUB": 1.0 / 10,
    "UNIVERSALIS": 1.0 / 15,  # not disclaimed, just same as XIVAPI for now
}

TICK_RATE = 0.02  # every how many seconds throttle checks
UNIVERSALIS_BASE_URL = "https://universalis.app/api"
CRAFTERS = [
    "Alchemist",
    "Armorer",
    "Blacksmith",
    "Carpenter",
    "Culinarian",
    "Goldsmith",
    "Leatherworker",
    "Weaver",
]


class Connector:
    def __init__(self, printer):

        self.printer = printer

    def connect(self, client):
        client.query = self.query
        client.uv_query = self.universalis_query

    def query_old(self, query):

        if not query.startswith("query"):
            query = "query " + query

        r = requests.get(
            self.apiURL,
            headers=self.header,
            json={"query": query},
        )

        if r.status_code != 200:
            self.printer.print("error", f"Query received status code {r.status_code}")
            if r.status_code == 429:
                sleepTime = int(r.headers["retry-after"])
                print("")  # new line because its often mid-loading, which has an \r end
                self.printer.print(
                    "info",
                    f"Recovering from error code 429: sleeping for {sleepTime} seconds",
                )
                time.sleep(sleepTime + 1)

                return self.query(query)  # repeat same query after timeout
            else:
                try:
                    r = json.loads(r.text)
                    print(r["errors"]["message"])
                except:
                    pass
            return None, None

        else:

            r = json.loads(r.text)

            if "errors" in r:
                self.printer.print("error", f"Errors found in query")
                self.printer.printTitle("Query")
                self.printer.printGraphQL(query)

                self.printer.printTitle("Response")
                self.printer.printJSON(r)

            return r["data"]

    last_query_times = {k: time.time() for k in THROTTLES.keys()}

    def throttle_query(self, source):

        if (source not in self.last_query_times) or (source is None):

            if "xivapi.com" in query:
                source = "XIVAPI"
            else:
                self.printer.print(
                    "error", f"Query source {source} not recognised, throttle skipped."
                )
                return True

        tht, lqt = THROTTLES[source], self.last_query_times[source]
        while time.time() - lqt < tht:
            time.sleep(TICK_RATE)

        self.last_query_times[source] = time.time()

        return True

    def query(self, query, source, raw=False):
        if source is None:
            if "xivapi.com" in query:
                source = "XIVAPI"
            elif "universalis.app" in query:
                source = "UNIVERSALIS"

        self.throttle_query(source)
        r = requests.get(query, verify=False)

        code = r.status_code
        if not (code == 200):
            self.printer.print(
                "error", f"Status code {code} for query {query}. Skipping"
            )
            return None

        if raw:
            d = r.content.decode("utf-8")
        else:
            d = r.json()
        return d

    def query_csv(self, query, source):

        if source is None:
            if "xivapi.com" in query:
                source = "XIVAPI"

        self.throttle_query(source)
        r = requests.get(query, verify=False)
        d = r.content.decode("utf-8")
        cr = csv.reader(d.splitlines())
        return list(cr)

    def universalis_query(self, *args):
        args = [str(x) for x in args]
        lst = [UNIVERSALIS_BASE_URL] + list(args)
        query = "/".join(lst)
        return self.query(query, "UNIVERSALIS")

    def get_craft_quests(self):
        base_url = "https://ffxiv.consolegameswiki.com/mediawiki/api.php?action=query&format=json&prop=revisions&list=&titles=__CRAFTER___Quests&rvprop=content"
        items = []
        for crafter in CRAFTERS:
            url = base_url.replace("__CRAFTER__", crafter)

            r = requests.get(url)
            d = json.loads(r.text)
            pages = d["query"]["pages"]

            txt_full = pages[list(pages.keys())[0]]["revisions"][0]["*"]

            end = re.search("! Hand-in Items(.|\n)+$", txt_full).group(0)
            # spl = end.split("||")
            # print(end)

            for line in end.split("\n"):
                if not line.startswith("|"):
                    continue

                cols = line.split("||")
                if len(cols) < 2:
                    continue

                try:
                    lvl = int(re.search("^\|(\d+)\s*\|", line).group(1))
                except:
                    lvl = -1

                if lvl > 60:
                    continue

                line = line.split("||")[1]
                for lin in line.split(","):
                    reg = re.search("^\s*(\d+)\s*\[\[([^\[]*)\]\]", lin)

                    if reg is None:
                        # print("---" * 10)
                        # print(lin)
                        # print(line)
                        continue

                    quantity = int(reg.group(1))
                    name = reg.group(2)
                    hq = "(HQ)" in lin

                    items.append(
                        {
                            "quantity": quantity,
                            "name": name,
                            "hq": hq,
                            "job": crafter,
                            "level": lvl,
                        }
                    )

        return items