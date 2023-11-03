from elasticsearch import Elasticsearch
from lxml import etree
import html
from HanTa import HanoverTagger as ht
from urllib.parse import urljoin
from urllib.parse import urlparse

# start elasticsearch-connection
# local
#es = Elasticsearch({'host': 'localhost', 'port': 9200, 'scheme': 'https'}, basic_auth=('elastic', 'elastic'), verify_certs=False, ssl_show_warn=False)
# uni-server
es = Elasticsearch({'host':'wom.handte.org', 'port': 443, 'path_prefix':'elastic', 'scheme':'https'},  basic_auth=('wom', 'H7kSk2~5GnybwE{}J4jdPj)qS74&tbXBK-b))+GN'), request_timeout=60, max_retries=5, retry_on_timeout=True)

index_name_uni = ""
index_name_Searching = "searching_institutes_temp"


def check_elastic():
    if not es.ping():
        raise Exception("No connection to Elasticsearch")


def getWordsBefore(start, html_string, word, number):
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
            if html_string[position] == '(' or html_string[position] == ')' or html_string[position] == '.' or html_string[position] == '!' or html_string[position] == '?' or html_string[position] == ':' or html_string[position] == '>' or html_string[position] == '<' or html_string[position] == '"' or html_string[position] == '“':
                break
            word = html_string[position] + word

    word = html.unescape(word)
    word = word.replace("–", "-")
    word = word.replace(" ", " ")
    return word


def getWordsAfter(end, html_string, word, number):
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
            if html_string[position] == '(' or html_string[position] == ')' or html_string[position] == '.' or html_string[position] == '!' or html_string[position] == '?' or html_string[position] == ':' or html_string[position] == '>' or html_string[position] == '"' or html_string[position] == '“' or html_string[position] == ',':
                break
            if html_string[position] == '0' or html_string[position] == '1' or html_string[position] == '2' or html_string[position] == '3' or html_string[position] == '4' or html_string[position] == '5' or html_string[position] == '6' or html_string[position] == '7' or html_string[position] == '8' or html_string[position] == '9':
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


