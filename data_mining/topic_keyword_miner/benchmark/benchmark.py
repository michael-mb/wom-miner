import time
from collections import Counter
import pandas as pd
import numpy as np
import seaborn as sns
from sklearn.metrics import confusion_matrix
from wordcloud import WordCloud
from naivebayes_classificator import extract as naivebayes_extract
from rake_extractor import extract as rake_extract
from textrank_extractor import extract as textrank_extract
from yake_extractor import extract as yake_extract
from tfidf_extractor import extract as tfidf_extract
from bert_extractor import extract as bert_extract
import matplotlib.pyplot as plt


TX = """
    The University of XYZ is a renowned institution known for its commitment to excellence in education and research. With a rich history spanning over several decades, the university has established itself as a leader in academia, attracting students from all corners of the globe.
    One of the key features that sets the University of XYZ apart is its strong focus on computer science and programming languages. As technology continues to advance at a rapid pace, proficiency in programming languages has become a valuable skill for aspiring professionals. The university recognizes this demand and offers a comprehensive range of computer science courses designed to equip students with the necessary knowledge and skills.
    Python, a high-level interpreted programming language, holds a special place in the curriculum at the University of XYZ. Known for its simplicity and elegance, Python is widely used in various domains, including web development, data analysis, artificial intelligence, and more. The university acknowledges the importance of Python's code readability and intuitive syntax, which makes it an ideal choice for novice programmers.
    In addition to Python, the university also offers courses in other programming languages such as Java and C++. These languages provide a solid foundation for students, enabling them to explore different programming paradigms and tackle complex problem-solving scenarios. By familiarizing students with a diverse set of languages, the university ensures they have a broad understanding of programming principles and are well-equipped to adapt to the evolving technological landscape.
    To enhance the learning experience, the University of XYZ utilizes innovative teaching methodologies. One such technique is the application of TextRank, a graph-based ranking algorithm widely used in natural language processing. TextRank enables automatic text summarization and keyword extraction, making it easier to distill relevant information from large documents. By employing TextRank, students can efficiently analyze and understand complex texts, extracting important keywords and phrases that capture the essence of the material.
    The underlying principles of TextRank rely on the concept of a graph, where words and phrases are represented as nodes connected by edges. Co-occurrence and semantic similarity play crucial roles in establishing the relationships between nodes, enabling the algorithm to determine the importance and relevance of each element. Through the use of TextRank, the university empowers students to navigate vast amounts of information and extract meaningful insights.
    The University of XYZ takes pride in its commitment to fostering an inclusive and collaborative learning environment. It encourages students to engage in coding competitions, hackathons, and collaborative projects to enhance their practical skills and foster teamwork. By providing ample opportunities for hands-on learning and real-world application, the university prepares students for the challenges they may face in their future careers.
    In conclusion, the University of XYZ is a leading institution that prioritizes computer science education and the mastery of programming languages. With a strong emphasis on Python and its inherent qualities, the university equips students with the necessary tools to excel in the rapidly evolving tech industry. By leveraging innovative techniques such as TextRank and promoting collaborative learning, the university ensures that students are well-prepared for the challenges and opportunities that lie ahead.A
    """

GT = set(
    [
        "University of XYZ",
        "renowned institution",
        "excellence in education and research",
        "rich history",
        "leader in academia",
        "students",
        "computer science",
        "programming languages",
        "technology",
        "proficiency",
        "aspiring professionals",
        "comprehensive range of courses",
        "Python",
        "high-level interpreted programming language",
        "simplicity",
        "elegance",
        "domains",
        "web development",
        "data analysis",
        "artificial intelligence",
        "code readability",
        "intuitive syntax",
        "novice programmers",
        "Java",
        "C++",
        "solid foundation",
        "programming paradigms",
        "problem-solving scenarios",
        "familiarizing students",
        "diverse set of languages",
        "programming principles",
        "evolving technological landscape",
        "learning experience",
        "innovative teaching methodologies",
        "TextRank",
        "graph-based ranking algorithm",
        "natural language processing",
        "automatic text summarization",
        "keyword extraction",
        "relevant information",
        "large documents",
        "graph",
        "words",
        "phrases",
        "nodes",
        "edges",
        "co-occurrence",
        "semantic similarity",
        "importance",
        "relevance",
        "material",
        "empowering students",
        "vast amounts of information",
        "meaningful insights",
        "fostering inclusive and collaborative learning environment",
        "coding competitions",
        "hackathons",
        "collaborative projects",
        "practical skills",
        "teamwork",
        "hands-on learning",
        "real-world application",
        "challenges",
        "future careers",
        "leading institution",
        "tech industry",
        "innovative techniques",
        "collaborative learning",
        "opportunities",
    ]
)


