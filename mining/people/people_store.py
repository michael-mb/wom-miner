"""Manages a list of found peoples, merging people with the same name together"""

from typing import Dict, List
from people.types import Person, MergedPerson
from people import name_analysis
from collections import Counter
import re

# TODO Dieser erste "naive" Ansatz schmeißt einfach alle namen raus, die Duplikate sind, ohne weitere Logik
#      Das kann noch verfeinert werden, z.B. um eine Analyse der URL
#      ("Behandle Personen als ungleich wenn sich die gefundene URL um mindestens X unterscheidet")

store : Dict[str, List[Person]] = dict()


def clear():
    """Clears the store"""
    store.clear()


def add_person(person:Person):
    """Adds a person to the store """
    # Save the person object to the corresponding key
    if person.name in store:
        store[person.name] += [person]
    else:
        store[person.name] = [person]


def normalize_homepage(s):
    s = re.sub(r"^https://www\.", "https://", s, count=1)
    return re.sub(r"^http://www\.", "http://", s, count=1)


def aggregate_people() -> List[MergedPerson]:
    """Merges the information for people with the same name, returning a list of distinct people."""
    people = []
    for name, data in store.items():
        p = MergedPerson(name)

        # Choose best title (our own algorithm)
        titles = [x.title for x in data if x.title] # Map to list of titles and only keep non-empty titles
        p.title = name_analysis.choose_best_title(titles)

        # Choose best email (majority decision)
        emails = [x.email for x in data if x.email]
        if emails:
            p.email = Counter(emails).most_common(1)[0][0]
        
        # List source (txt, table, ...) and found_in
        p.source = [x.source for x in data]
        p.found_in = [x.found_in for x in data]

        # Choose homepage (sort by number of occurrences)
        # Consider "www." and not "www." pages as equal
        homepages = [normalize_homepage(x.homepage) for x in data if x.homepage]

        if len(homepages) == 1:
            p.homepage = [homepages[0]]
        elif len(homepages) > 1:
            count_map = Counter(homepages)
            homepages_without_duplicates = list(dict.fromkeys(homepages))
            homepages_without_duplicates.sort(key=lambda x: count_map.get(x), reverse=True) # type: ignore
            p.homepage = homepages_without_duplicates
        
        people.append(p)

    return people
