from elasticsearch import Elasticsearch
import sys

# start elasticsearch-connection
# local
es = Elasticsearch({'host':'localhost', 'port': 9200, 'scheme': 'https'}, basic_auth=('elastic', 'elastic'), verify_certs=False, ssl_show_warn=False)
# uni-server
#es = Elasticsearch({'host':'wom.handte.org', 'port': 443, 'path_prefix':'elastic', 'scheme':'https'},  basic_auth=('wom', 'H7kSk2~5GnybwE{}J4jdPj)qS74&tbXBK-b))+GN'))

index_name_uni = ""

def check_elastic():
    if not es.ping():
        sys.exit("No connection to Elasticsearch")

def getWordsBefore(start, html, word, number):
    position = start
    counter = 0
    while True:
        position -= 1
        if position == -1:
            break
        else:
            if html[position] == ' ':
                counter += 1
                if counter == number:
                    break
            if html[position] == '\n':
                break
            # stop at special characters
            if html[position] == '(' or html[position] == ')' or html[position] == ',' or html[position] == '.' or html[position] == '!' or html[position] == '?' or html[position] == ':' or html[position] == '>' or html[position] == '<' or html[position] == ';' or html[position] == '"' or html[position] == '“':
                break
            word = html[position] + word

    word = word.replace(" ", "")
    word = word.replace("&#8211", "")
    return word

def getWordsAfter(end, html, word, number):
    position = end
    counter = 0
    while True:
        if position == len(html):
            break
        else:
            if html[position] == ' ':
                counter += 1
                if counter == number:
                    break
            if html[position] == '\n':
                break
            # stop at special characters
            if html[position] == '(' or html[position] == ')' or html[position] == ',' or html[position] == '.' or html[position] == '!' or html[position] == '?' or html[position] == ':' or html[position] == '>' or html[position] == ';' or html[position] == '"' or html[position] == '“' :
                break
            if html[position] == '<':
                temp = html[position] + html[position + 1] + html[position + 2] + html[position + 3]
                if temp == "<br>":
                    word += " "
                    counter += 1
                    position += 4
                    if counter == number:
                        break
                    continue
                else:
                    break
            word += html[position]
            position += 1

    word = word.replace(" ", "")
    word = word.replace("&#8211", "")
    return word

