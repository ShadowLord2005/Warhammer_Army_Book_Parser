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

def path_to_tags(path:str) -> BeautifulSoup:
    with Path(path).open(encoding="utf8") as file:
        path_tags = BeautifulSoup(file, builder=builder, from_encoding="utf-8")
    return path_tags


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


class ProfilePartIdentifierClasses(PartIdentifierParent):
    BASE_SIZE__RACE__FACTION__UNIT_TYPE = (["Base_Size","Race","Faction","Unit_Type"],"Unit-Profile_H4--Race---Faction---Unit-Type",4,"Unit-Profile_Body--Race---Faction---Unit-Type")
    STAT_LINE = (["Stat_Line"],"Unit-Profile_Unit-Stat-Line",2)
    NAME__POINTS = (["Name","Points"],"Header_H2",-1)
    WARGEAR__OPTIONS__SPECIAL_RULES = (["Wargear","Options","Special_Rules"],"Header_H4",-1, "Body_Body-Text")



class HeroProfilePartIdentifierClasses(PartIdentifierParent):
    BASE_SIZE__RACE__FACTION__UNIT_TYPE = (["Base_Size","Race","Faction","Unit_Type"],"Unit-Profile_Body--Race---Faction---Unit-Type",-1)
    STAT_LINE = (["Stat_Line"],"Unit-Profile_Unit-Stat-Line",2)
    NAME__POINTS = (["Name","Points"],"CharOverride-11",0)
    MIGHT__WILL__FATE = (["Might","Will","Fate"],"Unit-Profile_Might-Will-Fate-Numbers",3)
    WARGEAR__HEROIC_ACTIONS__OPTIONS__SPECIAL_RULES = (["Wargear","Heroic_Actions","Options","Special_Rules"],"CharOverride-13",-1)

class ArmyListPartIdentifierClasses(Enum):
    pass

class PageTypeIdentifierClasses(StrEnum):
    HERO_PROFILE_PAGE = "Unit-Profile_Might-Will-Fate-Numbers"
    UNIT_PROFILE_PAGE = "Unit-Profile_Unit-Stat-Line"

class PageTypes(Enum):
    HERO_PROFILE = auto()
    UNIT_PROFILE = auto()
    MULTI_PROFILE = auto()
    ARMY_LIST = auto()

builder = LXMLTreeBuilderForXML(
    multi_valued_attributes=HTMLTreeBuilder.DEFAULT_CDATA_LIST_ATTRIBUTES,
    empty_element_tags=HTMLTreeBuilder.DEFAULT_EMPTY_ELEMENT_TAGS,
    preserve_whitespace_tags=HTMLTreeBuilder.DEFAULT_PRESERVE_WHITESPACE_TAGS
)


class EBookPage:
    def __init__(self, page_path : Path) -> None:
        with page_path.open() as file:
            self.page_data = BeautifulSoup(file,builder=builder)
        page_number_tag  = self.page_data.find("title")
        assert page_number_tag is not None
        page_number_string = page_number_tag.string
        assert page_number_string is not None
        self.page_num = int(page_number_string.strip("Page "))
        if self.page_data.find(PageTypeIdentifierClasses.HERO_PROFILE_PAGE) is not None:
            self.page_type = None


class Profile:
    def __init__(self, profile_tags : BeautifulSoup) -> None:
        self.data = profile_tags
        self.wargear : list[tuple[str,str,str|None]] = []
        self.options : list[tuple[str,str, int, str|None]] = []
        self.options_parser()

    def wargear_parser(self):
        data = self.data.find_all(class_=ProfilePartIdentifierClasses.WARGEAR__OPTIONS__SPECIAL_RULES.identifier)
        header : Tag  | None = None
        for item in data:
            if item.string == "Wargear":
                header = item
                break
        if header is None:
            print("No Wargear")
            return
        body : list[Tag] = []
        for sibling in header.next_siblings:
            if sibling in data:
                break
            elif type(sibling) == Tag:
                body.append(sibling)
            else:
                continue
        items_tag = body[0]
        items_text = items_tag.get_text().replace(" and ",",")
        war_gear = items_text.split(",")
        for gear in war_gear:
            self.wargear.append((gear,"Standard",None))
        if len(body) == 1:
            print("No Special Wargear")
            print(self.wargear)
            return
        for i in range(1,len(body)):
            wargear_description = body[i]
            description_text = wargear_description.get_text().split("–")[1:]
            name_type = wargear_description.get_text().split("–")[0]
            if name_type.find(" Active ") != -1:
                wargear_type = "Active"
                wargear_name = name_type.replace(" Active ","").strip()
            elif name_type.find(" Passive ") != -1:
                wargear_type = "Passive"
                wargear_name = name_type.replace(" Passive ","").strip()
            else:
                wargear_type = "Other"
                wargear_name = name_type
            for i in range(len(self.wargear)):
                if self.wargear[i][0] == wargear_name:
                    self.wargear[i] = (wargear_name,wargear_type, "".join(description_text))
                    break
                elif i == len(self.wargear):
                    self.wargear.append((wargear_name,wargear_type, "".join(description_text)))
                else:
                    continue
        print(self.wargear)

    def options_parser(self):
        data = self.data.find_all(class_=ProfilePartIdentifierClasses.WARGEAR__OPTIONS__SPECIAL_RULES.identifier)
        header : Tag  | None = None
        for item in data:
            if item.string == "Options":
                header = item
                break
        if header is None:
            print("No Options")
            return
        option_items : list[Tag] = []
        option_descriptions : list[Tag] = []
        for sibling in header.next_siblings:
            if sibling in data:
                break
            elif type(sibling) == Tag:
                if sibling.get_text().find("points") != -1:
                    option_items.append(sibling)
                else:
                    option_descriptions.append(sibling)
            else:
                continue
        for tag in option_items:
            content = tag.get_text().split(".")
            option = content[0]
            cost = int(content[-1].removesuffix("points"))
            self.options.append((option,"Standard",cost,None))
        if len(option_descriptions) < 1:
            print("No Special Options")
            print(self.options)
            return
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
            for i in range(len(self.options)):
                if self.options[i][0] == option_name:
                    points = self.options[i][2]
                    self.options[i] = (option_name,option_type,points, "".join(description_text))
                    break
                elif i == len(self.options):
                    self.options.append((option_name,option_type, -1,"".join(description_text)))
                else:
                    continue
        print(self.options)




class HeroProfile(Profile):
    pass


frodo_tags = path_to_tags("epub/armies_lotr/OEBPS/ME_66_Army_Book_LotR_01-19_EPub-9.xhtml")

Profile(frodo_tags)

gandalf_tags = path_to_tags("epub/armies_lotr/OEBPS/ME_66_Army_Book_LotR_01-19_EPub-12.xhtml")

Profile(gandalf_tags)
