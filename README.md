# GitHub Portfolio Analyzer

Analiza los repositorios públicos de un usuario de GitHub y genera un reporte HTML autocontenido con métricas visuales: distribución de lenguajes, top repos y gráfico de actividad estilo contribution graph.

Se puede correr localmente o publicar en **GitHub Pages con actualización automática semanal** vía GitHub Actions.

---

## Features

- Obtiene todos los repositorios públicos vía la GitHub API (con paginación)
- Calcula distribución de lenguajes con barra segmentada y donut chart en colores oficiales de GitHub Linguist
- Top repositorios ordenados por estrellas y actividad reciente
- Gráfico de actividad de commits: grid de 52 semanas × 7 días, estilo GitHub contribution graph
- Reporte HTML autocontenido (sin CDNs externos — funciona offline y como página estática)
- Toggle ES / EN integrado en el mismo archivo
- Sin base de datos, sin servidor, sin IA — CLI puro → HTML estático

---

## Requisitos

- Python 3.11+
- Un [GitHub personal access token](https://github.com/settings/tokens) (opcional — evita rate limits: 60 req/hr vs 5 000)

---

## Instalación

```bash
git clone https://github.com/dajozu2513/github-portfolio-analyzer.git
cd github-portfolio-analyzer
pip install -r requirements.txt

# Opcional: crear .env con tu token
cp .env.example .env
# Editar .env y agregar GITHUB_TOKEN=ghp_...
```

---

## Uso local

```bash
python main.py --username YOUR_GITHUB_USERNAME
python main.py --username dajozu2513 --output ./output/report.html
```

El reporte se guarda en `./output/report.html`. Abrir en cualquier browser — no requiere conexión a internet después de generarse.

---

## Publicar en GitHub Pages

El proyecto incluye un workflow de GitHub Actions que regenera el reporte cada lunes y lo publica automáticamente en GitHub Pages.

### Pasos de configuración (una sola vez)

**1. Subir el repo a GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/dajozu2513/<nombre-del-repo>.git
git push -u origin main
```

**2. Activar GitHub Pages**

En el repo → **Settings → Pages → Source** → seleccionar la rama **`gh-pages`**, directorio raíz `/`. Guardar.

**3. Agregar el secret del token (opcional, recomendado)**

Para evitar rate limits de la API de GitHub, crear un [Personal Access Token](https://github.com/settings/tokens/new) (classic, scope: `public_repo`) y agregarlo como secret:

- Ir a **Settings → Secrets and variables → Actions → New repository secret**
- Nombre: `GH_PAT`
- Valor: `ghp_xxxxxxxxxx` (tu token)

> Si no se configura `GH_PAT`, el workflow funciona igual con autenticación anónima (60 req/hr). Para perfiles con muchos repos puede ser suficiente; para perfiles grandes se recomienda el token.

**4. Primera ejecución manual**

En la pestaña **Actions → Update Portfolio → Run workflow** para generar el reporte inmediatamente sin esperar al lunes.

**5. URL del reporte publicado**

```
https://dajozu2513.github.io/<nombre-del-repo>/
```

### Cómo funciona

- El workflow corre **automáticamente todos los lunes a las 8:00 UTC**
- También se puede disparar manualmente desde la pestaña Actions (`workflow_dispatch`)
- El script genera `index.html` en el runner → `peaceiris/actions-gh-pages` lo pushea a la rama `gh-pages`
- Ningún secret ni token se commitea al repo — todo se maneja como GitHub Secret

---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Jinja2](https://img.shields.io/badge/Jinja2-3.x-B41717)
![Requests](https://img.shields.io/badge/Requests-2.x-2CA5E0)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=github-actions&logoColor=white)
