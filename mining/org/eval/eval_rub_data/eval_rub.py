import json
import sys

print("Fakultäten: ")
print()

found_faculty = []
found_faculty_link = []

with open('found_rub_faculty.txt') as f:
    lines = f.readlines()

for line in lines:
    dict = json.loads(line.replace("'", '"'))

    found_faculty.append(dict.get('name'))

    link = dict.get('link')
    if "index" in link:
        link = link[0: link.rfind("index")]
    if not link.endswith("/"):
        link = link + "/"
    if "http:" in link:
        link = link.replace("http:", "https:")
    if ".rub." in link:
        link = link.replace(".rub.", ".ruhr-uni-bochum.")
    found_faculty_link.append(link)


truth_faculty = []
truth_faculty_link = []

with open('truth_rub_faculty.txt') as f:
    lines = f.readlines()

for line in lines:
    dict = json.loads(line.replace("'", '"'))

    truth_faculty.append(dict.get('name'))

    link = dict.get('link')
    if "index" in link:
        link = link[0: link.rfind("index")]
    if not link.endswith("/"):
        link = link + "/"
    if "http:" in link:
        link = link.replace("http:", "https:")
    if ".rub." in link:
        link = link.replace(".rub.", ".ruhr-uni-bochum.")
    truth_faculty_link.append(link)

print("Tatsächlich existierend: " + str(len(truth_faculty)))
print("Gefunden: " + str(len(found_faculty)))
print()

print("Namen:")
print()
count_correct = 0
count_half_correct = 0
count_incorrect = 0
count_double = 0

for found in found_faculty:
    if found in truth_faculty:
        count_correct = count_correct + 1
    else:
        counted = False
        for truth in truth_faculty:
            if truth.startswith(found):
                count_half_correct = count_half_correct + 1
                counted = True
        if not counted:
            counted = False
            for truth in truth_faculty:
                if truth.startswith(found[0:-1]):
                    count_half_correct = count_half_correct + 1
                    count_double = count_double + 1
                    counted = True
            if not counted:
                count_incorrect = count_incorrect + 1

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Name ist unvollständig, aber vorhanden): " + str(count_half_correct))
print("Doppelt gefunden, davon einer mindestens halb-korrekt: " + str(count_double))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print()

print("% mit doppelten (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / len(found_faculty) * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(found_faculty) * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(found_faculty) * count_incorrect) + "%")

print()

print("% ohne doppelten (gemessen an den existierenden):")
print("Korrekt gefunden: " + str(100 / len(truth_faculty) * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(truth_faculty) * (count_half_correct - count_double)) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(truth_faculty) * count_incorrect) + "%")

print()
print("Zusatz zu den halb-korrekten Namen:")
print("truth: Fakultät für Geschichtswissenschaften")
print("halb-korrekt: Fakultät für Geschichte")
print("halb-korrekt: Fakultät für Geschichtswissenschaft")


print()

print("Links (automatisch):")
print()

count_correct = 0
count_half_correct = 0
count_incorrect = 0
links_incorrect = []
links_incorrect_half = []

for found in found_faculty_link:
    if found in truth_faculty_link:
        count_correct = count_correct + 1
    else:
        counted = False
        for truth in truth_faculty_link:
            if found.startswith(truth):
                count_half_correct = count_half_correct + 1
                links_incorrect_half.append(found)
                counted = True
        if not counted:
            count_incorrect = count_incorrect + 1
            links_incorrect.append(found)

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Link ist vorhanden, aber hat hinten zu viel): " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / len(found_faculty) * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(found_faculty) * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(found_faculty) * count_incorrect) + "%")

print()
print("Zusatz zu den nicht korrekten Links:")
print("Link kann hier als nicht korrekt angezeigt werden und dennoch korrekt sein.")
print("Mehrere Links können auf die selbe Seite zeigen.")
print("Beispiel:")
print("https://dev.kath.ruhr-uni-bochum.de/ / https://www.kath.ruhr-uni-bochum.de/")
print("Nicht korrekte Links müssen noch einmal manuell überprüft werden.")

