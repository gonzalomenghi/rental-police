# 🛡️ Rental Police Dashboard

Dashboard operativo de control de calidad y auditoría de tareas pendientes para el equipo de PropHero.

## Stack

- **Frontend/App:** Streamlit
- **Datos:** Metabase (CSV público directo)
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
│   └── config.toml                 # Tema visual
├── sections/
│   ├── ir_coaches.py               # Pestaña 1: IR & Coaches Team
│   ├── rental_team.py              # Pestaña 2: Rental Team
│   └── supply_team.py              # Pestaña 3: Supply Team
└── utils/
    ├── data.py                     # Carga desde Metabase CSV
    └── filters.py                  # Toda la lógica Pandas de filtrado
```

## Setup local

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar localmente

```bash
streamlit run app.py
```

No se requieren credenciales ni configuración adicional. Los datos se cargan directamente desde la URL pública de Metabase.

## Despliegue en Streamlit Community Cloud

1. Subir el proyecto a un repositorio GitHub (puede ser privado)
2. Ir a [share.streamlit.io](https://share.streamlit.io) → conectar repo → seleccionar `app.py`
3. En **Settings → Viewer authentication**, agregar los emails o dominio del equipo

No es necesario configurar secrets. La URL quedará disponible en `https://tu-app.streamlit.app`

## Fuente de datos

Los datos se obtienen directamente desde Metabase vía CSV público, definido en `utils/data.py`:

```python
METABASE_URL = "https://metabase.prophero.com.au/public/question/e3c80ecb-a143-4fda-8f40-680d03ab4dac.csv"
```

El cache se refresca automáticamente cada 5 minutos. El botón **Refrescar datos** del sidebar fuerza una actualización inmediata.

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
