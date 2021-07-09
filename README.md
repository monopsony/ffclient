# ffclient

This small mess is a client that facilitates crafting and selling in FFXIV based on current market board prices. The client is entirely text-based and is run from the command line. The APIs used are: 
- [xivapi](https://xivapi.com/docs) for game info (recipe/item lists etc)
- [Universalis](https://universalis.app/docs) for market board information

## Requirements

You need python 3.4+ to run this as well as a variety of libraries. They can all be installed using the following command:
`pip install pandas numpy keyboard termcolor clipboard requests bs4`

## Setup

In the `para.py` file, set the "world" value to your prefered world. Note that if the name does not match, none of the requests will work. 

While in the ffclient directory, simply run `python Client.py`. A list of commands as well as their descriptions can be found using the `help` command or subcommand. 

By default, the client does not know of recipes or items. Use the `recipe update` and `item update` commands to fetch an up-to-date list. 

## Additional information

### Macros

In the `Macros.py` file, one can save a series of commands for convenience. An example of what such a file could look like is the following:

```python
craftq = '''
list set CraftQuests
sell list
sales filter (expProfit > 10000)
sales sort expProfit
sales show 20
'''

update = '''
recipe update
item update
list update CraftQuests
'''
```

When running the client, `macro crafthq` would automatically run all the lines given in the respective string of the `Macros.py` file. Note that if some commands require confirmation (such as `sell list`), those still need to be given manually.



