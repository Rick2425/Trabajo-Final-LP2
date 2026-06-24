import requests
import pandas as pd
import time
from datetime import datetime

class NYTDataExtractor:
    """
    Clase encargada de conectarse a la API oficial de The New York Times
    para extraer artículos sobre política de manera automatizada y estructurada.
    """
    def __init__(self, api_key):
        self.url_base = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
        self.api_key = api_key
        self.noticias_recolectadas = []

    def buscar_noticias_politica(self, paginas=1):
        """
        Fase 1: Realiza peticiones a la API filtrando noticias por la sección 
        de política de forma controlada.
        """
        print("[INFO] Conectando con la API de The New York Times...")
        
        params = {
            "q": "politics washington",
            "api-key": self.api_key
        }
        
        for pagina in range(paginas):
            params["page"] = pagina
            try:
                response = requests.get(self.url_base, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    articulos = data.get("response", {}).get("docs", [])
                    
                    # CORRECCIÓN AQUÍ: Separado de forma simple y tradicional
                    if not articulos:
                        print(f"[ADVERTENCIA] La API respondió bien, pero no devolvió artículos en la página {pagina}.")
                        continue
                        
                    print(f"[ÉXITO] Página {pagina} procesada. Se encontraron {len(articulos)} artículos.")
                    
                    for art in articulos:
                        titulo = art.get("headline", {}).get("main", "Sin título")
                        url = art.get("web_url", "Sin URL")
                        fecha_pub = art.get("pub_date", "Sin fecha")
                        resumen = art.get("abstract", "Sin resumen")
                        
                        byline = art.get("byline", {}).get("original", "By The New York Times")
                        autor = byline.replace("By ", "") if byline else "The New York Times"
                        
                        cuerpo_texto = art.get("lead_paragraph", "Sin texto disponible")
                        
                        noticia_data = {
                            "fuente": "The New York Times",
                            "url": url,
                            "titulo": titulo,
                            "fecha_publicacion": fecha_pub,
                            "autor": autor,
                            "seccion": "Politics",
                            "resumen": resumen,
                            "cuerpo_texto": cuerpo_texto,
                            "metodo_extraccion": "API",
                            "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        self.noticias_recolectadas.append(noticia_data)
                
                elif response.status_code == 401:
                    print("[ERROR 401] No autorizado. Tu API Key puede estar inactiva aún o mal copiada.")
                    print(f"Respuesta del servidor: {response.text}")
                elif response.status_code == 429:
                    print("[ADVERTENCIA] Límite de peticiones alcanzado. Esperando para reintentar...")
                    time.sleep(12)
                else:
                    print(f"[ERROR] Error en la API. Código de estado: {response.status_code}")
                    print(f"Detalle: {response.text}")
                    
                time.sleep(6)
                
            except Exception as e:
                print(f"[ERROR] Ocurrió una falla en la conexión con el NYT: {e}")
                
        return self.noticias_recolectadas

# ==============================================================================
# BLOQUE DE EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    # Tu API Key colocada correctamente
    MI_API_KEY = "ChjdPAXNDYUsBw8ElfYB2owOxY2JvghYbafA6nBGBsd55aS9"
    
    # Instanciamos el objeto extractor pasando la clave
    extractor = NYTDataExtractor(api_key=MI_API_KEY)
    
    # Ejecutamos la extracción de la página 0 (trae los 10 artículos más recientes)
    datos_nyt = extractor.buscar_noticias_politica(paginas=1)
    
    if datos_nyt:
        df_nyt = pd.DataFrame(datos_nyt)
        df_nyt.insert(0, 'id_noticia', range(1, len(df_nyt) + 1))
        
        import os
        directorio_actual = os.path.dirname(__file__)
        nombre_archivo = os.path.join(directorio_actual, "noticias_nyt.csv")
        
        df_nyt.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
        print(f"\n[ÉXITO] Base de datos internacional guardada como: '{nombre_archivo}'")
    else:
        print("\n[ALERTA] No se pudo generar el archivo CSV porque no se recibieron datos válidos.")