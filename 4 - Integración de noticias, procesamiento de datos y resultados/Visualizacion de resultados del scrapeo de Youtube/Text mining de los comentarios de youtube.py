# ============================================================
# CREACIÓN DE TABLA DE TOKENS PARA DASHBOARD QMD
# Proyecto: Análisis de encuadres discursivos en noticias políticas
#          y eco en comentarios de YouTube mediante web scraping
#
# Entrada:
#   data/raw/comentarios_youtube_politica_depurado.csv
#
# Salida única:
#   data/processed/tabla_tokens_dashboard.csv
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import unicodedata
import warnings

import pandas as pd
import spacy

warnings.filterwarnings("ignore")


# ============================================================
# 0. INTERFAZ VISUAL OPCIONAL CON RICH
# ============================================================

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TimeElapsedColumn,
    )
    from rich.table import Table

    RICH_OK = True
except Exception:
    RICH_OK = False


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


@dataclass
class TokenConfig:
    # Ruta principal del CSV depurado generado por el scraper
    ruta_entrada: Path = BASE_DIR / "data" / "raw" / "comentarios_youtube_politica_depurado.csv"

    # Salida única para el dashboard QMD
    carpeta_salida: Path = BASE_DIR / "data" / "processed"
    archivo_tokens: str = "tabla_tokens_dashboard.csv"

    # Configuración de procesamiento textual
    columna_texto: str = "texto_comentario"
    modelo_spacy: str = "es_core_news_sm"
    min_caracteres_token: int = 3
    usar_lematizacion: bool = True
    batch_size_spacy: int = 50

    # Columnas que se conservarán desde el CSV original
    columnas_contexto: List[str] = field(default_factory=lambda: [
        "video_id",
        "titulo_video",
        "medio",
        "canal",
        "fecha_video",
        "url_video",
        "puntaje_politico",
        "personajes_detectados",
        "partidos_detectados",
        "instituciones_detectadas",
        "temas_detectados",
        "likes_comentario",
        "fecha_comentario",
        "total_respuestas",
    ])

    # Stopwords adicionales propias de comentarios de YouTube
    stopwords_extra: List[str] = field(default_factory=lambda: [
        "jajaja", "jaja", "jeje", "xd", "xddd", "jajajaja",
        "q", "k", "ke", "xq", "porque", "pq", "pa", "ps", "pues",
        "si", "no", "mas", "más", "solo", "sólo", "asi", "así",
        "ahi", "ahí", "aca", "acá", "alla", "allá",
        "hacer", "decir", "ver", "ir", "ser", "estar", "tener", "dar",
        "video", "canal", "noticia", "noticias", "vivo", "directo",
        "señor", "señora", "gracias", "favor", "verdad", "gente",
        "peru", "perú", "peruano", "peruana", "peruanos", "peruanas",
        "youtube", "comentario", "comentarios", "like", "likes",
    ])


# ============================================================
# 2. CONSOLA CON RICH
# ============================================================

class ConsolaCarga:
    def __init__(self) -> None:
        self.rich = RICH_OK
        self.console = Console() if RICH_OK else None

    def titulo(self, texto: str) -> None:
        if self.rich:
            self.console.print(
                Panel.fit(
                    texto,
                    title="Text Mining",
                    border_style="cyan"
                )
            )
        else:
            print("=" * 70)
            print(texto)
            print("=" * 70)

    def info(self, texto: str) -> None:
        if self.rich:
            self.console.print(f"[cyan]➜[/cyan] {texto}")
        else:
            print(f"-> {texto}")

    def ok(self, texto: str) -> None:
        if self.rich:
            self.console.print(f"[green]✓[/green] {texto}")
        else:
            print(f"OK: {texto}")

    def warn(self, texto: str) -> None:
        if self.rich:
            self.console.print(f"[yellow]⚠[/yellow] {texto}")
        else:
            print(f"ADVERTENCIA: {texto}")

    def error(self, texto: str) -> None:
        if self.rich:
            self.console.print(f"[red]✗[/red] {texto}")
        else:
            print(f"ERROR: {texto}")

    def crear_progress(self):
        if not self.rich:
            return None

        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console,
        )

    def tabla_final(self, datos: Dict[str, object]) -> None:
        if self.rich:
            tabla = Table(title="Resultado de creación de tabla de tokens")
            tabla.add_column("Indicador", style="cyan")
            tabla.add_column("Valor", style="green")

            for clave, valor in datos.items():
                tabla.add_row(str(clave), str(valor))

            self.console.print(tabla)
        else:
            print("\nResultado final:")
            for clave, valor in datos.items():
                print(f"{clave}: {valor}")


