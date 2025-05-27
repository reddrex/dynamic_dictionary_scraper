import pandas as pd
import os

output_file = "colocaciones_fig.csv"

if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
    df_final = pd.read_csv(output_file)
    df_final = df_final.sort_values(by="lema", key=lambda col: col.str.lower())
    df_final.to_csv(output_file, index=False, encoding="utf-8")
    print(f"✅ CSV ordenado alfabéticamente y guardado: {output_file}")
else:
    print("⚠️ El archivo está vacío o no existe.")
