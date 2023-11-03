from elasticsearch import Elasticsearch
import sys
from lxml import etree
import html

# start elasticsearch-connection
# local
#es = Elasticsearch({'host': 'localhost', 'port': 9200, 'scheme': 'https'}, basic_auth=('elastic', 'elastic'), verify_certs=False, ssl_show_warn=False)
# uni-server
es = Elasticsearch({'host':'wom.handte.org', 'port': 443, 'path_prefix':'elastic', 'scheme':'https'},  basic_auth=('wom', 'H7kSk2~5GnybwE{}J4jdPj)qS74&tbXBK-b))+GN'), request_timeout=60, max_retries=5, retry_on_timeout=True)

index_name_uni = ""
index_name_Searching = "searching_lehrshuhl_temp"

def check_elastic():
    if not es.ping():
        sys.exit("No connection to Elasticsearch")


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
            if html_string[position] == '(' or html_string[position] == ')' or html_string[position] == ';' or html_string[position] == '.' or html_string[position] == '!' or html_string[position] == '?' or html_string[position] == ':' or html_string[position] == '>' or html_string[position] == '<' or html_string[position] == '"' or html_string[position] == '“':
                break
            word = html_string[position] + word

    word = word.replace(" ", "")
    word = word.replace("&#8211", "")
    word = word.replace("&amp", "")
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
            if html_string[position] == '(' or html_string[position] == ')' or html_string[position] == ';' or html_string[position] == '.' or html_string[position] == '!' or html_string[position] == '?' or html_string[position] == ':' or html_string[position] == '>' or html_string[position] == '"' or html_string[position] == '“':
                break
            if html_string[position] == '<':
                temp = html_string[position] + html_string[position + 1] + html_string[position + 2] + html_string[position + 3]
                if temp == "<br>":
                    word += " "
                    counter += 1
                    position += 4
                    if counter == number:
                        break
                    continue
                else:
                    break
            word += html_string[position]
            position += 1

    word = word.replace(" ", "")
    word = word.replace("&#8211", "")
    word = word.replace("&amp", "")
    return word


