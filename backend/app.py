
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for server-side rendering

from flask import Flask, request, jsonify
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)

# Load and parse dataset on upload
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        df = pd.read_csv(file)

        # Debugging: Print DataFrame shape and columns
        print("File uploaded successfully.")
        print("DataFrame shape:", df.shape)
        print("Columns in DataFrame:", df.columns)

        # Check if 'Taluk' column exists
        if 'Taluk' not in df.columns:
            raise ValueError("The column 'Taluk' does not exist in the uploaded file.")

        taluks = df['Taluk'].unique().tolist()
        df.to_csv('uploaded_dataset.csv', index=False)  # Save the uploaded file
        return jsonify({'taluks': taluks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Analyze and visualize dengue data
@app.route('/analyze', methods=['POST'])
def analyze_data():
    try:
        taluk = request.json['taluk']

        # Load the saved dataset
        df = pd.read_csv('uploaded_dataset.csv')
        
        # Filter data for the selected taluk
        df_taluk = df[df['Taluk'] == taluk]
        
        charts_html = ''
        village_html = ''
        demographic_html = ''
        detection_html = ''

        # Yearly cases bar chart
        yearly_cases = df_taluk.groupby('Year')['Cases'].sum()
        fig, ax = plt.subplots()
        yearly_cases.plot(kind='bar', ax=ax)
        ax.set_ylim(0, yearly_cases.max() * 1.2)
        charts_html += fig_to_html(fig, title="Yearly Dengue Cases")

        # Monthly cases bar chart
        highest_year = yearly_cases.idxmax()
        df_highest_year = df_taluk[df_taluk['Year'] == highest_year]
        monthly_cases = df_highest_year.groupby('Month')['Cases'].sum().sort_values(ascending=False)
        fig, ax = plt.subplots()
        monthly_cases.plot(kind='bar', color=monthly_cases.apply(lambda x: color_gradient(x, monthly_cases.max())), ax=ax)
        ax.set_ylim(0, monthly_cases.max() * 1.2)
        charts_html += fig_to_html(fig, title=f"Monthly Dengue Cases in {highest_year}")

        # Village-level heatmap
        if 'Village' in df_taluk.columns:
            village_cases = df_taluk.groupby('Village')['Cases'].sum().sort_values(ascending=False)
            fig, ax = plt.subplots(figsize=(10, 6))
            village_cases.plot(kind='bar', color=village_cases.apply(lambda x: color_gradient(x, village_cases.max())), ax=ax)
            ax.set_ylim(0, village_cases.max() * 1.2)
            plt.xticks(rotation=90, ha='right')
            village_html += fig_to_html(fig, title="Dengue Cases by Village (Heatmap)")

        # **Demographic Analysis**
        # Age distribution histogram
        if 'Age' in df_taluk.columns:
            fig, ax = plt.subplots()
            df_taluk['Age'].plot(kind='hist', bins=10, color='skyblue', ax=ax)
            ax.set_title("Age Distribution of Dengue Cases")
            ax.set_xlabel("Age")
            demographic_html += fig_to_html(fig)

        # Gender distribution bar chart
        if 'Gender' in df_taluk.columns:
            gender_counts = df_taluk['Gender'].value_counts()
            fig, ax = plt.subplots()
            gender_counts.plot(kind='bar', color=['#FF9999', '#66B2FF'], ax=ax)
            ax.set_title("Gender Distribution of Dengue Cases")
            ax.set_xlabel("Gender")
            ax.set_ylabel("Number of Cases")
            demographic_html += fig_to_html(fig)

        # **Detection Delay and Severity Analysis**
        if 'Days_to_Detection' in df_taluk.columns and 'Infection_Stage_encoded' in df_taluk.columns:
            # Scatter plot of Days_to_Detection vs Infection_Stage_encoded
            fig, ax = plt.subplots()
            ax.scatter(df_taluk['Days_to_Detection'], df_taluk['Infection_Stage_encoded'], alpha=0.6, color='purple')
            ax.set_title("Detection Delay vs. Infection Severity")
            ax.set_xlabel("Days to Detection")
            ax.set_ylabel("Infection Severity (Encoded)")
            detection_html += fig_to_html(fig)

            # Box plot for Infection Severity by Detection Delay groups
            fig, ax = plt.subplots()
            df_taluk['Detection_Delay_Group'] = pd.cut(df_taluk['Days_to_Detection'], bins=[0, 3, 7, 14, 30], labels=['0-3 Days', '4-7 Days', '8-14 Days', '15-30 Days'])
            df_taluk.boxplot(column='Infection_Stage_encoded', by='Detection_Delay_Group', ax=ax)
            ax.set_title("Infection Severity by Detection Delay Group")
            ax.set_xlabel("Detection Delay Group")
            ax.set_ylabel("Infection Severity (Encoded)")
            plt.suptitle("")
            detection_html += fig_to_html(fig)

        return jsonify({'html': charts_html, 'villageHtml': village_html, 'demographicHtml': demographic_html, 'detectionHtml': detection_html})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Helper function to render matplotlib figure as HTML image
def fig_to_html(fig, title=""):
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    img_b64 = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close(fig)
    return f"<h3>{title}</h3><img src='data:image/png;base64,{img_b64}'/>"

# Helper function for color gradient
def color_gradient(value, max_value):
    import matplotlib.colors as mcolors
    cmap = mcolors.LinearSegmentedColormap.from_list("", ["red", "yellow", "green"])
    normalized_value = value / max_value
    return cmap(normalized_value)

if __name__ == "__main__":
    app.run(debug=True)