def find_faculties():
    index_name_Searching = "searching_faculties_temp"
    counter_Fakus = 0

    # create second index for searching operations
    mappings = {
        "properties": {
            "text": {"type": "keyword"},
            "link": {"type": "keyword"}
        }
    }
    es.indices.create(index=index_name_Searching, mappings=mappings)

    # get ids from sides with "Fakultät" or "faculty"
    ids = []

    query = {
        "dis_max": {
            "queries": [
                {
                    "query_string": {
                        "query": "Fakultät",
                        "default_field": "html"
                    }
                }, {
                    "query_string": {
                        "query": "faculty",
                        "default_field": "html"
                    }
                }, {
                    "query_string": {
                        "query": "Faculty",
                        "default_field": "html"
                    }
                }
            ]
        }
    }

    docs_with_fakul = es.search(index=index_name_uni, query=query, size=500, sort=[{"name.keyword": "asc"}])

    current_i_max = len(docs_with_fakul.get('hits').get('hits')) - 1
    # get ids from current query
    for hit in docs_with_fakul.get('hits').get('hits'):
        ids.append(hit.get('_id'))

    # while loop until all results are done
    while (current_i_max >= 499):
        current_last_sort = docs_with_fakul.get('hits').get('hits')[current_i_max].get('sort')
        # get next result-page
        docs_with_fakul = es.search(index=index_name_uni, query=query, size=500, search_after=current_last_sort, sort=[{"name.keyword": "asc"}])

        current_i_max = len(docs_with_fakul.get('hits').get('hits')) - 1
        for hit in docs_with_fakul.get('hits').get('hits'):
            ids.append(hit.get('_id'))

    # go through all the docs from ids
    # get the word fakultät/ faculty with previous and following words
    # (examples: "Medizinische Fakultät", "Fakultät für Physik", "Fakultät für Angewandte Informatik", "Fakultät für Chemie und Biochemie") -> ger -> -1 +2 +3 +4
    # (examples: "Medical faculty", "faculty of chemistry", "faculty of applied science", "faculty of X and Y", "faculty of Business Administration and X / XY") -> eng -> -1 +2 +3 +4 +5 +6
    for id in ids:
        current_term = es.termvectors(index=index_name_uni, id=id, fields="html", term_statistics=False, field_statistics=False, payloads=False, positions=False, offsets=True)
        current_doc = es.get(index=index_name_uni, id=id)
        html = current_doc.get('_source').get('html')

        fakul_deu = []
        fakul_eng = []
        fakul = []
        
        if current_term.get('term_vectors').get('html').get('terms').get('fakultät') != None:
            fakul_deu = current_term.get('term_vectors').get('html').get('terms').get('fakultät').get('tokens')
        if current_term.get('term_vectors').get('html').get('terms').get('faculty') != None:
            fakul_eng = current_term.get('term_vectors').get('html').get('terms').get('faculty').get('tokens')

        if isinstance(fakul_deu, list):
            fakul = fakul + fakul_deu
        if isinstance(fakul_eng, list):
            fakul = fakul + fakul_eng

        for i in range(len(fakul)):
            start = fakul[i].get('start_offset')
            end = fakul[i].get('end_offset')

            fakul_string = ''
            for o in range(start, end):
                fakul_string += html[o]

            fakul_strings = []

            # -1
            fakul_words = getWordsBefore(start=start, html=html, word=fakul_string, number=2)
            if fakul_words not in fakul_strings:
                fakul_strings.append(fakul_words)
            # +2 +3 +4 +5 +6
            for p in range(3, 8):
                fakul_words = getWordsAfter(end=end, html=html, word=fakul_string, number=p)
                if fakul_words not in fakul_strings:
                    fakul_strings.append(fakul_words)

            # get the link to "fakultät" if existing
            # existing if with href
            link = None
            # search previous >
            # then look if href= found before < is found
            current_char = html[start]
            current_char_counter = start
            while current_char != ">":
                current_char_counter -= 1
                current_char = html[current_char_counter]

            last_dob = current_char_counter
            while current_char != "<":
                if start - current_char_counter > 150:
                    break
                if html[current_char_counter-6:current_char_counter] == 'href="':
                    link = html[current_char_counter:last_dob]
                    break
                if current_char == '"':
                    last_dob = current_char_counter
                current_char_counter -= 1
                current_char = html[current_char_counter]
                
            # if link not found yet -> search for deeper a tag
            # for something like this: <a href="link"><strong>Institut für Bla<\strong><\a>
            if link == None:
                current_char = html[start]
                current_char_counter = start
                while current_char != ">":
                    current_char_counter -= 1
                    current_char = html[current_char_counter]

                current_char_counter -= 1
                current_char = html[current_char_counter]
                while current_char != ">":
                    current_char_counter -= 1
                    current_char = html[current_char_counter]

                last_dob = current_char_counter
                while current_char != "<":
                    if start - current_char_counter > 150:
                        break
                    if html[current_char_counter - 6:current_char_counter] == 'href="':
                        link = html[current_char_counter:last_dob]
                        break
                    if current_char == '"':
                        last_dob = current_char_counter
                    current_char_counter -= 1
                    current_char = html[current_char_counter]

            # if link still None try for following
            # for something like this: <a href="link" title="Institut für Bla">BlaBlaBla<\a>
            if link == None:
                current_char = html[start]
                current_char_counter = start
                last_dob = current_char_counter
                while current_char != "<":
                    if start - current_char_counter > 150:
                        break
                    if html[current_char_counter - 6:current_char_counter] == 'href="':
                        link = html[current_char_counter:last_dob]
                        break
                    if current_char == '"':
                        last_dob = current_char_counter
                    current_char_counter -= 1
                    current_char = html[current_char_counter]

            # check if link is existing and absolute or relative
            if link == None:
                pass
            elif link == "":
                pass
            elif link.startswith("http"):
                pass # is absolute -> do nothing
            else:
                link = current_doc.get('_source').get('name') + link # link relativ -> add prefix

            # list of definitely wrong faculty-names
            # add more entries to list, if other wrong names are identified # todo
            sort_out_fakul_words = ["Fakultät", "the Faculty", "der Fakultät", "die Fakultät", "the faculty"]

            # add new doc to searching index
            for p in range(len(fakul_strings)):
                while fakul_strings[p].startswith(" "):
                    fakul_strings[p] = fakul_strings[p][1:]
                while fakul_strings[p].endswith(" ") or fakul_strings[p].endswith(","):
                    fakul_strings[p] = fakul_strings[p][:-1]
                if fakul_strings[p] in sort_out_fakul_words:
                    continue
                doc = {
                    "text": fakul_strings[p],
                    "link": link,
                }
                es.index(index=index_name_Searching, id=counter_Fakus, document=doc)
                counter_Fakus += 1

    # check for duplicated names
    es.indices.refresh(index=index_name_Searching)

    query_body_aggregation = {
        "duplicateNames": {
            "terms": {
                "field": "text",
                "min_doc_count": 2,
                "size": 10000
                # minimal appearance of fakultäts-string to be accepted as an fakultäts-name # todo evaluate a good min_doc_count
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
                    pass # todo more (somethings like: "Fakultät für Wirtschaftswissenschaften" and "XY Fakultät für Wirtschaftswissenschaften" -> unclear if needed or makes sense -> tests will show
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

    # get links for duplications
    fakus = []
    fakus_Link = []
    for i in range(len(fakus_sorted)):
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
                    # minimal appearance of link to be accepted as an fakultäts-link # todo evaluate a good min_doc_count
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
            print(fakus[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + fakus_Link[i] + '   (' + str(result_link_search.get('aggregations').get('duplicateWords').get('buckets')[0].get('doc_count')) + ')')
        else:
            print(fakus[i] + '   (' + str(aggs[i].get('doc_count')) + ')' + '   ' + 'None   (0)')

    # delete searching-index
    es.indices.delete(index=index_name_Searching)

    print("Number of found faculties: " + str(len(fakus)))

# main
if __name__ == '__main__':
    if es.indices.exists(index="searching_faculties_temp"):
        es.indices.delete(index="searching_faculties_temp")

    check_elastic()

    # check for index input
    if len(sys.argv) == 2:
        index_name_uni = sys.argv[1]
    else:
        index_name_uni = "test2" # default

    find_faculties()

    