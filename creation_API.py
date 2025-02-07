from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
import pandas as pd
from scipy.stats import spearmanr, kendalltau 
import numpy as np
import joblib
import statsmodels.api as sm
from sklearn.linear_model import Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split


df = pd.read_csv("the_final_merged_file.csv", sep='\t')
data_final = pd.read_csv("data_final.csv", sep='\t')

 # Import de la fonction de corrélation
def check_correlation(df , column1, column2):
    """" 
    Cette fonction a pour but de vérifier la corrélation entre deux colonnes en utilisant le test de Spearman et de Kendall.
    Etant donné que les résultats sont très similaires, on ne garde que le test de Spearman.
    
    """

    spearman_corr, spearman_p_value = spearmanr(df[column1], df[column2])
    kendall_corr, kendall_p_value = kendalltau(df[column1], df[column2])

    df_results = pd.DataFrame({
        'test': ['Spearman'],

        'correlation': [spearman_corr],
        'p_value': [np.round(spearman_p_value,2)]
    })

    return df_results


# modèles pré-entraînés du script train_models_API.py
ols_model = joblib.load("ols_model.pkl")
lasso_model = joblib.load("lasso_model.pkl")
rf_model = joblib.load("rf_model.pkl")

feature_cols = ['environmentScore', 'socialScore', 'governanceScore', 'highestControversy']


app = FastAPI(title="API de comparaison ESG et Rentabilité Financière")

@app.get("/company/")
def get_company(name: str):
    result = df[df['name'].str.contains(name, case=False, na=False)]
    if result.empty:
        raise HTTPException(status_code=404, detail="Entreprise non trouvée")
    return result[['name', 'Year', 'grade', 'roe_num']].to_dict(orient='records')

@app.get("/compare/continent/")
def compare_by_continent(continent: str):
    result = df[df['continent'].str.contains(continent, case=False, na=False)]
    if result.empty:
        raise HTTPException(status_code=404, detail="Continent non trouvé")
    return result[['name', 'Year', 'continent', 'grade', 'roe_num']].to_dict(orient='records')

@app.get("/compare/year/")
def compare_by_year(year: int):
    result = df[df['Year'] == year]
    if result.empty:
        raise HTTPException(status_code=404, detail="Année non trouvée")
    return result[['name', 'Year', 'grade', 'roe_num']].to_dict(orient='records')

@app.get("/compare/industry/continent/year/")
def compare(
    industry: Optional[str] = None,
    continent: Optional[str] = None,
    year: Optional[int] = None
):
    filtered_df = df
    if industry:
        filtered_df = filtered_df[filtered_df['global_industry'].str.contains(industry, case=False, na=False)]
    if continent:
        filtered_df = filtered_df[filtered_df['continent'].str.contains(continent, case=False, na=False)]
    if year:
        filtered_df = filtered_df[filtered_df['Year'] == year]

    if filtered_df.empty:
        raise HTTPException(status_code=404, detail="Aucun résultat trouvé")

    return filtered_df[['name', 'global_industry', 'continent', 'Year', 'grade', 'roe_num']].to_dict(orient='records')


@app.get("/correlation/")
def correlation(
    year: Optional[int] = None,
    industry: Optional[str] = None,
    continent: Optional[str] = None,
    country: Optional[str] = None
):

    filtered_df = df.copy() 

    if year:
        filtered_df = filtered_df[filtered_df['Year'] == year]
    
    if industry:
        filtered_df = filtered_df[filtered_df['global_industry'].str.contains(industry, case=False, na=False)]
    
    if continent:
        filtered_df = filtered_df[filtered_df['continent'].str.contains(continent, case=False, na=False)]
    
    if country:
        filtered_df = filtered_df[filtered_df['country'].str.contains(country, case=False, na=False)]

    # Vérification du nombre de lignes après filtrage
    if filtered_df.empty:
        raise HTTPException(status_code=404, detail="Aucun résultat trouvé pour les critères spécifiés")

    # Vérifier que les colonnes utilisées pour la corrélation ne sont pas vides ou constantes
    if filtered_df['roe_num'].nunique() <= 1 or filtered_df['grade'].nunique() <= 1:
        return {"message": "Corrélation impossible : manque de diversité dans les valeurs de ROE ou ESG."}

    # Calcul de la corrélation
    correlation_result = check_correlation(filtered_df, 'roe_num', 'grade')

    return correlation_result.to_dict(orient='records')