print()

print("Zusatz zu den halb-korrekten Links:")
print("truth: https://www2.wiwi.rub.de")
print("found: https://www2.wiwi.rub.de/dekanat")

print()

print("Links (manuelle Nachüberprüfung):")

print()

print("Links zur Überprüfung:")
print("Halb-korrekt:")
#print(links_incorrect_half)
print("Nicht korrekt:")
#print(links_incorrect)

print()

print("Ergebnisse manueller Überprüfung:")

manuell_zusatz_correct = 7
manuell_zusatz_correct_half = 3
not_current = 1
manuell_wrong = 0

now_correct = count_correct + manuell_zusatz_correct

print("Korrekt gefunden: " + str(now_correct))
print("Halb-korrekt gefunden (Link ist vorhanden, aber hat hinten zu viel): " + str(manuell_zusatz_correct_half))
print("Nicht korrekt gefunden: " + str(manuell_wrong))
print("Nicht mehr aktuell: " + str(not_current))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / len(found_faculty) * now_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(found_faculty) * manuell_zusatz_correct_half) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(found_faculty) * manuell_wrong) + "%")
print("Nicht mehr aktuell: " + str(100 / len(found_faculty) * not_current) + "%")

print()

print("---------------------------------")

print()

print("Lehrstühle: ")
print()

found_chair = []
found_chair_link = []
found_chair_upper = []

with open('found_rub_chair.txt') as f:
    lines = f.readlines()

for line in lines:
    dict = json.loads(line.replace("'", '"').replace("None", '""'))

    found_chair.append(dict.get('name').replace("&", 'und').replace("Lehrstuhl für ", '').replace("Lehrstuhl ", '').replace("Abteilung für ", '').replace("Abteilung ", '').replace("Abt. für ", '').replace("Abt. ", ''))
    found_chair_upper.append(dict.get('upper'))

    link = dict.get('link')

    if link == "":
        found_chair_link.append(None)
        continue

    if "index" in link:
        link = link[0: link.rfind("index")]
    if not link.endswith("/"):
        link = link + "/"
    if "http:" in link:
        link = link.replace("http:", "https:")
    if ".rub." in link:
        link = link.replace(".rub.", ".ruhr-uni-bochum.")
    found_chair_link.append(link)

truth_chair = []
truth_chair_link = []
truth_chair_upper = []

with open('truth_rub_chair.txt') as f:
    lines = f.readlines()

for line in lines:
    dict = json.loads(line.replace(' "', '').replace("'", '"').replace("None", '""'))

    truth_chair.append(dict.get('name').replace("&", 'und').replace("Lehrstuhl für ", '').replace("Lehrstuhl ", '').replace("Abteilung für ", '').replace("Abteilung ", '').replace("Abt. für ", '').replace("Abt. ", ''))
    truth_chair_upper.append(dict.get('upper'))

    link = dict.get('link')

    if link == "":
        truth_chair_link.append(None)
        continue

    if "index" in link:
        link = link[0: link.rfind("index")]
    if not link.endswith("/"):
        link = link + "/"
    if "http:" in link:
        link = link.replace("http:", "https:")
    if ".rub." in link:
        link = link.replace(".rub.", ".ruhr-uni-bochum.")
    truth_chair_link.append(link)

print("Tatsächlich existierend: " + str(len(truth_chair)))
print("Gefunden: " + str(len(found_chair)))
print()

print("Namen (automatisch):")
print()
count_correct = 0
count_half_correct = 0
count_incorrect = 0

chairs_half = []
chairs_bad = []

for found in found_chair:
    if found in truth_chair:
        count_correct = count_correct + 1
    else:
        counted = False
        for truth in truth_chair:
            if truth.startswith(found):
                count_half_correct = count_half_correct + 1
                chairs_half.append(found)
                counted = True
                break
        if not counted:
            count_incorrect = count_incorrect + 1
            chairs_bad.append(found)

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Name ist unvollständig, aber vorhanden): " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / len(found_chair) * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(found_chair) * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(found_chair) * count_incorrect) + "%")

