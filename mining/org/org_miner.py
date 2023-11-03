from elasticsearch import Elasticsearch
from lxml import etree
import html
from HanTa import HanoverTagger as ht
from urllib.parse import urljoin
from urllib.parse import urlparse

def getWordsBefore(start, html_string, word, number, without_comma):
    position = start
    counter = 0
    while True:
        position -= 1
        if position == -1:
            break
        else:
            if html_string[position] == ' ':
                counter += 1
                if counter == number:
                    break
            if html_string[position] == '\n':
                break
            # stop at special characters
            if html_string[position] == '(' or html_string[position] == ')' or html_string[position] == '.' or html_string[position] == '!' or html_string[position] == '?' or html_string[position] == ':' or html_string[position] == '>' or html_string[position] == '<' or html_string[position] == ';' or html_string[position] == '"' or html_string[position] == '“' or html_string[position] == '\\':
                break
            if without_comma:
                if html_string[position] == ',':
                    break
            word = html_string[position] + word

    word = html.unescape(word)
    word = word.replace("–", "-")
    word = word.replace(" ", " ")
    return word

def getWordsAfter(end, html_string, word, number, without_comma):
    position = end
    counter = 0
    while True:
        if position == len(html_string):
            break
        else:
            if html_string[position] == ' ':
                counter += 1
                if counter == number:
                    break
            if html_string[position] == '\n':
                break
            # stop at special characters
            if html_string[position] == '(' or html_string[position] == ')' or html_string[position] == '.' or html_string[position] == '!' or html_string[position] == '?' or html_string[position] == ':' or html_string[position] == '>' or html_string[position] == ';' or html_string[position] == '"' or html_string[position] == '“' or html_string[position] == '„' or html_string[position] == '\\':
                break
            if html_string[position] == '0' or html_string[position] == '1' or html_string[position] == '2' or html_string[position] == '3' or html_string[position] == '4' or html_string[position] == '5' or html_string[position] == '6' or html_string[position] == '7' or html_string[position] == '8' or html_string[position] == '9':
                break
            if without_comma:
                if html_string[position] == ',':
                    break
            if html_string[position] == '<':
                temp = html_string[position] + html_string[position + 1] + html_string[position + 2] + html_string[position + 3]
                if temp == "<br>":
                    word += ""
                    counter += 1
                    position += 4
                    if counter == number:
                        break
                    continue
                else:
                    break
            word += html_string[position]
            position += 1

    word = html.unescape(word)
    word = word.replace("–", "-")
    word = word.replace(" ", " ")
    return word

