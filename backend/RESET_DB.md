# Database Reset Script

Este script permite resetear completamente la base de datos, eliminando todos los datos y recreando las tablas desde cero.

## ⚠️ ADVERTENCIA

**Este script eliminará TODOS los datos de la base de datos. Esta acción NO se puede deshacer.**

## Uso

### Opción 1: Script Bash (Recomendado)

```bash
cd backend
./reset_db.sh
```

**Con datos de demostración:**
```bash
./reset_db.sh --create-demo-data
```

**Solo limpiar datos (mantener estructura):**
```bash
./reset_db.sh --flush-only
```

### Opción 2: Comando Django directamente

```bash
cd backend
source venv/bin/activate
python manage.py reset_database
```

**Opciones disponibles:**

- `--no-input`: Omitir confirmación (útil para scripts automatizados)
- `--create-demo-data`: Crear datos de demostración después del reset
- `--flush-only`: Usar `flush` en lugar de eliminar tablas (más seguro, mantiene la estructura)

**Ejemplos:**

```bash
# Reset completo con confirmación
python manage.py reset_database

# Reset sin confirmación
python manage.py reset_database --no-input

# Reset y crear datos de demo
python manage.py reset_database --create-demo-data

# Solo limpiar datos (no eliminar tablas)
python manage.py reset_database --flush-only
```

## Qué hace el script

1. **Elimina todas las tablas** (o hace flush si usas `--flush-only`)
2. **Ejecuta todas las migraciones** para recrear la estructura
3. **Opcionalmente crea datos de demostración** si usas `--create-demo-data`

## Soporte de Bases de Datos

El script soporta:
- ✅ PostgreSQL
- ✅ SQLite
- ✅ MySQL/MariaDB

## Solución de Problemas

Si encuentras errores:

1. **Verifica que estás en el directorio correcto:**
   ```bash
   cd backend
   ```

2. **Asegúrate de que el virtual environment está activado:**
   ```bash
   source venv/bin/activate
   ```

3. **Verifica la conexión a la base de datos** en `settings.py`

4. **Si hay problemas con permisos**, asegúrate de que el usuario de la base de datos tiene permisos para eliminar tablas

## Notas

- El script pide confirmación antes de ejecutarse (a menos que uses `--no-input`)
- Los datos de demostración se crean usando el comando `create_demo_users` si está disponible
- El modo `--flush-only` es más seguro pero puede dejar algunas secuencias o índices inconsistentes
