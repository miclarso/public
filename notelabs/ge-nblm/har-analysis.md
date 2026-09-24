# HAR Trace Analysis: NotebookLM Enterprise Codelab Session

This document provides a comprehensive, decoded analysis of the network traffic captured in the HAR traces for your NotebookLM Enterprise session. It maps out how the frontend connects to the Google Cloud backend, manages sources, and processes LLM generations.

*   **Session 1 (Notebook Creation & Web Source):** [ge_notebooklm_01.har](ge_notebooklm_01.har)
*   **Session 2 (Pasted Plain Text Document Source):** [ge_notebooklm_02.har](ge_notebooklm_02.har)
*   **Session 3 (Local PDF File Upload Source):** [ge_notebooklm_03.har](ge_notebooklm_03.har)
*   **Session 4 (Grounded Chat Q&A Query):** [ge_notebooklm_04.har](ge_notebooklm_04.har)
*   **Session 5 (Google Docs/Slides Datasource Addition):** [ge_notebooklm_05.har](ge_notebooklm_05.har)

---

## Overview of Architecture & Endpoints

NotebookLM Enterprise operates on top of **Vertex AI Search** and standard Google Cloud APIs. The UI is built using Google's standard web framework (**Wiz/BoQ**), but exhibits key architectural routing variations depending on whether a datasource is added via online crawling/literal text paste, a direct binary upload, a Google Drive document import, or for streaming chat logic.

A comprehensive mapping of all network sequence flows and high-level system components is documented in [har-diagrams.md](har-diagrams.md).

### Key Endpoints & Hostnames Identified:
1. **BoQ Wiz Batch RPCs Endpoint**:
   - URI: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute`
   - Hostname: `vertexaisearch.cloud.google.com`
   - Purpose: Primary gateway for metadata management. Individual metadata actions are multiplexed using obfuscated RPC IDs (e.g., `AzXHBd`, `kqBlec`, `LmGGPd`, `rG2vCb`).
2. **Wiz Streaming gRPC-over-HTTP Q&A Endpoint**:
   - URI: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/google.cloud.notebooklm.v1main.NotebookService/GenerateFreeFormStreamed`
   - Hostname: `vertexaisearch.cloud.google.com`
   - Purpose: Handles streaming text generation for user chat queries grounded in selected notebook datasources.
3. **Google Docs/Drive Picker Gateway**:
   - URI: `GET https://docs.google.com/picker/v2/home`
   - Hostname: `docs.google.com`
   - Purpose: Opens the native file picker interface to allow selection of secure cloud files (Google Docs, Slides, Sheets, Folders).
4. **Drive Batch REST API Endpoint**:
   - URI: `POST https://clients6.google.com/batch/drive/v3`
   - Hostname: `clients6.google.com`
   - Purpose: Batch requests to standard Google Drive API v3 to retrieve user directory metadata (titles, parents, MIME-types).
5. **Direct REST Binary File Upload Endpoint**:
   - URI: `POST https://discoveryengine.clients6.google.com/upload/v1alpha/projects/{project_id}/locations/global/notebooks/{notebook_id}/sources:uploadFile`
   - Hostname: `discoveryengine.clients6.google.com`
   - Purpose: Handles direct binary/stream uploads of local documents (e.g., PDF files).
6. **Thumbnail Render Servers (lh3)**:
   - URI: `GET https://lh3.google.com/u/0/d/{file_id}=w200-h150...`
   - Hostname: `lh3.google.com` and `lh3.googleusercontent.com`
   - Purpose: Renders user's document previews and slides thumbnail images inside the picker.

---

## Session 1: Notebook Creation & Web Source Addition

### Step-by-Step Walkthrough (Session 1)

#### 1. Notebook Creation (Entry #0)
* **Timestamp**: `2026-05-19T20:15:54.827Z`
* **Target Endpoint**: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute`
* **Hostname**: `vertexaisearch.cloud.google.com`
* **RPC ID**: `AzXHBd`
* **Wiz Action**: Notebook Instance Creation
* **Payload**:
  ```json
  [
    "projects/123456789012/locations/global",
    ["", null, null, null, null, [null, null, null, null, null, null, 1]]
  ]
  ```
* **Behind the Scenes**: The frontend triggers a request to create a new Notebook instance inside the user's Google Cloud project (`123456789012`).
* **Response / Result**: Creates notebook `74408a5d-2624-4016-865b-16667072aa47`.
  ```json
  {
    "70000": "projects/123456789012/locations/global/notebooks/74408a5d-2624-4016-865b-16667072aa47"
  }
  ```

#### 2. Listing & Synchronizing Notebook State (Entries #1, #8, #10-#15)
* **Timestamps**: `2026-05-19T20:15:55.553Z` to `2026-05-19T20:15:56.540Z`
* **Target Endpoint**: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute`
* **Hostname**: `vertexaisearch.cloud.google.com`
* **RPC IDs**: `rG2vCb`, `tHcQ6c`, `ca0cne`, `aKrKnb`
* **Behind the Scenes**:
  - The frontend initiates parallel calls to fetch the initial metadata, check if there are existing sources, retrieve default audio overview configurations, and populate the guide area. Since it is a brand-new notebook, the lists of sources and guide materials return empty.