# ============================================================
# 3. NORMALIZADOR DE TEXTO
# ============================================================

class NormalizadorTexto:
    @staticmethod
    def quitar_tildes(texto: str) -> str:
        texto = unicodedata.normalize("NFKD", texto)
        return "".join(c for c in texto if not unicodedata.combining(c))

    @classmethod
    def normalizar(cls, texto: object) -> str:
        if pd.isna(texto):
            return ""

        texto = str(texto).lower()
        texto = re.sub(r"http\S+|www\.\S+", " ", texto)
        texto = re.sub(r"@[\w_]+", " ", texto)
        texto = texto.replace("#", " ")
        texto = cls.quitar_tildes(texto)
        texto = re.sub(r"[^a-zñ0-9\s]", " ", texto)
        texto = re.sub(r"\s+", " ", texto).strip()

        return texto


# ============================================================
# 4. DICCIONARIO DE ENCUADRES DISCURSIVOS
# ============================================================

class DiccionarioEncuadres:
    """
    Diccionario interno para clasificar tokens o expresiones políticas
    en encuadres discursivos.

    No genera archivos extra. Solo se usa para enriquecer la tabla final.
    """

    ENTRADAS_BASE = [
        # termino, encuadre, subencuadre, polaridad_encuadre, peso_encuadre

        # Corrupción y abuso de poder
        ("corrupcion", "corrupcion_abuso_poder", "acusacion_corrupcion", "negativo", 4),
        ("corrupto", "corrupcion_abuso_poder", "acusacion_corrupcion", "negativo", 4),
        ("corrupta", "corrupcion_abuso_poder", "acusacion_corrupcion", "negativo", 4),
        ("coima", "corrupcion_abuso_poder", "soborno", "negativo", 4),
        ("soborno", "corrupcion_abuso_poder", "soborno", "negativo", 4),
        ("robo", "corrupcion_abuso_poder", "apropiacion", "negativo", 3),
        ("ladron", "corrupcion_abuso_poder", "acusacion_moral", "negativo", 3),
        ("delincuente", "corrupcion_abuso_poder", "acusacion_moral", "negativo", 3),

        # Legitimidad electoral
        ("fraude", "legitimidad_electoral", "fraude_electoral", "negativo", 4),
        ("voto", "legitimidad_electoral", "votacion", "neutro", 2),
        ("votos", "legitimidad_electoral", "votacion", "neutro", 2),
        ("eleccion", "legitimidad_electoral", "proceso_electoral", "neutro", 3),
        ("elecciones", "legitimidad_electoral", "proceso_electoral", "neutro", 3),
        ("electoral", "legitimidad_electoral", "proceso_electoral", "neutro", 3),
        ("jne", "legitimidad_electoral", "institucion_electoral", "neutro", 3),
        ("onpe", "legitimidad_electoral", "institucion_electoral", "neutro", 3),
        ("reniec", "legitimidad_electoral", "institucion_electoral", "neutro", 3),

        # Autoritarismo / democracia
        ("dictadura", "autoritarismo_democracia", "amenaza_democratica", "negativo", 5),
        ("dictador", "autoritarismo_democracia", "amenaza_democratica", "negativo", 5),
        ("autoritario", "autoritarismo_democracia", "amenaza_democratica", "negativo", 4),
        ("democracia", "autoritarismo_democracia", "defensa_democratica", "positivo", 3),
        ("libertad", "autoritarismo_democracia", "defensa_libertades", "positivo", 3),

        # Conflicto político
        ("censura", "conflicto_politico", "control_politico", "negativo", 4),
        ("vacancia", "conflicto_politico", "crisis_institucional", "negativo", 4),
        ("interpelacion", "conflicto_politico", "control_politico", "neutro", 3),
        ("mocion", "conflicto_politico", "control_politico", "neutro", 3),
        ("crisis", "conflicto_politico", "crisis_politica", "negativo", 3),

        # Institucionalidad
        ("congreso", "institucionalidad", "poder_legislativo", "neutro", 3),
        ("congresista", "institucionalidad", "poder_legislativo", "neutro", 3),
        ("parlamento", "institucionalidad", "poder_legislativo", "neutro", 3),
        ("gobierno", "institucionalidad", "poder_ejecutivo", "neutro", 2),
        ("ejecutivo", "institucionalidad", "poder_ejecutivo", "neutro", 2),
        ("presidencia", "institucionalidad", "poder_ejecutivo", "neutro", 2),

        # Judicialización política
        ("fiscalia", "judicializacion_politica", "ministerio_publico", "neutro", 3),
        ("fiscal", "judicializacion_politica", "ministerio_publico", "neutro", 2),
        ("jnj", "judicializacion_politica", "junta_nacional_justicia", "neutro", 3),
        ("investigacion", "judicializacion_politica", "investigacion_fiscal", "neutro", 2),
        ("sentencia", "judicializacion_politica", "decision_judicial", "neutro", 2),
        ("denuncia", "judicializacion_politica", "acusacion_legal", "negativo", 3),
        ("poder judicial", "judicializacion_politica", "poder_judicial", "neutro", 3),
        ("ministerio publico", "judicializacion_politica", "ministerio_publico", "neutro", 3),

        # Movilización social
        ("protesta", "movilizacion_social", "protesta", "negativo", 3),
        ("marcha", "movilizacion_social", "protesta", "neutro", 3),
        ("paro", "movilizacion_social", "paro", "negativo", 3),
        ("represion", "movilizacion_social", "represion_estatal", "negativo", 4),
        ("manifestacion", "movilizacion_social", "protesta", "neutro", 3),

        # Polarización
        ("terruco", "polarizacion", "estigmatizacion", "negativo", 5),
        ("terruqueo", "polarizacion", "estigmatizacion", "negativo", 5),
        ("caviar", "polarizacion", "etiqueta_ideologica", "negativo", 4),
        ("rojete", "polarizacion", "etiqueta_ideologica", "negativo", 4),
        ("zurdo", "polarizacion", "etiqueta_ideologica", "negativo", 3),
        ("fuji", "polarizacion", "identidad_politica", "neutro", 4),
        ("fujimorismo", "polarizacion", "identidad_politica", "neutro", 4),
        ("castillista", "polarizacion", "identidad_politica", "neutro", 4),
        ("cerronista", "polarizacion", "identidad_politica", "neutro", 4),
        ("dinista", "polarizacion", "identidad_politica", "neutro", 4),

        # Desconfianza mediática y desinformación
        ("mermelero", "desconfianza_mediatica", "acusacion_prensa", "negativo", 5),
        ("mentira", "desinformacion", "acusacion_falsedad", "negativo", 3),
        ("manipulacion", "desinformacion", "manipulacion_informativa", "negativo", 4),
        ("desinformacion", "desinformacion", "contenido_falso", "negativo", 5),
        ("fake news", "desinformacion", "acusacion_falsedad", "negativo", 5),
        ("prensa vendida", "desconfianza_mediatica", "sesgo_mediatico", "negativo", 5),

        # Actores políticos
        ("boluarte", "actor_politico", "gobierno", "neutro", 4),
        ("dina boluarte", "actor_politico", "gobierno", "neutro", 5),
        ("keiko", "actor_politico", "fujimorismo", "neutro", 4),
        ("keiko fujimori", "actor_politico", "fujimorismo", "neutro", 5),
        ("fujimori", "actor_politico", "fujimorismo", "neutro", 4),
        ("castillo", "actor_politico", "castillismo", "neutro", 4),
        ("pedro castillo", "actor_politico", "castillismo", "neutro", 5),
        ("porky", "actor_politico", "renovacion_popular", "neutro", 4),
        ("rafael lopez aliaga", "actor_politico", "renovacion_popular", "neutro", 5),
        ("acuna", "actor_politico", "app", "neutro", 4),
        ("cesar acuna", "actor_politico", "app", "neutro", 5),
        ("cerron", "actor_politico", "peru_libre", "neutro", 4),
        ("vladimir cerron", "actor_politico", "peru_libre", "neutro", 5),

        # Partidos y movimientos
        ("fuerza popular", "partidos_movimientos", "fujimorismo", "neutro", 5),
        ("peru libre", "partidos_movimientos", "izquierda_partidaria", "neutro", 5),
        ("renovacion popular", "partidos_movimientos", "derecha_partidaria", "neutro", 5),
        ("app", "partidos_movimientos", "alianza_para_el_progreso", "neutro", 3),
        ("accion popular", "partidos_movimientos", "partido", "neutro", 4),
        ("avanza pais", "partidos_movimientos", "partido", "neutro", 4),
        ("apra", "partidos_movimientos", "partido", "neutro", 4),
    ]

    def __init__(self) -> None:
        self.normalizador = NormalizadorTexto()
        self.df = self._crear_dataframe()
        self.mapa_unigramas = self._crear_mapa_unigramas()
        self.patrones_multiword = self._crear_patrones_multiword()

    def _crear_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(
            self.ENTRADAS_BASE,
            columns=[
                "termino",
                "encuadre",
                "subencuadre",
                "polaridad_encuadre",
                "peso_encuadre",
            ],
        )

        df["termino_norm"] = df["termino"].apply(self.normalizador.normalizar)
        return df

    def _crear_mapa_unigramas(self) -> Dict[str, Dict[str, object]]:
        mapa = {}

        for _, row in self.df.iterrows():
            termino = row["termino_norm"]

            if " " not in termino:
                mapa[termino] = row.to_dict()

        return mapa

    def _crear_patrones_multiword(self) -> List[Tuple[re.Pattern, Dict[str, object]]]:
        patrones = []

        for _, row in self.df.iterrows():
            termino = row["termino_norm"]

            if " " in termino:
                patron = re.compile(r"(?<!\w)" + re.escape(termino) + r"(?!\w)")
                patrones.append((patron, row.to_dict()))

        return patrones

    def buscar_unigrama(self, lema: str) -> Optional[Dict[str, object]]:
        return self.mapa_unigramas.get(lema)

    def buscar_multiword(self, texto_norm: str) -> List[Dict[str, object]]:
        encontrados = []

        for patron, datos in self.patrones_multiword:
            if patron.search(texto_norm):
                encontrados.append(datos)

        return encontrados


