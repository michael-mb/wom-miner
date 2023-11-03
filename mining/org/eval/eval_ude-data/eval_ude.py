import json
import sys

print("Complete manuel evaluation!")

print()

print("Fakultäten: ")
print()

found_faculty = []
found_faculty_link = []

with open('found_ude_faculty.txt') as f:
    lines = f.readlines()

for line in lines:
    dict = json.loads(line.replace("'", '"'))

    found_faculty.append(dict.get('name'))

    link = dict.get('link')
    if not link.endswith("/"):
        link = link + "/"
    if "http:" in link:
        link = link.replace("http:", "https:")
    found_faculty_link.append(link)

print("Tatsächlich existierend: 11")
print("Gefunden: " + str(len(found_faculty)))
print()

print("Namen:")
print()
count_correct = 11
count_half_correct = 1
count_incorrect = 1
count_double = 1

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Name ist unvollständig, aber vorhanden): " + str(count_half_correct))
print("Doppelt gefunden, davon einer mindestens halb-korrekt: " + str(count_double))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print()

print("% mit doppelten (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / len(found_faculty) * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(found_faculty) * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(found_faculty) * count_incorrect) + "%")
print("Doppelt gefunden (von den korrekten und halb-korrekten): " + str(100 / (count_correct + count_half_correct) * count_double) + "%")

print()

count_correct = 10
count_half_correct = 1
count_incorrect = 0

print("% ohne doppelten (gemessen an den tatsächlichen):")
print("Korrekt gefunden: " + str(100 / 11 * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / 11 * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / 11 * count_incorrect) + "%")

print()

print("Links:")
print()

count_none = 1
count_with = 12

print("Lehrstühle ohne Link: " + str(count_none) + " (" + str(100 / len(found_faculty_link) * count_none) + "%)")
print("Lehrstühle mit Link: " + str(count_with) + " (" + str(100 / len(found_faculty_link) * count_with) + "%)")

print()

count_correct = 10
count_half_correct = 0
count_incorrect = 2

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Link ist vorhanden, aber hat hinten zu viel): " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / count_with * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * count_incorrect) + "%")

print()

print("---------------------------------")

print()

print("Lehrstühle: ")
print()

found_chair = []
found_chair_link = []
found_chair_upper = []

with open('found_ude_chair.txt') as f:
    lines = f.readlines()

for line in lines:
    dict = json.loads(line.replace("'", '"'))

    found_chair.append(dict.get('name'))
    found_chair_upper.append(dict.get('upper'))

    link = dict.get('link')

    if link == "":
        found_chair_link.append(None)
        continue

    if not link.endswith("/"):
        link = link + "/"
    if "http:" in link:
        link = link.replace("http:", "https:")
    found_chair_link.append(link)

print("Gefunden: " + str(len(found_chair)))
print()

print("Namen:")
print()
count_correct = 149
count_half_correct = 28
count_incorrect = 1
count_double = 23

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Name ist unvollständig, aber vorhanden): " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))
print("Doppelt gefunden: " + str(count_double))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / len(found_chair) * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(found_chair) * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(found_chair) * count_incorrect) + "%")
print("Doppelt gefunden (von den korrekten und halb-korrekten): " + str(100 / (count_correct + count_half_correct) * count_double) + "%")

print()
print("Links:")
print()

count_none = found_chair_link.count('None/')
count_with = len(found_chair_link) - count_none

print("Lehrstühle ohne Link: " + str(count_none) + " (" + str(100 / len(found_chair_link) * count_none) + "%)")
print("Lehrstühle mit Link: " + str(count_with) + " (" + str(100 / len(found_chair_link) * count_with) + "%)")

print()

count_correct = 94
count_half_correct = 0
count_incorrect = 10

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Link ist vorhanden, aber hat hinten zu viel): " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / count_with * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * count_incorrect) + "%")

print()

print("Uppers:")

print()

count_none = found_chair_upper.count('None')
count_with = len(found_chair_upper) - count_none

print("Lehrstühle ohne Upper: " + str(count_none) + " (" + str(100 / len(found_chair_upper) * count_none) + "%)")
print("Lehrstühle mit Upper: " + str(count_with) + " (" + str(100 / len(found_chair_upper) * count_with) + "%)")

