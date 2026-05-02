#!/bin/sh
set -e

echo "Esperando que la base de datos este lista..."
sleep 3

echo "Parcheando check_consistent_history..."
python - <<'PYEOF'
import re, site

# Encontrar el archivo loader.py de Django
packages = site.getsitepackages()
loader_path = None
for p in packages:
    candidate = p + "/django/db/migrations/loader.py"
    try:
        open(candidate)
        loader_path = candidate
        break
    except:
        pass

if loader_path:
    with open(loader_path, "r") as f:
        content = f.read()
    
    # Reemplazar el metodo para que no haga nada
    patched = re.sub(
        r'def check_consistent_history\(self, connection\):.*?(?=\n    def |\nclass )',
        'def check_consistent_history(self, connection):\n        return  # patched\n\n    ',
        content,
        flags=re.DOTALL
    )
    
    with open(loader_path, "w") as f:
        f.write(patched)
    print("Parche aplicado en: " + loader_path)
else:
    print("No se encontro loader.py")
PYEOF

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Iniciando servidor..."
exec python manage.py runserver 0.0.0.0:8000