# ============================================================
# 5. TOKENIZADOR POLÍTICO
# ============================================================

class TokenizadorPolitico:
    def __init__(self, config: TokenConfig, consola: ConsolaCarga) -> None:
        self.config = config
        self.consola = consola
        self.normalizador = NormalizadorTexto()

        self.stopwords_extra = {
            self.normalizador.normalizar(w)
            for w in self.config.stopwords_extra
        }

        self.nlp = self._cargar_modelo_spacy()

    def _cargar_modelo_spacy(self):
        try:
            nlp = spacy.load(self.config.modelo_spacy)
            self.consola.ok(f"Modelo spaCy cargado: {self.config.modelo_spacy}")
            return nlp
        except OSError:
            raise OSError(
                f"No se encontró el modelo '{self.config.modelo_spacy}'.\n"
                f"Instálalo con:\n\n"
                f"py -m spacy download {self.config.modelo_spacy}\n"
            )

    def token_valido(self, token, token_txt: str, lema: str) -> bool:
        if token.is_space or token.is_punct:
            return False

        if token.is_stop:
            return False

        if len(token_txt) < self.config.min_caracteres_token:
            return False

        if token_txt.isnumeric():
            return False

        if token_txt in self.stopwords_extra:
            return False

        if lema in self.stopwords_extra:
            return False

        return True

    def procesar_comentario(self, row: Dict[str, object], doc) -> List[Dict[str, object]]:
        filas = []

        texto_norm = row.get("texto_norm", "")

        contexto = {
            col: row.get(col, None)
            for col in self.config.columnas_contexto
        }

        for posicion, token in enumerate(doc, start=1):
            token_txt = self.normalizador.normalizar(token.text)

            if self.config.usar_lematizacion:
                lema = self.normalizador.normalizar(token.lemma_)
            else:
                lema = token_txt

            if not lema:
                lema = token_txt

            if not self.token_valido(token, token_txt, lema):
                continue

            filas.append({
                "id_comentario_tm": row.get("id_comentario_tm"),
                "comentario_id": row.get("comentario_id", None),
                **contexto,
                "texto_comentario": row.get(self.config.columna_texto, ""),
                "texto_norm": texto_norm,
                "posicion_token": posicion,
                "token": token_txt,
                "lema": lema,
                "pos_spacy": token.pos_,
                "tag_spacy": token.tag_,
                "dependencia_spacy": token.dep_,
                "es_entidad": token.ent_type_ != "",
                "tipo_entidad": token.ent_type_ if token.ent_type_ else None,
                "tipo_match": "token",
            })

        return filas

    def procesar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        filas = []
        textos_norm = df["texto_norm"].fillna("").tolist()
        registros = df.to_dict("records")

        docs = self.nlp.pipe(
            textos_norm,
            batch_size=self.config.batch_size_spacy,
        )

        for row, doc in zip(registros, docs):
            filas.extend(self.procesar_comentario(row, doc))

        return pd.DataFrame(filas)