print()

print("Uppers (der gefundenen):")
print()

manuell_correct = 14
manuell_incorrect = 42

print("Korrekt gefunden: " + str(manuell_correct))
print("Nicht korrekt gefunden: " + str(manuell_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * manuell_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * manuell_incorrect) + "%")

print()

print("Die MSM (Fakultät für Betriebswirtschaftslehre) hat 24 Lehrstühle")

print("Stichprobe aller Lehrstühle, um eine grobe Aussage treffen zu können")

print("Die MSM tatsächlich: 24")

print("Von der MSM gefunden:")

count_correct = 17
count_half_correct = 6
count_incorrect = 1

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden: " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print("% (gemessen an den tatsächlichen):")
print("Korrekt gefunden: " + str(100 / 24 * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / 24 * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / 24 * count_incorrect) + "%")

print()

print("---------------------------------")

print()

print("Institute:")

print()

found_institute = []
found_institute_link = []
found_institute_upper = []

with open('found_ude_institute.txt') as f:
    lines = f.readlines()

for line in lines:
    dict = json.loads(line.replace("'", '"'))

    found_institute.append(dict.get('name').replace("&", 'und'))
    found_institute_upper.append(dict.get('upper'))

    link = dict.get('link')

    if link == "":
        found_institute_link.append(None)
        continue

    if not link.endswith("/"):
        link = link + "/"
    if "http:" in link:
        link = link.replace("http:", "https:")
    found_institute_link.append(link)


print("Gefunden: " + str(len(found_institute)))
print()

print("Namen:")
print()
count_correct = 369
count_half_correct = 221
count_incorrect = 88
count_double = 257
count_an = 263

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Name ist unvollständig, aber vorhanden): " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))
print("Doppelt gefunden (von den korrekten und halb-korrekten): " + str(count_double))
print("An-Institute (von den korrekten und halb-korrekten): " + str(count_an))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / len(found_institute) * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / len(found_institute) * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / len(found_institute) * count_incorrect) + "%")
print("Doppelt gefunden (von den korrekten und halb-korrekten): " + str(100 / (count_correct + count_half_correct) * count_double) + "%")
print("An-Institute (von den korrekten und halb-korrekten): " + str(100 / (count_correct + count_half_correct) * count_an) + "%")

print()

print("Links:")
print()

count_none = found_institute_link.count('None/')
count_with = len(found_institute_link) - count_none

print("Institute ohne Link: " + str(count_none) + " (" + str(100 / len(found_institute_link) * count_none) + "%)")
print("Institute mit Link: " + str(count_with) + " (" + str(100 / len(found_institute_link) * count_with) + "%)")

print()
print("Links (von den gefundenen Links):")
print()

count_correct = 136
count_half_correct = 10
count_incorrect = 39

print("Korrekt gefunden: " + str(count_correct))
print("Halb-korrekt gefunden (Link ist vorhanden, aber hat hinten zu viel): " + str(count_half_correct))
print("Nicht korrekt gefunden: " + str(count_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * count_correct) + "%")
print("Halb-korrekt gefunden: " + str(100 / count_with * count_half_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * count_incorrect) + "%")

print()

print("Uppers:")

print()

count_none = found_institute_upper.count('None')
count_with = len(found_institute_upper) - count_none

print("Institute ohne Upper: " + str(count_none) + " (" + str(100 / len(found_institute_upper) * count_none) + "%)")
print("Institute mit Upper: " + str(count_with) + " (" + str(100 / len(found_institute_upper) * count_with) + "%)")

print()

print("Manuelle Evaluation der Uppers (der gefundenen Uppers):")
print()

manuell_correct = 53
manuell_incorrect = 170

print("Korrekt gefunden: " + str(manuell_correct))
print("Nicht korrekt gefunden: " + str(manuell_incorrect))

print()

print("% (gemessen an den gefundenen):")
print("Korrekt gefunden: " + str(100 / count_with * manuell_correct) + "%")
print("Nicht korrekt gefunden: " + str(100 / count_with * manuell_incorrect) + "%")

print()