# Enterprise DMS

Enterprise DMS is a Django-based platform for managing enterprise records, document files, dossiers, CSV bulk imports, workflow cases, audit notes, and configurable reports through a web application and a versioned REST API.

The project models a common business problem: many organizations still manage people, clients, suppliers, files, reminders, and compliance documents through spreadsheets, shared folders, and manual follow-ups. Enterprise DMS turns that workflow into a structured backend with normalized data, document tracking, import automation, access control, and deployment-ready configuration.

## Why this project is interesting

This repository is more than a basic CRUD application. It demonstrates several backend concerns that appear in real internal tools and enterprise systems:

- **Normalized domain modeling:** organizations, sites, people, contacts, addresses, postal catalogs, document categories, files, dossiers, process templates, cases, case steps, and audit notes.
- **Document lifecycle management:** document categories, file uploads, ownership, status, issue dates, expiration dates, and dossier grouping.
- **Geographic data support:** a reusable `ZipCode` catalog connected to addresses, including normalized settlement names and indexed search fields.
- **Workflow tracking:** reusable process templates and case steps for modeling repeatable business procedures.
- **CSV import automation:** bulk upsert logic for spreadsheets using `Model_field` headers, row-level error tracking, import logs, and encoding fallback.
- **Configurable reports:** report definitions are centralized in `reports/config.py` instead of duplicating view logic for each report.
- **Versioned REST API:** Django REST Framework endpoints with authentication, filtering, searching, ordering, metadata, and health checks.
- **User and audit foundation:** custom user model, profiles, password reset token fields, and user history tracking.
- **Dockerized deployment:** MariaDB, Django/Gunicorn, Nginx, persistent volumes, static files, media files, and environment-based settings.
- **Public-safe configuration:** secrets and private files are kept out of the repository; deployment values are documented through `.env.example`.

## Main modules

### 1. Core enterprise data model

The `data` app contains the reusable business schema.

| Model | Purpose |
|---|---|
| `Organization` | Client, company, institution, supplier, or managed business entity. |
| `Site` | Branch, location, office, plant, worksite, or organizational unit. |
| `Person` | Employee, contractor, candidate, client contact, or managed individual. |
| `Contact` | Named contact linked to an organization or site. |
| `Address` | Address attached to an organization, site, or person. |
| `ZipCode` | Postal/geographic catalog used to normalize address data. |
| `DocumentCategory` | Configurable document type, including whether it applies to an organization, site, person, or general record. |
| `DocumentFile` | Uploaded file with category, owner, status, issue date, expiration date, and metadata. |
| `Dossier` | Grouping of required or related documents. |
| `DossierItem` | Checklist item inside a dossier, optionally linked to a real document. |
| `ProcessTemplate` | Reusable workflow definition. |
| `ProcessStepTemplate` | Reusable step inside a process template, optionally requiring a document category. |
| `Case` | Active workflow instance for a person or organization. |
| `CaseStep` | Trackable step inside a case, with status, assignee, due date, and completion date. |
| `AuditNote` | Internal note attached to an organization, person, or case. |

The model includes extension points such as `metadata = JSONField(...)` in several entities, which allows customer-specific attributes to be added without polluting the core schema.

### 2. Postal and address normalization

The project includes a dedicated `ZipCode` model instead of storing address text only as free-form strings.

Relevant details:

- stores postal code, settlement type, settlement, municipality/county, region/state, city, and country;
- normalizes settlement names using `unidecode` for more reliable matching;
- indexes common search combinations such as postal code + settlement and country + region + city;
- connects with `Address` through a foreign key;
- allows `Address.save()` to fill city, region, and country from the selected postal record when those fields are missing;
- supports CSV imports that can resolve `zip_code` / `codigo_postal` and settlement names.

This is useful in business systems because address data usually arrives from spreadsheets with inconsistent spelling, accents, abbreviations, and mixed formats.

### 3. Document and dossier management

Documents are not treated as isolated uploads. They are connected to structured records and can be grouped into dossiers.

