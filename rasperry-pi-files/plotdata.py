import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def createplot():
    # 1. Read the data directly from the CSV file
    df = pd.read_csv('all_contaminants.csv')

    # 2. Define the reference safe levels
    safe_levels = {
        'lead_ppb': 5,
        'cadmium_ppb': 5,
        'phosphate_ppm': 40,
        'nitrate_ppm': 10
    }

    # 3. Extract the data for plotting (pulling from the first row)
    labels = ['Lead (ppb)', 'Cadmium (ppb)', 'Phosphate (ppm)', 'Nitrate (ppm)']
    measured_values = df.iloc[0].tolist()  # Converts the first row to a list
    safe_values = [safe_levels[col] for col in df.columns]

    # 4. Set up the bar chart
    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot measured vs. safe levels
    rects1 = ax.bar(x - width/2, measured_values, width, label='Measured Level', color='skyblue', edgecolor='black')
    rects2 = ax.bar(x + width/2, safe_values, width, label='Safe Level Reference', color='red', alpha=0.7, edgecolor='black')

    # 5. Styling and formatting
    ax.set_ylabel('Concentration (ppm/ppb)')
    ax.set_title('Contaminant Levels (Read from CSV) vs. Safety Guidelines')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    # Use log scale to handle the wide range (1 ppm to 200 ppm)
    ax.set_yscale('log')
    ax.set_ylim(0.1, 1000)

    # Add data labels on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), 
                        textcoords="offset points",
                        ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)

    plt.tight_layout()
    plt.savefig('contaminants_plot.png')
    plt.show()
    
if __name__ == "__main__":
    createplot()