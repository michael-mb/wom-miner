from tabulate import tabulate, SEPARATING_LINE
import re
import pandas as pd
from pandas import DataFrame
from pathlib import Path
from people.name_analysis import full_title_group, is_normalized_name, choose_best_title
import logging
from tabulate import tabulate, SEPARATING_LINE

logger = logging.getLogger("evaluation")

out = []

def log(obj):
    if isinstance(obj, DataFrame):
        logger.debug("\n" + obj.to_string(show_dimensions=True, header=True, max_rows=100, max_colwidth=50))
    else:
        s = str(obj)
        if "\n" in s:
            logger.info("\n" + s)
        else:
            logger.info(s)


def load_ude_truth():
    path = Path(__file__).parent / f"../results/ground_truth.csv"
    truth = pd.read_csv(path, encoding="utf-8", header=None, skiprows=1)
    truth.columns = ["id", "name", "mail", "link", "org", "position"]
    truth = truth.fillna("")

    logger.debug("Before normalizing:")
    log(truth)

    truth = truth.drop(["id"], axis=1)
    # Columns: name, mail, link, org, position

    # Construct title from name
    truth["title"] = truth["name"].apply(lambda n: re.search(full_title_group + r"|()", n).group())
    truth["name"] = truth.apply(lambda x: x["name"].replace(x["title"], "").strip().strip(",").strip(), axis=1)

    # Columns: title, name, mail, link, org, position
    columnsTitles = ['title', 'name', 'mail', "link", "org", "position"]
    truth = truth.reindex(columns=columnsTitles)

    truth = truth.fillna("")
    log("Truth after normalizing:")
    log(truth)
    return truth


def load_rub_truth():
    path = Path(__file__).parent / f"../../../data_mining/ground_truth/RUB_persons.json"
    truth = pd.read_json(path, encoding="utf-8")#, dtype={"name":str, "anrede":str, "titel_1":str,"titel_2":str,
                                                #         "vorname":str, "nachname":str,"mail_arbeit":str, "jobtitel":str, "dozent":str,"organisation":str,
                                                #         "organisation_link":str, "funktion":str, "tel":str,"fax":str,"mail_2":str,"sprechzeit":str,"raum":str})
    truth.columns = ["name", "anrede", "title1", "vorname", "nachname", "title2", "leer", "jobtitel", "dozent", "org", "link", "funktion", "telefon", "telefax", "mail", "sprechstunde", "raum"]
    truth = truth.fillna("")
    logger.debug("Before normalizing:")
    log(truth)
    
    # Construct name from vormane and nachname
    truth = truth[truth['vorname'].str.len() > 0] # Special case: 70 people had no firstname => they are ignored
    truth["name"] = truth[["vorname", "nachname"]].apply(lambda x: " ".join(x), axis=1)
    # Construct title from title1 and title2
    truth["title"] = truth[["title1", "title2"]].apply(lambda x: ", ".join(filter(None, x)), axis=1)

    truth = truth.drop(["anrede", "vorname", "nachname", "leer", "dozent", "telefon", "telefax", "sprechstunde", "raum", "title1", "title2"], axis=1)
    # Columns: title, name, mail, link, org, jobtitel, funktion
    columnsTitles = ['title', 'name', 'mail', "link", "org", "jobtitel", "funktion"]
    truth = truth.reindex(columns=columnsTitles)

    truth = truth.fillna("")
    log("Truth after normalizing:")
    log(truth)
    return truth


def load_found(uni):
    path = Path(__file__).parent / f"../results/people-{uni}-cleaned.csv"
    found = pd.read_csv(path, encoding="utf-8", index_col=False, header=None, skiprows=1)
    found.columns = ["title", "name", "mail", "method", "link", "in"]

    found = found.fillna("")
    log("Found after normalizing:")
    log(found)
    return found


def remove(base, toRemove, reason):
    pass


def percentage(name, filter, base):
    return (name, len(filter.index), (len(filter.index) / len(base.index)) * 100)


