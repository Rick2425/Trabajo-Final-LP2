import pandas as pd
import os
from datetime import datetime

class DataUnifier:
    """
    Clase encargada de consolidar y homogeneizar los archivos CSV 
    de fuentes nacionales e internacionales en un único dataset maestro.
    """
    def __init__(self, archivo_peru, archivo_usa, archivo_salida):
        self.archivo_peru = archivo_peru
        self.archivo_usa = archivo_usa
        self.archivo_salida = archivo_salida

    def integrar_datasets(self):
        """
        Lee ambos archivos CSV, los concatena verticalmente, recalcula 
        un ID único global y exporta el archivo unificado final.
        """
        print("[INFO] Iniciando el proceso de unificación de noticias...")
        
        # Verificamos que ambos archivos existan antes de operar
        if not os.path.exists(self.archivo_peru) or not os.path.exists(self.archivo_usa):
            print("[ERROR] Falta alguno de los archivos CSV de origen. Asegúrate de haber ejecutado los scripts 01 y 02.")
            return False
            
        try:
            # 1. Cargar los CSVs
            df_peru = pd.read_csv(self.archivo_peru)
            df_usa = pd.read_csv(self.archivo_usa)
            
            print(f"[LEÍDO] '{self.archivo_peru}' contiene {len(df_peru)} noticias.")
            print(f"[LEÍDO] '{self.archivo_usa}' contiene {len(df_usa)} noticias.")
            
            # Quitar la columna 'id_noticia' vieja para que no choque al juntarse
            if 'id_noticia' in df_peru.columns:
                df_peru = df_peru.drop(columns=['id_noticia'])
            if 'id_noticia' in df_usa.columns:
                df_usa = df_usa.drop(columns=['id_noticia'])
                
            # 2. Concatenar filas de ambos mundos (Lego)
            df_maestro = pd.concat([df_peru, df_usa], ignore_index=True)
            
            # 3. Generar el nuevo ID unificado secuencial global (1, 2, 3...)
            df_maestro.insert(0, 'id_noticia', range(1, len(df_maestro) + 1))
            
            # 4. Guardar el archivo maestro final limpio
            df_maestro.to_csv(self.archivo_salida, index=False, encoding='utf-8-sig')
            
            print("-" * 60)
            print(f"[ÉXITO] Base de datos unificada integrada con {len(df_maestro)} filas totales.")
            print(f"[PROCESO COMPLETADO] Archivo maestro generado: '{self.archivo_salida}'")
            print("-" * 60)
            return True
            
        except Exception as e:
            print(f"[ERROR] Ocurrió un fallo al unificar los datasets: {e}")
            return False

# ==============================================================================
# BLOQUE DE EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    # Definimos las rutas de los archivos generados previamente
    origen_peru = "noticias_larepublica.csv"
    origen_usa = "noticias_nyt.csv"
    destino_final = "base_noticias_politicas.csv"
    
    # Instanciamos la clase unificadora
    unificador = DataUnifier(origen_peru, origen_usa, destino_final)
    
    # Ejecutamos la consolidación de datos
    unificador.integrar_datasets()