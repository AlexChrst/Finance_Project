# Finance_Project  

## Overview  

This project aims to analyze financial and ESG (Environmental, Social, and Governance) data from companies. It involves multiple stages, ranging from data scraping to correlation analysis.  

## Background  

The project is based on the analysis conducted by the authors of the following study:  
[K-MEANS AND AGGLOMERATIVE HIERARCHICAL CLUSTERING ANALYSIS OF ESG SCORES YEARLY VARIATIONS AND STOCK RETURNS: INSIGHTS FROM THE ENERGY SECTOR IN EUROPE AND THE UNITED STATES](https://www.researchgate.net/publication/374285566_K-MEANS_AND_AGGLOMERATIVE_HIERARCHICAL_CLUSTERING_ANALYSIS_OF_ESG_SCORES_YEARLY_VARIATIONS_AND_STOCK_RETURNS_INSIGHTS_FROM_THE_ENERGY_SECTOR_IN_EUROPE_AND_THE_UNITED_STATES).  

In this study, the authors examined correlations using two machine learning algorithms on energy sector data from Europe and the United States.  

## Project Scope  

Our project builds upon their research by:  
- Expanding the analysis to a broader range of countries and industries.  
- Enhancing the methodology to provide deeper insights.  

## Project Structure  

### Notebooks

- `first_approach.ipynb`: Contains the code for the correlation analysis conducted by the original authors, the import of the `merged_data.csv` dataset, and some cleaning and modifications of the data.  
- `scraping.ipynb`: Contains the code for scraping ESG data from online sources.  
- `merge.ipynb`: Imports the scraped ESG and ROE data and merges them. These processed data are then used in `first_approach.ipynb`.  
- `expanded_tests.ipynb`: Includes additional tests and in-depth analyses, such as normality tests and Spearman vs. Kendall correlation analysis.  
- `extend.ipynb`: Extends the analysis of the ESG-ROE relationship using advanced statistical and machine learning models, including OLS regression, LASSO regression, and Random Forest, with SHAP for interpretability, applied at global, sectoral, and geographical levels.

### Data files
- `real_tabulation_scraped_data.csv`: Contains the raw ESG data scraped from our web-scraping.
- `roe_results_tab.csv`: Contains the ROE (Return on Equity) data for various companies.
- `merged_data.csv`: The merged dataset combining ESG and ROE data, used for correlation analysis and further processing.
- `the_final_merged_file.csv`: The final merged dataset used for the expanded tests and in-depth analyses with continents and global sectors.
- `df_2024_with_variables.csv`: Contains the dataset for the year 2024 with additional ESG variables for extended analysis.

### Others

- `requirements.txt`: Lists the dependencies required to run the project.  

## Installation  

To install the necessary dependencies, run the following command:  

```sh
pip install -r requirements.txt