def metrics(found:DataFrame, truth:DataFrame, byAttribute:str, foundTotal:DataFrame, truthTotal:DataFrame, name:str):

    true_pos = found[found[byAttribute].isin(truth[byAttribute])]     # X in found and in truth
    false_pos = found[~found[byAttribute].isin(truth[byAttribute])]   # X in found but not in truth
    false_neg = truth[~truth[byAttribute].isin(found[byAttribute])]   # X in truth but not in found

    precision = len(true_pos.index) / len(found.index)
    recall = len(true_pos.index) / len(truth.index)
    f1 = 2 * ( (precision * recall) / (precision + recall) )

    out.append(SEPARATING_LINE)
    out.append(percentage(name + " - Truth Total", truth, truthTotal))
    out.append(percentage(name + " - Found Total", found, foundTotal))
    out.append(percentage("True positive (Precision)", true_pos, found))     # Precision: how many of the found are correct
    out.append(percentage("True positive (Recall)", true_pos, truth))        # Recall: How many of the truth was found
    out.append(("F1", "", f1*100))
    # out.append(percentage("Not correct (False positive)", false_pos, found))
    # out.append(percentage("Not found (False negative)", false_neg, truth))

    log(name + " - Not correct:")
    log(false_pos)
    log(name + " - Not found:")
    log(false_neg)


def evaluate_to_txt(truth:DataFrame, found:DataFrame, uni:str):
    global out
    out = []

    out.append(("Found Total",len(found.index),100))
    out.append(("Truth Total",len(truth.index),100))
    
    # Filter duplicates in Ground Truth
    cnt = len(truth.index)
    truth = truth.drop_duplicates(subset=["name"])
    out.append(("Truth Total (duplicates)", cnt - len(truth.index), (cnt - len(truth.index)) / cnt * 100))
    # out.append(("Truth Total without duplicates", len(truth.index), 100))

    # Filter non-normalized names in Ground Truth
    cnt = len(truth.index)
    truth = truth[truth["name"].apply(is_normalized_name)]
    out.append(("Truth Total invalid names", cnt - len(truth.index), (cnt - len(truth.index)) / cnt * 100))

    metrics(found, truth, "name", found, truth, "Total (by name)")

    # Normalize Email addresses
    truth["mail"] = truth["mail"].astype(str).apply(lambda x: x.lower())
    found["mail"] = found["mail"].astype(str).apply(lambda x: x.lower())
    if uni == "rub":
        truth["mail"] = truth["mail"].str.replace("ruhr-uni-bochum.de", repl="rub.de", regex=False)
        found["mail"] = found["mail"].str.replace("ruhr-uni-bochum.de", repl="rub.de", regex=False)
    elif uni == "ude":
        truth["mail"] = truth["mail"].str.replace("uni-duisburg-essen.de", repl="uni-due.de", regex=False)
        found["mail"] = found["mail"].str.replace("uni-duisburg-essen.de", repl="uni-due.de", regex=False)

    metrics(found[found["mail"].str.len() > 0], truth[truth["mail"].str.len() > 0], "mail", found, truth, "Total (by mail)")

    # Filter people without email addresses
    truth_filter = truth
    truth_filter = truth[truth["mail"].str.len() > 0]
    metrics(found, truth_filter, "name", found, truth, "People from Truth with Emails (by name)")

    # Filter Ärzte ("real" doctors)
    if uni == "ude":
        truth_filter = truth_filter[~truth_filter["org"].str.contains("[Kk]linik|[Hh]ospital") & ~truth_filter["position"].str.contains("[Aa]rzt|[Ää]rztin")]
    elif uni == "rub":
        truth_filter = truth_filter[~truth_filter["org"].str.contains("[Kk]linik|[Hh]ospital") & ~truth_filter["funktion"].str.contains("[Aa]rzt|[Ää]rztin")]
    else:
        raise ValueError(uni)
    metrics(found, truth_filter, "name", found, truth, "minus Doctors")

    # Filter Verwaltung & Sachbearbeiter
    if uni == "ude":
        excl_pos = r"Sachbearb|Sachgebiet|Technik und Verwaltung"
        excl_org = r"Dezernat|Dekanat"
        truth_filter = truth_filter[~truth_filter["position"].str.contains(excl_pos, flags=re.IGNORECASE) & ~truth_filter["org"].str.contains(excl_org, flags=re.IGNORECASE)]
    elif uni == "rub":
        excl_pos = r"Verwaltungsange|Verw\.-Angest"
        truth_filter = truth_filter[~truth_filter["jobtitel"].str.contains(excl_pos, flags=re.IGNORECASE)]
    metrics(found, truth_filter, "name", found, truth, "minus Verwaltung & Sachbearbeiter")

    # Filter external emails
    if uni == "ude":
        suffix = "uni-due.de"
    elif uni == "rub":
        suffix = "rub.de"
    truth_filter = truth_filter[truth_filter["mail"].str.contains(suffix, regex=False, case=False)]
    metrics(found, truth_filter, "name", found, truth, "minus externe Emails")

    # Filter Bibliothek
    truth_filter = truth_filter[~truth_filter["org"].str.contains("Bibliothek", regex=False, case=False)]
    metrics(found, truth_filter, "name", found, truth, "minus Bibliothek")

    return out


