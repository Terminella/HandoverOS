# HandoverOS – Data Engineering

## Overview

The Data Engineering module of HandoverOS is responsible for collecting, extracting, normalizing, validating, and preparing project-related information for downstream intelligence processing.

It provides a structured ingestion layer that transforms unstructured documents and repository information into standardized source records that can be consumed by the Intelligence Engine.

## Responsibilities

The Data Engineering module focuses on:

- Document ingestion and text extraction.
- Repository data ingestion through connectors.
- Source record creation and metadata preservation.
- Text normalization and data validation.
- Content hashing for source identification.
- Preparing structured records for intelligence processing.

## Architecture

The Data Engineering workflow follows these stages:

```text
Input Sources
     |
     v
Connectors
     |
     v
Document Extraction
     |
     v
Text Normalization
     |
     v
Data Validation
     |
     v
Source Records
     |
     v
Intelligence Engine
```

## 1. Document Ingestion

The document extraction component supports multiple file formats:

| Format | Description |
|---|---|
| PDF | Extracts text from PDF documents |
| DOCX | Extracts text from Word documents |
| TXT | Reads plain-text files |
| CSV | Extracts structured tabular information |

The extractor identifies the file type, extracts its content, and returns structured extraction results containing:

- Source filename
- Extracted content
- File type
- Character count

CSV extraction also handles headers, rows, missing values, duplicate headers, and inconsistent row structures.

## 2. Document Connector

The `DocumentConnector` connects document extraction with the Data Engineering ingestion workflow.

**File:** `connectors/document_connector.py`

Key responsibilities:

- Accepts project identifiers and document paths.
- Processes multiple documents in a single operation.
- Uses the DocumentExtractor to extract content.
- Generates SHA-256 content hashes.
- Creates standardized SourceRecord objects.
- Preserves document metadata.

This allows documents to enter the same structured ingestion workflow as other project sources.

## 3. Source Record Schema

**File:** `schemas/source_schema.py`

The SourceRecord schema provides a standardized representation of ingested information.

Important fields include:

| Field | Purpose |
|---|---|
| project_id | Identifies the associated project |
| source_type | Identifies the source category |
| source_name | Name of the source |
| source_id | Unique source identifier |
| title | Source title |
| content | Extracted or collected content |
| author | Source author, when available |
| created_at | Original creation timestamp |
| updated_at | Last modification timestamp |
| source_url | Original source location |
| ingested_at | Ingestion timestamp |
| content_hash | SHA-256 content hash |
| metadata | Additional source information |

The schema uses Pydantic validation to maintain structured and consistent source records.

## 4. Text Normalization

**File:** `preprocessing/normalizer.py`

The TextNormalizer prepares extracted content for further processing.

Its operations include:

- Unicode normalization using NFKC.
- Standardization of line endings.
- Removal of unnecessary leading and trailing whitespace.
- Reduction of excessive blank lines.
- Removal of repeated spaces and tabs.

The objective is to reduce formatting inconsistencies before data validation and intelligence processing.

## 5. Data Validation

**File:** `preprocessing/validator.py`

The validation component checks incoming records against the SourceRecord schema.

It helps ensure that:

- Required fields are present.
- Source types follow supported categories.
- Field types are valid.
- Unexpected fields are rejected.
- Records follow the expected structure.

Invalid records are prevented from proceeding through the validated ingestion workflow.

## 6. Ingestion Pipeline

**File:** `ingestion_pipeline.py`

The ingestion pipeline coordinates the Data Engineering workflow.

It combines:

1. Source connectors.
2. Document extraction.
3. Text normalization.
4. Schema validation.
5. Standardized source record generation.

The pipeline supports both default synthetic repository ingestion and custom connectors.

## 7. Integration with the Intelligence Engine

The Data Engineering module provides standardized source records to the Intelligence Engine.

The Intelligence Engine can then use these records for:

- Knowledge extraction.
- Evidence verification.
- Contradiction detection.
- Project knowledge reconstruction.
- Handover generation.

This separation allows data collection and preparation to remain independent of downstream intelligence processing.

## 8. Testing

The Data Engineering module includes tests for individual components and ingestion workflows.

Run the tests from the backend directory:

```bash
python -m pytest data_engineering/tests/ -v
```

Run document connector tests:

```bash
python -m pytest data_engineering/tests/test_document_connector.py -v
```

Run the Intelligence Engine tests:

```bash
python -m pytest intelligence/tests/ -v
```

## Module Structure

```text
data_engineering/
│
├── connectors/
│   ├── base_connector.py
│   ├── synthetic_repository_loader.py
│   └── document_connector.py
│
├── extractors/
│   └── document_extractor.py
│
├── generators/
│   └── repository_generator.py
│
├── preprocessing/
│   ├── normalizer.py
│   └── validator.py
│
├── schemas/
│   └── source_schema.py
│
├── services/
│   └── storage_service.py
│
├── storage/
│
├── tests/
│
└── ingestion_pipeline.py
```

## Contribution

**Module:** Data Engineering  
**Project:** HandoverOS – Knowledge Continuity and Project Handover Platform

The Data Engineering module establishes the data ingestion and preparation foundation required for reliable project knowledge reconstruction.