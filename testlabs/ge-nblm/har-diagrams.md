# HAR Trace Diagrams: NotebookLM Enterprise Architecture Flows

For the complete technical breakdown of the individual sessions, payloads, and API methods, see [har-analysis.md](har-analysis.md).

---

## 1. System Communication Architecture (High-Level)

This flowchart illustrates how the client-side UI frontend communicates across various Google Cloud backends and Google Workspace authentication gateways to manage workspace settings, ingest documents, and execute grounded generation.

```mermaid
flowchart TD
    subgraph Browser ["Client Web Browser: NotebookLM UI (Wiz/BoQ)"]
        UI["UI Frontend Application Layer"]
    end

    subgraph GoogleCloud ["Google Cloud Platform Gateway & Services"]
        BoQ["BoQ Wiz Batch RPC Gateway\nvertexaisearch.cloud.google.com"]
        StreamQ["Wiz Streaming gRPC Gateway\nvertexaisearch.cloud.google.com"]
        Signaler["Signaler Channel Real-time Sync\nsignaler-pa.clients6.google.com"]
        Discovery["Discovery Engine / Upload Gateway\ndiscoveryengine.clients6.google.com"]
    end

    subgraph DriveServices ["Google Drive & Workspace Services"]
        Picker["Google Picker Gateway\ndocs.google.com/picker"]
        DriveAPI["Drive Batch REST API\nclients6.google.com/drive"]
        LH3["Thumbnail Preview Servers\nlh3.googleusercontent.com"]
    end

    %% Flow lines & Annotations
    UI ==>|"1. RPCs: AzXHBd (Create), kqBlec (Add Source), LmGGPd (Overview)"| BoQ
    UI ==>|"2. GenerateFreeFormStreamed (Stream Q&A)"| StreamQ
    UI ==>|"3. multi-watch/channel (Long-poll status)"| Signaler
    UI ==>|"4. uploadFile (Direct Binary PDF upload)"| Discovery
    UI ==>|"5. Load Iframe / Impress logging"| Picker
    UI ==>|"6. batch/drive/v3 (Retrieve directory listing)"| DriveAPI
    UI ==>|"7. Fetch slide/doc thumbnail assets"| LH3

    %% Inner cloud service interactions
    BoQ -.->|"Ingest, chunk & index web sources"| Discovery
    DriveAPI -.->|"Imports selected document text downstream"| Discovery
    StreamQ -.->|"Retrieves grounded semantic embeddings"| Discovery

    %% Styling Elements
    style UI fill:#E8F0FE,stroke:#1A73E8,stroke-width:2px,color:#1A73E8
    style BoQ fill:#FEF7E0,stroke:#F9AB00,stroke-width:2px,color:#B06000
    style StreamQ fill:#FEF7E0,stroke:#F9AB00,stroke-width:2px,color:#B06000
    style Signaler fill:#FEF7E0,stroke:#F9AB00,stroke-width:2px,color:#B06000
    style Discovery fill:#E6F4EA,stroke:#137333,stroke-width:2px,color:#137333
    style Picker fill:#FCE8E6,stroke:#C5221F,stroke-width:2px,color:#C5221F
    style DriveAPI fill:#FCE8E6,stroke:#C5221F,stroke-width:2px,color:#C5221F
    style LH3 fill:#FCE8E6,stroke:#C5221F,stroke-width:2px,color:#C5221F

    classDef default font-family:Inter,sans-serif,font-size:12px;
```

---

## 2. Session Network Sequence Flows

The interactive sequence diagrams below detail how distinct user workflows are routed, negotiated, and processed under the hood.

### Sequence Flow A: Session 1 - Notebook Creation & Web Ingestion

This sequence maps out creating a new workspace project container and adding a crawling web URL datasource.

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser (UI Frontend)
    participant BoQ as BoQ Wiz Gateway
    participant Signaler as Signaler Channels
    participant Discovery as Discovery Engine Backend

    User->>BoQ: POST batchexecute (RPC: AzXHBd) Create Notebook
    BoQ-->>User: Returns Notebook UUID (74408a5d-...)
    
    par Parallel initial syncs
        User->>BoQ: POST batchexecute (RPCs: rG2vCb, tHcQ6c) Fetch status
        BoQ-->>User: HTTP 200 OK (Lists empty sources/guides)
    and Register status push channel
        User->>Signaler: POST multi-watch/channel Listen for updates
    end

    User->>BoQ: POST batchexecute (RPC: kqBlec) Add Web Source URL
    BoQ->>Discovery: Trigger background source crawler & ingestion
    BoQ-->>User: Returns tentative source ID (Pending Ingestion)
    
    loop Polling Workspace State
        User->>BoQ: POST batchexecute (RPC: rG2vCb) Check status
        BoQ-->>User: HTTP 200 OK (Returns status pending/completed)
    end

    Discovery-->>Signaler: Ingestion Succeeded (Returns document hash)
    Signaler-->>User: Push update event via active Channel

    User->>BoQ: POST batchexecute (RPC: LmGGPd) Request Overview & Suggested Qs
    BoQ->>Discovery: Run LLM pipeline to analyze doc contexts
    Discovery-->>BoQ: Return auto briefing + 3 custom questions
    BoQ-->>User: Renders briefing guide panel successfully
