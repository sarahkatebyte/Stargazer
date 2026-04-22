# Stargazer Glossary

A reference of terms and concepts covered while building this project.

---

## Python / Django

**ORM (Object Relational Mapper)**
A tool that lets you interact with a database using Python instead of raw SQL. Django's ORM translates Python like `CelestialBody.objects.filter(name='Orion')` into SQL like `SELECT * FROM apod_celestialbody WHERE name = 'Orion'`. Rails equivalent: Active Record.

**Model**
A Python class that represents a database table. Each attribute on the class is a column in the table. Example: `Apod`, `CelestialBody`, `Collection`.

**Migration**
A file that describes a change to the database schema — creating a table, adding a column, etc. You run `python manage.py makemigrations` to generate them and `python manage.py migrate` to apply them.

**Foreign Key**
A column in one table that references the primary key of another table. It's how relational databases link records together. Example: `Collection.apod_id` points to `Apod.id`.

**Join Table**
A table that sits between two other tables and links them together via foreign keys. Our `Collection` model is a join table linking `Apod` and `CelestialBody`. We chose an explicit model over Django's built-in `ManyToManyField` because we needed to store extra data (`collected_at`) on the relationship.

**Primary Key**
A unique identifier for each row in a table. Django automatically creates an `id` field as the primary key unless you specify otherwise.

**`get_or_create`**
A Django ORM method that either fetches an existing record or creates a new one. Prevents duplicates. Returns a tuple of `(object, created)` where `created` is a boolean.

**Management Command**
A custom command you can run with `python manage.py <name>`. We built `fetch_apod` to pull data from NASA's API and run the astronomy agent.

**Virtual Environment (venv)**
An isolated Python environment for your project. Keeps your project's dependencies separate from other Python projects on your machine. Always activate it with `source venv/bin/activate` before running Django commands.

**`__init__.py`**
An empty file that tells Python "this folder is a package" so you can import from it. Required in every folder Django needs to import from.

**Meta class**
An inner class used for configuration in Django models and DRF serializers. It holds settings *about* the class rather than logic that runs. Example: `model = Apod` and `fields = '__all__'` inside a serializer's `Meta`.

**`icontains`**
A Django ORM filter that performs a case-insensitive search. `filter(name__icontains='milky way')` matches "Milky Way", "milky way", "MILKY WAY".

---

## Django REST Framework (DRF)

**DRF (Django REST Framework)**
A library built on top of Django that makes it easy to build REST APIs. Provides serializers, generic views, and a browsable API UI.

**Serializer**
Converts between Python objects and JSON. Outgoing: Django model instance → JSON. Incoming: JSON → validated Python object. `ModelSerializer` auto-generates fields from a model.

**`fields = '__all__'`**
Tells a DRF serializer to include every field from the model in the JSON output. Alternative is listing fields manually: `fields = ['id', 'name']`.

**Generic Views**
Pre-built DRF view classes that handle common API patterns so you don't write boilerplate. `ListAPIView` returns a list, `RetrieveAPIView` returns a single object by ID or other lookup field.

**`as_view()`**
Converts a class-based view into a callable that Django's URL router can use.

**Browsable API**
A built-in DRF UI that lets you interact with your API in the browser. The "API" tab shows the human-friendly version, "JSON" shows the raw data your frontend receives.

---

## REST APIs

**REST (Representational State Transfer)**
A standard for building web APIs. Uses HTTP methods (GET, POST, PUT, DELETE) to perform operations on resources.

**Endpoint**
A URL that your API exposes. Example: `GET /api/apods/` returns all APODs, `GET /api/apods/2026-04-20/` returns one.

**HTTP Methods**
- `GET` — read data
- `POST` — create data
- `PUT/PATCH` — update data
- `DELETE` — delete data

**JSON (JavaScript Object Notation)**
The format APIs use to send data. A serializer converts your Python objects into JSON and back.

---

## Databases

**PostgreSQL (Postgres)**
A relational database. Stores data in tables with rows and columns. Django talks to it via the ORM.

**SQL (Structured Query Language)**
The language relational databases understand. Django's ORM writes SQL for you so you rarely need to write it directly.

**Query**
A request to the database for data. `CelestialBody.objects.all()` is a query that returns all rows in the `apod_celestialbody` table.

**QuerySet**
Django's representation of a database query that hasn't necessarily been executed yet. It's lazy — the actual SQL doesn't run until you iterate over it, call `.values()`, or use it in a template. You can chain multiple filters and ordering onto a QuerySet and Django builds one efficient SQL query. Rails equivalent: `Model.all` or `Model.where(...)`.

---

## Data Structures

**List (Array)**
An ordered collection of items. In Python: `[1, 2, 3]`. In our agent, `messages` is a list we keep appending to as the conversation grows.

