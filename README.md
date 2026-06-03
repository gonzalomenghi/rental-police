# 🛡️ Rental Police Dashboard

Dashboard operativo de control de calidad y auditoría de tareas pendientes para el equipo de PropHero.

## Stack

- **Frontend/App:** Streamlit
- **Datos:** Google Sheets (vía gspread)
- **Hosting:** Streamlit Community Cloud (gratuito)
- **Acceso:** Restringido por email corporativo

## Estructura del proyecto

```
rental_police/
├── app.py                          # Punto de entrada Streamlit
├── requirements.txt                # Dependencias
├── .gitignore
├── README.md
├── .streamlit/
│   ├── config.toml                 # Tema visual
│   └── secrets.toml.example        # Template de credenciales (no subir secrets.toml)
├── sections/
│   ├── ir_coaches.py               # Pestaña 1: IR & Coaches Team
│   ├── rental_team.py              # Pestaña 2: Rental Team
│   └── supply_team.py              # Pestaña 3: Supply Team
├── utils/
│   ├── data.py                     # Carga desde Google Sheets
│   └── filters.py                  # Toda la lógica Pandas de filtrado
└── data/
    └── export.csv                  # (opcional) CSV local para desarrollo
```

## Setup local

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar credenciales de Google Sheets

1. Ir a [console.cloud.google.com](https://console.cloud.google.com)
2. Crear proyecto → habilitar **Google Sheets API** y **Google Drive API**
3. Crear **Service Account** → descargar JSON de credenciales
4. Compartir tu Google Sheet con el email de la service account (como editor)
5. Copiar `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml`
6. Completar con los valores del JSON descargado y el ID del spreadsheet

### 3. Ejecutar localmente

```bash
streamlit run app.py
```

> **Desarrollo sin credenciales:** colocá tu CSV en `data/export.csv` y la app lo usará como fallback automático.

## Despliegue en Streamlit Community Cloud

1. Subir el proyecto a un repositorio GitHub (puede ser privado)
2. Ir a [share.streamlit.io](https://share.streamlit.io) → conectar repo → seleccionar `app.py`
3. En **Settings → Secrets**, pegar el contenido de tu `secrets.toml`
4. En **Settings → Viewer authentication**, agregar los emails o dominio del equipo

La URL quedará disponible en `https://tu-app.streamlit.app`

## Lógica de datos

Toda la lógica de filtrado está centralizada en `utils/filters.py`.
Las constantes de negocio (planes, stages, statuses) están al inicio del archivo para facilitar su mantenimiento.

### Columnas requeridas en el dataset

| Columna | Usado en |
|---|---|
| `investor_relations_name` | Pestaña 1 (secciones 1 y 2) |
| `coach` | Pestaña 1 (sección 3) |
| `rental_lead` | Pestaña 2 (sección 3) |
| `supply_lead` | Pestaña 3 |
| `pm_selected_plan` | Pestañas 1 y 2 |
| `stage` | Todas |
| `engagement_stage` | Pestaña 1 |
| `engagement_type` | Pestaña 1 |
| `set_up_status` | Todas (prioridad) |
| `subscription_plan_offer` | Pestaña 1 sección 1, Pestaña 2 sección 3B |
| `home_insurance_offer/choice/type` | Pestaña 1 sección 2 |
| `client_full_name/email` | Pestaña 1 sección 3 |
| `tech_bank_ownership_proof_urls` | Pestaña 1 sección 3 |
| `tech_id_copy_urls` | Pestaña 1 sección 3 |
| `pm_company` | Pestaña 2 sección 1 |
| `real_property_ready_date/property_ready_date/ready_delay_reason` | Pestaña 2 sección 2 |
| `actual_rent/lease_date/rent_contract_date` | Pestaña 2 sección 3A |
| `rent_insurance/rent_insurance_choice` | Pestaña 2 sección 3B |
| `suburb_section_name/area_cluster` | Pestaña 3 sección 1 |
| `country/test_flag/priority` | Pestaña 3 sección 1 |
| `already_tenanted/contract_date` | Pestaña 3 sección 2 |
| `supply_already_tenanted_tenant/rental/insurance` | Pestaña 3 sección 2 |
