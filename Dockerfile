# ─INSTRUCCION 1: imagen base 
FROM python:3.11-slim

# 'slim' = imagen minima sin herramientas extra (mas liviana)
# ── INSTRUCCION 2: variables de entorno 
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1 

# ── INSTRUCCION 3: directorio de trabajo 
WORKDIR /app

# Todos los comandos siguientes se ejecutan desde /app

# ── INSTRUCCION 4: instalar dependencias 
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
# Copiamos solo requirements.txt primero para aprovechar el cache
# de capas. Si el codigo cambia pero no las deps, Docker no
# reinstala todo -> builds mucho mas rapidos.
# ── INSTRUCCION 5: copiar el codigo f─
COPY . .
# ── INSTRUCCION 6: exponer puerto ───────────────────────────────────
EXPOSE 8000
# Documentacion: el contenedor escucha en el puerto 8000.
# No lo publica automaticamente; eso lo hace -p en docker run.
# ── INSTRUCCION 7: comando de inicio ────────────────────────────────
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


