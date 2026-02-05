#!/bin/bash
# Recrear contenedores y asegurar que migraciones y código actual se apliquen.
set -e
cd "$(dirname "$0")"

echo "=== Bajando contenedores ==="
docker-compose down

echo "=== Reconstruyendo imágenes (sin caché) ==="
docker-compose build --no-cache

echo "=== Levantando servicios ==="
docker-compose up -d

echo "=== Esperando a que el backend arranque (migrate se ejecuta en el command) ==="
sleep 10

echo "=== Estado de migraciones (tracking) ==="
docker-compose exec -T backend python manage.py showmigrations tracking || true

echo ""
echo "=== Listo. URLs ==="
echo "  Frontend: http://localhost:5173"
echo "  API:      http://localhost:8000/api/"
echo ""
echo "  Si no ves el formulario ESTRUCTURAL (Pliegues, Diámetros, etc.):"
echo "  - Haz un refresco forzado en el navegador (Ctrl+Shift+R o Cmd+Shift+R)"
echo "  - O abre la app en una ventana de incógnito"
echo "  - Ruta al formulario: Cliente → Nuevo Seguimiento"