print()

print("Namen (manuelle Nachkontrolle):")

print()
print("Halb:")
#print(chairs_half)
print("Ganz:")
#print(chairs_bad)
print()

manuell_zusatz_correct = 132
manuell_zusatz_correct_half = 89
manuell_wrong = 9

now_correct = count_correct + manuell_zusatz_correct

print("Korrekt gefunden: " + str(now_correct))
print("Halb-korrekt gefunden: " + str(manuell_zusatz_correct_half))
print("Nicht korrekt gefunden: " + str(manuell_wrong))
print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / len(found_chair) * now_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(found_chair) * manuell_zusatz_correct_half) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(found_chair) * manuell_wrong) + "%")

print()
print("5 Lehrstühle wurden bei den halb-korrekten doppelt gezählt, da diese nicht klar zuordnenbar waren")
print("Beispiel:")
print("Truth: Lehrstuhl für X und Y")
print("Truth: Lehrstuhl für X und Z")
print("Gefunden: Lehrstuhl für X")
print('"Lehrstuhl für X" existiert, der Name ist allerdings nicht komplett gefunden worden. Da es zwei mögliche Vollständige Namen gibt, wurde dieser Name doppelt als halb-korrekt gezählt.')

print()

"""
tat_found = 0
tat_half = 0
tat_not = 0


for truth in truth_chair:
    if truth in found_chair:
        tat_found = tat_found + 1
    else:
        counted = False
        for found in found_chair:
            if found.startswith(truth):
                tat_half = tat_half + 1
                counted = True
                break
        if not counted:
            tat_not = tat_not + 1

print(tat_found)
print(tat_half)
print(tat_not)

# --> manuelle Evaluation
"""

tat_found = 267
tat_half = 84
tat_not = 26

print("% (gemessen an den tatsächlichen):")
print("Korrekt gefunden: " + str(100 / len(truth_chair) * tat_found) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(truth_chair) * tat_half) + "%")
print("Nicht gefunden: " + str(100 / len(truth_chair) * tat_not) + "%")

print()
print("Links:")
print()

count_correct = 0
count_half_correct = 0
count_incorrect = 0
links_incorrect = []
links_incorrect_half = []

count_none = found_chair_link.count(None)
count_with = len(found_chair_link) - count_none

print("Lehrstühle ohne Link: " + str(count_none) + " (" + str(100 / len(found_chair_link) * count_none) + "%)")
print("Lehrstühle mit Link: " + str(count_with) + " (" + str(100 / len(found_chair_link) * count_with) + "%)")

print()
print("Links (automatisch von den gefundenen Links):")
print()

for found in found_chair_link:
    if found == None:
        continue
    if found in truth_chair_link:
        count_correct = count_correct + 1
    else:
        counted = False
        for truth in truth_chair_link:
            if truth == None:
                continue
            if found.startswith(truth):
                count_half_correct = count_half_correct + 1
                links_incorrect_half.append(found)
                counted = True
        if not counted:
            count_incorrect = count_incorrect + 1
            links_incorrect.append(found)

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Link ist vorhanden, aber hat hinten zu viel): " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / count_with * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * count_incorrect) + "%")

print()

print("Links (manuelle Nachüberprüfung von den gefundenen Links):")

print()

print("Links zur Überprüfung:")
print("Halb-korrekt:")
#print(links_incorrect_half)
print("Nicht korrekt:")
#print(links_incorrect)

print()

print("Ergebnisse manueller Überprüfung:")

manuell_zusatz_correct = 59
manuell_zusatz_correct_half = 31
manuell_wrong = 20

now_correct = count_correct + manuell_zusatz_correct