def check_entity_strings_and_upload(link_req_short, link_req_long, org_number, index_name_Searching, es, entity_strings, counter_Entity, tagger_ger, link, is_first, extra_links):
    for p in range(len(entity_strings)):
        try:
            while entity_strings[p].startswith(" ") or entity_strings[p].startswith(","):
                entity_strings[p] = entity_strings[p][1:]
            while entity_strings[p].endswith(" ") or entity_strings[p].endswith(","):
                entity_strings[p] = entity_strings[p][:-1]
            # no special chars
            if org_number == 0:
                if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234& -öäüÖÜÄ' for c in entity_strings[p]):
                    continue
            elif org_number == 1:
                if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234& -,.öäüÖÜÄ' for c in entity_strings[p]):
                    continue

                if "Abteilung" in entity_strings[p]:
                    if "Abteilung für" not in entity_strings[p]:
                        continue
                # some formatting
                if "für" in entity_strings[p]:
                    if "für " not in entity_strings[p]:
                        entity_strings[p] = entity_strings[p].replace("für", "für ")
            elif org_number == 2:
                if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234& -,.öäüÖÜÄ' for c in entity_strings[p]):
                    continue

                if "Zentrum" in entity_strings[p]:
                    if "Zentrum für" not in entity_strings[p]:
                        if not entity_strings[p].endswith("Zentrum"):
                            continue
                if "Institute" in entity_strings[p]:
                    if "Institute for" not in entity_strings[p]:
                        continue
                if "Institut" in entity_strings[p] and "Institute" not in entity_strings[p]:
                    if "Institut für" not in entity_strings[p]:
                        if not entity_strings[p].endswith("Institut"):
                            continue

                if "für" in entity_strings[p]:
                    if "für " not in entity_strings[p]:
                        entity_strings[p] = entity_strings[p].replace("für", "für ")
            if "  " in entity_strings[p] or '--' in entity_strings[p]:
                continue
            # string should have more than just 1 word
            current_enitity_splitted = entity_strings[p].split(" ")
            splitted_temp = []
            for t in current_enitity_splitted:
                if len(t) != 0:
                    splitted_temp.append(t)
            current_enitity_splitted = splitted_temp
            
            if len(current_enitity_splitted) < 2:
                continue

            if org_number == 2:
                wrong_ending = False
                for c in range(len(current_enitity_splitted)):
                    if current_enitity_splitted[c] == "Zentrum" or current_enitity_splitted[c] == "Institut" or current_enitity_splitted[c] == "Institute":
                        if c != 0:
                            if current_enitity_splitted[c - 1].endswith("ichen"):
                                wrong_ending = True
                                break
                            for c2 in range(c):
                                if current_enitity_splitted[c2][0].islower():
                                    wrong_ending = True
                                    break
                if wrong_ending:
                    continue

                # "-" should max appear twice
                if entity_strings[p].count("-") > 2:
                    continue

            # check if wordlength is long enough
            whitelist = ["für", "der", "des", "und", "&", "/", "1", "2", "3", "4", "I", "II", "III", "IV", "V", "VI", "i", "ii", "iii", "iv", "v", "vi", "-"]
            if is_first == False and org_number == 1:
                whitelist.append("of")
            if org_number == 2:
                whitelist.append("for")
            too_short = False
            for single_word in current_enitity_splitted:
                if single_word in whitelist:
                    continue
                if is_first:
                    if org_number == 0:
                        if len(single_word) == 4 or len(single_word) == 5:
                            if single_word.endswith("-"):
                                continue
                        if len(single_word) < 6:
                            too_short = True
                            break
                    elif org_number == 1 or org_number == 2:
                        if len(single_word) < 5:
                            too_short = True
                            break
                else:
                    if org_number == 0 or org_number == 2:
                        if len(single_word) < 2:
                            too_short = True
                            break
                    elif org_number == 1:
                        if len(single_word) < 3:
                            too_short = True
                            break
            if too_short:
                continue
            # if verb in string -> no legit name
            has_verb = False
            for single_word in current_enitity_splitted:
                tag_ger = tagger_ger.analyze(single_word)
        
                if tag_ger[1].startswith('V'):
                    has_verb = True
                    break
            if has_verb:
                continue
            # last word can't be an adjective
            last_word = current_enitity_splitted[-1]
            last_tag = tagger_ger.analyze(last_word)
            if last_tag[1].startswith('A'):
                continue
            if org_number == 1:
                # last word can't be a kon (KON) or special-char ($) or concat-word TRUNC
                if last_tag[1].startswith('KON') or last_tag[1].startswith('$') or last_tag[1].startswith('TRUNC'):
                    continue
            if org_number == 2:
                # last word can't be a kon (KON) or special-char ($) or concat-word TRUNC
                if last_tag[1].startswith('KON') or last_tag[1].startswith('$') or last_tag[1].startswith('TRUNC'):
                    continue
                # first word can't be an article (ART) or kon (KON) or special-char ($) or PPOSAT
                first_word = current_enitity_splitted[0]
                first_tag = tagger_ger.analyze(first_word)
                if first_tag[1].startswith('ART') or first_tag[1].startswith('KON') or first_tag[1].startswith('$') or first_tag[1].startswith('PPOSAT'):
                    continue

                # no "," infront of "Zentrum" or "Institut"
                pos_comma = entity_strings[p].find(",")
                if pos_comma != -1:
                    if pos_comma < entity_strings[p].find("Zentrum"):
                        continue
                if pos_comma != -1:
                    if pos_comma < entity_strings[p].find("Institut"):
                        continue
                # no "und" infront of "Zentrum" or "Institut"
                pos_und = entity_strings[p].find("und ")
                if pos_und != -1:
                    if pos_und < entity_strings[p].find("Zentrum"):
                        continue
                if pos_und != -1:
                    if pos_und < entity_strings[p].find("Institut"):
                        continue
            # no empty string
            if entity_strings[p] == "" or len(entity_strings[p]) == 0:
                continue
            if org_number == 0:
                # if word in front of fakultät -> has to end on an e -> "Medizinische/ Juristische Fakultät" and not "Medizinischen Fakultät"
                if is_first:
                    if current_enitity_splitted[0] != "Fakultät":
                        if not current_enitity_splitted[0].endswith("e"):
                            continue
                else:
                    if "Fakultät" in entity_strings[p]:
                        if current_enitity_splitted[0] != "Fakultät":
                            if not current_enitity_splitted[0].endswith("e"):
                                continue
                # filter out strings with known wrong words in it
                # blacklist
                if "Universität" in entity_strings[p] or "Institut" in entity_strings[p] or "Fach" in entity_strings[p] or "Fächer" in entity_strings[p]:
                    continue
            elif org_number == 1:
                # "Lehrstuhl" and " für" should just appear once
                if entity_strings[p].count("ehrstuhl") > 1 or entity_strings[p].count(" für") > 1:
                    continue
                # check wrong endings
                if entity_strings[p].endswith("-") or entity_strings[p].endswith("Lehrstuhl für Bürgerliches Recht") or entity_strings[p].endswith("Lehrstuhl für Öffentliches Recht") or entity_strings[p].endswith("Lehrstuhl für Wirtschaftsinformatik") or \
                        entity_strings[p].endswith("Lehrstuhl für Volkswirtschaftslehre") or entity_strings[p].endswith("Lehrstuhl für Software") or entity_strings[p].endswith("Lehrstuhl für Angewandte") or entity_strings[p].endswith("Lehrstuhl für Deutsche") or \
                        entity_strings[p].endswith("Lehrstuhl für Informatik") or entity_strings[p].endswith("Lehrstuhl für Didaktik") or entity_strings[p].endswith("Lehrstuhl für Neues") or entity_strings[p].endswith("Lehrstuhl für Christliche") or \
                        entity_strings[p].endswith("Lehrstuhl für Vergleichende") or entity_strings[p].endswith("Lehrstuhl Didaktik"):
                    continue
                # Blacklist
                # filter out strings with known wrong words in it
                # German so its Lehrstuhl not lehrstuhl
                if "niversität" in entity_strings[p] or "straße" in entity_strings[p] or "Fakultät" in entity_strings[p] or "lehrstuhl" in entity_strings[p] or "Lehrstuhl," in entity_strings[p] or "Lehrstuhl-" in entity_strings[p] or \
                        "Lehrstuhl -" in entity_strings[p] or "nstitut" in entity_strings[p] or "weitere" in entity_strings[p] or "Ausschreibung" in entity_strings[p] or "Masterarbeit" in entity_strings[p] or "Bachelorarbeit" in entity_strings[p] or \
                        " bei " in entity_strings[p] or "Student" in entity_strings[p] or "Newsletter" in entity_strings[p] or "Dipl" in entity_strings[p] or "Lehrstühle" in entity_strings[p] or "Betreuer" in entity_strings[p] or \
                        "entrum" in entity_strings[p] or "HK" in entity_strings[p] or "Hilfskraft" in entity_strings[p] or "IKS" in entity_strings[p]:
                    continue
            elif org_number == 2:
                # check wrong endings
                if entity_strings[p].endswith("-") or entity_strings[p].endswith("für") or entity_strings[p].endswith("for") or entity_strings[p].endswith("und"):
                    continue
                # check wrong startings
                if entity_strings[p].startswith("-") or entity_strings[p].startswith("für"):
                    continue
                # Blacklist
                # filter out strings with known wrong words in it
                # Zentrum not zentrum
                if "niversit" in entity_strings[p] or "Leiter" in entity_strings[p] or "Prof" in entity_strings[p] or "Direktor" in entity_strings[p] or "Organisationseinheit" in entity_strings[p] or "Wiki" in entity_strings[p] or "zentrum" in entity_strings[p] or \
                        "orlesung" in entity_strings[p] or "Startseite" in entity_strings[p] or "Einrichtung" in entity_strings[p] or "beide" in entity_strings[p] or "Report" in entity_strings[p] or "Projekt" in entity_strings[p] or "institut" in entity_strings[p] or \
                        "Jahre" in entity_strings[p] or " - " in entity_strings[p] or "Fakultät" in entity_strings[p] or "Stiftung" in entity_strings[p] or "An-Institut" in entity_strings[p] or " das " in entity_strings[p] or \
                        " den " in entity_strings[p] or "rofil" in entity_strings[p] or "Homepage" in entity_strings[p] or "eteiligt" in entity_strings[p] or "Besprechung" in entity_strings[p] or "Artikel" in entity_strings[p] or "ffiliated" in entity_strings[p] or \
                        "ssociated" in entity_strings[p] or "ielzahl" in entity_strings[p] or "Das" in entity_strings[p] or "Thema" in entity_strings[p] or "INSTITUT" in entity_strings[p] or "Unser" in entity_strings[p] or "Zum" in entity_strings[p] or \
                        "Lehrstuhl" in entity_strings[p] or "Chair" in entity_strings[p] or "Faculty" in entity_strings[p] or "Abteilung" in entity_strings[p] or "Department" in entity_strings[p]:
                    continue
                blacklist = ["Deutschen Institut", "Institute for Software"]
                if entity_strings[p] in blacklist:
                    continue
                # check wrong endings
                if entity_strings[p].endswith("Unsere") or entity_strings[p].endswith("unsere") or entity_strings[p].endswith("-") or entity_strings[p].endswith("und"):
                    continue
                # check wrong startings
                if entity_strings[p].startswith("Unsere") or entity_strings[p].startswith("unsere"):
                    continue
            # check if link is from wanted university
            if is_first:
                if link == None or link_req_short in link or link_req_long in link:
                    pass
                else:
                    continue
                # entity name is accepted -> load into elastic
                doc = {
                    "text": entity_strings[p],
                    "link": link,
                }
                es.index(index=index_name_Searching, id=counter_Entity, document=doc)
            else:
                if extra_links[p] == None or link_req_short in extra_links[p] or link_req_long in extra_links[p]:
                    pass
                else:
                    continue
                # entity name is accepted -> load into elastic
                doc = {
                    "text": entity_strings[p],
                    "link": extra_links[p],
                }
                es.index(index=index_name_Searching, id=counter_Entity, document=doc)
            counter_Entity += 1
        except:
            counter_Entity += 1
            continue

    return counter_Entity

