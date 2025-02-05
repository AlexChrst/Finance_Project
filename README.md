# Finance_Project

Ce projet a pour objectif d'analyser les données financières et ESG (Environnement, Social et Gouvernance) des entreprises. Il comprend plusieurs étapes, allant du scraping des données à l'analyse des corrélations.

## Structure du projet

- `first_approach.ipynb` : Contient le code des corrélations réalisées par les auteurs, l'import de la base `merged_data.csv` et quelques nettoyages et modifications de cette dernière.
- `scraping.ipynb` : Contient le code du scraping des données ESG à partir de sources en ligne.
- `merge.ipynb` : Contient le code qui importe les données scrappées ESG et ROE et les fusionne. Ces données sont ensuite utilisées dans le code `first_approach.ipynb`.
- `expanded_tests.ipynb` : Contient des tests supplémentaires et des analyses approfondies. Tests de normalité et corrélation de Spearman x Kendall
- `requirements.txt` : Liste des dépendances nécessaires pour exécuter le projet.

## Installation

Pour installer les dépendances nécessaires, exécutez la commande suivante :

```sh
pip install -r requirements.txt