print("Korrekt gefunden: " + str(now_correct))
print("Halb-korrekt gefunden (Link ist vorhanden, aber hat hinten zu viel): " + str(manuell_zusatz_correct_half))
print("Nicht korrekt gefunden: " + str(manuell_wrong))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * now_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / count_with * manuell_zusatz_correct_half) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * manuell_wrong) + "%")

print()

print("Uppers:")

print()

count_none = found_chair_upper.count(None)
count_with = len(found_chair_upper) - count_none

print("Lehrstühle ohne Upper: " + str(count_none) + " (" + str(100 / len(found_chair_upper) * count_none) + "%)")
print("Lehrstühle mit Upper: " + str(count_with) + " (" + str(100 / len(found_chair_upper) * count_with) + "%)")

print()

print("Manuelle Evaluation der Uppers (der gefundenen Uppers):")
print()

manuell_correct = 26
manuell_incorrect = 171

print("Korrekt gefunden: " + str(manuell_correct))
print("Nicht korrekt gefunden: " + str(manuell_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * manuell_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * manuell_incorrect) + "%")

print()

print("---------------------------------")

print()

print("Institute:")

print()

found_institute = []
found_institute_link = []
found_institute_upper = []

with open('found_rub_institute.txt') as f:
    lines = f.readlines()

for line in lines:
    dict = json.loads(line.replace("'", '"').replace("None", '""'))

    found_institute.append(dict.get('name').replace("&", 'und'))
    found_institute_upper.append(dict.get('upper'))

    link = dict.get('link')

    if link == "":
        found_institute_link.append(None)
        continue

    if "index" in link:
        link = link[0: link.rfind("index")]
    if not link.endswith("/"):
        link = link + "/"
    if "http:" in link:
        link = link.replace("http:", "https:")
    if ".rub." in link:
        link = link.replace(".rub.", ".ruhr-uni-bochum.")
    found_institute_link.append(link)

truth_institute = []
truth_institute_link = []
truth_institute_upper = []

with open('truth_rub_institute.txt') as f:
    lines = f.readlines()

for line in lines:
    dict = json.loads(line.replace(' "', '').replace('"', '').replace("'", '"').replace("None", '""'))

    if "Abt. " in dict.get('name'):
        continue

    truth_institute.append(dict.get('name').replace("&", 'und'))
    truth_institute_upper.append(dict.get('upper'))

    link = dict.get('link')

    if link == "":
        truth_institute_link.append(None)
        continue

    if "index" in link:
        link = link[0: link.rfind("index")]
    if not link.endswith("/"):
        link = link + "/"
    if "http:" in link:
        link = link.replace("http:", "https:")
    if ".rub." in link:
        link = link.replace(".rub.", ".ruhr-uni-bochum.")
    truth_institute_link.append(link)

print("Tatsächlich existierend: " + str(len(truth_institute)))
print("Gefunden: " + str(len(found_institute)))
print()

print("Namen (automatisch):")
print()
count_correct = 0
count_half_correct = 0
count_incorrect = 0

institute_half = []
institute_bad = []

for found in found_institute:
    if found in truth_institute:
        count_correct = count_correct + 1
    else:
        counted = False
        for truth in truth_institute:
            if truth.startswith(found):
                count_half_correct = count_half_correct + 1
                institute_half.append(found)
                counted = True
                break
        if not counted:
            count_incorrect = count_incorrect + 1
            institute_bad.append(found)

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Name ist unvollständig, aber vorhanden): " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / len(found_institute) * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(found_institute) * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(found_institute) * count_incorrect) + "%")

print()

print("Namen (manuelle Nachkontrolle):")

print()
print("Halb:")
#print(institute_half)
print("Ganz:")
#print(institute_bad)
print()

manuell_zusatz_correct = 353
manuell_zusatz_correct_half = 238
manuell_wrong = 137
manuell_double = 358
manuell_an = 340