def find_org(link_req_short, org_number, index_name_uni, index_name_Searching, es, index_name_result):
    print("First Round")

    tagger_ger = ht.HanoverTagger('morphmodel_ger.pgz')

    # get university domain
    aggs_get_timestamp = {
        "min_date": {
            "min": {
                "field": "timestamp"
            }
        }
    }
    aggs_timestamp = es.search(index=index_name_uni, aggregations=aggs_get_timestamp, size=0)
    timestamp = aggs_timestamp.get('aggregations').get('min_date').get('value_as_string')
    query_get_first = {
        "match": {
            "timestamp": timestamp
        }
    }
    query_timestamp = es.search(index=index_name_uni, query=query_get_first, size=1)
    link_req_long = query_timestamp.get('hits').get('hits')[0].get('_source').get('domain')

    counter_Entity = 0

    # create second index for searching operations
    mappings = {
        "properties": {
            "text": {"type": "keyword"},
            "link": {"type": "keyword"}
        }
    }
    if es.indices.exists(index=index_name_Searching):
        es.indices.delete(index=index_name_Searching)
    es.indices.create(index=index_name_Searching, mappings=mappings)

    print("Getting ids")

    ids = []
    query = {}

    if org_number == 0:
        query = {
            "dis_max": {
                "queries": [
                    {
                        "query_string": {
                            "query": "Fakultät",
                            "default_field": "content"
                        }
                    }
                ]
            }
        }
    elif org_number == 1:
        query = {
            "dis_max": {
                "queries": [
                    {
                        "query_string": {
                            "query": "Lehrstuhl",
                            "default_field": "content"
                        }
                    }, {
                        "query_string": {
                            "query": "Abteilung",
                            "default_field": "content"
                        }
                    }
                ]
            }
        }
    elif org_number == 2:
        query = {
            "dis_max": {
                "queries": [
                    {
                        "query_string": {
                            "query": "Institut",
                            "default_field": "content"
                        }
                    }, {
                        "query_string": {
                            "query": "Zentrum",
                            "default_field": "content"
                        }
                    }, {
                        "query_string": {
                            "query": "Institute",
                            "default_field": "content"
                        }
                    },
                ]
            }
        }

    docs_with_enitity = es.search(index=index_name_uni, query=query, size=500, sort=[{"timestamp": "asc"}])

    current_i_max = len(docs_with_enitity.get('hits').get('hits')) - 1
    # get ids from current query
    for hit in docs_with_enitity.get('hits').get('hits'):
        ids.append(hit.get('_id'))

    # while loop until all results are done
    while (current_i_max > 0):
        current_last_sort = docs_with_enitity.get('hits').get('hits')[current_i_max].get('sort')
        # get next result-page
        docs_with_enitity = es.search(index=index_name_uni, query=query, size=500, search_after=current_last_sort, sort=[{"timestamp": "asc"}])

        current_i_max = len(docs_with_enitity.get('hits').get('hits')) - 1

        for hit in docs_with_enitity.get('hits').get('hits'):
            ids.append(hit.get('_id'))

    print("Getting entity-names and links, checking them and loading them into Elasic")
    print("Needs some hours.")

    # go through all the docs from ids
    # get the word fakultät/ lehrstuhl/ institut with previous and following words
    # (examples: "Medizinische Fakultät", "Fakultät für Physik", "Fakultät für Angewandte Informatik", "Fakultät für Chemie und Biochemie")
    for id in ids:
        try:
            current_term = es.termvectors(index=index_name_uni, id=id, fields="content", term_statistics=False, field_statistics=False, payloads=False, positions=False, offsets=True)
            current_doc = es.get(index=index_name_uni, id=id)
            html_string = current_doc.get('_source').get('content')

            enitity = []

            if org_number == 0:
                fakul_deu = []
                if current_term.get('term_vectors').get('content').get('terms').get('fakultät') != None:
                    fakul_deu = current_term.get('term_vectors').get('content').get('terms').get('fakultät').get('tokens')

                if isinstance(fakul_deu, list):
                    enitity = enitity + fakul_deu
            elif org_number == 1:
                lehr_deu = []
                abt_deu = []

                if current_term.get('term_vectors').get('content').get('terms').get('lehrstuhl') != None:
                    lehr_deu = current_term.get('term_vectors').get('content').get('terms').get('lehrstuhl').get('tokens')
                if current_term.get('term_vectors').get('content').get('terms').get('abteilung') != None:
                    abt_deu = current_term.get('term_vectors').get('content').get('terms').get('abteilung').get('tokens')

                if isinstance(lehr_deu, list):
                    enitity = enitity + lehr_deu
                if isinstance(abt_deu, list):
                    enitity = enitity + abt_deu
            elif org_number == 2:
                inst_deu = []
                inst_eng = []
                zentrum_deu = []

                if current_term.get('term_vectors').get('content').get('terms').get('institut') != None:
                    inst_deu = current_term.get('term_vectors').get('content').get('terms').get('institut').get('tokens')
                if current_term.get('term_vectors').get('content').get('terms').get('zentrum') != None:
                    zentrum_deu = current_term.get('term_vectors').get('content').get('terms').get('zentrum').get('tokens')
                if current_term.get('term_vectors').get('content').get('terms').get('institute') != None:
                    inst_eng = current_term.get('term_vectors').get('content').get('terms').get('institute').get('tokens')

                if isinstance(inst_deu, list):
                    enitity = enitity + inst_deu
                if isinstance(zentrum_deu, list):
                    enitity = enitity + zentrum_deu
                if isinstance(inst_eng, list):
                    enitity = enitity + inst_eng

            

            for i in range(len(enitity)):
                try:
                    start = enitity[i].get('start_offset')
                    end = enitity[i].get('end_offset')
    
                    enitity_string = ''
                    for o in range(start, end):
                        enitity_string += html_string[o]
    
                    entity_strings = []

                    if org_number == 0:
                        # -1
                        fakul_words = getWordsBefore(start=start, html_string=html_string, word=enitity_string, number=2, without_comma=True)
                        if fakul_words not in entity_strings:
                            entity_strings.append(fakul_words)
                        # +2 +3 +4 +5 +6
                        for p in range(3, 8):
                            fakul_words = getWordsAfter(end=end, html_string=html_string, word=enitity_string, number=p, without_comma=True)
                            if fakul_words not in entity_strings:
                                entity_strings.append(fakul_words)
                    elif org_number == 1:
                        # +1 +2 +3 +4 +5 +6 +7 +8 +9 +10
                        for p in range(2, 12):
                            lehr_words = getWordsAfter(end=end, html_string=html_string, word=enitity_string, number=p, without_comma=False)
                            if lehr_words not in entity_strings:
                                entity_strings.append(lehr_words)
                    elif org_number == 2:
                        # -1 -2
                        for p in range(2, 4):
                            inst_words = getWordsBefore(start=start, html_string=html_string, word=enitity_string, number=p, without_comma=True)
                            if inst_words not in entity_strings:
                                entity_strings.append(inst_words)
                        # +2 +3 +4 +5 +6
                        for p in range(3, 8):
                            inst_words = getWordsAfter(end=end, html_string=html_string, word=enitity_string, number=p, without_comma=True)
                            if inst_words not in entity_strings:
                                entity_strings.append(inst_words)

                        # -1 +1
                        inst_words = getWordsBefore(start=start, html_string=html_string, word=enitity_string, number=2, without_comma=True)
                        inst_words = getWordsAfter(end=end, html_string=html_string, word=inst_words, number=2, without_comma=True)
                        if inst_words not in entity_strings:
                            entity_strings.append(inst_words)

                        # -1 -2 with +2 +3 +4 +5 +6
                        for p in range(3, 8):
                            for l in range(2, 4):
                                inst_words = getWordsBefore(start=start, html_string=html_string, word=enitity_string, number=l, without_comma=True)
                                inst_words = getWordsAfter(end=end, html_string=html_string, word=inst_words, number=p, without_comma=True)
                                if inst_words not in entity_strings:
                                    entity_strings.append(inst_words)
    
                    # get the link to "fakultät/lehrstuhl/institut" if existing
                    link = None
    
                    current_xpath_tree = etree.HTML(html_string)
    
                    start_block = -1
                    end_block = -1
    
                    while start != 0:
                        start = start - 1
                        if html_string[start] == ">":
                            start_block = start + 1
                            break
                    while end != len(html_string):
                        if html_string[end] == "<":
                            end_block = end
                            break
                        end = end + 1
    
                    if start_block == -1 or end_block == -1:
                        pass
                    else:
                        search = html_string[start_block:end_block]
                        search = html.unescape(search)
    
                        elems = current_xpath_tree.xpath('//*[contains(text(), "' + search + '")]')
                        links = []
    
                        for elem in elems:
                            current_path = elem.getroottree().getpath(elem)
    
                            while True:
                                link_path = current_path + "/@href"
                                elem_link = current_xpath_tree.xpath(link_path)
                                if elem_link == []:
                                    current_path = current_path[0: current_path.rfind("/")]
                                    if len(current_path) == 0:
                                        break
                                else:
                                    links.append(elem_link[0])
                                    break
    
                        # get link out of links with highest appearance -> if appearance is the same-> take shortest link
                        links_2 = []
                        links_app = []
                        for l in links:
                            # check if link is existing and absolute or relative
                            if l == None:
                                continue
                            elif l == "":
                                continue
                            elif bool(urlparse(l).netloc):
                                pass  # is absolute -> do nothing
                            else:
                                # link relativ -> make absolute
                                # use urllib
                                l = urljoin(current_doc.get('_source').get('url'), l)
    
                            if l not in links_2:
                                links_2.append(l)
                                links_app.append(1)
                            else:
                                index_link = links_2.index(l)
                                links_app[index_link] = links_app[index_link] + 1
    
                        highest = 0
                        highest_counter = 0
                        for app in links_app:
                            if app > highest:
                                highest = app
                                highest_counter = 1
                            elif app == highest:
                                highest_counter = highest_counter + 1
    
                        if highest_counter == 1:
                            index_link = links_app.index(highest)
                            link = links_2[index_link]
                        elif highest_counter > 1:
                            indices_link = [pos for pos, x in enumerate(links_app) if x == highest]
                            for indi in indices_link:
                                if link == None:
                                    link = links_2[indi]
                                elif len(link) > len(links_2[indi]):
                                    link = links_2[indi]
    
                    # add new doc to searching index
                    counter_Entity = check_entity_strings_and_upload(link_req_short=link_req_short, link_req_long=link_req_long, org_number=org_number, index_name_Searching=index_name_Searching, es=es, entity_strings=entity_strings, counter_Entity=counter_Entity, tagger_ger=tagger_ger, link=link, is_first=True, extra_links=None)
                    
                except:
                    continue
        except:
            continue

    print("Aggregation")

    # check for duplicated names
    es.indices.refresh(index=index_name_Searching)

    query_body_aggregation = {}

    if org_number == 0:
        query_body_aggregation = {
            "duplicateNames": {
                "terms": {
                    "field": "text",
                    "min_doc_count": 70,
                    "size": 10000
                }
            }
        }
    elif org_number == 1 or org_number == 2:
        query_body_aggregation = {
            "duplicateNames": {
                "terms": {
                    "field": "text",
                    "min_doc_count": 5,
                    "size": 10000
                }
            }
        }

    result_aggregation = es.search(index=index_name_Searching, aggregations=query_body_aggregation, size=10000)

    aggs = result_aggregation.get('aggregations').get('duplicateNames').get('buckets')

    # sort entities
    entities_sorted = []
    entities_appearance = []
    # filter out sub-names
    # example:
    # 1
    # Faculty of Business Administration and Economics -> correct and complete
    # Faculty of Business -> missing some parts -> filter it out
    # 2
    # Fakultät für Ingenieurwissenschaften  -> correct and complete
    # Fakultät für Ingenieurwissenschaften erschienen -> has to much -> filter it out
    for i in range(len(aggs)):
        if org_number == 1:
            if aggs[i].get('doc_count') < 50: # if doc_count under 50 -> name has to have a für
                splitted_key = aggs[i].get('key').split(" ")
                if len(splitted_key) > 2:
                    if splitted_key[1] == "für":
                        pass
                    else:
                        continue
                else:
                    continue
        if i == 0:
            entities_sorted.append(aggs[i].get('key'))
            entities_appearance.append(aggs[i].get('doc_count'))
        elif aggs[i].get('key') in entities_sorted:
            continue
        else:
            is_inserted = False
            for o in range(len(entities_sorted)):
                if entities_sorted[o].startswith(aggs[i].get('key')) or aggs[i].get('key').startswith(entities_sorted[o]) or entities_sorted[o].endswith(aggs[i].get('key')) or aggs[i].get('key').endswith(entities_sorted[o]):
                    is_inserted = True
                    if entities_appearance[o] > aggs[i].get('doc_count'):
                        pass
                    elif entities_appearance[o] < aggs[i].get('doc_count'):
                        entities_appearance[o] = aggs[i].get('doc_count')
                        entities_sorted[o] = aggs[i].get('key')
                    elif entities_appearance[o] == aggs[i].get('doc_count'):
                        if len(entities_sorted[o]) >= len(aggs[i].get('key')):
                            pass
                        else:
                            entities_appearance[o] = aggs[i].get('doc_count')
                            entities_sorted[o] = aggs[i].get('key')
                else:
                    if org_number == 1 or org_number == 2:
                        if len(entities_sorted[o]) > len(aggs[i].get('key')):
                            if aggs[i].get('key') in entities_sorted[o]:
                                is_inserted = True
                        elif len(entities_sorted[o]) < len(aggs[i].get('key')):
                            if entities_sorted[o] in aggs[i].get('key'):
                                is_inserted = True
                                entities_appearance[o] = aggs[i].get('doc_count')
                                entities_sorted[o] = aggs[i].get('key')
            if not is_inserted:
                if org_number == 0 or org_number == 2:
                    entities_sorted.append(aggs[i].get('key'))
                    entities_appearance.append(aggs[i].get('doc_count'))
                elif org_number == 1:
                    if aggs[i].get('doc_count') >= 50:
                        entities_sorted.append(aggs[i].get('key'))
                        entities_appearance.append(aggs[i].get('doc_count'))
                    else:
                        splitted_lehrs = aggs[i].get('key').split(" ")
                        if len(splitted_lehrs) < 3:
                            continue
                        elif splitted_lehrs[1] == "für":
                            entities_sorted.append(aggs[i].get('key'))
                            entities_appearance.append(aggs[i].get('doc_count'))
                        else:
                            entities_sorted.append(aggs[i].get('key'))
                            entities_appearance.append(aggs[i].get('doc_count'))

    entities_without_double = []
    for i in range(len(entities_sorted)):
        if entities_sorted[i] in entities_without_double:
            continue
        else:
            entities_without_double.append(entities_sorted[i])
    entities_sorted = entities_without_double

    entities_without_double_advanced = []
    entities_without_double_advanced_2 = []
    for i in range(len(entities_sorted)):
        if " für " in entities_sorted[i]:
            entities_without_double_advanced.append(entities_sorted[i])
            entities_without_double_advanced_2.append(entities_sorted[i].replace(" für ", " "))
    for i in range(len(entities_sorted)):
        if " für " not in entities_sorted[i]:
            if entities_sorted[i] not in entities_without_double_advanced_2:
                entities_without_double_advanced.append(entities_sorted[i])
    entities_sorted = entities_without_double_advanced

    # get links for duplications
    entities = []
    entities_Link = []
    for i in range(len(entities_sorted)):
        try:
            entities.append(entities_sorted[i])

            query_get_link = {
                "query_string": {
                    "query": entities_sorted[i],
                    "default_field": "text"
                }
            }
            aggs_get_link = {
                "duplicateWords": {
                    "terms": {
                        "field": "link",
                        "min_doc_count": 1,
                        "size": 10000
                    }
                }
            }

            result_link_search = es.search(index=index_name_Searching, query=query_get_link, aggregations=aggs_get_link, size=10000)

            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                entities_Link.append(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('key'))
            else:
                entities_Link.append(None)
        except:
            continue

    # delete searching-index
    es.indices.delete(index=index_name_Searching)

    entities_first_round = entities.copy()
    entities_link_first_round = entities_Link.copy()

    if org_number == 0:
        print("Number of found faculties: " + str(len(entities)))
    elif org_number == 1:
        print("Number of found chairs: " + str(len(entities)))
    elif org_number == 2:
        print("Number of found institutes: " + str(len(entities)))

    print("Second Round")
    print("Getting Shoulds")

    # create searching index again for second part
    # has to be empty
    es.indices.create(index=index_name_Searching, mappings=mappings)

    if org_number == 0:
        appended_fakus = []
        for a in entities:
            if " für " in a:
                a_2 = a[a.find(" für ") + 5:]
                appended_fakus.append(a_2)
        for a in entities:
            is_in = False
            for a_2 in appended_fakus:
                if a_2 in a:
                    is_in = True
                    break
            if is_in:
                continue
            else:
                appended_fakus.append(a)
        entities = appended_fakus

    sh = []
    for a in entities:
        sh.append({"match_phrase": {"content": a}})

    q = {}

    if org_number == 0:
        q["bool"] = {"should": sh, "minimum_should_match": "95%"}
    elif org_number == 1:
        q["bool"] = {"should": sh, "minimum_should_match": 3}
    elif org_number == 2:
        q["bool"] = {"should": sh, "minimum_should_match": "100%"} # doesn't makes sense -> institute lists have normaly 2 - 5 entries -> "minimum_should_match": 3 doesn't scale because of to many institutes

    print("Checking Shoulds results")
    

    docs_with_multiple_entities = es.search(index=index_name_uni, query=q, size=500, sort=[{"timestamp": "asc"}])

    current_multiple_i_max = len(docs_with_multiple_entities.get('hits').get('hits')) - 1

    extra_entities = []
    extra_links = []

    try:
        # while loop until all results are done
        while (current_multiple_i_max > 0):
            # for each document with multiple occurences of already found entities search for structure-patterns
            for i in range((current_multiple_i_max + 1)):
                current_html_string = docs_with_multiple_entities.get('hits').get('hits')[i].get('_source').get('content')

                try:
                    current_xpath_tree = etree.HTML(current_html_string)
                except:
                    continue
                structure = []

                for current_entity in entities:
                    if current_entity == None:
                        continue
                    if current_entity == "":
                        continue
                    try:
                        elems = current_xpath_tree.xpath('//*[contains(text(), "' + current_entity + '")]')
                    except:
                        continue

                    for elem in elems:
                        struct = elem.getroottree().getpath(elem)
                        structure.append(struct)

                firsts = []
                seconds = []

                max_len = len(structure)
                outer_len = 0
                while outer_len < max_len:
                    outer_struct = structure[outer_len]
                    outer_len += 1
                    inner_len = outer_len
                    while inner_len < max_len:
                        inner_struct = structure[inner_len]
                        inner_len += 1

                        if (outer_struct == inner_struct):
                            continue
                        elif len(outer_struct) == len(inner_struct):
                            counter_diff = 0
                            last_o = -1
                            for o in range(len(outer_struct)):
                                if outer_struct[o] != inner_struct[o]:
                                    counter_diff += 1
                                    last_o = o
                            if counter_diff == 1:
                                if outer_struct[last_o].isnumeric() and inner_struct[last_o].isnumeric():
                                    if outer_struct.find("]", last_o) < outer_struct.find("[", last_o) or (outer_struct.find("]", last_o) != -1 and outer_struct.find("[", last_o) == -1):
                                        if inner_struct.find("]", last_o) < inner_struct.find("[", last_o) or (inner_struct.find("]", last_o) != -1 and inner_struct.find("[", last_o) == -1):
                                            if outer_struct.rfind("[", 0, last_o) > outer_struct.rfind("]", 0, last_o) or (outer_struct.rfind("[", 0, last_o) != -1 and outer_struct.rfind("]", 0, last_o) == -1):
                                                if inner_struct.rfind("[", 0, last_o) > inner_struct.rfind("]", 0, last_o) or (inner_struct.rfind("[", 0, last_o) != -1 and inner_struct.rfind("]", 0, last_o) == -1):
                                                    first_part = outer_struct[0:outer_struct.rfind("[", 0, last_o) + 1]
                                                    second_part = outer_struct[outer_struct.find("]", last_o):]
                                                    firsts.append(first_part)
                                                    seconds.append(second_part)
                        elif len(outer_struct) - len(inner_struct) == 1 or len(outer_struct) - len(inner_struct) == -1:
                            struct_short = ""
                            struct_long = ""
                            if len(outer_struct) < len(inner_struct):
                                struct_short = outer_struct
                                struct_long = inner_struct
                            else:
                                struct_short = inner_struct
                                struct_long = outer_struct
                            for o in range(len(struct_short)):
                                if struct_short[o] != struct_long[o]:
                                    if struct_short[o].isnumeric() and struct_long[o].isnumeric():
                                        if struct_short[o + 1] == "]" and struct_long[o + 1].isnumeric():
                                            if struct_short[o + 1:] == struct_long[o + 2:]:
                                                first_part = struct_short[0:struct_short.rfind("[", 0, o + 1) + 1]
                                                second_part = struct_short[o + 1:]
                                                firsts.append(first_part)
                                                seconds.append(second_part)
                                    if struct_short[o] == "]" and struct_long[o].isnumeric():
                                        if struct_short[o:] == struct_long[o + 1:]:
                                            first_part = struct_short[0:struct_short.rfind("[", 0, o) + 1]
                                            second_part = struct_short[o:]
                                            firsts.append(first_part)
                                            seconds.append(second_part)
                                    break

                # now we got the html_string-paths to the searched elements
                # get neighbours out
                for o in range(len(firsts)):
                    counter_xpath = 1
                    while True:
                        current_path = "/" + firsts[o] + str(counter_xpath) + seconds[o] + "/text()"
                        found = current_xpath_tree.xpath(current_path)
                        counter_xpath += 1
                        if found == []:
                            break
                        else:
                            found = found[0]

                            # if found string is to long -> its no name -> its free text -> overjump
                            if len(found) > 125:
                                break

                            extra_entities.append(found)

                            current_path = current_path[0:-7]

                            while True:
                                link_path = current_path + "/@href"
                                elem_link = current_xpath_tree.xpath(link_path)
                                if elem_link == []:
                                    current_path = current_path[0: current_path.rfind("/")]
                                    if len(current_path) == 0:
                                        break
                                else:
                                    extra_links.append(elem_link[0])

                                    # check if link is existing and absolute or relative
                                    if extra_links[-1] == None:
                                        continue
                                    elif extra_links[-1] == "":
                                        continue
                                    elif bool(urlparse(extra_links[-1]).netloc):
                                        pass  # is absolute -> do nothing
                                    else:
                                        # link relativ -> make absolute
                                        # use urllib
                                        l = urljoin(docs_with_multiple_entities.get('hits').get('hits')[i].get('_source').get('url'), extra_links[-1])
                                    break

            current_multiple_last_sort = docs_with_multiple_entities.get('hits').get('hits')[current_multiple_i_max].get('sort')
            # get next result-page
            docs_with_multiple_entities = es.search(index=index_name_uni, query=q, size=500, search_after=current_multiple_last_sort, sort=[{"timestamp": "asc"}])
            
            current_multiple_i_max = len(docs_with_multiple_entities.get('hits').get('hits')) - 1
    except:
        pass

    print("Checking extra entities")
    counter_Entity = check_entity_strings_and_upload(link_req_short=link_req_short, link_req_long=link_req_long, org_number=org_number, index_name_Searching=index_name_Searching, es=es, entity_strings=extra_entities, counter_Entity=counter_Entity, tagger_ger=tagger_ger, link=None, is_first=False, extra_links=extra_links)

    print("Aggregation")

    query_body_aggregation = {}

    if org_number == 0:
        query_body_aggregation = {
            "duplicateNames": {
                "terms": {
                    "field": "text",
                    "min_doc_count": 10,
                    "size": 10000
                }
            }
        }
    elif org_number == 1:
        query_body_aggregation = {
            "duplicateNames": {
                "terms": {
                    "field": "text",
                    "min_doc_count": 3,
                    "size": 10000
                }
            }
        }
    elif org_number == 2:
        query_body_aggregation = {
            "duplicateNames": {
                "terms": {
                    "field": "text",
                    "min_doc_count": 40,
                    "size": 10000
                }
            }
        }

    result_aggregation = es.search(index=index_name_Searching, aggregations=query_body_aggregation, size=10000)

    aggs = result_aggregation.get('aggregations').get('duplicateNames').get('buckets')

    # get names and links for duplications
    extra_entities = []
    extra_entities_Link = []
    for i in range(len(aggs)):
        try:
            if org_number == 1:
                if aggs[i].get('doc_count') < 100:  # if doc_count under 50 -> name has to have a für
                    splitted_key = aggs[i].get('key').split(" ")
                    if len(splitted_key) > 2:
                        if splitted_key[1] == "für":
                            pass
                        else:
                            continue
                    else:
                        continue

            extra_entities.append(aggs[i].get('key'))

            query_get_link = {
                "query_string": {
                    "query": aggs[i].get('key'),
                    "default_field": "text"
                }
            }
            aggs_get_link = {
                "duplicateWords": {
                    "terms": {
                        "field": "link",
                        "min_doc_count": 1,
                        "size": 10000
                    }
                }
            }

            result_link_search = es.search(index=index_name_Searching, query=query_get_link, aggregations=aggs_get_link, size=10000)

            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                extra_entities_Link.append(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('key'))
            else:
                extra_entities_Link.append(None)
        except:
            continue

    # delete searching-index
    es.indices.delete(index=index_name_Searching)

    if org_number == 0:
        print("Number of extra found faculties: " + str(len(extra_entities)))
    elif org_number == 1:
        print("Number of extra found chairs: " + str(len(extra_entities)))
    elif org_number == 2:
        print("Number of extra found institutes: " + str(len(extra_entities)))

    # now upload found results into elastic
    print("Loading result-entities into Elastic")
    entities_all = entities_first_round
    entities_link_all = entities_link_first_round

    for i in range(len(extra_entities)):
        if extra_entities[i] not in entities_all:
            entities_all.append(extra_entities[i])
            if i >= len(extra_entities_Link):
                entities_link_all.append(None)
                continue
            entities_link_all.append(extra_entities_Link[i])

    for i in range(len(entities_all)):
        try:
            # create result doc
            result_dict = {
                "name": entities_all[i],
                "link": entities_link_all[i],
                "uni": link_req_short
            }

            if org_number == 0:
                result_dict["type"] = "faculty"
            elif org_number == 1:
                result_dict["type"] = "chair"
            elif org_number == 2:
                result_dict["type"] = "institute"

            # upload doc
            id = ""
            if org_number == 0:
                id = "" + link_req_short + "_" + "faculty" + "_" + entities_all[i]
            elif org_number == 1:
                id = "" + link_req_short + "_" + "chair" + "_" + entities_all[i]
            elif org_number == 2:
                id = "" + link_req_short + "_" + "institute" + "_" + entities_all[i]
            
            id = id.replace(" ", "_")
            es.index(index=index_name_result, id=id, document=result_dict)
        except:
            pass

