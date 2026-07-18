import re
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from bs4.builder import HTMLTreeBuilder, LXMLTreeBuilderForXML
from bs4.element import Tag

if TYPE_CHECKING:
    from typing import Self

    from bs4.element import PageElement

#Converts a string path to a Beautiful Soup object for further work
def path_to_tags(path:str) -> BeautifulSoup:
    with Path(path).open(encoding="utf8") as file:
        path_tags = BeautifulSoup(file, builder=builder, from_encoding="utf-8")
    return path_tags

#Enum for the different types of things (Wargear, Options, Special Rules, etc)
class Typer(Enum):
    STANDARD_ONLY = auto()
    SPECIAL_ONLY = auto()
    MIXED = auto()
    NONE = auto()

#Parent Enum for the different Part Identifiers that adds some functionality to help with identifying specific parts and their quantity
class PartIdentifierParent(str, Enum):
    identifier : str
    expected_num : int
    val_identifier : str | None

    def __new__(cls, parts : list[str], identifier : str, expected_num : int, val_identifier : str|None = None) -> Self:
        obj = str.__new__(cls,parts)
        obj._value_ = parts
        obj.identifier = identifier
        obj.val_identifier = val_identifier
        obj.expected_num = expected_num
        return obj

#Identifier Elements for a Standard Profile
class ProfilePartIdentifierClasses(PartIdentifierParent):
    BASE_SIZE__RACE__FACTION__UNIT_TYPE = (["Base_Size","Race","Faction","Unit_Type"],"Unit-Profile_H4--Race---Faction---Unit-Type",4,"Unit-Profile_Body--Race---Faction---Unit-Type")
    STAT_LINE = (["Stat_Line"],"Unit-Profile_Unit-Stat-Line",2)
    NAME__POINTS = (["Name","Points"],"Header_H2",1)
    WARGEAR__OPTIONS__SPECIAL_RULES = (["wargear","options","special rules"],"Header_H4",-1, "Body_Body-Text")


#Identifier Elements for a Hero Profile (May be converted to just have ones that are not in te standard profile) (NYI)
class HeroProfilePartIdentifierClasses(PartIdentifierParent):
    BASE_SIZE__RACE__FACTION__UNIT_TYPE = (["Base_Size","Race","Faction","Unit_Type"],"Unit-Profile_Body--Race---Faction---Unit-Type",-1)
    STAT_LINE = (["Stat_Line"],"Unit-Profile_Unit-Stat-Line",2)
    NAME__POINTS = (["Name","Points"],"CharOverride-11",0)
    MIGHT__WILL__FATE = (["Might","Will","Fate"],"Unit-Profile_Might-Will-Fate-Numbers",3)
    WARGEAR__HEROIC_ACTIONS__OPTIONS__SPECIAL_RULES = (["heroic actions"],"CharOverride-13",-1)

#Identifier Elements for an Army List (NYI)
class ArmyListPartIdentifierClasses(Enum):
    pass

#Individual identifier elements that tell what sort of page is being processed (NYI)
class PageTypeIdentifierClasses(StrEnum):
    HERO_PROFILE_PAGE = "Unit-Profile_Might-Will-Fate-Numbers"
    UNIT_PROFILE_PAGE = "Unit-Profile_Unit-Stat-Line"

#Class for the different page types (NYI)
class PageTypes(Enum):
    HERO_PROFILE = auto()
    UNIT_PROFILE = auto()
    MULTI_PROFILE = auto()
    ARMY_LIST = auto()

#Ensures that is is possible to suse class_ be using the HTML attributes with an XML Parser
builder = LXMLTreeBuilderForXML(
    multi_valued_attributes=HTMLTreeBuilder.DEFAULT_CDATA_LIST_ATTRIBUTES,
    empty_element_tags=HTMLTreeBuilder.DEFAULT_EMPTY_ELEMENT_TAGS,
    preserve_whitespace_tags=HTMLTreeBuilder.DEFAULT_PRESERVE_WHITESPACE_TAGS
)