# ============================================================
# 6. ENRIQUECEDOR CON ENCUADRES
# ============================================================

class EnriquecedorEncuadres:
    def __init__(self, diccionario: DiccionarioEncuadres, config: TokenConfig) -> None:
        self.diccionario = diccionario
        self.config = config

    def enriquecer(
        self,
        df_tokens: pd.DataFrame,
        df_original: pd.DataFrame,
    ) -> pd.DataFrame:
        df_tokens = self._agregar_encuadres_unigramas(df_tokens)
        df_multiword = self._crear_filas_multiword(df_original)

        if not df_multiword.empty:
            df_tokens = pd.concat([df_tokens, df_multiword], ignore_index=True)

        if df_tokens.empty:
            return df_tokens

        df_tokens["tiene_encuadre"] = df_tokens["encuadre"].notna()
        df_tokens["peso_encuadre"] = df_tokens["peso_encuadre"].fillna(0)

        return df_tokens

    def _agregar_encuadres_unigramas(self, df_tokens: pd.DataFrame) -> pd.DataFrame:
        if df_tokens.empty:
            columnas_extra = [
                "encuadre",
                "subencuadre",
                "polaridad_encuadre",
                "peso_encuadre",
                "termino_diccionario",
            ]

            for col in columnas_extra:
                df_tokens[col] = None

            return df_tokens

        encuadres = []

        for lema in df_tokens["lema"]:
            match = self.diccionario.buscar_unigrama(lema)

            if match:
                encuadres.append({
                    "encuadre": match["encuadre"],
                    "subencuadre": match["subencuadre"],
                    "polaridad_encuadre": match["polaridad_encuadre"],
                    "peso_encuadre": match["peso_encuadre"],
                    "termino_diccionario": match["termino"],
                })
            else:
                encuadres.append({
                    "encuadre": None,
                    "subencuadre": None,
                    "polaridad_encuadre": None,
                    "peso_encuadre": 0,
                    "termino_diccionario": None,
                })

        df_encuadres = pd.DataFrame(encuadres)

        return pd.concat(
            [df_tokens.reset_index(drop=True), df_encuadres],
            axis=1,
        )

    def _crear_filas_multiword(self, df_original: pd.DataFrame) -> pd.DataFrame:
        filas = []

        for row in df_original.to_dict("records"):
            texto_norm = row.get("texto_norm", "")
            encontrados = self.diccionario.buscar_multiword(texto_norm)

            if not encontrados:
                continue

            contexto = {
                col: row.get(col, None)
                for col in self.config.columnas_contexto
            }

            for match in encontrados:
                filas.append({
                    "id_comentario_tm": row.get("id_comentario_tm"),
                    "comentario_id": row.get("comentario_id", None),
                    **contexto,
                    "texto_comentario": row.get(self.config.columna_texto, ""),
                    "texto_norm": texto_norm,
                    "posicion_token": None,
                    "token": match["termino_norm"],
                    "lema": match["termino_norm"],
                    "pos_spacy": "MULTIWORD",
                    "tag_spacy": "MULTIWORD",
                    "dependencia_spacy": "MULTIWORD",
                    "es_entidad": False,
                    "tipo_entidad": None,
                    "tipo_match": "multiword",
                    "encuadre": match["encuadre"],
                    "subencuadre": match["subencuadre"],
                    "polaridad_encuadre": match["polaridad_encuadre"],
                    "peso_encuadre": match["peso_encuadre"],
                    "termino_diccionario": match["termino"],
                })

        return pd.DataFrame(filas)