class PredictionRequest_Global(BaseModel):
    environmentScore: float
    socialScore: float
    governanceScore: float
    highestControversy: float
    totalEsg: float
    esgPerformance_LAG_PERF: float
    esgPerformance_LEAD_PERF: float
    animalTesting_True: float
    nuclear_True: float

@app.post("/predict_roe/")
def predict_roe(request: PredictionRequest_Global):
    """ Prédiction du ROE en fonction des features ESG"""
    
    input_data = pd.DataFrame([{
        "const": 1.0,  # Ajout de la constante pour la régression linéaire
        "environmentScore": request.environmentScore,
        "socialScore": request.socialScore,
        "governanceScore": request.governanceScore,
        "highestControversy": request.highestControversy,
        "totalEsg": request.totalEsg,
        "esgPerformance_LAG_PERF": request.esgPerformance_LAG_PERF,
        "esgPerformance_LEAD_PERF": request.esgPerformance_LEAD_PERF,
        "animalTesting_True": request.animalTesting_True,
        "nuclear_True": request.nuclear_True
    }])

    # Prédiction en utilisant les modèles pré-entraînés
    ols_pred = ols_model.predict(input_data)[0]
    lasso_pred = lasso_model.predict(input_data)[0]
    rf_pred = rf_model.predict(input_data)[0]

    return {
        "ROE_prediction_OLS": round(ols_pred, 2),
        "ROE_prediction_Lasso": round(lasso_pred, 2),
        "ROE_prediction_RandomForest": round(rf_pred, 2)
    }

class Prediction_Request_Sector(BaseModel):
    industry: str
    environmentScore: float
    socialScore: float
    governanceScore: float
    highestControversy: float

@app.post("/predict_roe_by_sector/")
def predict_roe_by_sector(request: Prediction_Request_Sector):
    """ Prédiction du ROE pour un secteur donné en utilisant des modèles entraînés sur ce secteur (régression multiple, Lasso, Random Forest) """

    industry = request.industry
    environmentScore = request.environmentScore
    socialScore = request.socialScore
    governanceScore = request.governanceScore
    highestControversy = request.highestControversy

    df_sector = data_final[data_final["global_industry"].str.contains(industry, case=False, na=False)]
    
    if len(df_sector) < 10:
        raise HTTPException(status_code=400, detail=f"Pas assez de données pour le secteur {industry}.")

    # Feature extraction pour le secteur en question
    X_sector = df_sector[feature_cols]
    X_sector = sm.add_constant(X_sector)
    y_sector = df_sector["roe_num"]

    X_train, X_test, y_train, y_test = train_test_split(X_sector, y_sector, test_size=0.2, random_state=42)

    # Train des modèles sur ce secteur
    ols_sector = sm.OLS(y_train, X_train).fit()
    lasso_sector = Lasso(alpha=0.1).fit(X_train, y_train)
    rf_sector = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_train, y_train)

    # Création de l'input pour la prédiction
    input_data = pd.DataFrame([{
        "const": 1.0,
        "environmentScore": environmentScore,
        "socialScore": socialScore,
        "governanceScore": governanceScore,
        "highestControversy": highestControversy
    }])

    # Prédictions
    ols_pred = ols_sector.predict(input_data)[0]
    lasso_pred = lasso_sector.predict(input_data)[0]
    rf_pred = rf_sector.predict(input_data)[0]

    return {
        "sector": industry,
        "ROE_prediction_OLS": round(ols_pred, 2),
        "ROE_prediction_Lasso": round(lasso_pred, 2),
        "ROE_prediction_RandomForest": round(rf_pred, 2)
    }