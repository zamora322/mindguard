# MindGuard

MindGuard es un asistente basado en Inteligencia Artificial que se integra con el ecosistema de Google Workspace (Gmail, Google Calendar, Google Meet) para optimizar la gestión del tiempo de profesionales con alta carga laboral. El sistema analiza de forma asíncrona la información entrante, evalúa la relevancia de los compromisos y ofrece una interfaz centralizada donde el usuario puede visualizar su agenda depurada, recibir resúmenes contextuales y entender por qué ciertas tareas o reuniones han sido priorizadas o marcadas como prescindibles. 
Este repositorio contiene tanto el frontend construido con **Next.js** (utilizando el patrón de diseño atómico, CSS Modules y **Lucide React** para la iconografía) como el backend construido con **FastAPI**.

---

## Inicialización del Frontend (Next.js)

El frontend requiere **Node.js >= 20.9.0** debido a las especificaciones de Next.js.

Sigue estos pasos para levantarlo:

1. **Navega a la carpeta del frontend:**
   ```bash
   cd frontend
   ```

2. **(Opcional) Selecciona la versión correcta de Node con NVM:**
   ```bash
   nvm use 22
   ```

3. **Instala las dependencias (si no se han instalado):**
   ```bash
   npm install
   ```

4. **Inicia el servidor de desarrollo:**
   ```bash
   npm run dev
   ```

5. **Borrar caché de Next.js**
   
   **Sintaxis:** `rm -rf .next/* && npm run dev`
   **Uso:** Útil si notas que la aplicación no refleja los últimos cambios en el código. Borra la caché de compilación y desarrollo de Next.js.  
   **Nota:** Esta operación es segura y solo eliminará archivos temporales de compilación. Tu código y dependencias no se verán afectados.

*El frontend se ejecutará por defecto en: [http://localhost:3000](http://localhost:3000)*

---

## Inicialización del Backend (FastAPI)

El backend corre en un entorno virtual aislado con Python y FastAPI.

Pasos para levantarlo:

1. **Navega a la carpeta del backend:**
   ```bash
   cd backend
   ```

2. **Crea el entorno virtual (si no existe):**
   ```bash
   python -m venv .venv
   ```

3. **Activa el entorno virtual:**
   * En macOS / Linux:
     ```bash
     source .venv/bin/activate
     ```
   * En Windows:
     ```bash
     .venv\Scripts\activate
     ```

4. **Instala las dependencias requeridas:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Inicia el servidor de desarrollo de Uvicorn con recarga automática (hot reload):**
   ```bash
   uvicorn app.main:app --reload
   ```

*El backend se ejecutará en: [http://127.0.0.1:8000](http://127.0.0.1:8000)*
*La documentación interactiva de la API (Swagger UI) estará disponible en: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*

---

## Inicialización con Docker (Recomendado)

Si prefieres levantar todo el proyecto de forma unificada utilizando contenedores de Docker (sin necesidad de configurar entornos virtuales locales de Node/Python), puedes hacerlo con **Docker Compose**.

### Requisitos Previos:
- Tener instalado **Docker** y **Docker Compose**.
- Tener creados los archivos de variables de entorno `.env` en `backend/` y `.env` en `frontend/` (con tu `GOOGLE_CLIENT_ID` y demás variables).

### Pasos para iniciar la aplicación:

1. **Construir e iniciar los contenedores en segundo plano:**
   ```bash
   docker compose up --build -d
   ```

2. **Verificar el estado de los contenedores:**
   ```bash
   docker compose ps
   ```

3. **Ver los logs en tiempo real (opcional):**
   ```bash
   docker compose logs -f
   ```

4. **Detener los servicios:**
   ```bash
   docker compose down
   ```

### Reconstrucción de Contenedores

Si realizas cambios en el código o en las variables de entorno y necesitas volver a generar las imágenes de Docker:

* **Reconstruir y levantar todos los servicios a la vez:**
  ```bash
  docker compose up --build -d
  ```

* **Reconstruir un solo servicio (sin detener ni afectar los demás contenedores que estén corriendo):**
  ```bash
  # Reconstruir solo el frontend
  docker compose up --build -d frontend

  # Reconstruir solo el backend
  docker compose up --build -d backend

  # Reconstruir solo la base de datos
  docker compose up --build -d db
  ```

* **Eliminar la base de datos y volver a crearla:**
  ```bash
  docker compose down -v
  docker compose up --build -d db
  ```

*Una vez iniciados los contenedores, puedes acceder al frontend en [http://localhost:3000](http://localhost:3000) y al backend en [http://localhost:8000](http://localhost:8000).*

---

## Principios de Diseño SOLID en Backend (FastAPI)

El sistema de autenticación de FastAPI ha sido estructurado siguiendo buenas prácticas SOLID:
- **Responsabilidad Única (SRP):** El router de autenticación (`auth.py`) delega el comportamiento externo de intercambio de tokens y llamadas al proveedor de identidad a clases de servicio específicas.
- **Inversión de Dependencias (DIP):** Las rutas de FastAPI no dependen de clases concretas, sino de la interfaz abstracta `OAuthProvider`, inyectada dinámicamente mediante el sistema de dependencias de FastAPI.
- **Abierto/Cerrado (OCP):** Si en el futuro se requiere soporte para nuevos proveedores OAuth (ej. Microsoft, Apple o GitHub), basta con implementar la interfaz `OAuthProvider` en una clase nueva, sin modificar el router HTTP principal.