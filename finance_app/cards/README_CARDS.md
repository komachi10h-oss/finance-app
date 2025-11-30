# Cards App Patch v1

## Descripción
Este módulo agrega una app `cards` que se conecta automáticamente al sandbox de Belvo
y muestra movimientos individuales con gráfico de barras.

## Instalación
1. Copia la carpeta `cards/` dentro de tu proyecto Django.
2. Agrega `'cards'` y `'rest_framework'` a `INSTALLED_APPS`.
3. Configura tu `.env` con credenciales de Belvo.
4. Ejecuta:
   ```bash
   python manage.py makemigrations cards
   python manage.py migrate
   ```
5. Añade la ruta en `urls.py` principal:
   ```python
   path('cards/', include('cards.urls')),
   ```
6. Inicia el servidor y visita `/cards/`.

