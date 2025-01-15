import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service("/Users/issameabdeljalil/Downloads/chromedriver-mac-arm64/chromedriver") #à remplacer parce que c'est le chemin de mon chromedriver
    return webdriver.Chrome(service=service, options=chrome_options)

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

def main():
    input_file = "real_tabulation_scraped_data.csv"
    data = pd.read_csv(input_file, delimiter="\t", on_bad_lines='skip')
    #Il faudra tester avec plus d'entreprises par la suite 
    top_companies = data.head(10)
    
    driver = setup_driver()
    
    results = []
    try:
        for _, row in top_companies.iterrows():
            name = row["name"]
            date = row["date"]
            print(f"\nTraitement de {name} pour la date {date}")
            roe = scrape_roe(driver, name, date)
            results.append({"name": name, "date": date, "roe": roe})
    finally:
        driver.quit()

    output_file = "roe_results.csv"
    pd.DataFrame(results).to_csv(output_file, index=False)
    print(f"Résultats sauvegardés dans {output_file}")

if __name__ == "__main__":
    main()