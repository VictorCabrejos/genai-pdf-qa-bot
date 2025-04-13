# Guía de GitFlow para la Asignación SOLID

## Introducción

Esta guía explica cómo trabajar con GitFlow para la entrega de la asignación sobre principios SOLID. El uso de GitFlow y GitHub nos permitirá:

1. Trabajar colaborativamente como equipo
2. Mantener un historial de cambios
3. Revisar el trabajo de cada miembro
4. Facilitar la evaluación de contribuciones individuales

## Requisitos Previos - Instalación y Configuración

### 1. Instalar Git

Antes de comenzar, necesitas tener Git instalado en tu computadora:

1. **Descargar Git**:
   - Windows: [https://git-scm.com/download/win](https://git-scm.com/download/win)
   - MacOS: [https://git-scm.com/download/mac](https://git-scm.com/download/mac)
   - Linux: `sudo apt-get install git` (Ubuntu/Debian) o `sudo yum install git` (Fedora)

2. **Instalar Git**:
   - Ejecuta el instalador descargado
   - Puedes dejar las opciones por defecto durante la instalación
   - En Windows, se recomienda seleccionar "Git Bash" durante la instalación

3. **Configurar Git**:
   Abre una terminal (o Git Bash en Windows) y ejecuta:
   ```bash
   git config --global user.name "Tu Nombre"
   git config --global user.email "tu.email@ejemplo.com"
   ```
   Usa el mismo email que usas en GitHub.

### 2. Crear una cuenta de GitHub

Si aún no tienes una cuenta de GitHub:
1. Ve a [https://github.com/signup](https://github.com/signup)
2. Completa el formulario de registro
3. Verifica tu dirección de correo electrónico

## ¿Qué es GitFlow?

GitFlow es un modelo de flujo de trabajo para Git que define un conjunto de reglas para crear y gestionar ramas. Está diseñado para proyectos que tienen ciclos de lanzamiento planificados. Las principales ramas en GitFlow son:

- **main**: Contiene el código en producción
- **develop**: Rama principal de desarrollo donde se integran las features
- **feature/xxx**: Ramas temporales donde se desarrollan nuevas funcionalidades
- **release/xxx**: Ramas de preparación para un lanzamiento
- **hotfix/xxx**: Ramas para correcciones urgentes

![Diagrama GitFlow](https://wac-cdn.atlassian.com/dam/jcr:a9cea7b7-23c3-41a7-a4e0-affa053d9ea7/04%20(1).svg?cdnVersion=1196)

## Pasos para la asignación

### 1. Configuración inicial (una vez por equipo)

#### 1.1 Crear un repositorio de equipo
1. Un miembro del equipo crea un nuevo repositorio en GitHub:
   - Inicia sesión en GitHub
   - Haz clic en el botón "+" en la esquina superior derecha
   - Selecciona "New repository"
   - Nombra el repositorio (por ejemplo, "solid-principles-assignment-grupo1")
   - Marca la opción "Initialize this repository with a README"
   - Haz clic en "Create repository"

2. Añade a los demás miembros como colaboradores:
   - En GitHub, ve a tu repositorio
   - Haz clic en "Settings" (pestaña)
   - En el menú lateral, haz clic en "Collaborators"
   - Haz clic en "Add people"
   - Busca a tus compañeros por su nombre de usuario o email de GitHub
   - Selecciona a cada uno y haz clic en "Add [nombre] to this repository"
   - Tus compañeros recibirán un email de invitación que deben aceptar

#### 1.2 Hacer fork del repositorio base
1. Ve al repositorio base del profesor
2. Haz clic en el botón "Fork" en la esquina superior derecha
3. Selecciona tu cuenta como destino del fork

#### 1.3 Clonar el fork y configurar el repositorio
```bash
# Clonar el repositorio fork
git clone https://github.com/[tu-usuario]/[nombre-repositorio].git
cd [nombre-repositorio]

# Añadir el repositorio original como remoto "upstream"
git remote add upstream https://github.com/[usuario-profesor]/[nombre-repositorio].git

# Crear la rama develop
git checkout -b develop
git push -u origin develop
```

### 2. Flujo de trabajo individual (para cada miembro)

#### 2.1 Actualizar tu copia local
```bash
# Asegúrate de estar en la rama develop
git checkout develop

# Actualiza tu copia local
git pull origin develop
```

#### 2.2 Crear una rama de feature para tu parte del trabajo
```bash
# Crear una rama para tu funcionalidad
# Usa un nombre descriptivo: feature/[tu-nombre]/[descripcion-feature]
git checkout -b feature/maria/extractor-service
```

#### 2.3 Trabajar en tu rama de feature
1. Realiza los cambios necesarios según la asignación
2. Haz commits regulares con mensajes descriptivos:
```bash
git add [archivos-modificados]
git commit -m "Implementa la clase PDFExtractor siguiendo SRP"
```

#### 2.4 Subir tu rama de feature
```bash
# Sube tu rama al repositorio del equipo
git push -u origin feature/maria/extractor-service
```

#### 2.5 Crear Pull Request a la rama develop del equipo
1. Ve a GitHub, a la página del repositorio del equipo
2. GitHub sugerirá crear un Pull Request de tu nueva rama
3. Crea el Pull Request hacia la rama `develop`
4. Pide a otro miembro del equipo que revise tu código
5. Una vez aprobado, haz merge (o pide a otro miembro que lo haga)

### 3. Integración y entrega final (como equipo)

#### 3.1 Crear una rama release cuando todo esté listo
```bash
# Desde develop, crear una rama release
git checkout develop
git checkout -b release/v1.0.0
```

#### 3.2 Pruebas y ajustes finales
Realiza cualquier ajuste final y asegúrate de que todo funcione correctamente.

```bash
# Commit de ajustes finales si son necesarios
git add [archivos-modificados]
git commit -m "Ajustes finales para release v1.0.0"
git push -u origin release/v1.0.0
```

#### 3.3 Merge a main y etiquetado
```bash
# Fusionar la rama release con main
git checkout main
git merge --no-ff release/v1.0.0
git tag -a v1.0.0 -m "Versión 1.0.0"
git push origin main --tags

# También actualiza develop
git checkout develop
git merge --no-ff release/v1.0.0
git push origin develop
```

#### 3.4 Pull Request final al repositorio del profesor
1. Ve al repositorio fork en GitHub
2. Cambia a la rama `main`
3. Haz clic en "Contribute" y luego "Open Pull Request"
4. Asegúrate de que el PR va hacia el repositorio del profesor
5. Describe brevemente los cambios implementados y los miembros del equipo
6. Envía el Pull Request

### 4. Preparación del archivo ZIP para el aula virtual

Además del Pull Request en GitHub, prepara un archivo ZIP con tu solución para subir al aula virtual:

1. Clona tu repositorio en una carpeta limpia
2. Elimina la carpeta `.git` (y cualquier otro archivo innecesario)
3. Crea un archivo ZIP con la estructura del proyecto
4. Sube el archivo al aula virtual

## Ejemplos específicos para la asignación SOLID

Para que tengas claro cómo aplicar GitFlow a esta asignación específica, aquí hay ejemplos concretos basados en los escenarios de la tarea:

### Escenario 1: Refactorización del Procesador de PDF

Para este escenario de la tarea podrías dividir las tareas así:

#### Identificación de Features (Funcionalidades)

1. **Feature: Implementar PDFExtractor**
   - Rama: `feature/tu-nombre/pdf-extractor`
   - Archivos a crear/modificar:
     - `app/services/pdf/extractor.py` (nuevo)
   - Descripción: Implementa la clase PDFExtractor siguiendo el Principio de Responsabilidad Única

2. **Feature: Implementar TextChunker**
   - Rama: `feature/tu-nombre/text-chunker`
   - Archivos a crear/modificar:
     - `app/services/pdf/chunker.py` (nuevo)
   - Descripción: Implementa la clase TextChunker siguiendo el SRP

3. **Feature: Refactorizar PDF Routes**
   - Rama: `feature/tu-nombre/refactor-pdf-routes`
   - Archivos a crear/modificar:
     - `app/routes/pdf_routes.py` (modificación)
   - Descripción: Refactoriza las rutas de PDF para utilizar las nuevas clases

4. **Feature: Documentación y Tests**
   - Rama: `feature/tu-nombre/pdf-docs-and-tests`
   - Archivos a crear/modificar:
     - `informe-escenario1.md` (nuevo)
     - `tests/services/pdf/test_extractor.py` (nuevo, opcional)
     - `tests/services/pdf/test_chunker.py` (nuevo, opcional)
   - Descripción: Documenta la solución y explica qué principios SOLID se estaban violando

#### Ejemplos de Commits

```
git commit -m "Crea clase PDFExtractor con método extract_text para SRP"
git commit -m "Implementa manejo de documentos PDF con fitz en PDFExtractor"
git commit -m "Crea clase TextChunker con método chunk_text siguiendo SRP"
git commit -m "Refactoriza pdf_routes.py para usar PDFExtractor y TextChunker"
git commit -m "Añade documentación explicando violaciones de SRP encontradas"
```

### Escenario 2: Refactorización del Sistema de Autenticación

Para este escenario de la tarea podrías dividir las tareas así:

#### Identificación de Features (Funcionalidades)

1. **Feature: Crear AuthService**
   - Rama: `feature/tu-nombre/auth-service`
   - Archivos a crear/modificar:
     - `app/auth/services/auth_service.py` (nuevo)
   - Descripción: Implementa la clase AuthService para manejar la autenticación común

2. **Feature: Refactorizar Auth Routes**
   - Rama: `feature/tu-nombre/refactor-auth-routes`
   - Archivos a crear/modificar:
     - `app/auth/routes.py` (modificación)
   - Descripción: Refactoriza las rutas de autenticación para eliminar duplicación

3. **Feature: Documentación y Análisis**
   - Rama: `feature/tu-nombre/auth-docs`
   - Archivos a crear/modificar:
     - `informe-escenario2.md` (nuevo)
   - Descripción: Documenta la solución y explica cómo se aplicó el principio SRP

#### Ejemplos de Commits

```
git commit -m "Crea clase AuthService con método get_user_token"
git commit -m "Implementa validación de credenciales en AuthService"
git commit -m "Refactoriza login_for_access_token para usar AuthService"
git commit -m "Refactoriza login_json para usar AuthService y eliminar duplicación"
git commit -m "Añade documentación explicando la aplicación de SRP"
```

### Ejemplo de División de Trabajo en un Grupo de 4 (Escenario 1)

Si a tu grupo le corresponde el Escenario 1, podrían organizarse de la siguiente manera:

**Miembro 1:**
- Implementa PDFExtractor
- Participa en la documentación

**Miembro 2:**
- Implementa TextChunker
- Participa en la documentación

**Miembro 3:**
- Refactoriza las rutas de PDF
- Escribe tests para PDFExtractor

**Miembro 4:**
- Escribe tests para TextChunker
- Coordina la integración y finaliza el informe

### Ejemplo de División de Trabajo en un Grupo de 4 (Escenario 2)

Si a tu grupo le corresponde el Escenario 2, podrían organizarse de la siguiente manera:

**Miembro 1:**
- Implementa AuthService
- Participa en la documentación

**Miembro 2:**
- Refactoriza login_for_access_token
- Escribe tests para AuthService

**Miembro 3:**
- Refactoriza login_json
- Verifica integración con el sistema existente

**Miembro 4:**
- Implementa manejo de errores en AuthService
- Coordina la documentación y el informe final

## Verificación de contribuciones

El profesor podrá verificar las contribuciones individuales a través de:

- **Historial de commits**: Muestra quién hizo cada cambio.
- **Pull Requests**: Muestra quién propuso y revisó los cambios.
- **Insights > Contributors**: Muestra estadísticas de contribución por miembro.
- **Network graph**: Visualiza el flujo de trabajo y las ramas.

## Consejos adicionales

- **Commits regulares**: Haz commits pequeños y frecuentes que representen cambios lógicos.
- **Mensajes descriptivos**: Escribe mensajes de commit claros que expliquen el "qué" y el "por qué".
- **Revisa antes de subir**: Verifica tus cambios antes de subirlos (`git diff`).
- **Comunícate con tu equipo**: Coordinen qué hará cada uno para evitar conflictos.
- **Resuelve conflictos localmente**: Si hay conflictos, resuélvelos en tu máquina antes de hacer push.

## Preguntas frecuentes

**¿Qué hago si hay conflictos al hacer merge?**
1. Actualiza tu rama con la última versión de develop:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout feature/tu-feature
   git merge develop
   ```
2. Resuelve los conflictos manualmente
3. Completa el merge:
   ```bash
   git add [archivos-resueltos]
   git commit
   ```

**¿Cómo puedo ver qué cambios he hecho?**
```bash
# Ver cambios sin añadir al staging
git diff

# Ver cambios añadidos al staging
git diff --staged
```

**¿Cómo puedo deshacer cambios?**
```bash
# Deshacer cambios en un archivo
git checkout -- [archivo]

# Deshacer último commit (manteniendo los cambios)
git reset --soft HEAD~1

# Deshacer último commit (descartando los cambios)
git reset --hard HEAD~1
```

**¿Qué hago si olvidé hacer una rama antes de modificar archivos?**
```bash
# Guarda los cambios sin commit
git stash

# Crea y cambia a la nueva rama
git checkout -b feature/tu-nombre/tu-feature

# Aplica los cambios guardados a esta rama
git stash pop
```

**¿Cómo sé en qué rama estoy trabajando?**
```bash
git branch
```
La rama actual estará marcada con un asterisco (*).

**¿Cómo cambio de rama?**
```bash
git checkout nombre-de-la-rama
```

**¿Qué hago si cometí un error en mi último commit?**
```bash
# Modifica el último commit (si aún no has hecho push)
git commit --amend
```