def evaluate(truth:DataFrame, found:DataFrame, uni:str):

    cnt = len(truth.index)
    cnt_total = len(truth.index)
    log(f"Total truth: {cnt}")

    # Filter non-normalized names
    truth = truth[truth["name"].apply(is_normalized_name)]
    cnt_removed = cnt - len(truth.index)
    log(f"Removed {cnt_removed} ({round((cnt_removed / cnt_total)*100, 2)}) illegal names")
    cnt = len(truth.index)

    # Filter duplicates
    truth = truth.drop_duplicates(subset=["name"])
    cnt_removed = cnt - len(truth.index)
    log(f"Removed {cnt_removed} ({round((cnt_removed / cnt_total)*100, 2)}) duplicates from truth")
    cnt = len(truth.index)

    # Filter empty emails
    truth = truth[truth["mail"].str.len() > 0]
    cnt_removed = cnt - len(truth.index)
    log(f"Removed {cnt_removed} ({round((cnt_removed / cnt_total)*100, 2)}) empty emails")
    cnt = len(truth.index)

    # Filter external emails
    # if uni == "ude":
    #     suffix = r"uni-due\.de|uni-duisburg-essen\.de"
    # elif uni == "rub":
    #     suffix = r"rub\.de|ruhr-uni-bochum\.de"
    # truth = truth[truth["mail"].str.contains(suffix, flags=re.IGNORECASE)]
    # cnt_removed = cnt - len(truth.index)
    # log(f"Removed {cnt_removed} ({round((cnt_removed / cnt_total)*100, 2)}) external emails")
    # cnt = len(truth.index)

    # Filter Ärzte ("real" doctors)
    if uni == "ude":
        truth = truth[~truth["org"].str.contains("[Kk]linik|[Hh]ospital") & ~truth["position"].str.contains("[Aa]rzt|[Ää]rztin")]
    elif uni == "rub":
        truth = truth[~truth["org"].str.contains("[Kk]linik|[Hh]ospital") & ~truth["funktion"].str.contains("[Aa]rzt|[Ää]rztin")]
    cnt_removed = cnt - len(truth.index)
    log(f"Removed {cnt_removed} ({round((cnt_removed / cnt_total)*100, 2)}) doctors")
    cnt = len(truth.index)

    logger.debug("After normalizing and cleaning:")
    log(truth)

    # # Compute metrics
    true_pos = found[found["name"].isin(truth["name"])]     # X in found and in truth
    false_pos = found[~found["name"].isin(truth["name"])]   # X in found but not in truth
    false_neg = truth[~truth["name"].isin(found["name"])]   # X in truth but not in found

    data = [
        ("Truth total", len(truth.index), 100),
        ("Found total", len(found.index), 100),
        SEPARATING_LINE,
        ("True positive in Found (Precision)", len(true_pos.index), len(true_pos.index) / len(found.index) * 100),
        ("True positive in Truth (Recall)", len(true_pos.index), len(true_pos.index) / len(truth.index) * 100),
    ]

    log(tabulate(data, floatfmt=",.2f", headers=("Metric", "Count", "%")))
