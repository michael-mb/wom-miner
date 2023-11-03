from elasticsearch import Elasticsearch

es = Elasticsearch({'host':'wom.handte.org', 'port': 443, 'path_prefix':'elastic', 'scheme':'https'},  basic_auth=('wom', 'H7kSk2~5GnybwE{}J4jdPj)qS74&tbXBK-b))+GN'), request_timeout=60, max_retries=5, retry_on_timeout=True)

index_name_uni = ""

def find_lehrshuhl():
    query = {
        "dis_max": {
            "queries": [
                {
                    "query_string": {
                        "query": "Lehrstuhl",
                        "default_field": "links.text"
                    }
                }, {
                    "query_string": {
                        "query": "Abteilung",
                        "default_field": "links.text"
                    }
                }
            ]
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
        if "Lehrstuhl" in hit.get('key') or "Abteilung" in hit.get('key'):
            #if hit.get('doc_count') < 10:
            #    continue

            n = hit.get('key')
            if n.startswith("Lehrstuhl ") or n.startswith("Abteilung "):
                if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234 öäüÖÜÄ-,.' for c in n):
                    continue

                splitted = n.split(" ")
                if len(splitted) < 2 or len(splitted) > 11:
                    continue
                
                whitelist = ["für", "der", "des", "und", "&", "/", "1", "2", "3", "4", "I", "II", "III", "IV", "i", "ii", "iii", "iv", "-"]
                wrong_len = False
                for s in splitted:
                    if len(s) < 5 and not s.endswith(".") and not s.endswith("-"):
                        if s not in whitelist:
                            wrong_len = True
                            break
                if wrong_len:
                    continue

                while n.startswith(" "):
                    n = n[1:]
                
                if n not in fs:
                    fs.append(hit.get('key'))
                    fs_count.append(hit.get('doc_count'))

    for i in range(len(fs)):
        print(str(fs_count[i]) + " --- " + fs[i])

    print(len(fs))



# main
if __name__ == '__main__':

    #i_name = "crawl-rawdata-ude" # wird am Ende übergeben
    i_name = "crawl-rawdata-rub"  # wird am Ende übergeben

    index_name_uni = i_name

    find_lehrshuhl()