import re
import random
import os
from time import sleep

import json
from datetime import datetime

from geopy.geocoders import Nominatim

from selenium import webdriver
from chromedriver_py import binary_path
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

from ai_model import ModelHandler

class WallapopScraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--disable-search-engine-choice-screen")
        self.options.add_argument("--ignore-certificate-errors")
        self.options.add_argument("--ignore-ssl-errors")
        self.options.add_argument("--allow-insecure-localhost")
        self.options.add_argument("--ignore-urlfetcher-cert-requests")
        self.options.page_load_strategy = 'eager'
        
        """self.options.add_argument("--headless")  # Ejecutar en modo headless
        self.options.add_argument("--disable-gpu")  # Deshabilitar GPU para mejorar rendimiento en headless
        self.options.add_argument("--no-sandbox")  # Deshabilitar sandbox para mayor compatibilidad
        self.options.add_argument("--disable-dev-shm-usage")  # Manejo de memoria compartida

        # Opciones adicionales para suprimir advertencias y errores SSL
        self.options.add_argument("--log-level=3")  # Suprime advertencias y mensajes de error
        self.options.add_argument("--ignore-certificate-errors-spki-list")
        self.options.add_argument("--ignore-certificate-errors")"""

        self.svc = webdriver.ChromeService(executable_path=binary_path)
        self.driver = webdriver.Chrome(service=self.svc, options=self.options)

    def convert_into_search(self, user_search):
        user_search_list = []
        for item in user_search:
            if item == " ":
                user_search_list.append("%20")
            else:
                user_search_list.append(item)
        return "".join(user_search_list)

    def accept_terms_walla(self):
        try:
            accept_terms = self.driver.find_element(By.ID, "onetrust-accept-btn-handler")
            if accept_terms is not None:
                accept_terms_activate = accept_terms.send_keys(Keys.RETURN)
                return accept_terms_activate
        except Exception as e:
            return f"Error aceptando terminos y condiciones de Wallapop: {str(e)}"
        
        
    def is_search_valid(self):
        try:
            error = self.driver.find_element(By.CLASS_NAME, "ErrorBox__title")
            return False
        
        except:
            return True

    def get_coordinates(self, address):
        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            raise ValueError("No se pudieron obtener las coordenadas")
    

    def get_offers(self, user_search):
        
        model_name = 'roberta-base'
        local_model_path = './local_model'
        
        handler = ModelHandler(model_name, local_model_path)

        
        # Comprobar si hay resultados
        if  self.is_search_valid():                        
        
            offertas_array = []
            try:
                cards = self.driver.find_elements(By.CLASS_NAME, "ItemCardList__item")
                for card in cards:
                    
                    # Extraer información basica del producto
                    product_url = card.get_attribute("href")
                    titulo = card.find_element(By.CLASS_NAME, "ItemCard__title").text
                    precio = card.find_element(By.CLASS_NAME, "ItemCard__price").text
                    img_container = card.find_element(By.CLASS_NAME, "ItemCard__image ")
                    img_url = img_container.find_element(By.TAG_NAME, "img").get_attribute("src")
                    card_info = card.find_element(By.CLASS_NAME, "ItemCard__info")
                    envio = card_info.find_element(By.TAG_NAME, "wallapop-badge").text

                    # Abrir la URL del producto en una nueva pestaña
                    self.driver.execute_script("window.open(arguments[0]);", product_url)
                    self.driver.switch_to.window(self.driver.window_handles[1])

                    # Extraer información adicional del producto
                    sleep(3)
                    descripcion = self.driver.find_element(By.CLASS_NAME, "item-detail_ItemDetail__description__7rXXT").text
                    try:
                        location = self.driver.find_element(By.CLASS_NAME, "item-detail-location_ItemDetailLocation___QiCU").text
                    except:
                        location = None                    
                    # Extraer información adicional del vendedor
                    seller_name = self.driver.find_element(By.CLASS_NAME, "item-detail-header_ItemDetailHeader__text--typoMidM__VeCLc").text
                    seller_rating = self.driver.find_element(By.CLASS_NAME, "item-detail-header_ItemDetailHeader__text--typoLowS__9JNQi").text
                    try:
                        # Encuentra el elemento y extrae el texto
                        seller_avg_count_text = self.driver.find_element(By.CSS_SELECTOR, '[aria-label="View Reviews"]').text
                        
                        # Extraer el número
                        match = re.search(r'\d+', seller_avg_count_text)
                        if match:
                            seller_rating_count = int(match.group())
                        else:
                            seller_rating_count = None
                    except:
                        seller_rating_count = None
                        
                    seller_sells_count = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="sellsCounter"]').text
                    
                    # Extraer el número
                    match = re.search(r'\d+', seller_sells_count)
                    if match:
                        seller_sells_count = int(match.group())
                    else:
                        seller_sells_count = None
                    
                    # Cerrar la pestaña del producto y volver a la anterior
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])

                    lat, lng = self.get_coordinates(f"{location}, España")
                    print(location, lat, lng)
                    
                    # Creacion de diccionario en python
                    ofertas = {
                        titulo: {
                            "producto_url": product_url,
                            "titulo": titulo,
                            "precio": precio,
                            "descripcion": descripcion,
                            "location": {
                                "name": location,
                                "lat": lat,
                                "lng": lng,
                            },
                            "img": img_url,
                            "envio": envio,
                            "seller": {
                                "name": seller_name,
                                "rating_avg": seller_rating,
                                "rating_count": seller_rating_count,
                                "sells_count": seller_sells_count
                            },
                            "valid": handler.classify_product(titulo, descripcion, user_search)
                        }
                    }
                    
                    
                    # Nombre del modelo preentrenado y la ruta local

                    
                    offertas_array.append(ofertas)
                    
                return offertas_array
            
            except Exception as e:
                return f"Error recuperando datos: {str(e)}"
        else:
            return "Error en la busqueda"

    def search_offers(self, search_term):
        
        formatted_search = self.convert_into_search(search_term)
        
        web = f"https://es.wallapop.com/app/search?filters_source=search_box&keywords={formatted_search}&latitude=40.41956&longitude=-3.69196&order_by=newest"
        self.driver.get(web)
        
        sleep(random.randrange(5, 8))
        self.accept_terms_walla()
        
        sleep(random.randrange(25, 30))
        return self.get_offers(search_term)

# Uso de la clase
scraper = WallapopScraper()
offers = scraper.search_offers("Consola New Nintendo 3DS")

# Formatea la fecha y hora actuales para el nombre del archivo
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Nombre del archivo con fecha y hora
filename = f"offers-{current_time}.json"

# Guarda las ofertas en un archivo JSON en la raíz del proyecto
with open(filename, 'w', encoding='utf-8') as json_file:
    json.dump(offers, json_file, ensure_ascii=False, indent=4)

print(f"Offers saved to {filename}")




