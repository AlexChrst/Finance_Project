import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from typing import List, Dict
import queue
import threading
import os

# Queue pour stocker les résultats
result_queue = queue.Queue()

# Event pour signaler l'arrêt du writer
stop_writer = threading.Event()

def setup_driver():
    # Le code existant reste le même
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--enable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless=new")
    return webdriver.Chrome(options=chrome_options)

def scrape_roe(driver, company_name, date_str):
    url = "https://stockanalysis.com/"
    driver.get(url)
    
    csv_date = pd.to_datetime(date_str)
    target_year = csv_date.year
    
    print(f"Démarrage du scraping pour {company_name} (Date CSV: {date_str}, Année cible: {target_year})")
    
    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Search']"))
        )
        search_box.clear()
        search_box.send_keys(company_name)
        time.sleep(2)
        
        try:
            first_suggestion = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='search-result']"))
            )
            first_suggestion.click()
        except:
            search_box.send_keys(Keys.RETURN)
        
        print("Recherche effectuée...")
        time.sleep(3)
        
        # Clic sur Financials
        financials_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Financials"))
        )
        driver.execute_script("arguments[0].click();", financials_link)
        print("Clic sur Financials...")
        time.sleep(3)
        
        # Clic sur Ratios
        ratios_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Ratios"))
        )
        driver.execute_script("arguments[0].click();", ratios_link)
        print("Clic sur Ratios...")
        time.sleep(3)
        
        # Juste vérifier que le tableau est bien trouvé
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table[data-test='financials']"))
        )
        print("Tableau trouvé...")
        
        # Extraction des données JavaScript
        script = """
            function extractROE() {
                const table = document.querySelector('table[data-test="financials"]');
                const rows = Array.from(table.getElementsByTagName('tr'));
                const result = {
                    yearRow: [],
                    dateRow: [],
                    roeRow: null
                };
                
                if (rows.length >= 2) {
                    result.yearRow = Array.from(rows[0].cells).map(cell => cell.textContent.trim());
                    result.dateRow = Array.from(rows[1].cells).map(cell => cell.textContent.trim());
                }
                
                for (let row of rows) {
                    const firstCell = row.cells[0];
                    if (firstCell && firstCell.textContent.includes('Return on Equity')) {
                        result.roeRow = Array.from(row.cells).map(cell => cell.textContent.trim());
                        break;
                    }
                }
                
                return result;
            }
            return extractROE();
        """
        
        result = driver.execute_script(script)
        
        print("\nLigne des années:", result['yearRow'])
        print("Ligne des dates:", result['dateRow'])
        print("Ligne ROE:", result['roeRow'])
        
        if result['roeRow']:
            # Comme l'année 2024 correspond à Current, on doit le traiter différemment
            if target_year == 2024:
                if "Current" in result['yearRow']:
                    index = result['yearRow'].index("Current")
                    roe_value = result['roeRow'][index]
                    print(f"ROE trouvé (Current pour 2024): {roe_value}")
                    return roe_value
                else:
                    print("Colonne Current non trouvée pour 2024")
                    return None
            else:
                # Pour les autres années, on procède normalement donc en fonction de ce qu'on trouve dans le csv d'ESG
                target_column = f"FY {target_year}"
                if target_column in result['yearRow']:
                    index = result['yearRow'].index(target_column)
                    roe_value = result['roeRow'][index]
                    print(f"ROE trouvé pour {target_column}: {roe_value}")
                    return roe_value
                else:
                    print(f"Colonne {target_column} non trouvée")
                    return None
        else:
            print("Ligne ROE non trouvée dans le tableau")
            return None
            
    except Exception as e:
        print(f"Erreur générale lors du scraping pour {company_name}: {e}")
        driver.get(url)
        time.sleep(2)
        return None

def result_writer(output_file: str):
    """
    Thread dédié à l'écriture des résultats dans le fichier CSV
    """
    # Création du fichier avec les en-têtes s'il n'existe pas
    if not os.path.exists(output_file):
        pd.DataFrame(columns=['name', 'date', 'roe']).to_csv(output_file, index=False)
    
    while not stop_writer.is_set() or not result_queue.empty():
        try:
            # Attend un résultat pendant 1 seconde
            result = result_queue.get(timeout=1)
            
            # Écrit le résultat dans le CSV
            pd.DataFrame([result]).to_csv(output_file, mode='a', header=False, index=False)
            
            # Marque la tâche comme terminée
            result_queue.task_done()
        except queue.Empty:
            continue

def process_chunk(chunk: pd.DataFrame, chunk_id: int) -> None:
    """
    Traite un groupe d'entreprises et met les résultats dans la queue
    """
    driver = setup_driver()
    try:
        print(f"Worker {chunk_id} démarre le traitement de {len(chunk)} entreprises...")
        for _, row in chunk.iterrows():
            try:
                name = row["name"]
                date = row["date"]
                roe = scrape_roe(driver, name, date)
                
                # Au lieu de retourner les résultats, on les met dans la queue
                result_queue.put({"name": name, "date": date, "roe": roe})
                
                print(f"Worker {chunk_id}: Traitement terminé pour {name}")
            except Exception as e:
                print(f"Worker {chunk_id}: Erreur lors du traitement de {name}: {e}")
                result_queue.put({"name": name, "date": date, "roe": None})
    finally:
        driver.quit()

def parallel_scrape(data: pd.DataFrame, output_file: str, num_workers: int = 4):
    """
    Parallélise le processus de scraping avec sauvegarde progressive
    """
    # Démarre le thread d'écriture
    writer_thread = threading.Thread(target=result_writer, args=(output_file,))
    writer_thread.start()
    
    # Divise le DataFrame en groupes
    chunks = np.array_split(data, num_workers)
    
    # Crée et exécute les tâches pour chaque groupe
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_chunk, chunk, i) for i, chunk in enumerate(chunks)]
        
        # Attend que toutes les tâches soient terminées
        for future in futures:
            future.result()
    
    # Signale au writer de s'arrêter et attend qu'il termine
    stop_writer.set()
    writer_thread.join()

def main():
    # Configuration
    input_file = "real_tabulation_scraped_data.csv"
    output_file = "roe_results.csv"
    num_workers = 4
    
    print("Lecture du fichier d'entrée...")
    data = pd.read_csv(input_file, delimiter="\t", on_bad_lines='skip')
    
    print(f"Démarrage du traitement parallèle avec {num_workers} workers...")
    parallel_scrape(data, output_file, num_workers)
    
    # Lecture des résultats finaux pour les statistiques
    results_df = pd.read_csv(output_file)
    success_rate = (results_df['roe'].notna().sum() / len(results_df)) * 100
    
    print(f"\nRésumé:")
    print(f"Total des entreprises traitées: {len(results_df)}")
    print(f"Scraping réussis: {results_df['roe'].notna().sum()}")
    print(f"Scraping échoués: {results_df['roe'].isna().sum()}")
    print(f"Taux de réussite: {success_rate:.2f}%")

if __name__ == "__main__":
    main()