The document layer supports:

- configurable document categories;
- applicability rules for organization, site, person, or general records;
- required vs optional document categories;
- file uploads with extension validation;
- document status: pending, current, expired, rejected, archived;
- issue and expiration dates;
- dossier checklists through `DossierItem`;
- metadata for additional business-specific attributes.

Typical use cases:

- employee or contractor files;
- client and supplier documentation;
- compliance document tracking;
- onboarding checklists;
- administrative records;
- internal case files.

### 4. Workflow and case tracking

Enterprise DMS separates reusable process definitions from active case execution.

- `ProcessTemplate` defines a reusable process.
- `ProcessStepTemplate` defines ordered steps and required document categories.
- `Case` represents a real workflow instance.
- `CaseStep` tracks the status, due date, assignee, and completion of each step.

This makes the project adaptable to many processes: onboarding, supplier registration, document renewal, internal reviews, compliance follow-ups, and administrative procedures.

### 5. CSV bulk import system

The `imports` app is designed for business environments where users already manage information in spreadsheets.

The importer supports CSV headers using this pattern:

```text
Model_field
```

Example:

```text
Organization_trade_name,Organization_legal_name,Person_first_name,Person_last_name,Person_email,Address_zip_code
Acme,Acme Incorporated,Alice,Smith,alice@example.com,68000
```

Supported prefixes include:

```text
Organization, Site, Person, Contact, Address, ZipCode, DocumentCategory, Dossier, ProcessTemplate, Case, AuditNote
```

Technical details worth reviewing:

- validates file existence, extension, and empty files;
- supports multiple encodings: `utf-8-sig`, `utf-8`, and `latin-1`;
- groups CSV columns by model prefix;
- normalizes booleans and date fields;
- uses `transaction.atomic()` per row;
- applies safe `update_or_create` logic with fallback lookups;
- resolves ZIP/postal records from CSV values;
- stores row-level import status through `ImportLog` and `ImportRow`;
- preserves error details for review and retries.

### 6. Configurable report generation

The `reports` app uses a configuration-driven approach.

Generic endpoint:

```text
POST /reports/generate/
```

Report definitions live in:

```text
reports/config.py
```

Current report templates include:

- `organization_summary`
- `person_summary`
- `dossier_checklist`

Each report definition maps:

- target model;
- request field;
- lookup field;
- template path;
- output format;
- variables to extract from the object.

This design makes it easier to add new reports without creating a separate custom view for every document type.

### 7. Versioned REST API

The API is organized under:

```text
/api/v1/
```

Important endpoints include:

```text
/api/v1/health/
/api/v1/metadata/
/api/v1/auth/token/
/api/v1/auth/me/
/api/v1/organizations/
/api/v1/sites/
/api/v1/people/
/api/v1/contacts/
/api/v1/addresses/
/api/v1/zip-codes/
/api/v1/document-categories/
/api/v1/documents/
/api/v1/dossiers/
/api/v1/dossier-items/
/api/v1/process-templates/
/api/v1/process-step-templates/
/api/v1/cases/
/api/v1/case-steps/
/api/v1/audit-notes/
/api/v1/imports/jobs/
/api/v1/imports/logs/
/api/v1/imports/rows/
/api/v1/reports/authenticity/
/api/v1/users/users/
/api/v1/users/profiles/
/api/v1/users/history/
```

The API layer demonstrates:

- token authentication;
- session authentication support;
- authenticated access control;
- admin-only user management endpoint;
- search fields for key models;
- filterset fields;
- ordering support;
- dynamic metadata endpoint that exposes model fields and choices for frontend builders.

## Technical stack

- **Language:** Python
- **Backend framework:** Django
- **API framework:** Django REST Framework
- **Filtering:** django-filter
- **Database:** MariaDB / MySQL-compatible configuration
- **Web server:** Gunicorn behind Nginx
- **Deployment:** Docker Compose
- **Static/media:** separated static and media volumes
- **Data import:** pandas-based CSV importer
- **Documents:** DOCX/PDF/file handling utilities
- **Configuration:** environment variables through `.env.example`

