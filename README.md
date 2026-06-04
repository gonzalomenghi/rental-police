# 🛡️ Rental Police Dashboard

Dashboard operativo de control de calidad y auditoría de tareas pendientes para el equipo de PropHero.

## Stack

- **Frontend/App:** Streamlit
- **Datos:** Metabase (CSV público directo)
- **Hosting:** Streamlit Community Cloud (gratuito)
- **Acceso:** Restringido por email corporativo

---

## Estructura del proyecto

```
rental_police/
├── app.py                          # Punto de entrada Streamlit + CSS del Brand Design System
├── requirements.txt                # Dependencias
├── .streamlit/
│   └── config.toml                 # Tema visual (Ocean Blue / Space Blue / Sand)
├── data/
│   └── snapshots.json              # Historial semanal de KPIs (generado automáticamente)
├── sections/
│   ├── summary.py                  # Pestaña 0: Dashboard global con gráficos y WoW
│   ├── ir_coaches.py               # Pestaña 1: IR & Coaches Team
│   ├── rental_team.py              # Pestaña 2: Rental Team
│   └── supply_team.py              # Pestaña 3: Supply Team
└── utils/
    ├── data.py                     # Carga desde Metabase CSV
    ├── filters.py                  # Toda la lógica Pandas de filtrado y KPIs
    ├── ui.py                       # Componentes visuales del Brand Design System
    └── snapshot.py                 # Almacenamiento semanal para evolución WoW
```

---

## Pestañas

### 📊 Dashboard (nueva)
Vista global sin filtros de equipo aplicados:
- **KPI cards** con totales por área y delta vs. semana anterior
- **Bar chart** de alertas por sección, coloreado por equipo
- **Donut chart** de distribución porcentual por área
- **Gráfico de líneas WoW** con la evolución semanal de cada equipo (aparece a partir de 2 semanas de datos)
- Breakdown por área con mini-KPIs y deltas inline

### 👥 IR & Coaches Team
- Sub-A: Pending Subscription Offers — falta `subscription_plan_offer`
- Sub-B: PM Selected Plan Missing — falta `pm_selected_plan`
- Home Insurance Tracking — campos de seguro incompletos
- Missing Client's Info — nombre, email, documentos KYC

### 🏪 Rental Team
- Unassigned Property Managers — propiedades sin `pm_company`
- Ready-to-Rent Data Gaps — fechas clave faltantes
- Missing Lease & Subscription Info — datos contractuales post tenant-found

### 📍 Supply Team
- Missing Key Data — sin `suburb_section_name` o `area_cluster`
- Already Tenanted Properties — documentación incompleta para ya-alquilados

---

## Brand Design System

La UI sigue el Brand Styleguide oficial de PropHero:

| Token | Color | Uso |
|---|---|---|
| Ocean Blue | `#009CDF` | Botones, tags, color primario |
| Space Blue | `#26204E` | Sidebar, headers, tab activo |
| Sky Blue | `#A5D7FC` | Acentos secundarios |
| Sand | `#E8E2DC` | Fondos de paneles, mensajes info |
| Tipografía | Manrope 400/600/700 | Global vía Google Fonts |

Las tarjetas KPI siguen el concepto **"Parcels"**: contenedores blancos con borde izquierdo coloreado según severidad:

- 🚩 **CRITICAL_RED** `#C0392B` — alertas bloqueantes / Post-Reno (Alta)
- **WARNING_ORANGE** `#D4760A` — alertas medias / Pre-Reno (Media)
- **OCEAN_BLUE** `#009CDF` — métricas de conteo informacional

---

## Evolución semanal (Week-over-Week)

Al cargar el dashboard, `utils/snapshot.py` guarda automáticamente los KPIs de la semana actual en `data/snapshots.json` (clave ISO `YYYY-Www`). En semanas siguientes, la pestaña Dashboard muestra:
- Delta ↑/↓ en cada KPI card comparando con la semana anterior
- Gráfico de líneas con la evolución histórica por área

> **Nota en Streamlit Community Cloud:** el archivo `snapshots.json` persiste dentro del mismo deployment. Si el app se redeploya (nuevo push a main), el historial se reinicia salvo que el archivo sea commiteado al repositorio.

---

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

---

## Despliegue en Streamlit Community Cloud

1. Subir el proyecto a un repositorio GitHub (puede ser privado)
2. Ir a [share.streamlit.io](https://share.streamlit.io) → conectar repo → seleccionar `app.py`
3. En **Settings → Viewer authentication**, agregar los emails o dominio del equipo

No es necesario configurar secrets. La URL quedará disponible en `https://tu-app.streamlit.app`

---

## Fuente de datos

Los datos se obtienen directamente desde Metabase vía CSV público, definido en `utils/data.py`:

```python
METABASE_URL = "https://metabase.prophero.com.au/public/question/e3c80ecb-a143-4fda-8f40-680d03ab4dac.csv"
```

El cache se refresca automáticamente cada 5 minutos. El botón **Refrescar datos** del sidebar fuerza una actualización inmediata.

---

## Lógica de datos

Toda la lógica de filtrado está centralizada en `utils/filters.py`.
Las constantes de negocio (planes, stages, statuses) están al inicio del archivo para facilitar su mantenimiento.

Los componentes visuales compartidos (tarjetas KPI, función `show_detail`) viven en `utils/ui.py` para mantener consistencia visual entre pestañas.

### Columnas requeridas en el dataset

| Columna | Usado en |
|---|---|
| `investor_relations_name` | IR & Coaches (secciones 1 y 2) |
| `coach` | IR & Coaches (sección 3) |
| `rental_lead` | Rental Team |
| `supply_lead` | Supply Team |
| `pm_selected_plan` | IR & Coaches y Rental Team |
| `stage` | Todas |
| `engagement_stage` | IR & Coaches |
| `engagement_type` | IR & Coaches |
| `set_up_status` | Todas (cálculo de prioridad) |
| `subscription_plan_offer` | IR & Coaches sec. 1A, Rental Team sec. 3B |
| `home_insurance_offer/choice/type` | IR & Coaches sec. 2 |
| `client_full_name/email` | IR & Coaches sec. 3 |
| `tech_bank_ownership_proof_urls` | IR & Coaches sec. 3 |
| `tech_id_copy_urls` | IR & Coaches sec. 3 |
| `pm_company` | Rental Team sec. 1 |
| `real_property_ready_date/property_ready_date/ready_delay_reason` | Rental Team sec. 2 |
| `actual_rent/lease_date/rent_contract_date` | Rental Team sec. 3A |
| `rent_insurance/rent_insurance_choice` | Rental Team sec. 3B |
| `suburb_section_name/area_cluster` | Supply Team sec. 1 |
| `country/test_flag/priority` | Supply Team sec. 1 |
| `already_tenanted/contract_date` | Supply Team sec. 2 |
| `supply_already_tenanted_tenant/rental/insurance` | Supply Team sec. 2 |
