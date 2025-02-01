from fastapi import FastAPI, HTTPException, Body
from typing import List, Optional
import pandas as pd

df = pd.read_csv("the_final_merged_file.csv",sep='\t')

app = FastAPI(title="API de comparaison ESG et Rentabilité Financière")

# Création d'un endpoint pour rechercher une entreprise par nom
@app.get("/company/")
def get_company(name: str):
    result = df[df['name'].str.contains(name, case=False, na=False)]
    if result.empty:
        raise HTTPException(status_code=404, detail="Entreprise non trouvée")
    return result[['name', 'grade', 'roe']].to_dict(orient='records')


# Création d'un endpoint pour comparer par secteur

@app.post("/compare/industry/")
def compare_by_industry(
    global_industries: List[str] = Body(...),  # Le paramètre dans le corps de la requête
    year: Optional[int] = None
):
    # Logique de filtrage et de calcul
    result = df[df['global_industry'].str.lower().isin([industry.lower() for industry in global_industries])]
    if year:
        result = result[result['Year'] == year]
    if result.empty:
        raise HTTPException(status_code=404, detail="Aucun secteur ou année correspondante trouvée")
    grouped_result = result.groupby('global_industry').agg({
        'grade': 'mean',
        'roe_num': 'mean'
    }).reset_index()
    return grouped_result.to_dict(orient='records')



# Création d'un endpoint pour comparer par continent
@app.get("/compare/continent/")
def compare_by_continent(continent: str):
    result = df[df['continent'].str.contains(continent, case=False, na=False)]
    if result.empty:
        raise HTTPException(status_code=404, detail="Continent non trouvé")
    return result[['name', 'continent', 'grade', 'roe_num']].to_dict(orient='records')


# Création d'un endpoint pour filtrer par année
@app.get("/compare/year/")
def compare_by_year(year: int):
    result = df[df['Year'] == year]
    if result.empty:
        raise HTTPException(status_code=404, detail="Année non trouvée")
    return result[['name', 'Year', 'grade', 'roe_num']].to_dict(orient='records')

# Endpoint de filtres combinés
@app.get("/compare/")
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

    return filtered_df[['name', 'industry', 'continent', 'Year', 'grade', 'roe_num']].to_dict(orient='records')
