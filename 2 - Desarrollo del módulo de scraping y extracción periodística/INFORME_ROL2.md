# Reporte Técnico (Rol 2)

## 1. Definición y Justificación de Fuentes de Información
Para la construcción del dataset maestro orientado al análisis comparativo de discursos políticos, se seleccionaron estratégicamente dos fuentes con naturalezas técnicas distintas, permitiendo evaluar el comportamiento del flujo de datos bajo diferentes metodologías de adquisición:

* **Fuente Nacional (La República - Perú):** Se eligió debido a su relevancia en la coyuntura política peruana y su estructura web pública legible. Permite un *scraping* directo sobre sus secciones mediante peticiones HTTP estructuradas, facilitando la extracción del texto completo de las noticias.
* **Fuente Internacional (The New York Times - EE.UU.):** Se seleccionó como el estándar del periodismo anglosajón. Para esta fuente, la adquisición se diseñó mediante su **API oficial de Article Search**, garantizando un acceso legítimo, ético y estable a los metadatos y titulares del diario sin infringir sus Términos de Servicio (ToS).

## 2. Estrategia de Web Scraping, Extracción y Manejo de Restricciones
El desarrollo del módulo se dividió en tres scripts independientes bajo el paradigma de **Programación Orientada a Objetos (POO)**, garantizando la modularidad y portabilidad del código:

1.  **`01_scraper_larepublica.py` (Web Scraping):** Accede a la sección de política local mediante la librería `requests` y procesa el HTML con `BeautifulSoup`. Extrae variables clave: `titulo`, `url`, `fecha_publicacion`, `autor` y el `cuerpo_texto` completo.
    * *Manejo de Restricciones:* Se implementó un plan de **pausa ética** mediante `time.sleep(2)` entre peticiones para evitar la saturación del servidor y respetar las directrices implícitas de acceso no intrusivo.
2.  **`02_extractor_nyt.py` (Conexión a API):** Conecta con los servidores de la API del NYT enviando parámetros de consulta optimizados (`q: "politics washington"`) y autenticando mediante una credencial (`api-key`). Maneja las respuestas en formato JSON para mapear de manera homogénea la información internacional.
    * *Paginación:* Se diseñó un bucle de control (`for pagina in range(paginas)`) que modifica dinámicamente el parámetro de consulta para traer los bloques de datos secuencialmente.
3.  **`03_unificar_noticias.py` (Homogeneización e Integración):** Modula la fusión vertical de los archivos generados. Utiliza `pandas` para remover identificadores locales antiguos, concatenar los registros de ambas culturas y recalcular un ID secuencial global (`id_noticia`). Las rutas se gestionan dinámicamente con la librería nativa `os` para asegurar la compatibilidad multiplataforma en el repositorio de GitHub.

## 3. Limitaciones Identificadas y Decisiones de Diseño
Durante la implementación de la fase internacional se identificó una restricción crítica: el *Paywall* (muro de pago) comercial de *The New York Times*. La API pública restringe el acceso al cuerpo completo de las noticias por derechos de autor, entregando en su lugar el *Abstract* y el *Lead Paragraph*. 

**Decisión de Diseño:** Para evitar romper la estructura de la base de datos común, el código incluye un control de excepciones que asigna el valor predeterminado `"Sin texto disponible"` en caso de campos nulos en el párrafo introductorio. Esto mitiga el impacto técnico, protegiendo la integridad del CSV maestro y permitiendo que los roles posteriores (Procesamiento y Dashboard) operen con normalidad utilizando los campos de `titulo` y `resumen` para la minería de texto y análisis de sentimientos.

## 4. Resultados de la Extracción (Volumen de Datos)
El pipeline de datos consolidó con éxito un prototipo funcional integrado por **25 noticias políticas indexadas**, distribuidas de la siguiente manera:
* **Noticias Nacionales (La República):** 15 registros (Índices 1 al 15).
* **Noticias Internacionales (The New York Times):** 10 registros (Índices 16 al 25).

El archivo resultante, `base_noticias_politicas.csv`, posee 11 variables completamente estandarizadas y limpias (`id_noticia`, `fuente`, `url`, `titulo`, `fecha_publicacion`, `autor`, `seccion`, `resumen`, `cuerpo_texto`, `metodo_extraccion`, `fecha_extraccion`), quedando disponible en el repositorio compartido para el consumo inmediato del equipo.

## 5. Reflexión Crítica sobre el Uso de LLMs
Se utilizó un modelo de lenguaje (LLM) como herramienta de asistencia para acelerar el diseño de las plantillas iniciales de las clases en POO y optimizar la sintaxis limpia de los componentes de extracción. Sin embargo, la intervención humana fue indispensable para la validación y depuración del sistema:
* Se corrigió manualmente la lógica de consulta cuando la API del NYT rechazó filtros cruzados estrictos de sección (`section_name`), adaptando los parámetros a una búsqueda generalizada para evitar respuestas en blanco.
* Se reestructuraron las salidas de archivos empleando `os.path.dirname(__file__)` tras detectar fallas de entorno local al manejar rutas relativas string explícitas.
El LLM potenció la eficiencia del desarrollo, pero la supervisión crítica garantizó la adaptabilidad real del código frente a las restricciones operativas de los servidores externos.