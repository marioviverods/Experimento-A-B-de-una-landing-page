"""Revisión propuesta; requiere el CSV original. No ejecutada con microdatos."""
from pathlib import Path
import pandas as pd
from scipy import stats

path = Path(__file__).resolve().parent / 'data/landing_experiment.csv'
if not path.exists():
    raise SystemExit('Falta data/landing_experiment.csv. No se generan datos sustitutos.')
df = pd.read_csv(path)
required = {'user_id', 'date', 'landing', 'converted', 'gasto', 'traffic_source', 'user_type'}
missing = required - set(df.columns)
if missing:
    raise ValueError(f'Faltan columnas: {sorted(missing)}')
if df[list(required)].isna().any().any():
    raise ValueError('Hay nulos en variables requeridas; investigar antes de continuar.')
if df['user_id'].duplicated().any():
    raise ValueError('Hay usuarios repetidos; revisar unidad experimental y asignación.')
if set(df['landing']) != {'A', 'B'} or not df['converted'].isin([0, 1]).all():
    raise ValueError('Grupos o conversiones fuera del dominio esperado.')
df['date'] = pd.to_datetime(df['date'], errors='raise')
df['gasto'] = pd.to_numeric(df['gasto'], errors='raise')
if not df['gasto'].map(lambda x: float('-inf') < x < float('inf')).all():
    raise ValueError('Gasto contiene valores no finitos.')
if (df['gasto'] < 0).any():
    raise ValueError('Hay gasto negativo: revisar devoluciones y definición de la métrica.')
print('Fechas:', df['date'].min(), df['date'].max())
print('Registros:', len(df))
print('No convertidos con gasto distinto de cero:',
      int(((df['converted'] == 0) & (df['gasto'] != 0)).sum()))
print(df.groupby('landing').agg(usuarios=('user_id', 'count'),
                               conversion=('converted', 'mean'),
                               gasto_por_asignado=('gasto', 'mean')))

# Propuesta: gasto de todos los usuarios asignados, incluidos ceros.
# Welch evita imponer igualdad de varianzas; no valida independencia ni diseño.
a = df.loc[df['landing'] == 'A', 'gasto']
b = df.loc[df['landing'] == 'B', 'gasto']
if min(len(a), len(b)) < 2:
    raise ValueError('Se requieren al menos dos observaciones por grupo.')
res = stats.ttest_ind(a, b, equal_var=False)
print(f'Welch A−B: t={res.statistic:.6f}, p={res.pvalue:.6e}')
print('Diferencia media B−A:', b.mean() - a.mean())
print('Revisar distribución, extremos y supuestos antes de interpretar.')