def run_benchmark(extract_func, text):
    start_time = time.time()
    keywords = extract_func(text)
    end_time = time.time()
    execution_time = end_time - start_time
    return keywords, execution_time


def jaccard_similarity(set1, set2):
    intersection = len(set1.intersection(set2))
    union = len(set1) + len(set2) - intersection
    return intersection / union


def evaluate_extraction(extractor_func, text):
    ground_truth = GT
    keywords, execution_time = run_benchmark(extractor_func, text)
    extracted = set(keywords) if keywords else set()
    true_positives = len(ground_truth.intersection(extracted))
    precision = true_positives / len(extracted) if extracted else 0.0
    recall = true_positives / len(ground_truth)
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if precision + recall > 0
        else 0.0
    )
    jaccard = jaccard_similarity(ground_truth, extracted)
    number_of_keywords = len(extracted)

    return (
        keywords,
        execution_time,
        precision,
        recall,
        f1_score,
        jaccard,
        number_of_keywords,
    )


def plot_wordcloud(keywords_dict):
    fig, axs = plt.subplots(2, 3, figsize=(20, 10))

    for ax, (name, keywords) in zip(axs.flatten(), keywords_dict.items()):
        wordcloud = WordCloud(
            max_font_size=50, max_words=100, background_color="white"
        ).generate(" ".join(keywords))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.set_title(name)
        ax.axis("off")

    plt.tight_layout()
    plt.show()


def plot_confusion_matrix(confusion_matrices):
    fig, axs = plt.subplots(2, 3, figsize=(20, 10))

    for ax, (name, matrix) in zip(axs.flatten(), confusion_matrices.items()):
        sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", ax=ax)
        ax.set_title(f"Confusion Matrix - {name}")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")

    plt.tight_layout()
    plt.show()


def plot_top_keywords(keywords_dict, percentage=0.4):
    all_keywords = [
        keyword for keywords in keywords_dict.values() for keyword in keywords
    ]

    keyword_counter = Counter(all_keywords)
    sorted_keywords = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)
    no_of_keywords = int(
        np.ceil(len(sorted_keywords) * percentage)
    )  # Take top percentage

    top_keywords = [keyword[0] for keyword in sorted_keywords[:no_of_keywords]]

    wordcloud = WordCloud(
        max_font_size=50, max_words=no_of_keywords, background_color="white"
    ).generate(" ".join(top_keywords))

    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.title(f"Top {percentage*100}% Keywords Across All Approaches")
    plt.axis("off")
    plt.show()


