import logging
import os
import sys
from pathlib import Path
from people.evaluation_improved import evaluation as eval
from tabulate import tabulate, SEPARATING_LINE

if __name__ == "__main__":
    formatter = logging.Formatter(fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    # formatter = logging.Formatter(fmt="%(message)s")

    logfile = Path(__file__).parent / "people/evaluation_improved/evaluation.log"
    if logfile.is_file():
        os.remove(logfile)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(formatter)
    root.addHandler(consoleHandler)
    fileHandler = logging.FileHandler(logfile, encoding="utf-8")
    fileHandler.setFormatter(formatter)
    root.addHandler(fileHandler)

    log = logging.getLogger("people_eval")

    log.info("************************************************")
    log.info("********** Universität Duisburg-Essen **********")
    log.info("************************************************")
    # eval.evaluate(eval.load_ude_truth(), eval.load_found("ude"), "ude")
    dataToWriteUDE = eval.evaluate_to_txt(eval.load_ude_truth(), eval.load_found("ude"), "ude")
    log.info("*********************************************")
    log.info("********** Ruhr-Universität Bochum **********")
    log.info("*********************************************")
    # eval.evaluate(eval.load_rub_truth(), eval.load_found("rub"), "rub")
    dataToWriteRUB = eval.evaluate_to_txt(eval.load_rub_truth(), eval.load_found("rub"), "rub")

    dataToWrite = []

    for ude, rub in zip(dataToWriteUDE, dataToWriteRUB):
        # Merge the tuples, but skip the first column in RUB data (column "header")
        dataToWrite.append(ude + rub[1:])
    
    print(dataToWrite)

    with open(Path(__file__).parent / "people/evaluation_improved/evaluation.txt", "w", encoding="utf-8") as f:
        f.write(tabulate(dataToWrite, floatfmt=",.2f", headers=("Metric", "UDE Count", "UDE %", "RUB Count", "RUB %")))

    # # Setup logging 1
    # logfile = Path(__file__).parent / "people/evaluation/evaluation-ude.log"
    # if logfile.is_file():
    #     os.remove(logfile)
    # root = logging.getLogger()
    # root.setLevel(logging.INFO)
    # consoleHandler = logging.StreamHandler(sys.stdout)
    # consoleHandler.setFormatter(formatter)
    # root.addHandler(consoleHandler)
    # fileHandler = logging.FileHandler(logfile, encoding="utf-8")
    # fileHandler.setFormatter(formatter)
    # root.addHandler(fileHandler)

    # # Evaluate UDE
    # evaluate(load_ude_truth(), load_found("ude"), "ude")
    # root.removeHandler(consoleHandler)
    # root.removeHandler(fileHandler)

    # # Setup logging 2
    # logfile = Path(__file__).parent / "people/evaluation/evaluation-rub.log"
    # if logfile.is_file():
    #     os.remove(logfile)
    # root = logging.getLogger()
    # root.setLevel(logging.INFO)
    # consoleHandler = logging.StreamHandler(sys.stdout)
    # consoleHandler.setFormatter(formatter)
    # root.addHandler(consoleHandler)
    # fileHandler = logging.FileHandler(logfile, encoding="utf-8")
    # fileHandler.setFormatter(formatter)
    # root.addHandler(fileHandler)

    # # Evaluate RUB
    # evaluate(load_rub_truth(), load_found("rub"), "rub")