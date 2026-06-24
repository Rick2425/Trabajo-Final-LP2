import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

class LaRepublicaScraper:
    """
    Clase encargada de realizar el Web Scraping de la sección de política
    del diario La República de forma automatizada y ordenada.
    """
    def __init__(self, user_agent=None):
        self.url_base = "https://larepublica.pe/politica"
        self.headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.noticias_urls = []

    def obtener_urls_politica(self):
        """
        Fase 1: Conectarse a la página principal de política y extraer los enlaces (URLs)
        de las noticias del día.
        """
        print(f"[INFO] Conectando a la sección de política: {self.url_base}...")
        try:
            response = requests.get(self.url_base, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                print("[ÉXITO] Estructura HTML descargada correctamente.")
                
                enlaces = soup.find_all('a', href=True)
                print(f"[DEBUG] Se encontraron {len(enlaces)} etiquetas 'a' en total en la página.")
                
                for enlace in enlaces:
                    url = enlace['href']
                    
                    if url.startswith('/politica/'):
                        url = "https://larepublica.pe" + url
                    
                    if "larepublica.pe/politica/" in url and url not in self.noticias_urls:
                        if url != "https://larepublica.pe/politica" and url != "https://larepublica.pe/politica/":
                            self.noticias_urls.append(url)
                
                print(f"[INFO] Se han detectado {len(self.noticias_urls)} URLs únicas de noticias de política.")
                return self.noticias_urls
            else:
                print(f"[ERROR] No se pudo acceder. Código de estado HTTP: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[ERROR] Ocurrió un fallo en la conexión: {e}")
            return []

    def scrapear_detalle_noticias(self, limite=3):
        """
        Fase 2: Entra a un número limitado de URLs recolectadas para extraer
        la información detallada de cada noticia política.
        """
        if not self.noticias_urls:
            print("[ADVERTENCIA] No hay URLs cargadas para extraer detalle.")
            return []
        
        base_noticias = []
        urls_a_procesar = self.noticias_urls[:limite]
        
        print(f"\n[INFO] Iniciando el scraping de {len(urls_a_procesar)} noticias...")
        
        for i, url in enumerate(urls_a_procesar, start=1):
            print(f"[{i}/{len(urls_a_procesar)}] Procesando: {url}")
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extraer el título h1
                    titulo = soup.find('h1').text.strip() if soup.find('h1') else "Sin título"
                    
                    # Extraer el resumen o subtítulo (bajada)
                    resumen = soup.find('p', class_='bajaba') or soup.find('h2')
                    resumen = resumen.text.strip() if resumen else "Sin resumen"
                    
                    # Extraer la fecha
                    fecha = soup.find('time')
                    fecha_publicacion = fecha['datetime'] if fecha and fecha.has_attr('datetime') else (fecha.text.strip() if fecha else "Sin fecha")
                    
                    # Extraer el autor
                    autor = soup.find('span', class_='autor') or soup.find('a', rel='author')
                    autor = autor.text.strip() if autor else "Redacción La República"
                    
                    # Juntar los párrafos principales del cuerpo
                    parrafos = soup.find_all('p')
                    cuerpo_texto = " ".join([p.text.strip() for p in parrafos if len(p.text.strip()) > 30])
                    
                    noticia_data = {
                        "fuente": "La República",
                        "url": url,
                        "titulo": titulo,
                        "fecha_publicacion": fecha_publicacion,
                        "autor": autor,
                        "seccion": "Política",
                        "resumen": resumen,
                        "cuerpo_texto": cuerpo_texto[:600] + "...",  # Guardamos los primeros 600 caracteres
                        "metodo_extraccion": "Scraping",
                        "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    base_noticias.append(noticia_data)
                
                # Pausa prudencial ética entre solicitudes (2 segundos)
                time.sleep(2)
                
            except Exception as e:
                print(f"[ERROR] No se pudo procesar la URL {url}: {e}")
                
        return base_noticias

# ==============================================================================
# BLOQUE DE EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    # Instanciamos el objeto scraper
    scraper = LaRepublicaScraper()
    
    # 1. Obtener la lista de enlaces
    urls_detectadas = scraper.obtener_urls_politica()
    
    # 2. Extraer el contenido de las primeras noticias detectadas
    if urls_detectadas:
        lista_noticias = scraper.scrapear_detalle_noticias(limite=15)
        
        # 3. Guardar los datos recolectados en formato CSV
        if lista_noticias:
            df = pd.DataFrame(lista_noticias)
            # Creamos un ID único correlativo para cada fila
            df.insert(0, 'id_noticia', range(1, len(df) + 1))
            
            import os
            directorio_actual = os.path.dirname(__file__)
            nombre_archivo = os.path.join(directorio_actual, "noticias_larepublica.csv")
            
            df.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
            print(f"\n[ÉXITO] Base de datos cruda guardada correctamente como: '{nombre_archivo}'")
    else:
        print("[ALERTA] No se procesaron detalles porque la lista de URLs quedó vacía.")