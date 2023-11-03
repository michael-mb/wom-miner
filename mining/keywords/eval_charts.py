import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def load_csv_files(folder_path):
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    data_frames = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, sep=';')
            if 'quality_score' not in df.columns:
                raise ValueError(f"'quality_score' column not found in {file}")
            df["filename"] = os.path.basename(file)
            data_frames.append(df)
        except Exception as e:
            print(f"Error while processing {file}: {e}")
    return data_frames

def analyze_all_files(data_frames):
    all_data = pd.concat(data_frames, ignore_index=True)
    overall_stats = all_data["quality_score"].describe()

    plt.figure(figsize=(10, 6))
    sns.boxplot(data=all_data, x="quality_score", y="filename")
    plt.title("Box Plot of Quality Score Across All Files")
    plt.savefig("mining/keywords/eval_results/charts/box_plot.png")
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.histplot(all_data["quality_score"], bins=20, kde=True)
    plt.title("Histogram of Quality Score Across All Files")
    plt.savefig("mining/keywords/eval_results/charts/histogram.png")
    plt.close()

    return overall_stats

def analyze_individual_files(data_frames):
    for df in data_frames:
        file_stats = df["quality_score"].describe()
        print("Statistics for", df["filename"][0])
        print(file_stats)

        plt.figure(figsize=(6, 4))
        sns.histplot(df["quality_score"], bins=20, kde=True)
        plt.title(f"Histogram of Quality Score for {df['filename'][0]}")
        plt.savefig(os.path.join("mining/keywords/eval_results/charts", f"{df['filename'][0]}_histogram.png"))
        plt.close()

        plt.figure(figsize=(6, 4))
        sns.boxplot(data=df, x="quality_score")
        plt.title(f"Box Plot of Quality Score for {df['filename'][0]}")
        plt.savefig(os.path.join("mining/keywords/eval_results/charts", f"{df['filename'][0]}_box_plot.png"))
        plt.close()

        if "timestamp" in df.columns:
            plt.figure(figsize=(10, 6))
            sns.lineplot(data=df, x="timestamp", y="quality_score")
            plt.title(f"Line Plot: Quality Score Over Time for {df['filename'][0]}")
            plt.savefig(os.path.join("mining/keywords/eval_results/charts", f"{df['filename'][0]}_line_plot.png"))
            plt.close()

def analyze_by_uni(data_frames):
    all_data = pd.concat(data_frames, ignore_index=True)
    all_data['uni'] = all_data['filename'].apply(lambda x: x.split('_')[1])

    filtered_data = all_data[all_data['uni'].isin(['rub', 'ude'])]

    uni_stats = filtered_data.groupby('uni')["quality_score"].describe()
    print("Statistics by university for 'rub' and 'ude':")
    print(uni_stats)

    plt.figure(figsize=(10, 6))
    sns.boxplot(data=filtered_data, x="quality_score", y="uni")
    plt.title("Box Plot of Quality Score for Universities 'rub' and 'ude'")
    plt.savefig("mining/keywords/eval_results/charts/box_plot_by_rub_ude.png")
    plt.close()


def analyze_by_entity_type(data_frames):
    all_data = pd.concat(data_frames, ignore_index=True)
    all_data['entity_type'] = all_data['filename'].apply(lambda x: x.split('_')[0])

    entity_type_stats = all_data.groupby('entity_type')["quality_score"].describe()
    print("Statistics by entity type:")
    print(entity_type_stats)

    plt.figure(figsize=(10, 6))
    sns.boxplot(data=all_data, x="quality_score", y="entity_type")
    plt.title("Box Plot of Quality Score by Entity Type")
    plt.savefig("mining/keywords/eval_results/charts/box_plot_by_entity_type.png")
    plt.close()

def analyze_bar_plot(data_frames):
    all_data = pd.concat(data_frames, ignore_index=True)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=all_data, x="entity_type", y="quality_score", estimator=np.mean)
    plt.title("Bar Plot of Mean Quality Score by Entity Type")
    plt.savefig("mining/keywords/eval_results/charts/bar_plot_entity_type.png")
    plt.close()

def analyze_violin_plot(data_frames):
    all_data = pd.concat(data_frames, ignore_index=True)
    all_data['uni'] = all_data['filename'].apply(lambda x: x.split('_')[1])
    filtered_data = all_data[all_data['uni'].isin(['rub', 'ude'])]
    plt.figure(figsize=(10, 6))
    sns.violinplot(data=filtered_data, x="quality_score", y="uni")
    plt.title("Violin Plot of Quality Score for Universities 'rub' and 'ude'")
    plt.savefig("mining/keywords/eval_results/charts/violin_plot_by_rub_ude.png")
    plt.close()


def main():
    folder_path = "mining/keywords/eval_results/csv"
    data_frames = load_csv_files(folder_path)
    if not data_frames:
        print("No valid CSV files found in the folder.")
        return
    overall_stats = analyze_all_files(data_frames)
    print("\nOverall Statistics Across All Files:")
    print(overall_stats)
    analyze_individual_files(data_frames)
    analyze_by_entity_type(data_frames)
    analyze_by_uni(data_frames)
    analyze_violin_plot(data_frames)


if __name__ == "__main__":
    main()