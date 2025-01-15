import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time 

# Configuration du driver Selenium en mode visualisé (Headful)
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Ouvrir le navigateur en mode maximisé
    chrome_options.add_argument("--disable-gpu")  # Nécessaire pour Windows
    chrome_options.add_argument("--no-sandbox")  # Nécessaire pour certains environnements Linux
    service = Service("/Users/issameabdeljalil/Downloads/chromedriver-mac-arm64/chromedriver")  # Remplacez par le chemin vers votre ChromeDriver
    return webdriver.Chrome(service=service, options=chrome_options)

# Wrapper pour gérer les éléments Selenium
# Wrapper pour gérer les éléments Selenium
class SmartElement:
    def __init__(self, driver, locator):
        """
        Un wrapper pour les éléments Selenium qui gère la relocalisation automatique si l'élément devient obsolète.
        """
        self.driver = driver
        self.locator = locator
        self.element = None

    def get_element(self):
        """
        Récupère l'élément actuel, ou le relocalise si l'élément est obsolète.
        """
        try:
            if self.element:
                # Vérifie si l'élément est encore valide
                self.element.is_displayed()
            return self.element
        except (StaleElementReferenceException, AttributeError):
            try:
                # Relocalise l'élément si nécessaire
                self.element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(self.locator)
                )
                return self.element
            except TimeoutException:
                print(f"Impossible de localiser l'élément avec le locator : {self.locator}")
                return None

    def click(self):
        """
        Clique sur l'élément après relocalisation si nécessaire.
        """
        element = self.get_element()
        if element:
            element.click()
        else:
            print("Erreur : Impossible de cliquer sur l'élément, non trouvé.")

    def send_keys(self, keys):
        """
        Envoie des touches au champ texte après relocalisation si nécessaire.
        """
        element = self.get_element()
        if element:
            element.send_keys(keys)
        else:
            print("Erreur : Impossible d'envoyer des touches, élément non trouvé.")

    def clear(self):
        """
        Efface le contenu d'un champ texte.
        """
        element = self.get_element()
        if element:
            element.clear()
        else:
            print("Erreur : Impossible de nettoyer le champ, élément non trouvé.")

    def find_elements(self, by, value):
        """
        Trouve les sous-éléments dans cet élément.
        """
        element = self.get_element()
        if element:
            return element.find_elements(by, value)
        else:
            print("Erreur : Impossible de trouver les sous-éléments, élément non trouvé.")
            return []

    def text(self):
        """
        Récupère le texte de l'élément.
        """
        element = self.get_element()
        return element.text if element else None


# Fonction pour scraper le ROE
def scrape_roe(driver, company_name, year):
    url = "https://stockanalysis.com/"
    driver.get(url)
    
    try:
        # Rechercher la barre de recherche
        search_box_locator = (By.CSS_SELECTOR, "input[aria-label='Search']")
        search_box = SmartElement(driver, search_box_locator)
        
        # Nettoyer et envoyer les touches
        if search_box.get_element() is None:
            print("Erreur : La barre de recherche n'a pas été trouvée.")
            return None

        search_box.clear()
        search_box.send_keys(company_name)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)  # Pause pour que le résultat s'affiche
        
        # Cliquer sur "Financials"
        financials_link_locator = (By.LINK_TEXT, "Financials")
        financials_link = SmartElement(driver, financials_link_locator)
        if financials_link.get_element() is None:
            print("Erreur : Le lien 'Financials' n'a pas été trouvé.")
            return None
        financials_link.click()
        time.sleep(2)
        
        # Cliquer sur "Ratios"
        ratios_link_locator = (By.LINK_TEXT, "Ratios")
        ratios_link = SmartElement(driver, ratios_link_locator)
        if ratios_link.get_element() is None:
            print("Erreur : Le lien 'Ratios' n'a pas été trouvé.")
            return None
        ratios_link.click()
        time.sleep(2)
        
        # Localiser le tableau
        table_locator = (By.CSS_SELECTOR, "table[data-test='financials']")
        table = SmartElement(driver, table_locator)

        if table.get_element() is None:
            print("Erreur : Le tableau des ratios n'a pas été trouvé.")
            return None

        # Rechercher les lignes dans le tableau
        rows = table.find_elements(By.TAG_NAME, "tr")
        roe_value = None

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 0 and "Return on Equity" in row.text:
                for i, cell in enumerate(cells):
                    if cell.text.strip() == str(year):
                        roe_value = cells[i + 1].text.strip()  # Valeur ROE après l'année
                        break
                break  # Quitter la boucle après avoir trouvé la ligne correspondante
        
        if roe_value:
            print(f"ROE pour {company_name} en {year} : {roe_value}")
            return roe_value
        else:
            print(f"ROE introuvable pour {company_name} en {year}")
            return None

    except Exception as e:
        print(f"Erreur lors du scraping pour {company_name}: {e}")
        print("HTML actuel de la page :")
        print(driver.page_source)  # Aide à diagnostiquer
        return None


# Fonction principale
def main():
    # Charger le fichier CSV
    input_file = "real_tabulation_scraped_data.csv"  # Remplacez par le chemin vers votre fichier CSV
    data = pd.read_csv(input_file, delimiter="\t", on_bad_lines='skip')
    
    # Sélectionner les 10 premières entreprises
    top_companies = data.head(6)
    
    # Configurer Selenium
    driver = setup_driver()
    
    results = []
    try:
        for _, row in top_companies.iterrows():
            name = row["name"]
            date = row["date"]
            year = pd.to_datetime(date).year  # Extraire l'année
            
            print(f"Scraping ROE pour {name} en {year}...")
            roe = scrape_roe(driver, name, year)  # Utiliser le nom complet de l'entreprise
            results.append({"name": name, "year": year, "roe": roe})
    finally:
        driver.quit()  # Fermer le navigateur
    
    # Sauvegarder les résultats dans un fichier CSV
    output_file = "roe_results.csv"
    pd.DataFrame(results).to_csv(output_file, index=False)
    print(f"Résultats sauvegardés dans {output_file}")

if __name__ == "__main__":
    main()
