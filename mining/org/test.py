
"""
with open('RUB_Ground_Truth.json', encoding="utf-8") as f:
    lines = f.readlines()

#print(lines)
ff = open("truth_rub_faculty.txt", "a")
fl = open("truth_rub_chair.txt", "a")
fi = open("truth_rub_institute.txt", "a")

current_f = ""

for i in range(len(lines)):
    line = lines[i]

    if line.startswith('               "name": "'):
        fakul = line[24: line.rfind('"')]
        link = lines[i + 1][25: lines[i + 1].rfind('"')]

        dict = {
            "name": fakul,
            "link": link,
            "uni": "rub",
            "type": "faculty",
            "upper": "rub"
        }

        ff.write(str(dict))
        ff.write("\n")

        current_f = fakul

    if line.startswith('                       "name": "'):
        if "Abt. ohne Zuweisung" in line:
            continue
        inst = line[31: line.rfind('"')]
        link = lines[i + 1][32: lines[i + 1].rfind('"')]

        dict = {
            "name": inst,
            "link": link,
            "uni": "rub",
            "type": "institute",
            "upper": current_f
        }

        fi.write(str(dict))
        fi.write("\n")

    if line.startswith('                               "name": "'):
        lehr = line[38: line.rfind('"')]
        link = lines[i + 1][39: lines[i + 1].rfind('"')]

        dict = {
            "name": lehr,
            "link": link,
            "uni": "rub",
            "type": "chair",
            "upper": current_f
        }

        fl.write(str(dict))
        fl.write("\n")




ff.close()
fl.close()
fi.close()
"""
from elasticsearch import Elasticsearch

es = Elasticsearch({'host':'wom.handte.org', 'port': 443, 'path_prefix':'elastic', 'scheme':'https'},  basic_auth=('wom', 'H7kSk2~5GnybwE{}J4jdPj)qS74&tbXBK-b))+GN'), request_timeout=60, max_retries=5, retry_on_timeout=True)

index_name_Searching = "org-ude"

query = {
    "match": {
        "uni": "ude"
    }
}

docs = es.search(index=index_name_Searching, query=query, size=1500)

ff = open("found_ude_faculty.txt", "a")
fl = open("found_ude_chair.txt", "a")
fi = open("found_ude_institute.txt", "a")

for hit in docs.get('hits').get('hits'):
    line = "{'name': '" + hit.get('_source').get('name') + "', 'link': '" + str(hit.get('_source').get('link')) + "', 'upper': '" + str(hit.get('_source').get('upper')) + "'}"
    line = line.replace("\u0308", "ö")

    if hit.get('_source').get('type') == "faculty":
        ff.write(str(line))
        ff.write("\n")
    
    if hit.get('_source').get('type') == "chair":
        fl.write(str(line))
        fl.write("\n")
    
    if hit.get('_source').get('type') == "institute":
        fi.write(str(line))
        fi.write("\n")

ff.close()
fl.close()
fi.close()
