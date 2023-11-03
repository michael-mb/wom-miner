from elasticsearch import Elasticsearch
from lxml import etree
from urllib.parse import urljoin
from urllib.parse import urlparse

es = Elasticsearch({'host':'wom.handte.org', 'port': 443, 'path_prefix':'elastic', 'scheme':'https'},  basic_auth=('wom', 'H7kSk2~5GnybwE{}J4jdPj)qS74&tbXBK-b))+GN'), request_timeout=60, max_retries=5, retry_on_timeout=True)

index_name_uni = ""
index_name_Searching = "searching_faculties_temp_2"

def find_faculties():
    query = {
        "match": {
            "links.text": "Fakultät"
        }
    }
    aggs = {
        "f": {
            "terms": {
                "size": 10000,
                "field": "links.text.keyword"
            }
        }
    }
    docs = es.search(index=index_name_uni, query=query, aggregations=aggs, size=0)

    fs = []
    fs_count = []
    for hit in docs.get('aggregations').get('f').get('buckets'):
        if "Fakultät" in hit.get('key'):
            if hit.get('doc_count') < 10:
                continue

            n = hit.get('key')
            
            if n.endswith(" Fakultät"):
                if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234 öäüÖÜÄ-' for c in n):
                    continue

                splitted = n.split(" ")
                if len(splitted) != 2:
                    continue

                if not splitted[0].endswith("e"):
                    continue
                
                too_short = False
                for s in splitted:
                    if len(s) < 8:
                        too_short = True
                        break
                if too_short:
                    continue

                while n.startswith(" "):
                    n = n[1:]
                
                if n not in fs:
                    fs.append(hit.get('key'))
                    fs_count.append(hit.get('doc_count'))

            elif n.startswith("Fakultät für"):
                if n.endswith("-"):
                    continue

                if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234 öäüÖÜÄ--' for c in n):
                    continue

                splitted = n.split(" ")
                if len(splitted) < 3 or len(splitted) > 7:
                    continue

                wrong_len = False
                for i in range(len(splitted)):
                    if splitted[i] == "für" or splitted[i] == "und":
                        continue
                    if splitted[i].endswith("-"):
                        if splitted[i + 1] != "und":
                            wrong_len = True
                            break
                        else:
                            continue
                    if len(splitted[i]) < 6:
                        wrong_len = True
                        break
                if wrong_len:
                    continue

                while n.startswith(" "):
                    n = n[1:]
                
                if n not in fs:
                    fs.append(hit.get('key'))
                fs_count.append(hit.get('doc_count'))

    fs_no_double = []

    for i in range(len(fs)):
        if i == 0:
            fs_no_double.append(fs[i])
        elif fs[i] in fs_no_double:
            continue
        else:
            is_inserted = False
            for o in range(len(fs_no_double)):
                if fs[i] in fs_no_double[o]:
                    fs[i] = fs_no_double[o]
                    is_inserted = True
                    break
                elif fs_no_double[o] in fs[i]:
                    is_inserted = True
                    break
            if not is_inserted:
                fs_no_double.append(fs[i])

    fs = fs_no_double

    for i in range(len(fs)):
        print(str(fs_count[i]) + " --- " + fs[i])
    """
    fs_links = []

    for f in fs:
        q = {
            "match_phrase": {
                "links.text": f
            }
        }
        docs = es.search(index=index_name_uni, query=q, size=10000)

        l = []
        l_count = []

        for hit in docs.get('hits').get('hits'):
            for link in hit.get('_source').get('links'):
                if link.get('text') == f:
                    #fs_links.append(link.get('target'))
                    if link.get('target') not in l:
                        l.append(link.get('target'))
                        l_count.append(1)
                    else:
                        index = l.index(link.get('target'))
                        l_count[index] = l_count[index] + 1

        highest = 0
        current = ""
        for i in range(len(l)):
            if l_count[i] > highest:
                highest = l_count[i]
                current = l[i]
        fs_links.append(current)
    """
            
    print("-------------------------------")
    mappings = {
        "properties": {
            "text": {"type": "keyword"},
            "link": {"type": "keyword"}
        }
    }
    if es.indices.exists(index=index_name_Searching):
        es.indices.delete(index=index_name_Searching)
    es.indices.create(index=index_name_Searching, mappings=mappings)

    appended_fakus = []
    for a in fs:
        if " für " in a:
            a_2 = a[a.find(" für ") + 5:]
            appended_fakus.append(a_2)
    for a in fs:
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

    for i in range(len(extra_fakus)):
        n = extra_fakus[i]

        if n == "":
            continue

        if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234 öäüÖÜÄ-()' for c in n):
            continue

        if n.endswith("-"):
            continue

        splitted = n.split(" ")
        if len(splitted) < 2 or len(splitted) > 7:
            continue

        wrong_len = False
        for i in range(len(splitted)):
            if splitted[i] == "für" or splitted[i] == "und" or splitted[i] == "of":
                continue
            if splitted[i].endswith("-"):
                continue
                #if splitted[i + 1] != "und":
                #    wrong_len = True
                #    break
                #else:
                #    continue
            if len(splitted[i]) < 6:
                wrong_len = True
                break
        if wrong_len:
            continue
        

        doc = {
            "text": extra_fakus[i],
            "link": extra_links[i],
        }
        es.index(index=index_name_Searching, id=i, document=doc)

    es.indices.refresh(index=index_name_Searching)

    query_body_aggregation = {
        "duplicateNames": {
            "terms": {
                "field": "text",
                "min_doc_count": 70,
                "size": 10000
            }
        }
    }
    result_aggregation = es.search(index=index_name_Searching, aggregations=query_body_aggregation, size=0)

    aggs = result_aggregation.get('aggregations').get('duplicateNames').get('buckets')

    for i in range(len(aggs)):
        print(str(aggs[i].get('doc_count')) + " --- " + aggs[i].get('key'))






    es.indices.delete(index=index_name_Searching)

