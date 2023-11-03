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
index_name_Searching = "searching_faculties_temp"


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
            if html_string[position] == '(' or html_string[position] == ')' or html_string[position] == ',' or html_string[position] == '.' or html_string[position] == '!' or html_string[position] == '?' or html_string[position] == ':' or html_string[position] == '>' or html_string[position] == '<' or html_string[position] == ';' or html_string[position] == '"' or html_string[position] == '“' or html_string[position] == '\\':
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
            if html_string[position] == '(' or html_string[position] == ')' or html_string[position] == ',' or html_string[position] == '.' or html_string[position] == '!' or html_string[position] == '?' or html_string[position] == ':' or html_string[position] == '>' or html_string[position] == ';' or html_string[position] == '"' or html_string[position] == '“' or html_string[position] == '\\':
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


def find_faculties(link_req_short):
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

    counter_Fakus = 0

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

    # get ids from sides with "Fakultät" or "faculty"
    ids = []

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

    docs_with_fakul = es.search(index=index_name_uni, query=query, size=500, sort=[{"timestamp": "asc"}])

    current_i_max = len(docs_with_fakul.get('hits').get('hits')) - 1
    # get ids from current query
    for hit in docs_with_fakul.get('hits').get('hits'):
        ids.append(hit.get('_id'))

    # while loop until all results are done
    while (current_i_max >= 499):
        current_last_sort = docs_with_fakul.get('hits').get('hits')[current_i_max].get('sort')
        # get next result-page
        docs_with_fakul = es.search(index=index_name_uni, query=query, size=500, search_after=current_last_sort, sort=[{"timestamp": "asc"}])

        current_i_max = len(docs_with_fakul.get('hits').get('hits')) - 1
        for hit in docs_with_fakul.get('hits').get('hits'):
            ids.append(hit.get('_id'))

    # go through all the docs from ids
    # get the word fakultät/ faculty with previous and following words
    # (examples: "Medizinische Fakultät", "Fakultät für Physik", "Fakultät für Angewandte Informatik", "Fakultät für Chemie und Biochemie") -> ger -> -1 +2 +3 +4
    # (examples: "Medical faculty", "faculty of chemistry", "faculty of applied science", "faculty of X and Y", "faculty of Business Administration and X / XY") -> eng -> -1 +2 +3 +4 +5 +6
    for id in ids:
        try:
            current_term = es.termvectors(index=index_name_uni, id=id, fields="content", term_statistics=False, field_statistics=False, payloads=False, positions=False, offsets=True)
            current_doc = es.get(index=index_name_uni, id=id)
            html_string = current_doc.get('_source').get('content')

            fakul_deu = []
            fakul = []

            if current_term.get('term_vectors').get('content').get('terms').get('fakultät') != None:
                fakul_deu = current_term.get('term_vectors').get('content').get('terms').get('fakultät').get('tokens')

            if isinstance(fakul_deu, list):
                fakul = fakul + fakul_deu

            for i in range(len(fakul)):
                try:
                    start = fakul[i].get('start_offset')
                    end = fakul[i].get('end_offset')
    
                    fakul_string = ''
                    for o in range(start, end):
                        fakul_string += html_string[o]
    
                    fakul_strings = []
    
                    # -1
                    fakul_words = getWordsBefore(start=start, html_string=html_string, word=fakul_string, number=2)
                    if fakul_words not in fakul_strings:
                        fakul_strings.append(fakul_words)
                    # +2 +3 +4 +5 +6
                    for p in range(3, 8):
                        fakul_words = getWordsAfter(end=end, html_string=html_string, word=fakul_string, number=p)
                        if fakul_words not in fakul_strings:
                            fakul_strings.append(fakul_words)
    
                    # get the link to "fakultät" if existing
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
                    for p in range(len(fakul_strings)):
                        try:
                            while fakul_strings[p].startswith(" ") or fakul_strings[p].startswith(","):
                                fakul_strings[p] = fakul_strings[p][1:]
                            while fakul_strings[p].endswith(" ") or fakul_strings[p].endswith(","):
                                fakul_strings[p] = fakul_strings[p][:-1]
                            # no special chars
                            if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234& -öäüÖÜÄ' for c in fakul_strings[p]):
                                continue
                            if "  " in fakul_strings[p] or '--' in fakul_strings[p]:
                                continue
                            #if "  " in fakul_strings[p] or "=" in fakul_strings[p] or "'" in fakul_strings[p] or "|" in fakul_strings[p] or '"' in fakul_strings[p] or "#" in fakul_strings[p] or "," in fakul_strings[p] or ":" in fakul_strings[p] or '"' in fakul_strings[p] or "'" in fakul_strings[p] or "?" in fakul_strings[p] or "!" in fakul_strings[p] or "." in fakul_strings[p] or "/" in fakul_strings[p]:
                            #    continue
                            # string should have more than just 1 word
                            current_fakul_splitted = fakul_strings[p].split(" ")
                            if len(current_fakul_splitted) < 2:
                                continue
                            # check if wordlength is long enough
                            whitelist = ["für", "der", "des", "und", "&", "/", "1", "2", "3", "4", "I", "II", "III", "IV", "i", "ii", "iii", "iv", "-"]
                            too_short = False
                            for single_word in current_fakul_splitted:
                                if single_word in whitelist:
                                    continue
                                if len(single_word) == 4 or len(single_word) == 5:
                                    if single_word.endswith("-"):
                                        continue
                                if len(single_word) < 6:
                                    too_short = True
                                    break
                            if too_short:
                                continue
                            # if verb in string -> no legit name
                            has_verb = False
                            for single_word in current_fakul_splitted:
                                tag_ger = tagger_ger.analyze(single_word)
        
                                if tag_ger[1].startswith('V'):
                                    has_verb = True
                                    break
                            if has_verb:
                                continue
                            # last word can't be an adjective
                            last_word = current_fakul_splitted[-1]
                            last_tag = tagger_ger.analyze(last_word)
                            if last_tag[1].startswith('A'):
                                continue
                            # if word in front of fakultät -> has to end on an e -> "Medizinische/ Juristische Fakultät" and not "Medizinischen Fakultät"
                            if current_fakul_splitted[0] != "Fakultät":
                                if not current_fakul_splitted[0].endswith("e"):
                                    continue
                            # check wrong endings
                            if fakul_strings[p].endswith("Unsere") or fakul_strings[p].endswith("unsere") or fakul_strings[p].endswith("-") or fakul_strings[p].endswith("und"):
                                continue
                            # check wrong startings
                            if fakul_strings[p].startswith("Unsere") or fakul_strings[p].startswith("unsere"):
                                continue
                            # filter out strings with known wrong words in it
                            # blacklist
                            if "Universität" in fakul_strings[p] or "Institut" in fakul_strings[p] or "Fach" in fakul_strings[p] or "Fächer" in fakul_strings[p]:
                                continue
                            # check if link is from wanted university
                            if link == None or link_req_short in link or link_req_long in link:
                                pass
                            else:
                                continue
                            # entity name is accepted -> load into elastic
                            doc = {
                                "text": fakul_strings[p],
                                "link": link,
                            }
                            es.index(index=index_name_Searching, id=counter_Fakus, document=doc)
                            counter_Fakus += 1
                        except:
                            counter_Fakus += 1
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
                "min_doc_count": 70,
                "size": 10000
                # minimal appearance of fakultäts-string to be accepted as an fakultäts-name
            }
        }
    }
    result_aggregation = es.search(index=index_name_Searching, aggregations=query_body_aggregation, size=10000)

    aggs = result_aggregation.get('aggregations').get('duplicateNames').get('buckets')

    # sort fakus
    fakus_sorted = []
    fakus_appearance = []
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
            fakus_sorted.append(aggs[i].get('key'))
            fakus_appearance.append(aggs[i].get('doc_count'))
        elif aggs[i].get('key') in fakus_sorted:
            continue
        else:
            is_inserted = False
            for o in range(len(fakus_sorted)):
                if fakus_sorted[o].startswith(aggs[i].get('key')) or aggs[i].get('key').startswith(fakus_sorted[o]) or fakus_sorted[o].endswith(aggs[i].get('key')) or aggs[i].get('key').endswith(fakus_sorted[o]):
                    is_inserted = True
                    if fakus_appearance[o] > aggs[i].get('doc_count'):
                        pass
                    elif fakus_appearance[o] < aggs[i].get('doc_count'):
                        fakus_appearance[o] = aggs[i].get('doc_count')
                        fakus_sorted[o] = aggs[i].get('key')
                    elif fakus_appearance[o] == aggs[i].get('doc_count'):
                        if len(fakus_sorted[o]) >= len(aggs[i].get('key')):
                            pass
                        else:
                            fakus_appearance[o] = aggs[i].get('doc_count')
                            fakus_sorted[o] = aggs[i].get('key')
                else:
                    pass  # (somethings like: "Fakultät für Wirtschaftswissenschaften" and "XY Fakultät für Wirtschaftswissenschaften" -> unclear if needed or makes sense -> tests will show -> currently not needed
            if not is_inserted:
                fakus_sorted.append(aggs[i].get('key'))
                fakus_appearance.append(aggs[i].get('doc_count'))

    fakus_without_double = []
    for i in range(len(fakus_sorted)):
        if fakus_sorted[i] in fakus_without_double:
            continue
        else:
            fakus_without_double.append(fakus_sorted[i])
    fakus_sorted = fakus_without_double

    fakus_without_double_advanced = []
    fakus_without_double_advanced_2 = []
    for i in range(len(fakus_sorted)):
        if " für " in fakus_sorted[i]:
            fakus_without_double_advanced.append(fakus_sorted[i])
            fakus_without_double_advanced_2.append(fakus_sorted[i].replace(" für ", " "))
    for i in range(len(fakus_sorted)):
        if " für " not in fakus_sorted[i]:
            if fakus_sorted[i] not in fakus_without_double_advanced_2:
                fakus_without_double_advanced.append(fakus_sorted[i])
    fakus_sorted = fakus_without_double_advanced

    # get links for duplications
    fakus = []
    fakus_Link = []
    for i in range(len(fakus_sorted)):
        try:
            fakus.append(fakus_sorted[i])

            query_get_link = {
                "query_string": {
                    "query": fakus_sorted[i],
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
                fakus_Link.append(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('key'))
            else:
                fakus_Link.append(None)

            # prints to verify the results (next 5 lines)
            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                print(fakus[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + fakus_Link[i] + '   (' + str(
                    result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('doc_count')) + ')')
            else:
                print(fakus[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + 'None   (0)')
        except:
            continue

    # delete searching-index
    es.indices.delete(index=index_name_Searching)

    print("Number of found faculties: " + str(len(fakus)))
    print("---------------------------------")

    # create searching index again for second part
    # has to be empty
    es.indices.create(index=index_name_Searching, mappings=mappings)

    first_fakus = fakus.copy()

    appended_fakus = []
    for a in fakus:
        if " für " in a:
            a_2 = a[a.find(" für ") + 5:]
            appended_fakus.append(a_2)
    for a in fakus:
        is_in = False
        for a_2 in appended_fakus:
            if a_2 in a:
                is_in = True
                break
        if is_in:
            continue
        else:
            appended_fakus.append(a)
    fakus = appended_fakus

    # starting part two of search (with html_string-tags)
    sh = []
    for a in fakus:
        sh.append({"match_phrase": {"content": a}})

    q = {}

    q["bool"] = {"should": sh, "minimum_should_match": "90%"}

    docs_with_multiple_faku = es.search(index=index_name_uni, query=q, size=500, sort=[{"timestamp": "asc"}])

    current_multiple_i_max = len(docs_with_multiple_faku.get('hits').get('hits')) - 1

    extra_fakus = []
    extra_links = []

    # while loop until all results are done
    while (current_multiple_i_max > 0):
        # for each document with multiple occurences of already found chairs search for structure-patterns
        # like above
        for i in range((current_multiple_i_max + 1)):
            current_html_string = docs_with_multiple_faku.get('hits').get('hits')[i].get('_source').get('content')

            try:
                current_xpath_tree = etree.HTML(current_html_string)
            except:
                continue
            # current_xpath_tree = etree.fromstring(current_html_string)
            structure = []

            for current_faku in fakus:
                if current_faku == None:
                    continue
                if current_faku == "":
                    continue
                try:
                    elems = current_xpath_tree.xpath('//*[contains(text(), "' + current_faku + '")]')
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

                        extra_fakus.append(found)

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
                                    l = urljoin(docs_with_multiple_faku.get('hits').get('hits')[i].get('_source').get('url'), extra_links[-1])
                                break

        current_multiple_last_sort = docs_with_multiple_faku.get('hits').get('hits')[current_multiple_i_max].get('sort')
        # get next result-page
        docs_with_multiple_faku = es.search(index=index_name_uni, query=q, size=500, search_after=current_multiple_last_sort, sort=[{"timestamp": "asc"}])
        current_multiple_i_max = len(docs_with_multiple_faku.get('hits').get('hits')) - 1

    # check extra found fakus and push them into searching-index
    for p in range(len(extra_fakus)):
        try:
            while extra_fakus[p].startswith(" ") or extra_fakus[p].startswith(","):
                extra_fakus[p] = extra_fakus[p][1:]
            while extra_fakus[p].endswith(" ") or extra_fakus[p].endswith(","):
                extra_fakus[p] = extra_fakus[p][:-1]
            # no special chars
            if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234& -öäüÖÜÄ' for c in extra_fakus[p]):
                continue
            if "  " in extra_fakus[p] or '--' in extra_fakus[p]:
                continue
            #if "  " in extra_fakus[p] or "=" in extra_fakus[p] or "'" in extra_fakus[p] or "|" in extra_fakus[p] or '"' in extra_fakus[p] or "#" in extra_fakus[p] or "," in extra_fakus[p] or ":" in extra_fakus[p] or '"' in extra_fakus[p] or "'" in extra_fakus[p] or "?" in extra_fakus[p] or "!" in extra_fakus[p] or "." in extra_fakus[p]:
            #    continue
            # string should have more than just 1 word
            current_fakul_splitted = extra_fakus[p].split(" ")
            if len(current_fakul_splitted) < 2:
                continue
            # check if wordlength is long enough
            whitelist = ["für", "der", "des", "und", "&", "/", "1", "2", "3", "4", "I", "II", "III", "IV", "i", "ii", "iii", "iv", "-"]
            too_short = False
            for single_word in current_fakul_splitted:
                if single_word in whitelist:
                    continue
                if len(single_word) < 2:
                    too_short = True
                    break
            if too_short:
                continue
            # if verb in string -> no legit name
            has_verb = False
            for single_word in current_fakul_splitted:
                tag_ger = tagger_ger.analyze(single_word)

                if tag_ger[1].startswith('V'):
                    has_verb = True
                    break
            if has_verb:
                continue
            # last word can't be an adjective
            last_word = current_fakul_splitted[-1]
            last_tag = tagger_ger.analyze(last_word)
            if last_tag[1].startswith('A'):
                continue
            # if word in front of fakultät -> has to end on an e -> "Medizinische/ Juristische Fakultät" and not "Medizinischen Fakultät"
            if "Fakultät" in extra_fakus[p]:
                if current_fakul_splitted[0] != "Fakultät":
                    if not current_fakul_splitted[0].endswith("e"):
                        continue
            # check wrong startings or endings
            if extra_fakus[p].endswith("Unsere") or extra_fakus[p].endswith("unsere"):
                continue
            # Blacklist
            # filter out strings with known wrong words in it
            if "Universität" in extra_fakus[p] or "Institut" in extra_fakus[p]:
                continue
            # check if link is from wanted university
            if extra_links[p] == None or link_req_short in extra_links[p] or link_req_long in extra_links[p]:
                pass
            else:
                continue
            # entity name is accepted -> load into elastic
            doc = {
                "text": extra_fakus[p],
                "link": extra_links[p],
            }
            es.index(index=index_name_Searching, id=counter_Fakus, document=doc)
            counter_Fakus += 1
        except:
            counter_Fakus += 1
            continue

    # check for duplicated names
    es.indices.refresh(index=index_name_Searching)

    query_body_aggregation = {
        "duplicateNames": {
            "terms": {
                "field": "text",
                "min_doc_count": 10,
                "size": 10000
                # minimal appearance of fakultäts-string to be accepted as an fakultäts-name
            }
        }
    }
    result_aggregation = es.search(index=index_name_Searching, aggregations=query_body_aggregation, size=10000)

    aggs = result_aggregation.get('aggregations').get('duplicateNames').get('buckets')

    # get names and links for duplications
    extra_fakus = []
    extra_fakus_Link = []
    for i in range(len(aggs)):
        try:
            extra_fakus.append(aggs[i].get('key'))

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
                extra_fakus_Link.append(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('key'))
            else:
                extra_fakus_Link.append(None)

            # prints to verify the results (next 5 lines)
            if len(result_link_search.get('aggregations').get('duplicateWords').get('buckets')) > 0:
                print(extra_fakus[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + extra_fakus_Link[i] + '   (' + str(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('doc_count')) + ')')
            else:
                print(extra_fakus[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + 'None   (0)')
        except:
            continue

    # delete searching-index
    es.indices.delete(index=index_name_Searching)

    print("Number of extra found faculties: " + str(len(extra_fakus)))

# main
if __name__ == '__main__':
    #if es.indices.exists(index="searching_faculties_temp"):
    #    es.indices.delete(index="searching_faculties_temp")

    check_elastic()

    i_name = "crawl-rawdata-ude" # wird am Ende übergeben
    #i_name = "crawl-rawdata-rub"  # wird am Ende übergeben

    index_name_uni = i_name
    index_name_Searching = index_name_Searching + i_name[i_name.rfind("-"):]

    link_req_short = i_name[i_name.rfind("-") + 1:]

    find_faculties(link_req_short=link_req_short)