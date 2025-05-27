from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from tqdm import tqdm
import os

# ── Configuración de archivo de salida y duplicados ──────────────────────────
output_file = "colocaciones_fig.csv"
definiciones_existentes = set()

# Si existe y no está vacío, leemos definiciones ya guardadas
if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
    df_existente = pd.read_csv(output_file)
    for _, row in df_existente.iterrows():
        definiciones_existentes.add((row["lema"], row["definicion"]))
else:
    # Creamos CSV con cabecera si no existe o está vacío
    pd.DataFrame(columns=["lema", "categoria", "url", "definicion", "ejemplos", "frases"]) \
      .to_csv(output_file, index=False, encoding="utf-8")

# ── Funciones auxiliares ────────────────────────────────────────────────────
def cargar_lemas(path):
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

def extraer_definiciones_fig_por_articulo(driver, lema_original):
    url = f"https://diesgital.com/search?q={lema_original}"
    driver.get(url)
    time.sleep(2)

    resultados = []
    articulos = driver.find_elements(By.CSS_SELECTOR, "article.diesgital-article")

    for articulo in articulos:
        try:
            lema = articulo.find_element(By.CSS_SELECTOR, "span.diesgital-article-header__lemma").text.strip()
            categoria = articulo.find_element(By.CSS_SELECTOR, "span.diesgital-article-header__text").text.strip()
        except:
            continue

        bloques = articulo.find_elements(By.CSS_SELECTOR, "div.diesgital-article__meaning-container")
        for bloque in bloques:
            try:
                defin = bloque.find_element(
                    By.CSS_SELECTOR,
                    "span.diesgital-article-meaning__definition"
                ).text.strip()
            except:
                continue

            if not defin.lower().startswith("en sentido figurado"):
                continue

            # Clic en Ver más si existe
            try:
                btn = bloque.find_element(By.XPATH, ".//button[contains(., 'Ver más')]")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
            except:
                pass

            # Ejemplos
            ejemplos = []
            for s in bloque.find_elements(By.CSS_SELECTOR, "ul.diesgital-article-examples__list li span"):
                text = s.text.strip()
                if text:
                    ejemplos.append(text)

            # Frases
            frases = []
            for s in bloque.find_elements(By.CSS_SELECTOR, "ul.diesgital-article-phrases__list li span"):
                text = s.text.strip()
                if text:
                    frases.append(text)

            resultados.append({
                "lema": lema,
                "categoria": categoria,
                "url": url,
                "definicion": defin,
                "ejemplos": " || ".join(ejemplos),
                "frases": " || ".join(frases)
            })

    return resultados

# ── Configuración de Selenium ────────────────────────────────────────────────
def iniciar_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

driver = iniciar_driver()
lemas = cargar_lemas("lemas_limpios.txt")

for lema in tqdm(lemas, desc="Scrapeando lemas", unit="lema"):
    try:
        datos = extraer_definiciones_fig_por_articulo(driver, lema)
    except Exception as e:
        print(f"\n⚠️ Error con lema '{lema}': {e}")
        try:
            driver.quit()
        except:
            pass
        print("🔁 Reiniciando navegador...")
        time.sleep(5)
        driver = iniciar_driver()
        continue

    nuevos = []
    for d in datos:
        clave = (d["lema"], d["definicion"])
        if clave not in definiciones_existentes:
            definiciones_existentes.add(clave)
            nuevos.append(d)

    if nuevos:
        pd.DataFrame(nuevos).to_csv(
            output_file,
            mode="a",
            header=False,
            index=False,
            encoding="utf-8"
        )

# ── Cierre de navegador ──────────────────────────────────────────────────────
driver.quit()

# ── Ordenar CSV final por lema ────────────────────────────────────────────────
if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
    df_final = pd.read_csv(output_file)
    df_final = df_final.sort_values(
        by="lema",
        key=lambda col: col.str.lower()
    )
    df_final.to_csv(output_file, index=False, encoding="utf-8")
    print(f"✅ CSV final ordenado por lema guardado en: {output_file}")
else:
    print("⚠️ No hay datos para ordenar.")