now_correct = count_correct + manuell_zusatz_correct
print("Korrekt gefunden: " + str(now_correct))
print("Halb-korrekt gefunden: " + str(manuell_zusatz_correct_half))
print("Nicht korrekt gefunden: " + str(manuell_wrong))
print("Von den korrekten und halb-korrekten doppelt: " + str(manuell_double))
print("Von den korrekten und halb-korrekten An-Insitute: " + str(manuell_an))
print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / len(found_institute) * now_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(found_institute) * manuell_zusatz_correct_half) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(found_institute) * manuell_wrong) + "%")
print("Doppelte unter den korrekten und halb-korrekten: " + str(100 / (now_correct + manuell_zusatz_correct_half) * manuell_double) + "%")
print("An-Institute unter den korrekten und halb-korrekten: " + str(100 / (now_correct + manuell_zusatz_correct_half) * manuell_an) + "%")

print()
print("Zusatz:")
print("Zählt als Halb:")
print("Truth: Max-Planck-Institut für Sicherheit und Privatsphäre")
print("Gefunden: Institut für Sicherheit und Privatsphäre")

print()
print("Weiterer Zusatz:")
print("Im Ground Truth sind nur eigene Institute. Keine An-Institute.")

print()

tat_found = 67
tat_half = 1
tat_not = 5

print("% (gemessen an den tatsächlichen):")
print("Korrekt gefunden: " + str(100 / len(truth_institute) * tat_found) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(truth_institute) * tat_half) + "%")
print("Nicht gefunden: " + str(100 / len(truth_institute) * tat_not) + "%")

print()
print("Links:")
print()

count_correct = 0
count_half_correct = 0
count_incorrect = 0
links_incorrect = []
links_incorrect_half = []

count_none = found_institute_link.count(None)
count_with = len(found_institute_link) - count_none

print("Institute ohne Link: " + str(count_none) + " (" + str(100 / len(found_institute_link) * count_none) + "%)")
print("Institute mit Link: " + str(count_with) + " (" + str(100 / len(found_institute_link) * count_with) + "%)")

print()
print("Links (automatisch von den gefundenen Links):")
print()

for found in found_institute_link:
    if found == None:
        continue
    if found in truth_institute_link:
        count_correct = count_correct + 1
    else:
        counted = False
        for truth in truth_institute_link:
            if truth == None:
                continue
            if found.startswith(truth):
                count_half_correct = count_half_correct + 1
                links_incorrect_half.append(found)
                counted = True
        if not counted:
            count_incorrect = count_incorrect + 1
            links_incorrect.append(found)

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Link ist vorhanden, aber hat hinten zu viel): " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / count_with * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * count_incorrect) + "%")

print()

print("Links (manuelle Nachüberprüfung von den gefundenen Links):")

print()

print("Links zur Überprüfung:")
print("Halb-korrekt:")
#print(links_incorrect_half)
print("Nicht korrekt:")
#print(links_incorrect)

print()

print("Ergebnisse manueller Überprüfung:")

manuell_zusatz_correct = 64
manuell_zusatz_correct_half = 48
manuell_wrong = 54

now_correct = count_correct + manuell_zusatz_correct

print("Korrekt gefunden: " + str(now_correct))
print("Halb-korrekt gefunden (Link ist vorhanden, aber hat hinten zu viel): " + str(manuell_zusatz_correct_half))
print("Nicht korrekt gefunden: " + str(manuell_wrong))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * now_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / count_with * manuell_zusatz_correct_half) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * manuell_wrong) + "%")

print()

print("Uppers:")

print()

count_none = found_institute_upper.count(None)
count_with = len(found_institute_upper) - count_none

print("Institute ohne Upper: " + str(count_none) + " (" + str(100 / len(found_institute_upper) * count_none) + "%)")
print("Institute mit Upper: " + str(count_with) + " (" + str(100 / len(found_institute_upper) * count_with) + "%)")

print()

print("Manuelle Evaluation der Uppers (der gefundenen Uppers):")
print()

manuell_correct = 59
manuell_incorrect = 419

print("Korrekt gefunden: " + str(manuell_correct))
print("Nicht korrekt gefunden: " + str(manuell_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * manuell_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * manuell_incorrect) + "%")

print()