#Generic Profile Class for all character profiles
class Profile:
    def __init__(self, profile_tags : BeautifulSoup) -> None:
        #Make the tags accessible from within functions
        self.data = profile_tags

        #Set up the items from a page to be accessible in functions
        self.name : str
        self.cost : int
        self.wargear : list[tuple[str,str,str|None]] = []
        self.wargear_type : Typer
        self.options : list[tuple[str,str, int, str|None]] = []
        self.options_type : Typer
        self.special_rules : list[tuple[str, str, str|None, str|None]] = []
        self.rules_type : Typer
        print("------------------")
        self.name_cost_parser()
        self.wargear_parser()
        self.options_parser()
        self.rules_parser()
        print("------------------")

    #Function to get the name and cost from a page
    def name_cost_parser(self):
        data = self.data.find(class_=ProfilePartIdentifierClasses.NAME__POINTS.identifier)
        if data == None:
            print("No Name or Points Cost")
            return
        content = data.get_text().split(".")
        self.name = content[0]
        self.cost = int(content[-1].removesuffix("points"))
        print(f"Name: {self.name}\nCost: {self.cost}")
        return

    #Function to get the wargear from a page
    def wargear_parser(self):
        data = self.data.find_all(class_=ProfilePartIdentifierClasses.WARGEAR__OPTIONS__SPECIAL_RULES.identifier)
        header : Tag  | None = None
        #As the identifier can get many items this looks for the one we are after
        #Note that these are actually the headers above the data that we a looking for
        for item in data:
            if item.get_text().lower() == "wargear":
                header = item
                break
        #If a character has no default wargear this exits the function
        if header is None:
            self.wargear_type = Typer.NONE
            return
        body : list[Tag] = []
        #This looks at all of the tags on the same level as the header in the order they occur in the document and puts them all into a list until it reaches the next header then breaks out of the for loop
        for sibling in header.next_siblings:
            if sibling in data:
                break
            #This checks that the siblings are Tags not random strings of whitespace which can occur when using siblings
            elif type(sibling) == Tag:
                body.append(sibling)
            else:
                continue
        #We know that the first tag in the body of wargear is a list of all the wargear items that a character has. This function just splits them into a list, declares that they are standard and, as such, they have no description
        items_tag = body[0]
        items_text = items_tag.get_text().replace(" and ",",")
        war_gear = items_text.split(",")
        for gear in war_gear:
            self.wargear.append((gear.strip(),"Standard",None))

        #This checks if there is only one tag meaning that no wargear has a description and thus it is all standard. If so it exits
        if len(body) == 1:
            self.wargear_type = Typer.STANDARD_ONLY
            return

        #This gets all the items of special wargear, determines whether they are active or passive and then adds the name, type and description to the list of wargear
        for i in range(1,len(body)):
            wargear_description = body[i]
            #This splits the wargear to have the name and type in one part and then the description in the other(s)
            description_text = wargear_description.get_text().split("–")[1:]
            name_type = wargear_description.get_text().split("–")[0]
            #This then checks which type it is and then sets the type an name appropriately
            if name_type.find(" Active ") != -1:
                wargear_type = "Active"
                wargear_name = name_type.replace(" Active ","").strip()
            elif name_type.find(" Passive ") != -1:
                wargear_type = "Passive"
                wargear_name = name_type.replace(" Passive ","").strip()
            else:
                wargear_type = "Other"
                wargear_name = name_type

            #This then checks which items of wargear listed in the opening line match ones discovered in the special types and then replaces them as appropriate adding the new type and description.
            #If it can't be found it adds it to the bottom of the list
            for i in range(len(self.wargear)):
                if self.wargear[i][0] == wargear_name:
                    self.wargear[i] = (wargear_name,wargear_type, "".join(description_text).strip())
                    break
                elif i == len(self.wargear):
                    self.wargear.append((wargear_name,wargear_type, "".join(description_text).strip()))
                else:
                    continue
        for gear in self.wargear:
            if gear[1] == "Standard":
                self.wargear_type = Typer.MIXED
                return
            else:
                continue
        self.wargear_type = Typer.SPECIAL_ONLY
        return

    #Function to get the options from a page
    def options_parser(self):
        data = self.data.find_all(class_=ProfilePartIdentifierClasses.WARGEAR__OPTIONS__SPECIAL_RULES.identifier)
        header : Tag  | None = None

        #As the identifier can get many items this looks for the one we are after
        #Note that these are actually the headers above the data that we a looking for
        for item in data:
            if item.get_text().lower() == "options":
                header = item
                break
        if header is None:
            self.options_type = Typer.NONE
            return
        option_items : list[Tag] = []
        option_descriptions : list[Tag] = []

        #This looks at all of the tags on the same level as the header in the order they occur in the document and puts them all into a list until it reaches the next header then breaks out of the for loop
        for sibling in header.next_siblings:
            if sibling in data:
                break
            elif type(sibling) == Tag:
                #This checks if the tag is an item itself of a description of a special option
                if sibling.get_text().find("points") != -1:
                    option_items.append(sibling)
                else:
                    option_descriptions.append(sibling)
            else:
                continue

        #This converts a tag which is an option into the name of the option and the cost in points.
        #It then adds it to the list of options with the "Standard" type and no description
        for tag in option_items:
            content = tag.get_text().split(".")
            option = content[0].strip()
            cost = int(content[-1].removesuffix("points"))
            self.options.append((option,"Standard",cost,None))

        #This then checks for any special wargear and if there is none exits
        if len(option_descriptions) < 1:
            self.options_type = Typer.STANDARD_ONLY
            return

        #This then iterates through all the special wargear, gets their name, type and description and adds it to the main list
        for description in option_descriptions:
            description_text = description.get_text().split("–")[1:]
            name_type = description.get_text().split("–")[0]
            if name_type.find(" Active ") != -1:
                option_type = "Active"
                option_name = name_type.replace(" Active ","").strip()
            elif name_type.find(" Passive ") != -1:
                option_type = "Passive"
                option_name = name_type.replace(" Passive ","").strip()
            else:
                option_type = "Other"
                option_name = name_type

            #This goes through all of the options and matches up the descriptions with any of them that are special, appending if no match is found
            for i in range(len(self.options)):
                if self.options[i][0] == option_name:
                    points = self.options[i][2]
                    self.options[i] = (option_name,option_type,points, "".join(description_text).strip())
                    break
                elif i == len(self.options):
                    self.options.append((option_name,option_type, -1,"".join(description_text).strip()))
                else:
                    continue
        for option in self.options:
            if option[1] == "Standard":
                self.option_type = Typer.MIXED
                return
            else:
                continue
        self.option_type = Typer.SPECIAL_ONLY
        return

    #Function to get the special rules from a page
    def rules_parser(self):
        data = self.data.find_all(class_=ProfilePartIdentifierClasses.WARGEAR__OPTIONS__SPECIAL_RULES.identifier)
        header : Tag  | None = None

        #As the identifier can get many items this looks for the one we are after
        #Note that these are actually the headers above the data that we a looking for
        for item in data:
            if item.get_text().lower() == "special rules":
                header = item
                break
        if header is None:
            self.rules_type = Typer.NONE
            return

        #This then goes through and gets all of the sibling tags that are special rules
        body : list[Tag] = []
        for sibling in header.next_siblings:
            if sibling in data:
                break
            elif type(sibling) == Tag:
                body.append(sibling)
            else:
                continue

        #This then checks if there are any standard special rules which if they exist are always the first item in the list of body tags
        if body[0].get_text().find("–") == -1:
            #This then gets a list of all of the special rules in the standard block by splitting on any comma that is not inside of a pair of brackets
            simple_rules_tag = body[0]
            simple_rules_text = simple_rules_tag.get_text()
            simple_rules = re.split(r',\s*(?![^()]*\))', simple_rules_text)

            #The individual rules are then added to the main rules list in with the correct formatting for standard types
            for rule in simple_rules:
                self.special_rules.append((rule, "Standard", None, None))

            #This then checks if there are any non-standard rules and if not exits
            if len(body) == 1:
                self.rules_type = Typer.STANDARD_ONLY
                return
            self.rules_type = Typer.MIXED
            i = 1
        else:
            self.rules_type = Typer.SPECIAL_ONLY
            i=0

        #The list of body tags is iterated over (Starting at 0 for no standard rules and 1 if there are standard rules) to get all of the other special rules
        while i < len(body):
            rule_type : str
            rule_name : str
            rule_description : list[str] = []

            #The rule item is got and then split on the marker which separates the name and type from the short description
            rule = body[i]
            rule_short = rule.get_text().split("–")[1:]
            rule_name_type = rule.get_text().split("–")[0]
            #The type is then checked before the name and type are set
            if rule_name_type.find(" Active ") != -1:
                rule_type = "Active"
                rule_name = rule_name_type.replace(" Active ","").strip()
            elif rule_name_type.find(" Passive ") != -1:
                rule_type = "Passive"
                rule_name = rule_name_type.replace(" Passive ","").strip()
            else:
                rule_type = "Other"
                rule_name = rule_name_type

            #As the full description is found in the next tag the value of i is increased before a new while loop is created
            i += 1
            while i < len(body):
                #This loop checks if the text of the tag has the separation marker which indicates it is a new item and if so breaks the while loop
                body_text = body[i].get_text()
                if body_text.find("–") != -1:
                    break
                else:
                    #If the body text is not a new rule it is added to the list of descriptions and i is increased
                    i += 1
                    rule_description.append(body_text)

            #Once either a new rule has been found or the end of the body list has been reached the rule is added to the list of special rules
            self.special_rules.append((rule_name, rule_type, "".join(rule_short), "\n".join(rule_description)))
            #If the end of the list has not been reached then the first while loop runs again and a new special rule is found
        return

    #Function to check for other headers
    def has_other_headers(self) -> tuple[bool, list[Tag]]:
        data = self.data.find_all(class_=ProfilePartIdentifierClasses.WARGEAR__OPTIONS__SPECIAL_RULES.identifier)
        other_headers : list[Tag] = []
        #This checks if the headers discovered are the ones we are looking for and adds any others to a list
        for item in data:
            if item.get_text().lower() in ProfilePartIdentifierClasses.WARGEAR__OPTIONS__SPECIAL_RULES.value:
                continue
            else:
                other_headers.append(item)
        #If there are other headers this returns true and a list of them
        return ((len(other_headers) > 0), other_headers)



class HeroProfile(Profile):
    pass


frodo_tags = path_to_tags("epub/armies_lotr/OEBPS/ME_66_Army_Book_LotR_01-19_EPub-9.xhtml")

Profile(frodo_tags)

saw_tags = path_to_tags("epub/armies_lotr/OEBPS/ME_66_Army_Book_LotR_01-19_EPub-10.xhtml")

Profile(saw_tags)

gandalf_tags = path_to_tags("epub/armies_lotr/OEBPS/ME_66_Army_Book_LotR_01-19_EPub-12.xhtml")

Profile(gandalf_tags)

gimli_tags = path_to_tags("epub/armies_lotr/OEBPS/ME_66_Army_Book_LotR_01-19_EPub-15.xhtml")

Profile(gimli_tags)