## Architecture overview

```text
User / Browser / API Client
    |
    v
Nginx reverse proxy
    |
    v
Django + Gunicorn
    |
    +-- EnterpriseApp -> settings, URLs, WSGI/ASGI, shared config
    +-- users         -> authentication, profiles, permissions, user history
    +-- data          -> organizations, sites, people, addresses, ZIP codes, documents, dossiers, cases
    +-- imports       -> CSV upload, bulk processing, import logs, row-level errors
    +-- reports       -> report definitions, generation views, authenticity records
    +-- api/v1        -> REST API layer, serializers, permissions, metadata
    |
    v
MariaDB
```

The project uses separate database settings for application data and enterprise data, which makes it easier to isolate business records from app-level configuration when needed.

## Project structure

```text
EnterpriseApp/       Django settings, URLs, WSGI/ASGI, configuration helpers
data/                Core enterprise models, admin, forms, views, serializers
users/               Custom user model, profiles, password recovery token data, user history
imports/             CSV import models, forms, views, and importer utilities
reports/             Report definitions, report views, report tools, authenticity model
api/v1/              Versioned REST API serializers, views, permissions, URLs
static/              CSS, JavaScript, and generic image assets
templates/           Django templates for admin and application pages
Dockerfile           Production-oriented Python/Django image
docker-compose.yml   MariaDB + Django/Gunicorn + Nginx orchestration
```

## Getting started locally

```bash
cp EnterpriseApp/.env.example EnterpriseApp/.env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py migrate data --database=enterprise_data
python manage.py createsuperuser
python manage.py runserver
```

Development-only tools can be installed separately:

```bash
pip install -r requirements-dev.txt
```

## Running with Docker

```bash
docker compose build
docker compose up
```

Default local URL:

```text
http://localhost:20001
```

The Docker setup includes:

- MariaDB 11;
- Django/Gunicorn application container;
- Nginx reverse proxy;
- persistent database volume;
- static file volume;
- media file volume.

## Environment variables

Create your local environment file from the example:

```bash
cp EnterpriseApp/.env.example EnterpriseApp/.env
```

Main database variables:

```env
DB_ENGINE=django.db.backends.mysql
DB_APP_NAME=enterprise_dms_appdata
DB_DATA_NAME=enterprise_dms_database
DB_USER=enterprise_dms_user
DB_PASSWORD=replace-me
DB_HOST=db
DB_PORT=3306
```

## Security and privacy notes

This repository is intended to be safe for public review:

- real `.env` files should not be committed;
- private media files should not be committed;
- credentials are loaded from environment variables;
- development-only dependencies are separated from production dependencies;
- generated files and uploaded private files should stay outside Git;
- customer-specific business rules should live in private extension apps when needed.

## Suggested recruiter review path

A quick technical review can focus on:

1. `data/models.py` to review the normalized domain model, including ZIP/postal catalog, addresses, dossiers, documents, process templates, and cases.
2. `imports/csv_importer.py` to review the bulk import pipeline, row-level transactions, ZIP resolution, and error tracking.
3. `api/v1/views.py`, `api/v1/serializers.py`, and `api/v1/urls.py` to review the REST API layer.
4. `reports/config.py` and `reports/views.py` to review configurable report generation.
5. `users/models.py` and `users/views.py` to review authentication, profiles, password recovery support, and user history.
6. `docker-compose.yml` and `Dockerfile` to review deployment setup.
7. `EnterpriseApp/settings.py` to review environment-based configuration and app organization.

## Why this project matters

Enterprise DMS shows how manual administrative workflows can be transformed into a maintainable Django system: structured records, normalized addresses, document control, CSV automation, process tracking, user access, reporting, and API access.

It is especially relevant for roles involving Django, backend development, REST APIs, data modeling, internal tools, business automation, CSV/data pipelines, and Docker-based deployment.

## License

This project is distributed under the [MIT License](LICENSE).