def create_result_index(es, index_name_result):
    if not es.indices.exists(index=index_name_result):
        settings = {
            "analysis": {
                "analyzer": {
                    "searchabilityAnalyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "asciifolding"
                        ]
                    }
                }
            }
        }
        mappings = {
            "properties": {
                "name": {
                    "type": "text",
                    "analyzer": "searchabilityAnalyzer",
                    "search_analyzer": "searchabilityAnalyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 250
                        }
                    }
                },
                "link": {
                    "type": "text",
                    "analyzer": "searchabilityAnalyzer",
                    "search_analyzer": "searchabilityAnalyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 250
                        }
                    }
                },
                "uni": {
                    "type": "text",
                    "analyzer": "searchabilityAnalyzer",
                    "search_analyzer": "searchabilityAnalyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 10
                        }
                    }
                },
                "type": {
                    "type": "text",
                    "analyzer": "searchabilityAnalyzer",
                    "search_analyzer": "searchabilityAnalyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 15
                        }
                    }
                },
                "upper": {
                    "type": "text",
                    "analyzer": "searchabilityAnalyzer",
                    "search_analyzer": "searchabilityAnalyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 250
                        }
                    }
                }
            }
        }
        es.indices.create(index=index_name_result, mappings=mappings, settings=settings)

def connections(es, index_name_result, index_name_uni, link_req_short):
    print("Calculating faculty uppers")
    # getting all faculty docs
    query_faculty = {
        "match": {
            "type": "faculty"
        }
    }

    docs_faculty = es.search(index=index_name_result, query=query_faculty, size=10000)
    # updating faculties
    update_body = {
        "doc": {
            "upper": link_req_short
        }
    }

    for f in docs_faculty.get('hits').get('hits'):
        es.update(index=index_name_result, id=f.get('_id'), body=update_body)

    # getting faculty links
    fs = []
    for f in docs_faculty.get('hits').get('hits'):
        if f.get('_source').get('link') not in fs and not f.get('_source').get('link') == None:
            fs.append(f.get('_source').get('link'))

    for what in range(2):
        query = {}

        if what == 0:
            print("Calculating chair uppers")

            query = {
                "match": {
                    "type": "chair"
                }
            }

        if what == 1:
            print("Calculating institute uppers")

            query = {
                "match": {
                    "type": "institute"
                }
            }

        docs = es.search(index=index_name_result, query=query, size=10000)

        for c in docs.get('hits').get('hits'):
            try:
                current_name = c.get('_source').get('name')

                query_inner = {
                    "match_phrase": {
                        "content": current_name
                    }
                }
                aggs_inner = {
                    "aggs": {
                        "terms": {
                            "size": 10000,
                            "field": "url"
                        }
                    }
                }

                docs_inner = es.search(index=index_name_uni, query=query_inner, aggregations=aggs_inner, size=0)

                ls = []
                ls_count= []

                for b in docs_inner.get('aggregations').get('aggs').get('buckets'):
                    till = b.get('key').find("/", b.get('key').find("/", 8) + 1 ) + 1
                    if till == -1 or till == 0:
                        till = b.get('key').find("/", 8) + 1
                    current = b.get('key')[0:  till]
                    if current not in ls:
                        if current != None:
                            ls.append(current)
                            ls_count.append(1)
                    else:
                        i = ls.index(current)
                        ls_count[i] = ls_count[i] + 1

                current_best = 0
                current_link = ""
                multiple = 0

                for l in ls:
                    for f in fs:
                        counter = 0

                        if len(l) > len(f):
                            for i in range(len(f)):
                                if l[i] == f[i]:
                                    counter = counter + 1
                                else:
                                    break
                        else:
                            for i in range(len(l)):
                                if l[i] == f[i]:
                                    counter = counter + 1
                                else:
                                    break
                        
                        if counter > current_best:
                            current_best = counter
                            current_link = f
                            multiple = 0
                        elif counter == current_best:
                            if current_link != f:
                                multiple = multiple + 1

                if multiple != 0:
                    query_get_faculty_name = {
                        "match": {
                            "link": current_link
                        }
                    }
                    docs_faculty_name = es.search(index=index_name_result, query=query_get_faculty_name, size=1)

                    f_name = docs_faculty_name.get('hits').get('hits')[0].get('_source').get('name')

                    update_body = {
                        "doc": {
                            "upper": f_name
                        }
                    }

                    es.update(index=index_name_result, id=c.get('_id'), body=update_body)
            except Exception as e:
                print(e)
                pass


