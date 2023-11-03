from lxml.html import HtmlElement
from typing import List


class MergedPerson:
    """A person with multiple found_in and homepage values"""
    def __init__(self, name:str):
        self.name : str = name
        """Name of the person"""
        self.source : List[str] = []
        """From which sources (e.g. txt or table) the metadata was extracted"""
        self.title : str = ""
        """Academic grade / title"""
        self.email : str = ""
        """Email of the person"""
        self.found_in : List[str] = []
        """URLs where the person was found"""
        self.homepage : List[str] = []
        """URLs of ther person's homepage"""


class Person:
    def __init__(self, name, source):
        self.name : str = name
        """Name of the person"""
        self.source : str = source
        """From which source (e.g. txt or table) the person was extracted"""
        self.title : str = ""
        """Academic grade / title"""
        self.email : str = ""
        """Email of the person"""
        self.found_in : str = ""
        """URL where the person was found"""
        self.homepage : str = ""
        """URL of ther person's homepage"""
    
    def __eq__(self, __value: object) -> bool:
        """Returns True if both objects have the same found_in URL and the same name"""
        return self.name == __value.name and self.found_in == __value.found_in # type: ignore
    
    def __str__(self) -> str:
        return ("Person {\n"
                f"  name     = {self.name}\n"
                f"  title    = {self.title}\n"
                f"  email    = {self.email}\n"
                f"  found_in = {self.found_in}\n"
                f"  homepage = {self.homepage}\n"
                "}")
    __repr__ = __str__

class TableConfiguration:
    def __init__(self) -> None:
        self.i_title : int|None = None
        """Index of a potential column for academic grades"""
        self.i_firstname : int|None = None
        """Index of a potential column for firstname"""
        self.i_lastname : int|None = None
        """Index of a potential column for lastname or the full name"""
        self.i_email : int|None = None
        """Index of a potential column for email"""
        self.swap_lastname : bool = False
        """Wether to swap lastname and firstname in a name column"""
    def __str__(self) -> str:
        return f"Table(title={self.i_title}, firstname={self.i_firstname}, lastname={self.i_lastname}, email={self.i_email}, swap_lastname={self.swap_lastname})"

class WebPage:
    def __init__(self, id, url, html) -> None:
        self.id : str = id
        self.url : str = url
        self.html : str = html
        self.root : HtmlElement|None = None
        self.txt : str = ""
        self.lang : str = ""