# ============================================================
# 7. PIPELINE PRINCIPAL
# ============================================================

class TablaTokensPipeline:
    def __init__(self, config: Optional[TokenConfig] = None) -> None:
        self.config = config or TokenConfig()
        self.consola = ConsolaCarga()
        self.normalizador = NormalizadorTexto()
        self.diccionario = DiccionarioEncuadres()
        self.tokenizador = TokenizadorPolitico(self.config, self.consola)
        self.enriquecedor = EnriquecedorEncuadres(self.diccionario, self.config)

        self.config.carpeta_salida.mkdir(parents=True, exist_ok=True)

    def _resolver_ruta_entrada(self) -> Path:
        posibles_rutas = [
            self.config.ruta_entrada,
            BASE_DIR / "comentarios_youtube_politica_depurado.csv",
            BASE_DIR / "data" / "raw" / "comentarios_youtube_politica_depurado.csv",
        ]

        for ruta in posibles_rutas:
            if ruta.exists():
                return ruta

        raise FileNotFoundError(
            "No se encontró el archivo comentarios_youtube_politica_depurado.csv.\n"
            "Colócalo en una de estas rutas:\n"
            f"1) {BASE_DIR / 'comentarios_youtube_politica_depurado.csv'}\n"
            f"2) {BASE_DIR / 'data' / 'raw' / 'comentarios_youtube_politica_depurado.csv'}"
        )

    def cargar_data(self) -> pd.DataFrame:
        ruta = self._resolver_ruta_entrada()

        self.consola.info(f"Leyendo archivo: {ruta}")

        df = pd.read_csv(ruta, encoding="utf-8-sig")

        if self.config.columna_texto not in df.columns:
            raise ValueError(
                f"No existe la columna '{self.config.columna_texto}' en el CSV.\n"
                f"Columnas encontradas: {list(df.columns)}"
            )

        df = df.copy()
        df["id_comentario_tm"] = range(1, len(df) + 1)
        df["texto_norm"] = df[self.config.columna_texto].apply(
            self.normalizador.normalizar
        )

        return df

    def construir_tokens_con_rich(self, df_original: pd.DataFrame) -> pd.DataFrame:
        progress = self.consola.crear_progress()

        if progress is None:
            return self.tokenizador.procesar_dataframe(df_original)

        filas = []
        textos_norm = df_original["texto_norm"].fillna("").tolist()
        registros = df_original.to_dict("records")

        docs = self.tokenizador.nlp.pipe(
            textos_norm,
            batch_size=self.config.batch_size_spacy,
        )

        with progress:
            task = progress.add_task(
                "Tokenizando comentarios con spaCy",
                total=len(registros),
            )

            for row, doc in zip(registros, docs):
                filas.extend(self.tokenizador.procesar_comentario(row, doc))
                progress.advance(task)

        return pd.DataFrame(filas)

    def construir_tabla_tokens(self) -> pd.DataFrame:
        self.consola.titulo("CREANDO TABLA DE TOKENS PARA DASHBOARD QMD")

        df_original = self.cargar_data()
        self.consola.ok(f"Comentarios cargados: {len(df_original)}")

        self.consola.info("Procesando comentarios y creando tokens...")
        df_tokens = self.construir_tokens_con_rich(df_original)
        self.consola.ok(f"Tokens generados: {len(df_tokens)}")

        self.consola.info("Añadiendo encuadres discursivos...")
        df_tokens = self.enriquecedor.enriquecer(df_tokens, df_original)

        if not df_tokens.empty:
            df_tokens.insert(0, "id_token", range(1, len(df_tokens) + 1))
            tokens_con_encuadre = int(df_tokens["tiene_encuadre"].sum())
        else:
            tokens_con_encuadre = 0
            self.consola.warn("No se generaron tokens válidos.")

        ruta_salida = self.config.carpeta_salida / self.config.archivo_tokens
        df_tokens.to_csv(ruta_salida, index=False, encoding="utf-8-sig")

        self.consola.titulo("TABLA DE TOKENS CREADA")

        self.consola.tabla_final({
            "Comentarios analizados": len(df_original),
            "Tokens generados": len(df_tokens),
            "Tokens con encuadre": tokens_con_encuadre,
            "Archivo generado": ruta_salida,
        })

        return df_tokens


# ============================================================
# 8. EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    pipeline = TablaTokensPipeline()
    pipeline.construir_tabla_tokens()