#### 3. Real-time Signaler Push Channel Setup (Entry #7)
* **Timestamp**: `2026-05-19T20:15:55.908Z`
* **Target Endpoint**: `POST https://signaler-pa.clients6.google.com/punctual/multi-watch/channel`
* **Hostname**: `signaler-pa.clients6.google.com`
* **Behind the Scenes**: A persistent long-polling channel is opened, registering interest in real-time updates for project `123456789012` and notebook `74408a5d-2624-4016-865b-16667072aa47`.

#### 4. Adding the Website Datasource (Entry #22)
* **Timestamp**: `2026-05-19T20:16:14.785Z`
* **Target Endpoint**: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute`
* **Hostname**: `vertexaisearch.cloud.google.com`
* **RPC ID**: `kqBlec`
* **Wiz Action**: Create/Add Datasource
* **Payload**:
  ```json
  [
    "projects/123456789012/locations/global/notebooks/74408a5d-2624-4016-865b-16667072aa47",
    [
      [
        null,
        null,
        ["https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview"],
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        1
      ]
    ]
  ]
  ```
* **Behind the Scenes**: The user pastes the Google Cloud documentation URL and clicks "Add". 
* **Response / Result**: Instantly registers a new source resource `sources/8862a51d-6620-4136-a6f8-701c82ff078a` with the tentative title `"What is NotebookLM Enterprise? | Google Cloud Documentation"` and status showing pending ingestion.
  ```json
  {
    "70000": "projects/123456789012/locations/global/notebooks/74408a5d-2624-4016-865b-16667072aa47/sources/8862a51d-6620-4136-a6f8-701c82ff078a"
  }
  ```

#### 5. Document Ingestion & Text Extraction (Entries #23, #25)
* **Timestamps**: `2026-05-19T20:16:16.538Z` and `2026-05-19T20:16:17.864Z`
* **Target Endpoint**: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute`
* **Hostname**: `vertexaisearch.cloud.google.com`
* **RPC ID**: `rG2vCb` (Polling/Checking notebook contents)
* **Behind the Scenes**:
  - The backend initiates web fetching, HTML parsing, text cleaning, and embedding generation for the given documentation page.
  - By Entry #25, the ingestion completes successfully. The source metadata returns a document hash (`"c6351fcb-df04-45e6-8994-379479019c47"`) indicating that the content has been chunked and indexed.

#### 6. Automatic Guide Synthesis & Suggested Questions (Entries #26, #27)
* **Timestamp**: `2026-05-19T20:16:17.865Z` (parallelized instantly after ingestion finishes)
* **Target Endpoint**: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute`
* **Hostname**: `vertexaisearch.cloud.google.com`
* **RPC ID**: `LmGGPd`
* **Wiz Action**: Synthesize Notebook Overview & Recommendations
* **Behind the Scenes**: Once a datasource is successfully added, NotebookLM runs its core LLM pipeline to analyze the indexed source document and automatically generate a briefing overview of the notebook along with three context-aware suggested follow-up questions.

---

## Session 2: Pasted Plain Text Datasource Addition

### Step-by-Step Walkthrough (Session 2)

#### 1. Ingesting Pasted Plain Text Source (Entry #1)
* **Timestamp**: `2026-05-19T22:54:39.656Z`
* **Target Endpoint**: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute`
* **Hostname**: `vertexaisearch.cloud.google.com`
* **RPC ID**: `kqBlec`
* **Wiz Action**: Create/Add Datasource (Pasted Text)
* **Decoded Request Payload (Excerpt)**:
  ```json
  [
    "projects/123456789012/locations/global/notebooks/74408a5d-2624-4016-865b-16667072aa47",
    [
      [
        null,
        [
          "Pasted Text",
          "---\nid: getting-started-with-agent-gateway\nsummary: Deploy a governed multi-tool ADK agent on Agent Runtime that calls MCP servers on Cloud Run through Agent Gateway.\n..."
        ],
        null,
        2,
        null,
        null,
        null,
        null,
        null,
        null,
        1
      ]
    ]
  ]
  ```
* **Behind the Scenes**:
  - The user selects the "Pasted Text" option, names it "Pasted Text", and pastes the full text of the **Agent Gateway Codelab instructions**.
  - The frontend packages the literal text data string in the second index of the nested source array and sets the source class identifier to `2`.