def main():
    text = TX

    extractors = {
        "TF-IDF": tfidf_extract,
        "TextRank": textrank_extract,
        "RAKE": rake_extract,
        "YAKE": yake_extract,
        "NaiveBayes": naivebayes_extract,
        "BERT": bert_extract,
    }

    benchmark_results = []
    keywords_dict = {}
    confusion_matrices = {}

    custom_palette = ["#2980B9", "#3498DB", "#85C1E9", "#AED6F1", "#D6EAF8", "#EBF5FB"]

    fig, ax = plt.subplots(2, 3, figsize=(20, 10))

    for i, (extractor_name, extractor_func) in enumerate(extractors.items()):
        (
            keywords,
            execution_time,
            precision,
            recall,
            f1_score,
            jaccard,
            number_of_keywords,
        ) = evaluate_extraction(extractor_func, text)
        benchmark_results.append(
            {
                "Extractor": extractor_name,
                "Execution Time": execution_time,
                "Precision": precision,
                "Recall": recall,
                "F1-Score": f1_score,
                "Jaccard Similarity": jaccard,
                "Number of Keywords": number_of_keywords,
            }
        )
        keywords_dict[extractor_name] = keywords

        ground_truth = GT
        extracted = set(keywords) if keywords else set()
        labels = list(ground_truth.union(extracted))
        actual = np.array([1 if label in ground_truth else 0 for label in labels])
        predicted = np.array([1 if label in extracted else 0 for label in labels])
        cm = confusion_matrix(actual, predicted)
        confusion_matrices[extractor_name] = cm

        sns.barplot(
            x="Extractor",
            y="Execution Time",
            data=pd.DataFrame(benchmark_results),
            ax=ax[0, 0],
            palette=custom_palette,
        )
        ax[0, 0].set_xlabel("Extractor")
        ax[0, 0].set_ylabel("Execution Time")
        ax[0, 0].set_title("Execution Time by Extractor")
        ax[0, 0].annotate(
            f"{execution_time:.2f}", (i, execution_time), ha="center", va="bottom"
        )

        sns.barplot(
            x="Extractor",
            y="Precision",
            data=pd.DataFrame(benchmark_results),
            ax=ax[0, 1],
            palette=custom_palette,
        )
        ax[0, 1].set_xlabel("Extractor")
        ax[0, 1].set_ylabel("Precision")
        ax[0, 1].set_title("Precision by Extractor")
        ax[0, 1].annotate(f"{precision:.2f}", (i, precision), ha="center", va="bottom")

        sns.barplot(
            x="Extractor",
            y="Recall",
            data=pd.DataFrame(benchmark_results),
            ax=ax[0, 2],
            palette=custom_palette,
        )
        ax[0, 2].set_xlabel("Extractor")
        ax[0, 2].set_ylabel("Recall")
        ax[0, 2].set_title("Recall by Extractor")
        ax[0, 2].annotate(f"{recall:.2f}", (i, recall), ha="center", va="bottom")

        sns.barplot(
            x="Extractor",
            y="F1-Score",
            data=pd.DataFrame(benchmark_results),
            ax=ax[1, 0],
            palette=custom_palette,
        )
        ax[1, 0].set_xlabel("Extractor")
        ax[1, 0].set_ylabel("F1-Score")
        ax[1, 0].set_title("F1-Score by Extractor")
        ax[1, 0].annotate(f"{f1_score:.2f}", (i, f1_score), ha="center", va="bottom")

        sns.barplot(
            x="Extractor",
            y="Jaccard Similarity",
            data=pd.DataFrame(benchmark_results),
            ax=ax[1, 1],
            palette=custom_palette,
        )
        ax[1, 1].set_xlabel("Extractor")
        ax[1, 1].set_ylabel("Jaccard Similarity")
        ax[1, 1].set_title("Jaccard Similarity by Extractor")
        ax[1, 1].annotate(f"{jaccard:.2f}", (i, jaccard), ha="center", va="bottom")

        sns.barplot(
            x="Extractor",
            y="Number of Keywords",
            data=pd.DataFrame(benchmark_results),
            ax=ax[1, 2],
            palette=custom_palette,
        )
        ax[1, 2].set_xlabel("Extractor")
        ax[1, 2].set_ylabel("Number of Keywords")
        ax[1, 2].set_title("Number of Keywords by Extractor")
        ax[1, 2].annotate(
            f"{number_of_keywords}", (i, number_of_keywords), ha="center", va="bottom"
        )

    plt.tight_layout()
    plt.show()

    plot_confusion_matrix(confusion_matrices)
    plot_wordcloud(keywords_dict)
    plot_top_keywords(keywords_dict)


if __name__ == "__main__":
    main()
