"""Methods for extracting names, emails and academic titles, mostly via Regexes"""

# Unicode-aware version of 're':
# https://pypi.org/project/regex/
import regex
import re
from typing import List

# see https://www.regular-expressions.info/unicode.html#prop for documentation

def is_normalized_name(s:str):
    """Returns True if the passed string is in the form 'Firstname [Middlenames] Lastname'"""
                       # Starting with uppercase: \p{Lu}
                       # |     Then any letter: \p{L}* (ignoring case since there are names such as "DiCaprio" where upper and lowercases are mixed)
                       # |     |     Names must end with a lowercase letter: \p{Ll}
                       # |     |     |     Then maybe other firstnames with "-" or " " separated: ([- ]\p{Lu}\p{L}*\p{Ll})*
                       # |     |     |     |                        A separator
                       # |     |     |     |                        | Then maybe prefixes like von, d' de etc. (not covered. Instead, we exclude special characters 
                       #                                              and numbers that we expect to be NOT included in names: []()!\/$%{}=?+" )
                       #                                              and also linebreaks 
                       # |     |     |     |                        | |                                         Lastname(s) are identical to firstname(s), but cannot be separated by ' '
                       # |     |     |     |                        | |                                         |
    r = regex.compile(r"^\p{Lu}\p{L}*\p{Ll}([- ]\p{Lu}\p{L}*\p{Ll})* [^0-9\[\]\(\)!\\/\$%\{\}=\?\+\t\r\n\v\f\"]*\p{Lu}\p{L}*\p{Ll}(-\p{Lu}\p{L}*\p{Ll})*$")
    return bool(r.match(s))

# ----------------------------------------------------------------------------------------------------
# The following regexes are for the title-search
# Sources for the academic grades:
# - https://de.wikipedia.org/wiki/Liste_akademischer_Grade_(Deutschland)
# - https://www.oesterreich.gv.at/themen/leben_in_oesterreich/titel_und_auszeichnungen/1.html
# - https://de.wikipedia.org/wiki/Professor#Abk%C3%BCrzungen
# - https://de.wikipedia.org/wiki/Juniorprofessur#Amtsbezeichnung_bzw._Titel
# ----------------------------------------------------------------------------------------------------

bachelorMasterOf = r"Arts|Science|Engineering|Laws|Fine Arts|Music|Education|Musical Arts|Business Administration"
# The title starts with one of these prefixes ...
# prefixes = rf"(Prof(essor|\.)|D(oktor|r\.)|Dipl(om|\.)|Mag(ister|\.)|Ph\.|B(achelor of ({bachelorMasterOf})|\.)|M(aster of ({bachelorMasterOf})|\.)|MBA|LL\.|BBA|Bakk(alaure|\.))" # (with long forms)
# prefixes = rf"((([Aa]o|[Aa]pl|[Aa]ss|[Aa]ssoz|[Hh]on|[Jj]un|[Jj]r)\.(\s+|-))?Prof\.|Dr\.|Dipl\.|Mag\.|Ph\.|PhD|B(achelor of ({bachelorMasterOf})|\.)|M(aster of ({bachelorMasterOf})|\.)|MBA|LL\.|BBA|Bakk\.)" # (with multi-whitespace)
# The prefixes after "Bakk" are from Ground Truth UDE
prefixes = rf"((([Aa]o|[Aa]pl|[Aa]ssoz|[Hh]on|[Jj]un|[Jj]r|Univ)\.[ -]?)?Prof\.|Dr\.|Dipl\.|Mag\.|Ph\.|Ph?D|B(achelor of ({bachelorMasterOf})|\.)|M(aster of ({bachelorMasterOf})|\.)|MBA|LL\.|BBA|Bakk\.|[Ww]iss\.|[Aa]kad\.|[Aa]ss\.|[Pp]riv\.|[Rr]eg\.|StD|StR|[Tt]echn\.|[Cc]and\.)"

# ... followed by some other titles (maybe separated by a space or a hyphen and ending with a dot, like Dipl.-Ing, Dr.-Ing. or M.Sc.)
# The other titles may also be separated by comma, e.g. https://cinch.uni-due.de/en/team/members/
# '(FH)' is also a middle title, e.g. https://www.uni-due.de/wasserbau/mitarbeiter_farghaly.php
middles = r"((, ?| | ?- ?)?([A-Za-zÖÄÜöäü]+\.|\(?FH\)?),?)*"