# main
if __name__ == '__main__':

    i_name = "crawl-rawdata-ude" # wird am Ende übergeben
    #i_name = "crawl-rawdata-rub"  # wird am Ende übergeben

    index_name_uni = i_name
    index_name_Searching = index_name_Searching + i_name[i_name.rfind("-"):]

    link_req_short = i_name[i_name.rfind("-") + 1:]

    find_faculties()

    print("................................")

    i_name = "crawl-rawdata-rub"

    index_name_uni = i_name
    index_name_Searching = index_name_Searching + i_name[i_name.rfind("-"):]

    link_req_short = i_name[i_name.rfind("-") + 1:]

    #find_faculties()

"""
1838 --- Fakultät für Philologie --- http://www.dekphil.rub.de/ --- https://www.dekphil.ruhr-uni-bochum.de/
1305 --- Fakultät für Philosophie und Erziehungswissenschaft --- https://www.pe.ruhr-uni-bochum.de/fakultaet/index.html.de --- https://www.pe.ruhr-uni-bochum.de/
947 --- Fakultät für Maschinenbau --- http://www.mb.rub.de/ --- https://www.mb.rub.de/
884 --- Fakultät für Bau- und Umweltingenieurwissenschaften --- http://www.fbi.ruhr-uni-bochum.de/index.html.de --- https://www.fbi.ruhr-uni-bochum.de/
744 --- Medizinische Fakultät --- https://www.medizin.ruhr-uni-bochum.de/index.html.de --- https://www.medizin.ruhr-uni-bochum.de/
678 --- Fakultät für Mathematik --- http://www.ruhr-uni-bochum.de/ffm --- https://math.ruhr-uni-bochum.de/
655 --- Fakultät für Psychologie --- http://www.psy.ruhr-uni-bochum.de/ --- https://www.psy.ruhr-uni-bochum.de/
594 --- Fakultät für Chemie und Biochemie --- https://www.chemie.ruhr-uni-bochum.de/ --- https://www.chemie.ruhr-uni-bochum.de/
515 --- Fakultät für Biologie und Biotechnologie --- http://www.biologie.ruhr-uni-bochum.de/ --- https://www.biologie.ruhr-uni-bochum.de/
445 --- Fakultät für Ostasienwissenschaften --- http://www.ruhr-uni-bochum.de/oaw --- https://www.ruhr-uni-bochum.de/oaw/de/index.shtml
437 --- Fakultät für Wirtschaftswissenschaft --- http://www.wiwi.rub.de --- https://www2.wiwi.rub.de/
342 --- Fakultät für Geschichtswissenschaft --- http://www.ruhr-uni-bochum.de/geschichtswissenschaft --- http://www.gw.ruhr-uni-bochum.de/
307 --- Fakultät für Geschichte --- http://www.ruhr-uni-bochum.de/geschichtswissenschaft --- http://www.gw.ruhr-uni-bochum.de/
303 --- Fakultät für Informatik --- https://informatik.rub.de --- https://informatik.rub.de/
282 --- Fakultät für Sozialwissenschaft --- http://www.sowi.rub.de/index.html.de --- https://www.sowi.ruhr-uni-bochum.de/index.html
267 --- Juristische Fakultät --- http://www.jura.ruhr-uni-bochum.de/ --- https://www.jura.rub.de/
221 --- Fakultät für Physik und Astronomie --- https://www.physik.ruhr-uni-bochum.de/ --- https://www.physik.ruhr-uni-bochum.de/
172 --- Fakultät für Geowissenschaften --- https://www.geos.ruhr-uni-bochum.de/ --- https://www.geos.ruhr-uni-bochum.de/
158 --- Katholisch-Theologische Fakultät --- https://index.html.de --- https://www.kath.ruhr-uni-bochum.de/
86 --- Fakultät für Sportwissenschaft --- http://www.sportwissenschaft.ruhr-uni-bochum.de --- https://sport.ruhr-uni-bochum.de/de
52 --- Evangelisch-Theologische Fakultät --- http://www.ev-theol.ruhr-uni-bochum.de/ --- http://www.ev.ruhr-uni-bochum.de/
41 --- Fakultät für Elektrotechnik und Informationstechnik --- http://www.ei.ruhr-uni-bochum.de/ --- https://etit.ruhr-uni-bochum.de/
"""