def org_miner (rawdata_index_name, es):
    print("Org_Miner starting")

    index_name_uni = rawdata_index_name
    index_name_f_Searching = "searching_faculties_temp"
    index_name_l_Searching = "searching_lehrshuhl_temp"
    index_name_i_Searching = "searching_institutes_temp"
    
    index_name_result = "org"

    link_req_short = rawdata_index_name[rawdata_index_name.rfind("-") + 1:]

    index_name_f_Searching = index_name_f_Searching + "-" + link_req_short
    index_name_l_Searching = index_name_l_Searching + "-" + link_req_short
    index_name_i_Searching = index_name_i_Searching + "-" + link_req_short
    
    index_name_result = index_name_result + "-" + link_req_short

    print("Creating result index")
    create_result_index(es=es, index_name_result=index_name_result)

    # fakultät = 0
    # lehrstuhl = 1
    # institut = 2
    print("Org_Miner starting faculties")
    find_org(link_req_short=link_req_short, org_number=0, index_name_uni=index_name_uni, index_name_Searching=index_name_f_Searching, es=es, index_name_result=index_name_result)
    print("Org_Miner starting chairs")
    find_org(link_req_short=link_req_short, org_number=1, index_name_uni=index_name_uni, index_name_Searching=index_name_l_Searching, es=es, index_name_result=index_name_result)
    print("Org_Miner starting institutes")
    find_org(link_req_short=link_req_short, org_number=2, index_name_uni=index_name_uni, index_name_Searching=index_name_i_Searching, es=es, index_name_result=index_name_result)

    print("Calculating Connections for all Orgs")
    connections(es=es, index_name_result=index_name_result, index_name_uni=index_name_uni, link_req_short=link_req_short)

    print("Org_Miner finished")
    