def find_institutes(link_req_short):
    tagger_ger = ht.HanoverTagger('morphmodel_ger.pgz')
    counter_instis = 0

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

    # get ids from sides with "Institut" or "institute"
    ids = []

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

    docs_with_inst = es.search(index=index_name_uni, query=query, size=500, sort=[{"timestamp": "asc"}])

    current_i_max = len(docs_with_inst.get('hits').get('hits')) - 1
    # get ids from current query
    for hit in docs_with_inst.get('hits').get('hits'):
        ids.append(hit.get('_id'))

    # while loop until all results are done
    while (current_i_max >= 499):
        current_last_sort = docs_with_inst.get('hits').get('hits')[current_i_max].get('sort')
        # get next result-page
        docs_with_inst = es.search(index=index_name_uni, query=query, size=500, search_after=current_last_sort, sort=[{"timestamp": "asc"}])

        current_i_max = len(docs_with_inst.get('hits').get('hits')) - 1
        for hit in docs_with_inst.get('hits').get('hits'):
            ids.append(hit.get('_id'))

    # go through all the docs from ids
    # get the word Institut/ institute with previous and following words
    # -1 +2 +3 +4 +5 +6
    for id in ids:
        try:
            current_term = es.termvectors(index=index_name_uni, id=id, fields="content", term_statistics=False, field_statistics=False, payloads=False, positions=False, offsets=True)
            current_doc = es.get(index=index_name_uni, id=id)
            html_string = current_doc.get('_source').get('content')

            inst_deu = []
            inst_eng = []
            zentrum_deu = []
            inst = []

            if current_term.get('term_vectors').get('content').get('terms').get('institut') != None:
                inst_deu = current_term.get('term_vectors').get('content').get('terms').get('institut').get('tokens')
            if current_term.get('term_vectors').get('content').get('terms').get('zentrum') != None:
                zentrum_deu = current_term.get('term_vectors').get('content').get('terms').get('zentrum').get('tokens')
            if current_term.get('term_vectors').get('content').get('terms').get('institute') != None:
                inst_eng = current_term.get('term_vectors').get('content').get('terms').get('institute').get('tokens')

            if isinstance(inst_deu, list):
                inst = inst + inst_deu
            if isinstance(zentrum_deu, list):
                inst = inst + zentrum_deu
            if isinstance(inst_eng, list):
                inst = inst + inst_eng

            for i in range(len(inst)):
                try:
                    start = inst[i].get('start_offset')
                    end = inst[i].get('end_offset')

                    inst_string = ''
                    for o in range(start, end):
                        inst_string += html_string[o]

                    inst_strings = []

                    # -1 -2
                    for p in range(2, 4):
                        inst_words = getWordsBefore(start=start, html_string=html_string, word=inst_string, number=p)
                        if inst_words not in inst_strings:
                            inst_strings.append(inst_words)
                    # +2 +3 +4 +5 +6
                    for p in range(3, 8):
                        inst_words = getWordsAfter(end=end, html_string=html_string, word=inst_string, number=p)
                        if inst_words not in inst_strings:
                            inst_strings.append(inst_words)

                    # -1 +1
                    inst_words = getWordsBefore(start=start, html_string=html_string, word=inst_string, number=2)
                    inst_words = getWordsAfter(end=end, html_string=html_string, word=inst_words, number=2)
                    if inst_words not in inst_strings:
                        inst_strings.append(inst_words)

                    # -1 -2 with +2 +3 +4 +5 +6
                    for p in range(3, 8):
                        for l in range(2, 4):
                            inst_words = getWordsBefore(start=start, html_string=html_string, word=inst_string, number=l)
                            inst_words = getWordsAfter(end=end, html_string=html_string, word=inst_words, number=p)
                            if inst_words not in inst_strings:
                                inst_strings.append(inst_words)

                    # get the link to "Institut" if existing
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
                    for p in range(len(inst_strings)):
                        try:
                            while inst_strings[p].startswith(" "):
                                inst_strings[p] = inst_strings[p][1:]
                            while inst_strings[p].endswith(" ") or inst_strings[p].endswith(","):
                                inst_strings[p] = inst_strings[p][:-1]
                            # no special chars
                            if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234& -,.üöäÜÖÄ' for c in inst_strings[p]):
                                continue
                            if "  " in inst_strings[p] or '--' in inst_strings[p]:
                                continue
                            #if "„" in inst_strings[p] or "  " in inst_strings[p] or "$" in inst_strings[p] or "=" in inst_strings[p] or "'" in inst_strings[p] or "|" in inst_strings[p] or '"' in inst_strings[p] or "#" in inst_strings[p] or "/" in inst_strings[p] or ";" in inst_strings[p] or "\\" in inst_strings[p]: # or "" in inst_strings[p]
                            #    continue
                            if "Zentrum" in inst_strings[p]:
                                if "Zentrum für" not in inst_strings[p]:
                                    if not inst_strings[p].endswith("Zentrum"):
                                        continue
                            if "Institute" in inst_strings[p]:
                                if "Institute for" not in inst_strings[p]:
                                    continue
                            if "Institut" in inst_strings[p] and "Institute" not in inst_strings[p]:
                                if "Institut für" not in inst_strings[p]:
                                    if not inst_strings[p].endswith("Institut"):
                                        continue

                            if "für" in inst_strings[p]:
                                if "für " not in inst_strings[p]:
                                    inst_strings[p] = inst_strings[p].replace("für", "für ")

                            # string should have more than just 1 word
                            current_inst_splitted = inst_strings[p].split(" ")
                            if len(current_inst_splitted) < 2:
                                continue

                            wrong_ending = False
                            for c in range(len(current_inst_splitted)):
                                if current_inst_splitted[c] == "Zentrum" or current_inst_splitted[c] == "Institut" or current_inst_splitted[c] == "Institute":
                                    if c != 0:
                                        if current_inst_splitted[c - 1].endswith("ichen"):
                                            wrong_ending = True
                                            break
                                        for c2 in range(c):
                                            if current_inst_splitted[c2][0].islower():
                                                wrong_ending = True
                                                break
                            if wrong_ending:
                                continue

                            # check if wordlength is long enough
                            whitelist = ["für", "der", "des", "und", "&", "1", "2", "3", "4", "I", "II", "III", "IV", "i", "ii", "iii", "iv", "-", "for"]
                            too_short = False
                            for single_word in current_inst_splitted:
                                if single_word in whitelist:
                                    continue
                                if len(single_word) < 5:
                                    too_short = True
                                    break
                            if too_short:
                                continue
                            # if verb in string -> no legit name
                            has_verb = False
                            for single_word in current_inst_splitted:
                                tag_ger = tagger_ger.analyze(single_word)

                                if tag_ger[1].startswith('V'):
                                    has_verb = True
                                    break
                            if has_verb:
                                continue
                            # "-" and " für" should max appear twice
                            if inst_strings[p].count("-") > 2:
                                continue
                            # last word can't be an adjective (ADJ) or article (ART) or kon (KON) or special-char ($) or concat-word TRUNC
                            last_word = current_inst_splitted[-1]
                            last_tag = tagger_ger.analyze(last_word)
                            if last_tag[1].startswith('A') or last_tag[1].startswith('KON') or last_tag[1].startswith('$') or last_tag[1].startswith('TRUNC'):
                                continue
                            # first word can't be an article (ART) or kon (KON) or special-char ($) or PPOSAT
                            first_word = current_inst_splitted[0]
                            first_tag = tagger_ger.analyze(first_word)
                            if first_tag[1].startswith('ART') or first_tag[1].startswith('KON') or first_tag[1].startswith('$') or first_tag[1].startswith('PPOSAT'):
                                continue
                            # no "," infront of "Zentrum" or "Institut"
                            pos_comma = inst_strings[p].find(",")
                            if pos_comma != -1:
                                if pos_comma < inst_strings[p].find("Zentrum"):
                                    continue
                            if pos_comma != -1:
                                if pos_comma < inst_strings[p].find("Institut"):
                                    continue
                            # no "und" infront of "Zentrum" or "Institut"
                            pos_und = inst_strings[p].find("und ")
                            if pos_und != -1:
                                if pos_und < inst_strings[p].find("Zentrum"):
                                    continue
                            if pos_und != -1:
                                if pos_und < inst_strings[p].find("Institut"):
                                    continue
                            # no empty string
                            if inst_strings[p] == "" or len(inst_strings[p]) == 0:
                                continue
                            # check wrong endings
                            if inst_strings[p].endswith("-") or inst_strings[p].endswith("für") or inst_strings[p].endswith("for") or inst_strings[p].endswith("und"):
                                continue
                            # check wrong startings
                            if inst_strings[p].startswith("-") or inst_strings[p].startswith("für"):
                                continue
                            # Blacklist
                            # filter out strings with known wrong words in it
                            # Zentrum not zentrum
                            if "niversit" in inst_strings[p] or "Leiter" in inst_strings[p] or "Prof" in inst_strings[p] or "Direktor" in inst_strings[p] or "Organisationseinheit" in inst_strings[p] or "Wiki" in inst_strings[p] or "zentrum" in inst_strings[p] or \
                                    "orlesung" in inst_strings[p] or "Startseite" in inst_strings[p] or "Einrichtung" in inst_strings[p] or "beide" in inst_strings[p] or "Report" in inst_strings[p] or "Projekt" in inst_strings[p] or "institut" in inst_strings[p] or \
                                    "Jahre" in inst_strings[p] or " - " in inst_strings[p] or "Fakultät" in inst_strings[p] or "Stiftung" in inst_strings[p] or "An-Institut" in inst_strings[p] or " das " in inst_strings[p] or \
                                    " den " in inst_strings[p] or "rofil" in inst_strings[p] or "Homepage" in inst_strings[p] or "eteiligt" in inst_strings[p] or "Besprechung" in inst_strings[p] or "Artikel" in inst_strings[p] or "ffiliated" in inst_strings[p] or \
                                    "ssociated" in inst_strings[p] or "ielzahl" in inst_strings[p] or "Das" in inst_strings[p] or "Thema" in inst_strings[p] or "INSTITUT" in inst_strings[p] or "Unser" in inst_strings[p] or "Zum" in inst_strings[p]: #  or "" in inst_strings[p]
                                continue
                            blacklist = ["Deutschen Institut", "Institute for Software"]
                            if inst_strings[p] in blacklist:
                                continue
                            # check if link is from wanted university
                            if link == None or link_req_short in link or link_req_long in link:
                                pass
                            else:
                                continue
                            # entity name is accepted -> load into elastic
                            doc = {
                                "text": inst_strings[p],
                                "link": link,
                            }
                            es.index(index=index_name_Searching, id=counter_instis, document=doc)
                            counter_instis += 1
                        except:
                            counter_instis += 1
                            continue
                except:
                    continue
        except:
            continue

    # check for duplicated names
    es.indices.refresh(index=index_name_Searching)

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

    # sort instis
    instis_sorted = []
    instis_appearance = []
    # filter out sub-names
    # example:
    # 1
    # Faculty of Business Administration and Economics -> correct and complete
    # Faculty of Business -> missing some parts -> filter it out
    # 2
    # Fakultät für Ingenieurwissenschaften  -> correct and complete
    # Fakultät für Ingenieurwissenschaften erschienen -> has to much -> filter it out
    for i in range(len(aggs)):
        if i == 0:
            instis_sorted.append(aggs[i].get('key'))
            instis_appearance.append(aggs[i].get('doc_count'))
            continue
        elif aggs[i].get('key') in instis_sorted:
            continue
        else:
            is_inserted = False
            for o in range(len(instis_sorted)):
                if instis_sorted[o].startswith(aggs[i].get('key')) or aggs[i].get('key').startswith(instis_sorted[o]) or instis_sorted[o].endswith(aggs[i].get('key')) or aggs[i].get('key').endswith(instis_sorted[o]):
                    is_inserted = True
                    if instis_appearance[o] > aggs[i].get('doc_count'):
                        pass
                    elif instis_appearance[o] < aggs[i].get('doc_count'):
                        instis_appearance[o] = aggs[i].get('doc_count')
                        instis_sorted[o] = aggs[i].get('key')
                    elif instis_appearance[o] == aggs[i].get('doc_count'):
                        if len(instis_sorted[o]) >= len(aggs[i].get('key')):
                            pass
                        else:
                            instis_appearance[o] = aggs[i].get('doc_count')
                            instis_sorted[o] = aggs[i].get('key')
                else:
                    if len(instis_sorted[o]) > len(aggs[i].get('key')):
                        if aggs[i].get('key') in instis_sorted[o]:
                            is_inserted = True
                    elif len(instis_sorted[o]) < len(aggs[i].get('key')):
                        if instis_sorted[o] in aggs[i].get('key'):
                            is_inserted = True
                            instis_appearance[o] = aggs[i].get('doc_count')
                            instis_sorted[o] = aggs[i].get('key')
            if not is_inserted:
                instis_sorted.append(aggs[i].get('key'))
                instis_appearance.append(aggs[i].get('doc_count'))

    instis_without_double = []
    for i in range(len(instis_sorted)):
        if instis_sorted[i] in instis_without_double:
            continue
        else:
            instis_without_double.append(instis_sorted[i])
    instis_sorted = instis_without_double

    instis_without_double_advanced = []
    instis_without_double_advanced_2 = []
    for i in range(len(instis_sorted)):
        if " für " in instis_sorted[i]:
            instis_without_double_advanced.append(instis_sorted[i])
            instis_without_double_advanced_2.append(instis_sorted[i].replace(" für ", " "))
    for i in range(len(instis_sorted)):
        if " für " not in instis_sorted[i]:
            if instis_sorted[i] not in instis_without_double_advanced_2:
                instis_without_double_advanced.append(instis_sorted[i])
    instis_sorted = instis_without_double_advanced

    # get links for duplications
    instis = []
    instis_Link = []
    for i in range(len(instis_sorted)):
        try:
            instis.append(instis_sorted[i])

            query_get_link = {
                "query_string": {
                    "query": instis_sorted[i],
                    "default_field": "text"
                }
            }
            aggs_get_link = {
                "duplicateWords": {
                    "terms": {
                        "field": "link",
                        "min_doc_count": 1,
                        "size": 10000
                        # minimal appearance of link to be accepted as an Instituts-link
                    }
                }
            }

            result_link_search = es.search(index=index_name_Searching, query=query_get_link, aggregations=aggs_get_link, size=10000)

            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                instis_Link.append(
                    result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('key'))
            else:
                instis_Link.append(None)

            # prints to verify the results (next 5 lines)
            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                print(instis[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + instis_Link[i] + '   (' + str(
                    result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('doc_count')) + ')')
            else:
                print(instis[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + 'None   (0)')
        except:
            continue


    # delete searching-index
    es.indices.delete(index=index_name_Searching)

    print("Number of found institutes: " + str(len(instis)))
    print("-----------------------------------")

    # create searching index again for second part
    # has to be empty
    es.indices.create(index=index_name_Searching, mappings=mappings)

    # starting part two of search (with html-tags)
    sh = []
    for a in instis:
        # sh.append({"query_string": {"query": a.get('key'), "default_field": "content"}})
        sh.append({"match_phrase": {"content": a}})

    q = {}

    q["bool"] = {"should": sh, "minimum_should_match": 10}

    extra_instis = []
    extra_links = []

    docs_with_multiple_inst = es.search(index=index_name_uni, query=q, size=500, sort=[{"timestamp": "asc"}])

    current_multiple_i_max = len(docs_with_multiple_inst.get('hits').get('hits')) - 1

    # while loop until all results are done
    while (current_multiple_i_max > 0):
        # for each document with multiple occurences of already found institutes search for structure-patterns
        # like above
        for i in range((current_multiple_i_max + 1)):
            current_html = docs_with_multiple_inst.get('hits').get('hits')[i].get('_source').get('content')
            try:
                current_xpath_tree = etree.HTML(current_html)
            except:
                continue
            # current_xpath_tree = etree.fromstring(current_html)
            structure = []

            for current_inst in instis:
                if current_inst == None:
                    continue
                if current_inst == "":
                    continue
                try:
                    elems = current_xpath_tree.xpath('//*[contains(text(), "' + current_inst + '")]')
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

            # now we got the html-paths to the searched elements
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
                        
                        extra_instis.append(found)

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
                                    l = urljoin(docs_with_multiple_inst.get('hits').get('hits')[i].get('_source').get('url'), extra_links[-1])
                                break

        current_multiple_last_sort = docs_with_multiple_inst.get('hits').get('hits')[current_multiple_i_max].get('sort')
        # get next result-page
        docs_with_multiple_inst = es.search(index=index_name_uni, query=q, size=500, search_after=current_multiple_last_sort, sort=[{"timestamp": "asc"}])
        current_multiple_i_max = len(docs_with_multiple_inst.get('hits').get('hits')) - 1

    for p in range(len(extra_instis)):
        try:
            while extra_instis[p].startswith(" "):
                extra_instis[p] = extra_instis[p][1:]
            while extra_instis[p].endswith(" ") or extra_instis[p].endswith(","):
                extra_instis[p] = extra_instis[p][:-1]
            # no special chars
            if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234& -,.üöäÜÖÄ' for c in extra_instis[p]):
                continue
            if "  " in extra_instis[p] or '--' in extra_instis[p]:
                continue
            #if "„" in extra_instis[p] or "  " in extra_instis[p] or "$" in extra_instis[p] or "=" in extra_instis[p] or "'" in extra_instis[p] or "|" in extra_instis[p] or '"' in extra_instis[p] or "#" in extra_instis[p] or "/" in extra_instis[p] or \
            #        ";" in extra_instis[p] or "\\" in extra_instis[p] or "." in extra_instis[p] or ":" in extra_instis[p]: # or "" in extra_instis[p]
            #    continue
            if "Zentrum" in extra_instis[p]:
                if "Zentrum für" not in extra_instis[p]:
                    if not extra_instis[p].endswith("Zentrum"):
                        continue
            if "Institute" in extra_instis[p]:
                if "Institute for" not in extra_instis[p]:
                    continue
            if "Institut" in extra_instis[p] and "Institute" not in extra_instis[p]:
                if "Institut für" not in extra_instis[p]:
                    if not extra_instis[p].endswith("Institut"):
                        continue

            if "für" in extra_instis[p]:
                if "für " not in extra_instis[p]:
                    extra_instis[p] = extra_instis[p].replace("für", "für ")

            # string should have more than just 1 word
            current_inst_splitted = extra_instis[p].split(" ")
            if len(current_inst_splitted) < 2:
                continue

            wrong_ending = False
            for c in range(len(current_inst_splitted)):
                if current_inst_splitted[c] == "Zentrum" or current_inst_splitted[c] == "Institut" or current_inst_splitted[c] == "Institute":
                    if c != 0:
                        if current_inst_splitted[c - 1].endswith("ichen"):
                            wrong_ending = True
                            break
                        for c2 in range(c):
                            if current_inst_splitted[c2][0].islower():
                                wrong_ending = True
                                break
            if wrong_ending:
                continue

            # check if wordlength is long enough
            whitelist = ["für", "der", "des", "und", "&", "1", "2", "3", "4", "I", "II", "III", "IV", "i", "ii", "iii", "iv", "-", "for"]
            too_short = False
            for single_word in current_inst_splitted:
                if single_word in whitelist:
                    continue
                if len(single_word) < 2:
                    too_short = True
                    break
            if too_short:
                continue
            # if verb in string -> no legit name
            has_verb = False
            for single_word in current_inst_splitted:
                tag_ger = tagger_ger.analyze(single_word)

                if tag_ger[1].startswith('V'):
                    has_verb = True
                    break
            if has_verb:
                continue
            # "-" and " für" should max appear twice
            if extra_instis[p].count("-") > 2:
                continue
            # last word can't be an adjective (ADJ) or article (ART) or kon (KON) or special-char ($) or concat-word TRUNC
            last_word = current_inst_splitted[-1]
            last_tag = tagger_ger.analyze(last_word)
            if last_tag[1].startswith('A') or last_tag[1].startswith('KON') or last_tag[1].startswith('$') or last_tag[1].startswith('TRUNC'):
                continue
            # first word can't be an article (ART) or kon (KON) or special-char ($) or PPOSAT
            first_word = current_inst_splitted[0]
            first_tag = tagger_ger.analyze(first_word)
            if first_tag[1].startswith('ART') or first_tag[1].startswith('KON') or first_tag[1].startswith('$') or first_tag[1].startswith('PPOSAT'):
                continue
            # no "," infront of "Zentrum" or "Institut"
            pos_comma = extra_instis[p].find(",")
            if pos_comma != -1:
                if pos_comma < extra_instis[p].find("Zentrum"):
                    continue
            if pos_comma != -1:
                if pos_comma < extra_instis[p].find("Institut"):
                    continue
            # no "und" infront of "Zentrum" or "Institut"
            pos_und = extra_instis[p].find("und")
            if pos_und != -1:
                if pos_und < extra_instis[p].find("Zentrum"):
                    continue
            if pos_und != -1:
                if pos_und < extra_instis[p].find("Institut"):
                    continue
            # no empty string
            if extra_instis[p] == "" or len(extra_instis[p]) == 0:
                continue
            # check wrong endings
            if extra_instis[p].endswith("-") or extra_instis[p].endswith("für") or extra_instis[p].endswith("for") or extra_instis[p].endswith("und"):
                continue
            # check wrong startings
            if extra_instis[p].startswith("-") or extra_instis[p].startswith("für"):
                continue
            # Blacklist
            # filter out strings with known wrong words in it
            # Zentrum not zentrum
            if "niversit" in extra_instis[p] or "Leiter" in extra_instis[p] or "Prof" in extra_instis[p] or "Direktor" in extra_instis[p] or "Organisationseinheit" in extra_instis[p] or "Wiki" in extra_instis[p] or "zentrum" in extra_instis[p] or \
                    "orlesung" in extra_instis[p] or "Startseite" in extra_instis[p] or "Einrichtung" in extra_instis[p] or "beide" in extra_instis[p] or "Report" in extra_instis[p] or "Projekt" in extra_instis[p] or "institut" in extra_instis[p] or \
                    "beide" in extra_instis[p] or "Jahre" in extra_instis[p] or " - " in extra_instis[p] or "Fakultät" in extra_instis[p] or "Stiftung" in extra_instis[p] or "An-Institut" in extra_instis[p] or " das " in extra_instis[p] or \
                    " den " in extra_instis[p] or "rofil" in extra_instis[p] or "Homepage" in extra_instis[p] or "eteiligt" in extra_instis[p] or "Besprechung" in extra_instis[p] or "Artikel" in extra_instis[p] or "ffiliated" in extra_instis[p] or \
                    "ssociated" in extra_instis[p] or "ielzahl" in extra_instis[p] or "Das" in extra_instis[p] or "Thema" in extra_instis[p] or "INSTITUT" in extra_instis[p] or "Unser" in extra_instis[p] or "Zum" in extra_instis[p] or \
                    "Lehrstuhl" in extra_instis[p] or "Chair" in extra_instis[p] or "Faculty" in extra_instis[p] or "Abteilung" in extra_instis[p] or "Department" in extra_instis[p]: #  or "" in extra_instis[p]
                continue
            blacklist = ["Deutschen Institut"]
            if extra_instis[p] in blacklist:
                continue
            # check if link is from wanted university
            if extra_links[p] == None or link_req_short in extra_links[p] or link_req_long in extra_links[p]:
                pass
            else:
                continue
            # entity name is accepted -> load into elastic
            doc = {
                "text": extra_instis[p],
                "link": extra_links[p],
            }
            es.index(index=index_name_Searching, id=counter_instis, document=doc)
            counter_instis += 1
        except:
            counter_instis += 1
            continue

    # check for duplicated names
    es.indices.refresh(index=index_name_Searching)

    query_body_aggregation = {
        "duplicateNames": {
            "terms": {
                "field": "text",
                "min_doc_count": 40,
                "size": 10000
                # minimal appearance of fakultäts-string to be accepted as an fakultäts-name
            }
        }
    }
    result_aggregation = es.search(index=index_name_Searching, aggregations=query_body_aggregation, size=10000)

    aggs = result_aggregation.get('aggregations').get('duplicateNames').get('buckets')

    # get names and links for duplications
    extra_instis = []
    extra_instis_Link = []
    for i in range(len(aggs)):
        try:
            extra_instis.append(aggs[i].get('key'))

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
                        # minimal appearance of link to be accepted as an fakultäts-link
                    }
                }
            }

            result_link_search = es.search(index=index_name_Searching, query=query_get_link, aggregations=aggs_get_link, size=10000)

            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                extra_instis_Link.append(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('key'))
            else:
                extra_instis_Link.append(None)

            # prints to verify the results (next 5 lines)
            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                print(extra_instis[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + extra_instis_Link[i] + '   (' + str(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('doc_count')) + ')')
            else:
                print(extra_instis[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + 'None   (0)')
        except:
            continue

    # delete searching-index
    es.indices.delete(index=index_name_Searching)

    print("Number of extra found institutes: " + str(len(extra_instis)))

# main
if __name__ == '__main__':
    #if es.indices.exists(index="searching_institutes_temp"):
    #    es.indices.delete(index="searching_institutes_temp")
    
    check_elastic()

    i_name = "crawl-rawdata-ude" # wird am Ende übergeben
    #i_name = "crawl-rawdata-rub"  # wird am Ende übergeben

    index_name_uni = i_name
    index_name_Searching = index_name_Searching + i_name[i_name.rfind("-"):]

    link_req_short = i_name[i_name.rfind("-") + 1:]
    
    find_institutes(link_req_short=link_req_short)