# Because we are interested in all titles together, the title is grouped in brackets. Later, we can refer to these groups with findall() or groups()
full_title_group = r"(" + prefixes + middles + r")"

# Candidates for quick search for titles
# Note that B. and M. leads to some false positives (e.g. email addresses like mam.mustermann). We filter them out later
possible_title_candidates = ["Prof.", "Dr.", "Dipl.", "B.", "M.", "Ing.", "Ph.", "PhD", "MBA", "LL.", "BBA", "Mag.", "Ass."]
possible_title_candidates_long = ["Professor", "Doktor", "Diplom", "Bachelor", "Master", "Ing.", "Magister", "Magistra", "Assistenz"]

def choose_best_title(titles:List[str]):
    """Chooses the best matching title in a candidate list"""

    if not titles:
        return ""
    elif len(titles) == 1:
        # Title not ambiguous
        best = titles[0]
    else:
        # Choose the best match:
        # 1) Prefer titles with Prof in the name (note that e.g. Jun.-Prof. does not start with 'Prof.')
        # 2) Prefer titles starting with Dr
        # 2) Prefer titles starting with Ph
        # 3) Prefer longer titles
        best = titles[0]
        for title in titles[1:]:
            if "Prof" in title and not "Prof" in best:
                best = title
            elif title.startswith("Dr") and not best.startswith("Dr") and not best.startswith("Prof"):
                best = title
            elif title.startswith("Ph") and not best.startswith("Ph") and not best.startswith("Dr") and not best.startswith("Prof"):
                best = title
            elif len(title) > len(best):
                best = title
    
    # if the title itself contains multiple title (comma-separated), we only take the first non-empty title
    # TODO Do we want this?
    # if ',' in best:
    #     for s in best.split(','):
    #         if s:
    #             best = s
    #             break

    # Remove accidental spaces (see e.g. https://www.bwsl.msm.uni-due.de/en/team/ => Max Briesemeister)
    best = re.sub(r" ?- ?", "-", best)

    return best


def try_title_before_name(txt:str, name:str):
    """Tries to extract a title before a name, e.g. 'Dr.-Ing. Max Mustermann'"""
    # print(txt) # ONLY DEBUGGING

    # The title is followed by the name, separated by whitespace
    # NOTE: It is intentional that even newline characters (\s) are searched. We assume that a line with "Prof..." is incomplete without a name
    r = re.compile(full_title_group + r"\s+" + name)

    # regex.findall() returns ALL matching groups as a two-dimensional list. The first index is the match itself (1st match of title+name, 2nd match of title+name),
    # the second index are the groups. We only look for the 1st group, i.e. [0][0], [1][0], ... The other (inner) groups would be "achelor of" etc.
    return choose_best_title([groups[0] for groups in r.findall(txt)])


def try_title_after_name_in_brackets(txt:str, name:str):
    """Tries to extract a title after a name with brackets, e.g. 'Max Mustermann (Dr.-Ing.)'"""
    # print(txt) # ONLY DEBUGGING

    # The title in brackets follows the name
    r = re.compile(name + r" \( ?" + full_title_group + r" ?\)")
    return choose_best_title([groups[0] for groups in r.findall(txt)])


def try_title_after_name_with_comma(txt:str, name:str):
    """Tries to extract a title after a name with comma 'Max Mustermann, Dr.-Ing.'"""
    # print(txt) # ONLY DEBUGGING

    # The title follows the name, separated by a comma
    # The title is only recognized if nothing but whitespaces are following after the title.
    # Otherwise we are in danger to include titles of the next person
    r = re.compile(name + r", " + full_title_group + r" ?(\n|$)")
    return choose_best_title([groups[0] for groups in r.findall(txt)])