def find_lehrshuhl():
    counter_lehrs = 0

    # create second index for searching operations
    mappings = {
        "properties": {
            "text": {"type": "keyword"},
            "link": {"type": "keyword"}
        }
    }
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
                }, {
                    "query_string": {
                        "query": "chair",
                        "default_field": "content"
                    }
                }, {
                    "query_string": {
                        "query": "department",
                        "default_field": "content"
                    }
                },
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
        current_term = es.termvectors(index=index_name_uni, id=id, fields="content", term_statistics=False, field_statistics=False, payloads=False, positions=False, offsets=True)
        current_doc = es.get(index=index_name_uni, id=id)
        html_string = current_doc.get('_source').get('content')

        lehr_deu = []
        lehr_eng = []
        abt_deu = []
        abt_eng = []
        lehr = []

        if current_term.get('term_vectors').get('content').get('terms').get('lehrstuhl') != None:
            lehr_deu = current_term.get('term_vectors').get('content').get('terms').get('lehrstuhl').get('tokens')
        if current_term.get('term_vectors').get('content').get('terms').get('chair') != None:
            lehr_eng = current_term.get('term_vectors').get('content').get('terms').get('chair').get('tokens')
        if current_term.get('term_vectors').get('content').get('terms').get('abteilung') != None:
            abt_deu = current_term.get('term_vectors').get('content').get('terms').get('abteilung').get('tokens')
        if current_term.get('term_vectors').get('content').get('terms').get('department') != None:
            abt_eng = current_term.get('term_vectors').get('content').get('terms').get('department').get('tokens')

        if isinstance(lehr_deu, list):
            lehr = lehr + lehr_deu
        if isinstance(lehr_eng, list):
            lehr = lehr + lehr_eng
        if isinstance(abt_deu, list):
            lehr = lehr + abt_deu
        if isinstance(abt_eng, list):
            lehr = lehr + abt_eng

        for i in range(len(lehr)):
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
            # existing if with href
            link = None
            # search previous >
            # then look if href= found before < is found
            # for something like this: <a href="link">lehrstuhl für Bla<\a>
            current_char = html_string[start]
            current_char_counter = start
            while current_char != ">" and current_char_counter > -1 and current_char_counter < len(html_string):
                current_char_counter -= 1
                current_char = html_string[current_char_counter]

            last_dob = current_char_counter
            while current_char != "<" and current_char_counter > -1 and current_char_counter < len(html_string):
                if start - current_char_counter > 150:
                    break
                if html_string[current_char_counter - 6:current_char_counter] == 'href="':
                    link = html_string[current_char_counter:last_dob]
                    break
                if current_char == '"':
                    last_dob = current_char_counter
                current_char_counter -= 1
                current_char = html_string[current_char_counter]

            # if link not found yet -> search for deeper a tag
            # for something like this: <a href="link"><strong>lehrstuhl für Bla<\strong><\a>
            if link == None:
                current_char = html_string[start]
                current_char_counter = start
                while current_char != ">" and current_char_counter > -1 and current_char_counter < len(html_string):
                    current_char_counter -= 1
                    current_char = html_string[current_char_counter]

                current_char_counter -= 1
                current_char = html_string[current_char_counter]
                while current_char != ">" and current_char_counter > -1 and current_char_counter < len(html_string):
                    current_char_counter -= 1
                    current_char = html_string[current_char_counter]

                last_dob = current_char_counter
                while current_char != "<" and current_char_counter > -1 and current_char_counter < len(html_string):
                    if start - current_char_counter > 150:
                        break
                    if html_string[current_char_counter - 6:current_char_counter] == 'href="':
                        link = html_string[current_char_counter:last_dob]
                        break
                    if current_char == '"':
                        last_dob = current_char_counter
                    current_char_counter -= 1
                    current_char = html_string[current_char_counter]

            # if link still None try for following
            # for something like this: <a href="link" title="lehrstuhl für Bla">BlaBlaBla<\a>
            if link == None:
                current_char = html_string[start]
                current_char_counter = start
                last_dob = current_char_counter
                while current_char != "<" and current_char_counter > -1 and current_char_counter < len(html_string):
                    if start - current_char_counter > 150:
                        break
                    if html_string[current_char_counter - 6:current_char_counter] == 'href="':
                        link = html_string[current_char_counter:last_dob]
                        break
                    if current_char == '"':
                        last_dob = current_char_counter
                    current_char_counter -= 1
                    current_char = html_string[current_char_counter]

            # check if link is existing and absolute or relative
            if link == None:
                pass
            elif link == "":
                pass
            elif link.startswith("http"):
                pass  # is absolute -> do nothing
            else:
                link = current_doc.get('_source').get('url') + link  # link relativ -> add prefix

            # list of definitely wrong lehrstuhle-names
            # add more entries to list, if other wrong names are identified # todo
            sort_out_lehr_words = ["Lehrstuhl", "Lehrstühle", "Abteilung", "Chair", "chair", "Department", "department", "Lehrstuhl für", "Lehrstühle für", "Abteilung für", "Chair for", "chair for", "Department for", "department for", "Lehrstuhl Prof"]

            # add new doc to searching index
            for p in range(len(lehr_strings)):
                lehr_strings[p] = lehr_strings[p].replace("[&hellip", " ")
                while lehr_strings[p].startswith(" "):
                    lehr_strings[p] = lehr_strings[p][1:]
                while lehr_strings[p].endswith(" ") or lehr_strings[p].endswith(","):
                    lehr_strings[p] = lehr_strings[p][:-1]
                if lehr_strings[p].endswith("von Prof"):
                    lehr_strings[p] = lehr_strings[p][:-9]
                if lehr_strings[p].endswith("von"):
                    lehr_strings[p] = lehr_strings[p][:-4]
                if lehr_strings[p] in sort_out_lehr_words:
                    continue
                if "chair" in lehr_strings[p]:
                    if "chair for" not in lehr_strings[p]:
                        continue
                if "Chair" in lehr_strings[p]:
                    if "Chair for" not in lehr_strings[p]:
                        continue
                if "Department" in lehr_strings[p]:
                    if "Department for" not in lehr_strings[p]:
                        continue
                if "department" in lehr_strings[p]:
                    if "department for" not in lehr_strings[p]:
                        continue
                if "Abteilung" in lehr_strings[p]:
                    if "Abteilung für" not in lehr_strings[p]:
                        continue
                doc = {
                    "text": lehr_strings[p],
                    "link": link,
                }
                es.index(index=index_name_Searching, id=counter_lehrs, document=doc)
                counter_lehrs += 1

    # check for duplicated names
    es.indices.refresh(index=index_name_Searching)

    query_body_aggregation = {
        "duplicateNames": {
            "terms": {
                "field": "text",
                "min_doc_count": 1,
                "size": 10000
                # minimal appearance of lehrstuhls-string to be accepted as an lehrstuhls-name # todo evaluate a good min_doc_count
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
                    pass  # todo more (somethings like: "Fakultät für Wirtschaftswissenschaften" and "XY Fakultät für Wirtschaftswissenschaften" -> unclear if needed or makes sense -> tests will show
            if not is_inserted:
                lehrs_sorted.append(aggs[i].get('key'))
                lehrs_appearance.append(aggs[i].get('doc_count'))

    lehrs_without_double = []
    for i in range(len(lehrs_sorted)):
        if lehrs_sorted[i] in lehrs_without_double:
            continue
        else:
            lehrs_without_double.append(lehrs_sorted[i])
    lehrs_sorted = lehrs_without_double

    # get links for duplications
    lehrs = []
    lehrs_Link = []
    for i in range(len(lehrs_sorted)):
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
                    "min_doc_count": 2,
                    "size": 10000
                    # minimal appearance of link to be accepted as an lehrstuhls-link # todo evaluate a good min_doc_count
                }
            }
        }

        result_link_search = es.search(index=index_name_Searching, query=query_get_link, aggregations=aggs_get_link,
                                       size=10000)

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

    print("Number of found lehrshuhl: " + str(len(lehrs)))
    print("-----------------------------------")

    # starting part two of search (with html-tags)
    sh = []
    for a in lehrs:
        # sh.append({"query_string": {"query": a.get('key'), "default_field": "content"}})
        sh.append({"match_phrase": {"content": a}})

    q = {}

    q["bool"] = {"should": sh, "minimum_should_match": 2}  # todo -> minimum_should_match -> evaluate a good value

    docs_with_multiple_lehr = es.search(index=index_name_uni, query=q, size=500, sort=[{"timestamp": "asc"}])

    current_multiple_i_max = len(docs_with_multiple_lehr.get('hits').get('hits')) - 1

    extra_lehrs = []
    extra_links = []

    # for each document with multiple occurences of already found chairs search for structure-patterns
    for i in range((current_multiple_i_max + 1)):
        current_html = docs_with_multiple_lehr.get('hits').get('hits')[i].get('_source').get('content')

        current_xpath_tree = etree.HTML(current_html)
        # current_xpath_tree = etree.fromstring(current_html)
        structure = []

        for current_lehr in lehrs:
            elems = current_xpath_tree.xpath("//*[contains(text(), '" + current_lehr + "')]")

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
                            if outer_struct.find("]", last_o) < outer_struct.find("[", last_o) or (
                                    outer_struct.find("]", last_o) != -1 and outer_struct.find("[", last_o) == -1):
                                if inner_struct.find("]", last_o) < inner_struct.find("[", last_o) or (
                                        inner_struct.find("]", last_o) != -1 and inner_struct.find("[", last_o) == -1):
                                    if outer_struct.rfind("[", 0, last_o) > outer_struct.rfind("]", 0, last_o) or (
                                            outer_struct.rfind("[", 0, last_o) != -1 and outer_struct.rfind("]", 0,
                                                                                                            last_o) == -1):
                                        if inner_struct.rfind("[", 0, last_o) > inner_struct.rfind("]", 0, last_o) or (
                                                inner_struct.rfind("[", 0, last_o) != -1 and inner_struct.rfind("]", 0,
                                                                                                                last_o) == -1):
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
                    if len(found) > 100:
                        break
                    
                    extra_lehrs.append(found)

                    # check for link
                    if "/a/" in current_path:
                        link_path = current_path[0: current_path.find("/a/") + 3] + "@href"
                        elem_link = current_xpath_tree.xpath(link_path)
                        if elem_link == []:
                            extra_links.append(None)
                        else:
                            extra_links.append(elem_link[0])
                    elif "/area/" in current_path:
                        link_path = current_path[0: current_path.find("/area/") + 6] + "@href"
                        elem_link = current_xpath_tree.xpath(link_path)
                        if elem_link == []:
                            extra_links.append(None)
                        else:
                            extra_links.append(elem_link[0])
                    elif "/base/" in current_path:
                        link_path = current_path[0: current_path.find("/base/") + 6] + "@href"
                        elem_link = current_xpath_tree.xpath(link_path)
                        if elem_link == []:
                            extra_links.append(None)
                        else:
                            extra_links.append(elem_link[0])
                    elif "/link/" in current_path:
                        link_path = current_path[0: current_path.find("/link/") + 6] + "@href"
                        elem_link = current_xpath_tree.xpath(link_path)
                        if elem_link == []:
                            extra_links.append(None)
                        else:
                            extra_links.append(elem_link[0])
                    else:
                        extra_links.append(None)

                    # check if extra links are absolute or relative
                    if extra_links[-1] == None:
                        pass
                    elif extra_links[-1] == "":
                        pass
                    elif extra_links[-1].startswith("http"):
                        pass  # is absolute -> do nothing
                    else:
                        extra_links[-1] = docs_with_multiple_inst.get('hits').get('hits')[i].get('_source').get('url') + extra_links[-1]  # link relativ -> add prefix

    # while loop until all results are done
    while (current_multiple_i_max >= 499):
        current_multiple_last_sort = docs_with_multiple_lehr.get('hits').get('hits')[current_multiple_i_max].get('sort')
        # get next result-page
        docs_with_multiple_lehr = es.search(index=index_name_uni, query=q, size=500, search_after=current_multiple_last_sort, sort=[{"timestamp": "asc"}])

        current_multiple_i_max = len(docs_with_multiple_lehr.get('hits').get('hits')) - 1

        # for each document with multiple occurences of already found chairs search for structure-patterns
        # like above
        for i in range((current_multiple_i_max + 1)):
            current_html = docs_with_multiple_lehr.get('hits').get('hits')[i].get('_source').get('content')

            current_xpath_tree = etree.HTML(current_html)
            # current_xpath_tree = etree.fromstring(current_html)
            structure = []

            for current_lehr in lehrs:
                elems = current_xpath_tree.xpath("//*[contains(text(), '" + current_lehr + "')]")

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
                                if outer_struct.find("]", last_o) < outer_struct.find("[", last_o) or (
                                        outer_struct.find("]", last_o) != -1 and outer_struct.find("[", last_o) == -1):
                                    if inner_struct.find("]", last_o) < inner_struct.find("[", last_o) or (
                                            inner_struct.find("]", last_o) != -1 and inner_struct.find("[",
                                                                                                       last_o) == -1):
                                        if outer_struct.rfind("[", 0, last_o) > outer_struct.rfind("]", 0, last_o) or (
                                                outer_struct.rfind("[", 0, last_o) != -1 and outer_struct.rfind("]", 0,
                                                                                                                last_o) == -1):
                                            if inner_struct.rfind("[", 0, last_o) > inner_struct.rfind("]", 0,
                                                                                                       last_o) or (
                                                    inner_struct.rfind("[", 0, last_o) != -1 and inner_struct.rfind("]",
                                                                                                                    0,
                                                                                                                    last_o) == -1):
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
                        if len(found) > 100:
                            break
                        
                        extra_lehrs.append(found)

                        # check for link
                        if "/a/" in current_path:
                            link_path = current_path[0: current_path.find("/a/") + 3] + "@href"
                            elem_link = current_xpath_tree.xpath(link_path)
                            if elem_link == []:
                                extra_links.append(None)
                            else:
                                extra_links.append(elem_link[0])
                        elif "/area/" in current_path:
                            link_path = current_path[0: current_path.find("/area/") + 6] + "@href"
                            elem_link = current_xpath_tree.xpath(link_path)
                            if elem_link == []:
                                extra_links.append(None)
                            else:
                                extra_links.append(elem_link[0])
                        elif "/base/" in current_path:
                            link_path = current_path[0: current_path.find("/base/") + 6] + "@href"
                            elem_link = current_xpath_tree.xpath(link_path)
                            if elem_link == []:
                                extra_links.append(None)
                            else:
                                extra_links.append(elem_link[0])
                        elif "/link/" in current_path:
                            link_path = current_path[0: current_path.find("/link/") + 6] + "@href"
                            elem_link = current_xpath_tree.xpath(link_path)
                            if elem_link == []:
                                extra_links.append(None)
                            else:
                                extra_links.append(elem_link[0])
                        else:
                            extra_links.append(None)

                        # check if extra links are absolute or relative
                        if extra_links[-1] == None:
                            pass
                        elif extra_links[-1] == "":
                            pass
                        elif extra_links[-1].startswith("http"):
                            pass  # is absolute -> do nothing
                        else:
                            extra_links[-1] = docs_with_multiple_inst.get('hits').get('hits')[i].get('_source').get('url') + extra_links[-1]  # link relativ -> add prefix

    # print extra found insitutes
    # for tests
    for i in range(len(extra_lehrs)):
        print(extra_lehrs[i] + "   " + str(extra_links[i]))

    print("Number of extra found lehrstuhl: " + str(len(extra_lehrs)))

    # delete searching-index
    es.indices.delete(index=index_name_Searching)


# main
if __name__ == '__main__':
    #if es.indices.exists(index="searching_lehrshuhl_temp"):
    #    es.indices.delete(index="searching_lehrshuhl_temp")
    
    check_elastic()

    i_name = "crawl-rawdata-ude" # wird am Ende übergeben

    index_name_uni = i_name
    index_name_Searching = index_name_Searching + i_name[i_name.rfind("-"):]

    # check for index input
    #if len(sys.argv) == 2:
    #    index_name_uni = sys.argv[1]
    #else:
    #    index_name_uni = "test2"  # default

    find_lehrshuhl()

