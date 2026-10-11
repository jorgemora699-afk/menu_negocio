# QR Menu 📱

Plataforma SaaS multi-inquilino para crear y publicar menús digitales de restaurantes y bares. Cada negocio administra sus categorías y productos desde un panel, personaliza la apariencia de su menú y obtiene un código QR para que sus clientes lo consulten desde el celular.


## Problema

Los menús impresos son costosos de actualizar y se desgastan. Cambiar un precio o agotar un plato implica reimprimir, y los negocios pequeños no suelen tener un sistema propio para manejarlo.

## Funcionalidades

**Panel de administración (por negocio)**
- Registro e inicio de sesión con JWT (sesión de 7 días).
- CRUD de categorías con emoji y de productos con imagen (Cloudinary).
- Ordenamiento de categorías y productos con botones de reordenar.
- Edición del perfil del negocio.
- Personalización del menú: colores con selector y combinaciones tipográficas por negocio.
- Exportación de la tarjeta con el código QR.

**Menú público (clientes)**
- Acceso por URL propia del negocio (`/:slug`) o escaneando el QR.
- Diseño responsive pensado para celular.
- Datos servidos desde un endpoint público `/api/menu/{slug}`.

## Modelo de datos

- Arquitectura **multi-inquilino**: cada negocio tiene su `slug` único y sus datos aislados.
- Relación negocio → categorías → productos.
- Configuración de tema (colores y tipografías) guardada por negocio.
- Imágenes en Cloudinary, con la URL almacenada en PostgreSQL.


## Arquitectura

```
Cliente (celular)                    Administrador
     │ escanea QR                         │
     ▼                                    ▼
Frontend React + Vite (Vercel)  ──►  API REST Flask (Railway)
                                          │
                                ┌─────────┴─────────┐
                                ▼                   ▼
                          PostgreSQL           Cloudinary
```

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React, Vite, React Router |
| Backend | Flask, SQLAlchemy |
| Base de datos | PostgreSQL |
| Autenticación | JWT |
| Multimedia | Cloudinary |
| Despliegue | Vercel (frontend), Railway (backend) |

## Estructura del proyecto

```
qr-menu/
├── backend/        # API REST en Flask
│   ├── app/
│   │   ├── models/
│   │   ├── services/
│   │   └── routes/
│   └── migrations/
├── frontend/       # Aplicación React + Vite
│   └── src/
│       ├── pages/
│       └── components/
└── docs/           # Capturas y diagrama ER
```

## Instalación local

**Requisitos:** Python 3.10+, Node 18+ y PostgreSQL.

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
flask db upgrade
flask run
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```


## Autor

**Jorge Alejandro Mora**