def compute_title(txt:str, name:str|None = None):
    """Computes the title of a person in the given text. It is assumed that the title of a person
       is the longest prefix/suffix starting with common titles like Prof., Dr., etc. (Prof. takes precedence over Dr.)
       
       name: Name of the person whose titles should be extracted. Important to not confuse the person's title with titles of other people.
             If the param is not given, the algorithm simply looks for any title in the passed text and returns it"""
    
    # Preprocessing
    # Note that we perform preprocessing with the ful text, but this does not matter since we search only for the name in try_title... methods
    # Everything else will be ignored
    
    # 1. Replace long forms with short forms. This makes regex-searching easier.
    txt = txt.replace("Junior-",       "Jun.-") \
             .replace("Universitäts-", "Univ.-") \
             .replace("Professor",     "Prof.") \
             .replace("Professorin",   "Prof.") \
             .replace("Doktor",        "Dr.") \
             .replace("Diplom-",       "Dipl.-") \
             .replace("Magister",      "Mag.") \
             .replace("Magistra",      "Mag.")

    # 2. Trim double whitespaces but keep lines
    txt = "\n".join(" ".join(line.split()).strip() for line in txt.splitlines()).strip()

    # 3. If the prefix is separated with ' - ', transform it to a comma-separator, e.g. Max Mustermann - Prof. => Max Mustermann, Prof.
    txt = re.sub(" - " + prefixes, r", \g<1>", txt)
    # 4. Remove whitespace in ' - ', e.g. Dr. - Ing.
    txt = txt.replace(" - ", "-")

    if name:
        return try_title_before_name(txt, name) or try_title_after_name_in_brackets(txt, name) or try_title_after_name_with_comma(txt, name)
    else:
        # This is mostly important for the table analysis
        r = re.compile(full_title_group)
        return choose_best_title([groups[0] for groups in r.findall(txt)])
    

# This regex search the most frequently titles
# Author of the following regex: Arman Arzani
r"(?:^Prof\.? *|\(([^\)]+)\)|paed. *|Master of Agricommerce *|Wiss.Ass.|päd.OStRätin i. HD *|M\.Ed\. *|Päd. *|Master of Science *|AR Dr\. rer\. nat\. *|Jun\.- *|ORätin *|-Wirtsch\.-Inf *|Prof\.|Prof\. *|Dr\. *|Inform\. *|med\. *|M\.Sc\. *|Dipl. *|PhD *|essorin *|Dipl\.-Math\. *|Mag\. soc\. oec\. *|-Ök\. *|-Öko\. *|Soz\.-Wiss\. *|-Sportlehrer *|-Soz\.-Wiss\. *|-Chem\. *|-Kffr\. *|-Kff\. *|-Phys\. *|PD *|-Biol\. *|-Wirt\.-Inf\. *|-Math\. *|Inf\. *|-Psych\. * |\([a-zA-Z]+\) *|-Kfm\. *|\([a-z\.A-Z]+\)| Dipl\. Inform\. *|Dipl\.-Biol\. *|Dipl\.-Wirt\.-Inf\. *|phil\. *|rer\. *|Mag\. soc\. oec\. *|nat\. *|M\. A\. *|M\.Sc *|soc\. *|-Geol\. *|oec\. *|medic\. *|i\.R\. *|-Wirt\.|-Soz\.Wiss\. *| M\.S\.c * |-Volksw\. *|Priv\.-Doz\. *|B\.Eng\. *|apl\. *|M\.Sc\. *|M\. Sc\. * |Dipl\.-Kfm\. *|Dipl\.-Ing\. *|-Ing\. *|Mag\. soc\. oec\. *|Mag\. soc\. oec\. *|pol\. *|B\. Sc\. *|Dipl\.-Psych\. *|phil *|nat *|Dipl\.-Ök\. *|-BWL *|M\.A\. *|Dipl\.-Kff\. *|Dipl\.-Kffr\. *|Dipl\.-Chem\. *|Dipl\.-Phys\. *|Dipl\. Soz\.-Wiss\. *|-Hdl\. *|MSc *|M\.Eng\. *|Oec\. *|M\. Ed\. *|Umweltwiss\. *|M\.B\.A\. *|B\.Sc\. *|-Arb\.\/|Psychologische Psychotherapeutin *|jur\. *|Heil-Päd\. *|-Region\.-Wiss\. *|M\.Eng\. *|-Pol\. *|Soz\.Wiss\. *|B\.Sc\. *|-Oec\. *|Akad\. ORat *|h\.c\. *|essor *|päd\.OStRätin i\. *|päd\.OStRätin i\. HD *|Akad\. Rat *|Priv\. Doz\. *|-Soz\. *|Ing\. *|m-Geogr\. *|techn\. *|Apl\. *|- Päd\. *|techn\.|- Päd\. *|habil\. *|essor h\.c\. *|Biol\. *|Univ\.-|Univ\.- *|Psych\. *|Akad\. *|-Päd\. *|Ph\.D *|-Soz\.-Arb\.\/-Soz\.-Päd\. *|Ing\. *|Phys\. *|techn\. *|Sportwiss\. *|M\.Sc\., *|Mag\. *|, *|M\. Eng\. *|OStR i\.H\. *|sc\. *|-Finanzwirt M\.I\.Tax *|-Hdl\., MBA *|\b, M.A. |\b, Ph.D.)"