**Dictionary (Hash Map)**
A collection of key-value pairs. O(1) lookup time. In Python: `{"name": "Orion", "type": "nebula"}`. Used in our `lookup_coordinates` function.

**Append-only History Buffer**
What our `messages` list actually is — we only ever add to it, never remove. The full history is sent to the API on every request so Claude has context.

**O(1) vs O(n)**
Big O notation describes how performance scales with input size.
- O(1) — constant time, doesn't matter how big the input is (dictionary lookup)
- O(n) — linear time, gets slower as input grows (if/elif chain)

---

## AI / Agents

**Agentic Loop**
A loop where Claude calls a tool, gets the result, and decides what to do next — repeating until the task is done or a max turns limit is hit.

**Tool Use**
A way of giving Claude functions it can call. You define the tool name, description, and input schema. Claude decides when and how to call it.

**System Prompt**
Instructions you give Claude before the conversation starts. Defines its role and behaviour. We cache ours to reduce API costs.

**Prompt Caching**
Stores the system prompt so it doesn't need to be re-processed on every loop iteration. Reduces cost by ~90% for the cached portion.

**Max Turns**
A safety limit on how many times the agentic loop can run. Prevents runaway loops and controls cost.

**`stop_reason`**
Why Claude stopped generating. `end_turn` means it finished naturally. `tool_use` means it wants to call a tool and is waiting for results.

---

## TypeScript / React

**TypeScript**
JavaScript with types. Lets you define the shape of data so errors get caught before the code runs in the browser.

**Type**
A TypeScript definition of the shape of an object. Example: `type Apod = { date: string, title: string }`. The browser never sees this — it gets stripped out at compile time.

**JSX**
Looks like HTML but is actually JavaScript/TypeScript. React lets you write UI structure directly in your component files.

**Component**
A reusable chunk of UI. A function that returns JSX. Example: `App`, `ApodCard`.

**State**
Data a component owns and controls. When it changes, the component re-renders. Managed with `useState`.

**Props**
Data passed down from a parent component to a child. Read-only from the child's perspective. State in a parent becomes props in a child.

**`useState`**
A React hook that gives a component memory. Returns `[value, setter]`. When you call the setter, React re-renders the component with the new value.

**`useEffect`**
A React hook that runs code at a specific moment in the component lifecycle. `useEffect(() => { ... }, [])` runs once when the component mounts.

**Mounting**
When a component appears on screen for the first time. React creates the DOM elements and inserts them into the page.

**DOM (Document Object Model)**
The browser's representation of your HTML as a tree of objects that JavaScript can read and modify. React writes to the DOM when it renders components.

**Vite**
A build tool for frontend projects. In development it runs a local server with hot reload. For production it compiles and bundles your code into static files Django can serve.

**Proxy**
In our Vite config, a proxy forwards `/api` requests from the frontend dev server (port 5173) to Django (port 8000). This lets both run simultaneously in development.

---

## General

**Race Condition**
When two processes compete for the same resource at the same time and the outcome depends on timing. Example: two users buying the last concert ticket simultaneously.

**Boilerplate**
Generic starter code that gets generated automatically. Usually needs to be replaced with your actual code.

**`.env` file**
A file that stores environment variables like API keys. Never committed to git. Loaded by `python-dotenv` in Django.

**`.gitignore`**
Tells git which files not to track. We added `venv/`, `.env`, and `__pycache__/` so they never get committed.

---

## Astronomy / Coordinate System

**Right Ascension (RA)**
The celestial equivalent of longitude. Measures how far east a body is along the celestial equator, in hours (0h–24h). Example: `05h 35m 17s` for the Orion Nebula.

**Declination (Dec)**
The celestial equivalent of latitude. Measures how far north or south a body is from the celestial equator, in degrees (−90° to +90°). Example: `−05° 23' 28"` for the Orion Nebula.

**Celestial Sphere**
An imaginary sphere around the Earth where every star and deep-sky object has a fixed position described by RA and Dec. Think of it like a globe but for the sky.

---

## Debugging

**Type Mismatch**
When your code assumes a variable has one shape but the actual data has a different shape. In our case, the TypeScript type said `apod_id` and `celestial_body_id` but the API returned `apod` and `celestial_body` — so every lookup silently returned `undefined`.

**`console.log`**
A JavaScript debugging tool that prints values to the browser's DevTools console. Useful for inspecting state mid-render. Always remove before shipping — you never want logs visible in production.

**Silent Failure**
When code doesn't throw an error but also doesn't do what you expect. Our image lookup was a silent failure — no crash, just no image. Caused by reading a field name that didn't exist (`undefined` instead of a number).

---

## Management Commands

**`add_arguments`**
A Django management command method that lets you define CLI arguments. `nargs='?'` means the argument is optional — the command works with or without it. Example: `python manage.py fetch_apod 2026-04-19`.
