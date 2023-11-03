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
index_name_Searching = "searching_lehrshuhl_temp"

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
            if html_string[position] == '(' or html_string[position] == ')' or html_string[position] == '.' or html_string[position] == '!' or html_string[position] == '?' or html_string[position] == ':' or html_string[position] == '>' or html_string[position] == '<' or html_string[position] == '"' or html_string[position] == '“' or html_string[position] == '\\':
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
            if html_string[position] == '(' or html_string[position] == ')' or html_string[position] == '.' or html_string[position] == '!' or html_string[position] == '?' or html_string[position] == ':' or html_string[position] == '>' or html_string[position] == '"' or html_string[position] == '“' or html_string[position] == '„' or html_string[position] == '\\':
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
    word = word.replace("–", "-") # i want normal "-"
    word = word.replace(" ", " ") # i want normal " "
    word = word.replace("f&uuml;r", "für") # sometimes doesn't work with unescape
    return word


def find_lehrshuhl(link_req_short):
    tagger_ger = ht.HanoverTagger('morphmodel_ger.pgz')
    counter_lehrs = 0

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

    # get ids from sides with "lehrstuhl" or "lehrstuhle"
    ids = []

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

    docs_with_lehr = es.search(index=index_name_uni, query=query, size=500, sort=[{"timestamp": "asc"}])

    current_i_max = len(docs_with_lehr.get('hits').get('hits')) - 1
    # get ids from current query
    for hit in docs_with_lehr.get('hits').get('hits'):
        ids.append(hit.get('_id'))

    # while loop until all results are done
    while (current_i_max >= 499):
        current_last_sort = docs_with_lehr.get('hits').get('hits')[current_i_max].get('sort')
        # get next result-page
        docs_with_lehr = es.search(index=index_name_uni, query=query, size=500, search_after=current_last_sort, sort=[{"timestamp": "asc"}])

        current_i_max = len(docs_with_lehr.get('hits').get('hits')) - 1
        for hit in docs_with_lehr.get('hits').get('hits'):
            ids.append(hit.get('_id'))

    # go through all the docs from ids
    # get the word lehrstuhl/ lehrstuhle with previous and following words
    # -1 +2 +3 +4 +5 +6
    for id in ids:
        try:
            current_term = es.termvectors(index=index_name_uni, id=id, fields="content", term_statistics=False, field_statistics=False, payloads=False, positions=False, offsets=True)
            current_doc = es.get(index=index_name_uni, id=id)
            html_string = current_doc.get('_source').get('content')

            lehr_deu = []
            abt_deu = []
            lehr = []

            if current_term.get('term_vectors').get('content').get('terms').get('lehrstuhl') != None:
                lehr_deu = current_term.get('term_vectors').get('content').get('terms').get('lehrstuhl').get('tokens')
            if current_term.get('term_vectors').get('content').get('terms').get('abteilung') != None:
                abt_deu = current_term.get('term_vectors').get('content').get('terms').get('abteilung').get('tokens')

            if isinstance(lehr_deu, list):
                lehr = lehr + lehr_deu
            if isinstance(abt_deu, list):
                lehr = lehr + abt_deu

            for i in range(len(lehr)):
                try:
                    start = lehr[i].get('start_offset')
                    end = lehr[i].get('end_offset')
    
                    lehr_string = ''
                    for o in range(start, end):
                        lehr_string += html_string[o]
    
                    lehr_strings = []
    
                    # +1 +2 +3 +4 +5 +6 +7 +8 +9 +10
                    for p in range(2, 12):
                        lehr_words = getWordsAfter(end=end, html_string=html_string, word=lehr_string, number=p)
                        if lehr_words not in lehr_strings:
                            lehr_strings.append(lehr_words)
    
                    # get the link to "lehrstuhl" if existing
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
                    for p in range(len(lehr_strings)):
                        try:
                            while lehr_strings[p].startswith(" "):
                                lehr_strings[p] = lehr_strings[p][1:]
                            while lehr_strings[p].endswith(" ") or lehr_strings[p].endswith(","):
                                lehr_strings[p] = lehr_strings[p][:-1]
    
                            # no special chars
                            if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234& -,.öäüÖÜÄ' for c in lehr_strings[p]):
                                continue
                            if "  " in lehr_strings[p] or '--' in lehr_strings[p]:
                                continue
                            #if "%" in lehr_strings[p] or "  " in lehr_strings[p] or "#" in lehr_strings[p] or ":" in lehr_strings[p] or ">" in lehr_strings[p] or "<" in lehr_strings[p] or "=" in lehr_strings[p] or "$" in lehr_strings[p] or \
                            #        "'" in lehr_strings[p] or "|" in lehr_strings[p] or '"' in lehr_strings[p] or '--' in lehr_strings[p] or '…' in lehr_strings[p] or ';' in lehr_strings[p] or '\\' in lehr_strings[p]:
                            #    continue
                            # some further checking
                            if "Abteilung" in lehr_strings[p]:
                                if "Abteilung für" not in lehr_strings[p]:
                                    continue
                            # some formatting
                            if "für" in lehr_strings[p]:
                                if "für " not in lehr_strings[p]:
                                    lehr_strings[p] = lehr_strings[p].replace("für", "für ")
    
                            # string should have more than just 1 word
                            current_lehr_splitted = lehr_strings[p].split(" ")
                            splitted_temp = []
                            for t in current_lehr_splitted:
                                if len(t) != 0:
                                    splitted_temp.append(t)
                            current_lehr_splitted = splitted_temp
    
                            if len(current_lehr_splitted) < 2:
                                continue
                            # check if wordlength is long enough
                            whitelist = ["für", "der", "des", "und", "&", "/", "1", "2", "3", "4", "I", "II", "III", "IV", "i", "ii", "iii", "iv", "-"]
                            too_short = False
                            for single_word in current_lehr_splitted:
                                if single_word in whitelist:
                                    continue
                                if len(single_word) < 5:
                                    too_short = True
                                    break
                            if too_short:
                                continue
                            # if verb in string -> no legit name
                            has_verb = False
                            for single_word in current_lehr_splitted:
                                tag_ger = tagger_ger.analyze(single_word)
    
                                if tag_ger[1].startswith('V'):
                                    has_verb = True
                                    break
                            if has_verb:
                                continue
                            # last word can't be an adjective (ADJ) or article (ART) or kon (KON) or special-char ($) or concat-word TRUNC
                            last_word = current_lehr_splitted[-1]
                            last_tag = tagger_ger.analyze(last_word)
                            if last_tag[1].startswith('A') or last_tag[1].startswith('KON') or last_tag[1].startswith('$') or last_tag[1].startswith('TRUNC'):
                                continue
                            # "Lehrstuhl" and " für" should just appear once
                            if lehr_strings[p].count("ehrstuhl") > 1 or lehr_strings[p].count(" für") > 1:
                                continue
                            # check wrong endings
                            if lehr_strings[p].endswith("-") or lehr_strings[p].endswith("Lehrstuhl für Bürgerliches Recht") or lehr_strings[p].endswith("Lehrstuhl für Öffentliches Recht") or lehr_strings[p].endswith("Lehrstuhl für Wirtschaftsinformatik") or \
                                    lehr_strings[p].endswith("Lehrstuhl für Volkswirtschaftslehre") or lehr_strings[p].endswith("Lehrstuhl für Software") or lehr_strings[p].endswith("Lehrstuhl für Angewandte") or lehr_strings[p].endswith("Lehrstuhl für Deutsche") or \
                                    lehr_strings[p].endswith("Lehrstuhl für Informatik") or lehr_strings[p].endswith("Lehrstuhl für Didaktik") or lehr_strings[p].endswith("Lehrstuhl für Neues") or lehr_strings[p].endswith("Lehrstuhl für Christliche") or \
                                    lehr_strings[p].endswith("Lehrstuhl für Vergleichende") or lehr_strings[p].endswith("Lehrstuhl Didaktik"):
                                continue
                            # no empty string
                            if lehr_strings[p] == "":
                                continue
                            # Blacklist
                            # filter out strings with known wrong words in it
                            # Germanm so its Lehrstuhl not lehrstuhl
                            if "niversität" in lehr_strings[p] or "straße" in lehr_strings[p] or "Fakultät" in lehr_strings[p] or "lehrstuhl" in lehr_strings[p] or "Lehrstuhl," in lehr_strings[p] or "Lehrstuhl-" in lehr_strings[p] or \
                                    "Lehrstuhl -" in lehr_strings[p] or "Institut" in lehr_strings[p] or "weitere" in lehr_strings[p] or "Ausschreibung" in lehr_strings[p] or "Masterarbeit" in lehr_strings[p] or "Bachelorarbeit" in lehr_strings[p] \
                                    or " bei " in lehr_strings[p] or "Student" in lehr_strings[p] or "Newsletter" in lehr_strings[p] or "Dipl" in lehr_strings[p] or "Lehrstühle" in lehr_strings[p] or "Betreuer" in lehr_strings[p]:
                                continue
                            # check if link is from wanted university
                            if link == None or link_req_short in link or link_req_long in link:
                                pass
                            else:
                                continue
                            # entity name is accepted -> load into elastic
                            doc = {
                                "text": lehr_strings[p],
                                "link": link,
                            }
                            es.index(index=index_name_Searching, id=counter_lehrs, document=doc)
                            counter_lehrs += 1
                        except:
                            counter_lehrs += 1
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

    # sort lehrs
    lehrs_sorted = []
    lehrs_appearance = []
    # filter out sub-names
    # example:
    # 1
    # Faculty of Business Administration and Economics -> correct and complete
    # Faculty of Business -> missing some parts -> filter it out
    # 2
    # Fakultät für Ingenieurwissenschaften  -> correct and complete
    # Fakultät für Ingenieurwissenschaften erschienen -> has to much -> filter it out
    for i in range(len(aggs)):
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
            lehrs_sorted.append(aggs[i].get('key'))
            lehrs_appearance.append(aggs[i].get('doc_count'))
            continue
        elif aggs[i].get('key') in lehrs_sorted:
            continue
        else:
            is_inserted = False
            for o in range(len(lehrs_sorted)):
                if lehrs_sorted[o].startswith(aggs[i].get('key')) or aggs[i].get('key').startswith(lehrs_sorted[o]) or lehrs_sorted[o].endswith(aggs[i].get('key')) or aggs[i].get('key').endswith(lehrs_sorted[o]):
                    is_inserted = True
                    if lehrs_appearance[o] > aggs[i].get('doc_count'):
                        pass
                    elif lehrs_appearance[o] < aggs[i].get('doc_count'):
                        lehrs_appearance[o] = aggs[i].get('doc_count')
                        lehrs_sorted[o] = aggs[i].get('key')
                    elif lehrs_appearance[o] == aggs[i].get('doc_count'):
                        if len(lehrs_sorted[o]) >= len(aggs[i].get('key')):
                            pass
                        else:
                            lehrs_appearance[o] = aggs[i].get('doc_count')
                            lehrs_sorted[o] = aggs[i].get('key')
                else:
                    if len(lehrs_sorted[o]) > len(aggs[i].get('key')):
                        if aggs[i].get('key') in lehrs_sorted[o]:
                            is_inserted = True
                    elif len(lehrs_sorted[o]) < len(aggs[i].get('key')):
                        if lehrs_sorted[o] in aggs[i].get('key'):
                            is_inserted = True
                            lehrs_appearance[o] = aggs[i].get('doc_count')
                            lehrs_sorted[o] = aggs[i].get('key')
            if not is_inserted:
                if aggs[i].get('doc_count') >= 50:
                    lehrs_sorted.append(aggs[i].get('key'))
                    lehrs_appearance.append(aggs[i].get('doc_count'))
                else:
                    splitted_lehrs = aggs[i].get('key').split(" ")
                    if len(splitted_lehrs) < 3:
                        continue
                    elif splitted_lehrs[1] == "für":
                        lehrs_sorted.append(aggs[i].get('key'))
                        lehrs_appearance.append(aggs[i].get('doc_count'))
                    else:
                        lehrs_sorted.append(aggs[i].get('key'))
                        lehrs_appearance.append(aggs[i].get('doc_count'))

    lehrs_without_double = []
    for i in range(len(lehrs_sorted)):
        if lehrs_sorted[i] in lehrs_without_double:
            continue
        else:
            lehrs_without_double.append(lehrs_sorted[i])
    lehrs_sorted = lehrs_without_double

    lehrs_without_double_advanced = []
    lehrs_without_double_advanced_2 = []
    for i in range(len(lehrs_sorted)):
        if " für " in lehrs_sorted[i]:
            lehrs_without_double_advanced.append(lehrs_sorted[i])
            lehrs_without_double_advanced_2.append(lehrs_sorted[i].replace(" für ", " "))
    for i in range(len(lehrs_sorted)):
        if " für " not in lehrs_sorted[i]:
            if lehrs_sorted[i] not in lehrs_without_double_advanced_2:
                lehrs_without_double_advanced.append(lehrs_sorted[i])
    lehrs_sorted = lehrs_without_double_advanced

    # get links for duplications
    lehrs = []
    lehrs_Link = []
    for i in range(len(lehrs_sorted)):
        try:
            lehrs.append(lehrs_sorted[i])

            query_get_link = {
                "query_string": {
                    "query": lehrs_sorted[i],
                    "default_field": "text"
                }
            }
            aggs_get_link = {
                "duplicateWords": {
                    "terms": {
                        "field": "link",
                        "min_doc_count": 1,
                        "size": 10000
                        # minimal appearance of link to be accepted as an lehrstuhls-link
                    }
                }
            }

            result_link_search = es.search(index=index_name_Searching, query=query_get_link, aggregations=aggs_get_link, size=10000)

            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                lehrs_Link.append(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('key'))
            else:
                lehrs_Link.append(None)

            # prints to verify the results (next 5 lines)
            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                print(lehrs[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + lehrs_Link[i] + '   (' + str(
                    result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('doc_count')) + ')')
            else:
                print(lehrs[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + 'None   (0)')
        except:
            continue

    # delete searching-index
    es.indices.delete(index=index_name_Searching)

    print("Number of found lehrshuhl: " + str(len(lehrs)))
    print("-----------------------------------")

    # create searching index again for second part
    # has to be empty
    es.indices.create(index=index_name_Searching, mappings=mappings)

    # starting part two of search (with html-tags)
    sh = []
    for a in lehrs:
        # sh.append({"query_string": {"query": a.get('key'), "default_field": "content"}})
        sh.append({"match_phrase": {"content": a}})

    q = {}

    q["bool"] = {"should": sh, "minimum_should_match": 3}

    docs_with_multiple_lehr = es.search(index=index_name_uni, query=q, size=500, sort=[{"timestamp": "asc"}])

    current_multiple_i_max = len(docs_with_multiple_lehr.get('hits').get('hits')) - 1

    extra_lehrs = []
    extra_links = []

    # while loop until all results are done
    while (current_multiple_i_max >= 499):
        current_multiple_i_max = len(docs_with_multiple_lehr.get('hits').get('hits')) - 1

        # for each document with multiple occurences of already found chairs search for structure-patterns
        # like above
        for i in range((current_multiple_i_max + 1)):
            current_html = docs_with_multiple_lehr.get('hits').get('hits')[i].get('_source').get('content')

            try:
                current_xpath_tree = etree.HTML(current_html)
            except:
                continue
            # current_xpath_tree = etree.fromstring(current_html)
            structure = []

            for current_lehr in lehrs:
                if current_lehr == None:
                    continue
                if current_lehr == "":
                    continue
                try:
                    elems = current_xpath_tree.xpath('//*[contains(text(), "' + current_lehr + '")]')
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

                        extra_lehrs.append(found)

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
                                    l = urljoin(docs_with_multiple_lehr.get('hits').get('hits')[i].get('_source').get('url'), extra_links[-1])
                                break

        current_multiple_last_sort = docs_with_multiple_lehr.get('hits').get('hits')[current_multiple_i_max].get('sort')
        # get next result-page
        docs_with_multiple_lehr = es.search(index=index_name_uni, query=q, size=500, search_after=current_multiple_last_sort, sort=[{"timestamp": "asc"}])

    for p in range(len(extra_lehrs)):
        try:
            while extra_lehrs[p].startswith(" "):
                extra_lehrs[p] = extra_lehrs[p][1:]
            while extra_lehrs[p].endswith(" ") or extra_lehrs[p].endswith(","):
                extra_lehrs[p] = extra_lehrs[p][:-1]

            # no special chars
            if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234& -,.öäüÖÜÄ' for c in extra_lehrs[p]):
                continue
            if "  " in extra_lehrs[p] or '--' in extra_lehrs[p]:
                continue
            #if "%" in extra_lehrs[p] or "  " in extra_lehrs[p] or "#" in extra_lehrs[p] or ":" in extra_lehrs[p] or ">" in extra_lehrs[p] or "<" in extra_lehrs[p] or "=" in extra_lehrs[p] or "$" in extra_lehrs[p] or \
            #        "'" in extra_lehrs[p] or "|" in extra_lehrs[p] or '"' in extra_lehrs[p] or '--' in extra_lehrs[p] or '\\' in extra_lehrs[p]:
            #    continue
            # some further checking
            if "Abteilung" in extra_lehrs[p]:
                if "Abteilung für" not in extra_lehrs[p]:
                    continue
            # some formatting
            if "für" in extra_lehrs[p]:
                if "für " not in extra_lehrs[p]:
                    extra_lehrs[p] = extra_lehrs[p].replace("für", "für ")

            # string should have more than just 1 word
            current_lehr_splitted = extra_lehrs[p].split(" ")
            splitted_temp = []
            for t in current_lehr_splitted:
                if len(t) != 0:
                    splitted_temp.append(t)
            current_lehr_splitted = splitted_temp

            if len(current_lehr_splitted) < 2:
                continue
            # check if wordlength is long enough
            whitelist = ["für", "der", "des", "und", "&", "/", "1", "2", "3", "4", "I", "II", "III", "IV", "i", "ii", "iii", "iv", "-", "of"]
            too_short = False
            for single_word in current_lehr_splitted:
                if single_word in whitelist:
                    continue
                if len(single_word) < 3:
                    too_short = True
                    break
            if too_short:
                continue
            # if verb in string -> no legit name
            has_verb = False
            for single_word in current_lehr_splitted:
                tag_ger = tagger_ger.analyze(single_word)

                if tag_ger[1].startswith('V'):
                    has_verb = True
                    break
            if has_verb:
                continue
            # last word can't be an adjective (ADJ) or article (ART) or kon (KON) or special-char ($) or concat-word TRUNC
            last_word = current_lehr_splitted[-1]
            last_tag = tagger_ger.analyze(last_word)
            if last_tag[1].startswith('A') or last_tag[1].startswith('KON') or last_tag[1].startswith('$') or last_tag[1].startswith('TRUNC'):
                continue
            # "Lehrstuhl" and " für" should just appear once
            if extra_lehrs[p].count("ehrstuhl") > 1 or extra_lehrs[p].count(" für") > 1:
                continue
            # check wrong endings
            if extra_lehrs[p].endswith("-") or extra_lehrs[p].endswith("Lehrstuhl für Bürgerliches Recht") or extra_lehrs[p].endswith("Lehrstuhl für Öffentliches Recht") or extra_lehrs[p].endswith("Lehrstuhl für Wirtschaftsinformatik") or \
                                    extra_lehrs[p].endswith("Lehrstuhl für Volkswirtschaftslehre") or extra_lehrs[p].endswith("Lehrstuhl für Software") or extra_lehrs[p].endswith("Lehrstuhl für Angewandte") or extra_lehrs[p].endswith("Lehrstuhl für Deutsche"):
                continue
            # no empty string
            if extra_lehrs[p] == "":
                continue
            # Blacklist
            # filter out strings with known wrong words in it
            if "niversität" in extra_lehrs[p] or "straße" in extra_lehrs[p] or "Fakultät" in extra_lehrs[p] or "lehrstuhl" in extra_lehrs[p] or "Lehrstuhl," in extra_lehrs[p] or "nstitut" in extra_lehrs[p] or \
                    "entrum" in extra_lehrs[p] or "HK" in extra_lehrs[p] or "Hilfskraft" in extra_lehrs[p] or "IKS" in extra_lehrs[p] or "Lehrstuhl-" in extra_lehrs[p] or "Lehrstuhl -" in extra_lehrs[p] or \
                    "Institut" in extra_lehrs[p] or "weitere" in extra_lehrs[p] or "Ausschreibung" in extra_lehrs[p] or "Masterarbeit" in extra_lehrs[p] or "Bachelorarbeit" in extra_lehrs[p] or \
                    " bei " in extra_lehrs[p] or "Student" in extra_lehrs[p] or "Newsletter" in extra_lehrs[p] or "Dipl" in extra_lehrs[p] or "Lehrstühle" in extra_lehrs[p] or "Betreuer" in extra_lehrs[p]:
                continue
            # check if link is from wanted university
            if extra_links[p] == None or link_req_short in extra_links[p] or link_req_long in extra_links[p]:
                pass
            else:
                continue
            # entity name is accepted -> load into elastic
            doc = {
                "text": extra_lehrs[p],
                "link": extra_links[p],
            }
            es.index(index=index_name_Searching, id=counter_lehrs, document=doc)
            counter_lehrs += 1
        except:
            counter_lehrs += 1
            continue

    # check for duplicated names
    es.indices.refresh(index=index_name_Searching)

    query_body_aggregation = {
        "duplicateNames": {
            "terms": {
                "field": "text",
                "min_doc_count": 3,
                "size": 10000
            }
        }
    }
    result_aggregation = es.search(index=index_name_Searching, aggregations=query_body_aggregation, size=10000)

    aggs = result_aggregation.get('aggregations').get('duplicateNames').get('buckets')

    # get names and links for duplications
    extra_lehrs = []
    extra_lehrs_Link = []

    adding = 0

    for i in range(len(aggs)):
        try:
            if aggs[i].get('doc_count') < 100:  # if doc_count under 50 -> name has to have a für or for
                splitted_key = aggs[i].get('key').split(" ")
                if len(splitted_key) > 2:
                    if splitted_key[1] == "für":
                        pass
                    else:
                        adding = adding + 1
                        continue
                else:
                    adding = adding + 1
                    continue

            extra_lehrs.append(aggs[i].get('key'))

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
                extra_lehrs_Link.append(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('key'))
            else:
                extra_lehrs_Link.append(None)

            # prints to verify the results (next 4 lines)
            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                print(extra_lehrs[i + adding] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + extra_lehrs_Link[i + adding] + '   (' + str(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('doc_count')) + ')')
            else:
                print(extra_lehrs[i + adding] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + 'None   (0)')
        except:
            continue

    # delete searching-index
    es.indices.delete(index=index_name_Searching)

    print("Number of extra found lehrstuhl: " + str(len(extra_lehrs)))


# main
if __name__ == '__main__':
    #if es.indices.exists(index="searching_lehrshuhl_temp"):
    #    es.indices.delete(index="searching_lehrshuhl_temp")
    
    check_elastic()

    #i_name = "crawl-rawdata-ude" # wird am Ende übergeben
    i_name = "crawl-rawdata-rub"  # wird am Ende übergeben

    index_name_uni = i_name
    index_name_Searching = index_name_Searching + i_name[i_name.rfind("-"):]
    
    link_req_short = i_name[i_name.rfind("-") + 1:]

    find_lehrshuhl(link_req_short=link_req_short)