* **Response / Result**:
  - The server registers the source resource path:
    `projects/123456789012/locations/global/notebooks/74408a5d-2624-4016-865b-16667072aa47/sources/0f82515f-e0b8-4933-be7c-a94b496c1827`
  - The backend parses the markdown content, automatically re-names the source to: `"Agent Gateway: Secure AI Agent Governance"`, and records the token size/length (`5334` tokens / `11386` characters).

#### 2. Querying Consolidated Notebook State (Entry #4)
* **Timestamp**: `2026-05-19T22:54:50.526Z`
* **Target Endpoint**: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute`
* **Hostname**: `vertexaisearch.cloud.google.com`
* **RPC ID**: `rG2vCb`
* **Behind the Scenes**: The frontend polls the notebook workspace state.
* **Response / Result**:
  - The notebook now has **two distinct sources** successfully loaded, chunked, and ready for Q&A grounding:
    1. **Source 1:** `"What is NotebookLM Enterprise? | Google Cloud Documentation"` (Web URL).
    2. **Source 2:** `"Agent Gateway: Secure AI Agent Governance"` (Pasted text document).

---

## Session 3: Local PDF File Upload Source

### Step-by-Step Walkthrough (Session 3)

#### 1. Local Binary File Upload (Entry #5)
* **Timestamp**: `2026-05-19T23:02:22.554Z`
* **Target Endpoint**: `POST https://discoveryengine.clients6.google.com/upload/v1alpha/projects/123456789012/locations/global/notebooks/74408a5d-2624-4016-865b-16667072aa47/sources:uploadFile`
* **Hostname**: `discoveryengine.clients6.google.com`
* **Wiz Action**: None (Bypasses BoQ Wiz batch wrapper entirely)
* **Request Payload**: Raw binary stream starting with `%PDF-1.5 ...` (representing the physical PDF file).
* **Behind the Scenes**:
  - The browser bypasses the Wiz `batchexecute` gate entirely for the upload transport, streaming the raw binary buffer of the local document straight to the REST API route.
* **Response / Result**: The Discovery Engine server ingests the PDF stream, parses it, and returns a raw JSON containing the newly created document source identity structure:
  ```json
  {
    "sourceId": {
      "id": "c33ec846-a0aa-46d8-88ab-213f52e77be1"
    }
  }
  ```

---

## Session 4: Grounded Chat Q&A Query

### Step-by-Step Walkthrough (Session 4)

#### 1. Grounded Query Streaming Call (Entry #0)
* **Timestamp**: `2026-05-20T01:53:23Z`
* **Target Endpoint**: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/google.cloud.notebooklm.v1main.NotebookService/GenerateFreeFormStreamed`
* **Hostname**: `vertexaisearch.cloud.google.com`
* **Wiz Action / API Method**: `google.cloud.notebooklm.v1main.NotebookService/GenerateFreeFormStreamed` (gRPC-over-HTTP low-latency streaming API)
* **Decoded Request Payload**:
  ```json
  [
    null,
    [
      [
        [["8862a51d-6620-4136-a6f8-701c82ff078a"]],
        [["0f82515f-e0b8-4933-be7c-a94b496c1827"]],
        [["4b2ff3bb-405d-445f-947e-fcc775401e96"]],
        [["c33ec846-a0aa-46d8-88ab-213f52e77be1"]]
      ],
      "What differentiates NotebookLM Enterprise from its personal version for business environments?",
      {
        "70000": "projects/123456789012/locations/global/notebooks/74408a5d-2624-4016-865b-16667072aa47"
      }
    ]
  ]
  ```
* **Behind the Scenes**:
  - The user types a chat question in the Gemini Enterprise / NotebookLM Q&A box and submits.
  - The browser packages the request by explicitly providing:
    1. The target Notebook path: `projects/123456789012/locations/global/notebooks/74408a5d-2624-4016-865b-16667072aa47`
    2. The array of active grounding sources currently selected in the UI checklist (includes the web URL source, the pasted text, and the uploaded PDF).
    3. The prompt query string: `"What differentiates NotebookLM Enterprise from its personal version for business environments?"`.
  - The backend receives the streaming request, performs vector retrieval against the selected index contexts, passes the grounded context snippets to the Gemini LLM, and streams back response chunks in real-time.
* **Decoded Streaming Response Chunks (Wiz Format)**:
  - *Chunk 1:* `NotebookLM Enterprise is designed to be a highly compliant, enterprise-ready version of the NotebookLM product, specifically fortified with...` (coupled with citation IDs grounding the answer to specific sections of your uploaded document).

---

## Session 5: Google Docs/Slides Datasource Addition

### Step-by-Step Walkthrough (Session 5)

#### 1. Loading Google Picker (Entries #1 - #3)
* **Timestamp**: `2026-05-20T08:36:31Z` (relative timestamp)
* **Target Endpoints**: 
  - `GET https://apis.google.com/js/api.js`
  - `GET https://docs.google.com/picker/v2/home`