```

---

### Sequence Flow B: Session 2 & 5 - Web Crawling vs. Google Picker & Drive Ingestion Routing

This flow contrasts adding text manually vs. utilizing the secure, native Google Docs & Google Slides gateway and directory mapping integration.

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser (UI Frontend)
    participant BoQ as BoQ Wiz Gateway
    participant Discovery as Discovery Engine Backend
    participant Picker as Google Picker Gateway
    participant Drive as Drive API v3 Gateway
    participant LH3 as Thumbnail Previews

    rect rgb(235, 245, 235)
        Note over User, Discovery: Web URL Crawling or Paste Text Addition
        User->>BoQ: POST batchexecute (RPC: kqBlec) Source array class = 2 (Paste Text)
        BoQ->>Discovery: Ingest raw inline text characters
        Discovery-->>BoQ: Text successfully indexed & sized
        BoQ-->>User: Source loaded: 'Agent Gateway: Secure AI Agent Governance'
    end

    rect rgb(240, 240, 255)
        Note over User, LH3: Native Google Drive / Picker Ingestion Workflow
        User->>User: Selects 'Google Drive' or 'Google Slides' source
        User->>Picker: GET picker/v2/home Load Iframe container
        Picker-->>User: Renders Native Google Picker Dialog
        User->>Picker: Select target folder or slide presentation
        Picker->>Drive: POST batch/drive/v3 (Standard Drive directory lookup)
        Drive-->>Picker: Returns lists of directories & documents details
        Picker->>LH3: GET thumbnail preview assets (lh3.googleusercontent.com)
        LH3-->>Picker: Renders live previews in UI selection list
        User->>User: Clicks 'Import/Select'
        User->>BoQ: POST batchexecute (RPC: rG2vCb) Sends Document ID & Access pointer
        BoQ->>Discovery: Downstream fetch Slide/Doc text elements
        Discovery->>Discovery: Vectorize slide pages, index, and save embeddings
        Discovery-->>BoQ: Ingestion completed successfully
        BoQ-->>User: UI checklist updates with Google Slide datasource
    end
```

---

### Sequence Flow C: Session 3 - Local Binary PDF Ingestion Flow

Direct local binary/stream uploads bypass the multiplexed `batchexecute` gate and connect straight to the REST API endpoint context.

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser (UI Frontend)
    participant BoQ as BoQ Wiz Gateway
    participant Discovery as Discovery Engine Backend

    Note over User, Discovery: Local Binary PDF Ingestion Flow (Bypasses Wiz RPC Batch)
    User->>User: Clicks 'Upload File' (PDF document selection)
    User->>Discovery: POST /upload/v1alpha/projects/{project}/locations/global/notebooks/{notebook}/sources:uploadFile
    Note over User, Discovery: Raw binary stream starting with %PDF-1.5 is sent directly to REST API
    Discovery->>Discovery: Parse raw stream, extract text structure, and generate vector indices
    Discovery-->>User: Returns metadata JSON with sourceId: c33ec846-a0aa-46d8-88ab-213f52e77be1
    User->>BoQ: POST batchexecute (RPC: rG2vCb) Register the newly created local upload source
    BoQ-->>User: Consolidated notebook workspace checklist updated
```

---

### Sequence Flow D: Session 4 - Grounded Streamed Chat Q&A Generation

Low-latency gRPC-over-HTTP streaming generation flow grounding prompt queries using semantic indices retrieved across active selections.

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser (UI Frontend)
    participant StreamQ as Wiz Streaming gRPC Gateway
    participant Discovery as Discovery Engine Backend

    User->>User: Types query 'What differentiates NotebookLM Enterprise from its personal version?'
    User->>StreamQ: POST GenerateFreeFormStreamed (gRPC-over-HTTP stream)
    Note over User, StreamQ: Payload contains query, notebook path, and target grounding source IDs list
    StreamQ->>Discovery: Query semantic vector retrieval
    Discovery->>Discovery: Perform vector similarity metrics match on active grounding sources context chunks
    Discovery-->>StreamQ: Returns matching grounded document context snippets & citation bindings
    StreamQ->>StreamQ: Injects context snippets into Gemini enterprise prompt context window
    StreamQ->>StreamQ: Triggers grounded LLM generation pipeline
    
    loop Stream Response Generation
        StreamQ-->>User: Yields streaming text chunks (Wiz Format) in real-time + associated Citation ID markers
    end
    Note over User, StreamQ: Response fully loaded & grounded visually inside UI chat history container
```
