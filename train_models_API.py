import pandas as pd
import numpy as np
import joblib
import statsmodels.api as sm
from sklearn.linear_model import Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Charger les données
data_final = pd.read_csv("data_final.csv", sep='\t')

# Définition des features et de la target
feature_cols = ['environmentScore', 'socialScore', 'governanceScore',
                'highestControversy', 'totalEsg',
                'esgPerformance_LAG_PERF', 'esgPerformance_LEAD_PERF',
                'animalTesting_True', 'nuclear_True']

X = data_final[feature_cols]
X = sm.add_constant(X)
y = data_final["roe_num"]

# Séparation en train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entraînement des modèles
ols_model = sm.OLS(y_train, X_train).fit()
lasso_model = Lasso(alpha=0.1).fit(X_train, y_train)
rf_model = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_train, y_train)

# Sauvegarde des modèles
joblib.dump(ols_model, "ols_model.pkl")
joblib.dump(lasso_model, "lasso_model.pkl")
joblib.dump(rf_model, "rf_model.pkl")

print("Modèles sauvegardés avec succès.")