* **Hostnames**: `apis.google.com` and `docs.google.com`
* **Behind the Scenes**:
  - When selecting "Google Drive" or "Google Slides" in the add-source UI modal, the browser loads the client API loader libraries and dynamically initializes the secure native **Google Picker** iframe inside the UI.

#### 2. Logging Impression & Restricting Mime-Types (Entry #15)
* **Target Endpoint**: `POST https://docs.google.com/picker/logImpressions`
* **Hostname**: `docs.google.com`
* **Behind the Scenes**:
  - The picker records analytics telemetry. The initialization parameters define the targeted mime-types allowed for import:
    `application/vnd.google-apps.folder`, `application/vnd.google-apps.document`, and `application/vnd.google-apps.presentation` (Google Slides).

#### 3. Catalog Retrieval & Batch Directory Search (Entries #24, #27, #33)
* **Target Endpoint**: `POST https://clients6.google.com/batch/drive/v3`
* **Hostname**: `clients6.google.com`
* **Behind the Scenes**:
  - The Picker communicates with the standard Google Drive REST API, issuing batch operations to fetch the directory structures, lists of folders, document metadata, and Slides presentations available under your active account context.

#### 4. Rendering Previews & Thumbnails (Entries #35 - #139)
* **Target Endpoints**: `GET https://lh3.google.com/u/0/d/{file_id}=w200-h150-p-k-nu`
* **Hostnames**: `lh3.google.com` and `lh3.googleusercontent.com`
* **Behind the Scenes**:
  - Renders visual preview thumbnail files of the slides files and folders listing so the user can interactively pick which slide presentation to select as a grounding source.

#### 5. Registering Source in NotebookLM Workspace (Entry #142)
* **Target Endpoint**: `POST https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute`
* **Hostname**: `vertexaisearch.cloud.google.com`
* **RPC ID**: `rG2vCb` (or dynamic `kqBlec` depending on import state)
* **Behind the Scenes**:
  - Once you select a Slides presentation document and click "Import/Select", the browser dispatches the document ID and credentials pointer.
  - The NotebookLM backend downstream calls Google Drive API, reads the Slides text elements, chunks the text by slide index, vectorizes them, and dynamically attaches it as a registered datasource context to your notebook.

---

## API Endpoint Mapping Reference Table

| Wiz RPC ID / Action | HTTP Method | Target API Endpoint (Hostname & Path) | Description | Payload Key Data | Response Key Data |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`AzXHBd`** | `POST` | `https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute` | Notebook creation | Parent GCP Project Path | Notebook UUID (`74408a5d-...`) |
| **`rG2vCb`** | `POST` | `https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute` | Fetch Notebooks List / State | Location Path | Ingested Sources List & Processing Status |
| **`tHcQ6c`** | `POST` | `https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute` | Get Specific Notebook Detail | Notebook Path | Metadata & Timestamp Sync |
| **`aKrKnb`** | `POST` | `https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute` | Get Audio Overview Status | AudioOverview Resource Path | Status of Generated Podcast / Audio |
| **`LmGGPd`** | `POST` | `https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute` | Get Guide Briefing & Suggested Qs | Notebook Path | LLM Generated Summary + 3 Suggested Questions |
| **`kqBlec`** | `POST` | `https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/batchexecute` | Create Web or Paste Datasource | Notebook Path + URL or literal text string | Newly Registered Source Resource Path |
| **`GenerateFreeFormStreamed`** | `POST` | `https://vertexaisearch.cloud.google.com/notebooklm/global/_/CloudNotebookLmUi/data/google.cloud.notebooklm.v1main.NotebookService/GenerateFreeFormStreamed` | Grounded Chat Q&A Streaming Generation | Notebook Path + groundings list + chat query string | Decoded real-time text stream containing answers & citations |
| **`sources:uploadFile`** | `POST` | `https://discoveryengine.clients6.google.com/upload/v1alpha/projects/{project_id}/locations/global/notebooks/{notebook_id}/sources:uploadFile` | Upload Local Binary Document | Binary File Stream (`application/pdf`) | Created Document sourceId (`c33ec846-...`) |
| **`Picker/home`** | `GET` | `https://docs.google.com/picker/v2/home` | Open native Google Doc picker | Mime-type options (`vnd.google-apps.presentation`) | Renders the Picker Iframe container |
| **`Drive/batch`** | `POST` | `https://clients6.google.com/batch/drive/v3` | Standard batch query for user Drive files | Directory lists requests and starting tokens | JSON file array metadata listing titles and folders |
| **`lh3/thumbnail`** | `GET` | `https://lh3.google.com/u/0/d/{file_id}` | Render Slides/Docs Preview Previews | Document file identifier | Streams dynamic preview thumbnails images |
