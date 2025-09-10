# UltraRAG MCP Servers Documentation

## Panoramica

UltraRAG implementa un'architettura modulare basata su **Model Context Protocol (MCP) servers** che fornisce funzionalità specializzate per il Retrieval-Augmented Generation (RAG). Ogni server è progettato per gestire una specifica fase del pipeline RAG e può essere utilizzato indipendentemente o in combinazione con altri server.

## Architettura dei Server

Tutti i server MCP sono configurati per supportare due modalità di trasporto:
- **stdio**: Comunicazione tramite standard input/output (per integrazione diretta)
- **http**: Comunicazione tramite HTTP REST API (per deployment distribuito)

Ogni server espone le sue funzionalità tramite **tools** e **prompts** che possono essere chiamati da agenti AI esterni.

---

## 1. SayHello Server (Porta 8001)

**Scopo**: Server di test e validazione della connessione MCP.

### Funzionalità
- **Tool**: `greet(name: str)` - Funzione di saluto semplice per testare la connettività
- **Output**: Messaggio di saluto personalizzato

### Utilizzo
```python
# Esempio di chiamata
result = greet("Alice")
# Output: {"msg": "Hello, Alice!"}
```

---

## 2. Retriever Server (Porta 8002)

**Scopo**: Gestisce il retrieval di documenti e la creazione di indici per la ricerca semantica.

### Funzionalità Principali

#### Inizializzazione
- **`retriever_init`**: Inizializza il retriever con modelli locali (infinity-emb)
- **`retriever_init_openai`**: Inizializza il retriever con modelli OpenAI

#### Embedding
- **`retriever_embed`**: Genera embeddings per documenti locali
- **`retriever_embed_openai`**: Genera embeddings tramite API OpenAI

#### Indicizzazione
- **`retriever_index`**: Crea indici FAISS per ricerca veloce
- **`retriever_index_lancedb`**: Crea indici LanceDB per ricerca vettoriale
- **`retriever_index_milvus`**: Crea collezioni Milvus per ricerca vettoriale scalabile

#### Ricerca
- **`retriever_search`**: Ricerca semantica standard
- **`retriever_search_maxsim`**: Ricerca con MaxSim per embeddings multi-token
- **`retriever_search_lancedb`**: Ricerca tramite LanceDB
- **`retriever_search_milvus`**: Ricerca tramite Milvus (raccomandato per produzione)

#### Ricerca Web
- **`retriever_exa_search`**: Ricerca tramite API Exa
- **`retriever_tavily_search`**: Ricerca tramite API Tavily

#### Deployment
- **`retriever_deploy_service`**: Deploy del servizio di retrieval
- **`retriever_deploy_search`**: Chiamata a servizio di retrieval remoto

### Dipendenze
- `faiss` (CPU/GPU)
- `infinity-emb`
- `lancedb`
- `pymilvus` (raccomandato per produzione)
- `exa_py`
- `tavily-python`

---

## 3. Generation Server (Porta 8003)

**Scopo**: Gestisce la generazione di testo tramite modelli LLM locali e remoti.

### Funzionalità Principali

#### Inizializzazione vLLM
- **`initialize_local_vllm`**: Avvia server vLLM locale per inferenza GPU

#### Generazione Testo
- **`generate`**: Genera testo da prompt testuali
- **`multimodal_generate`**: Genera testo da prompt multimodali (testo + immagini)

### Caratteristiche
- Supporto per modelli locali (vLLM) e remoti (OpenAI-compatible)
- Gestione asincrona con retry automatico
- Supporto per prompt complessi e multimodali
- Controllo della concorrenza tramite semafori

### Dipendenze
- `vllm`
- `openai`
- `PIL` (per immagini)

---

## 4. Corpus Server (Porta 8004)

**Scopo**: Gestisce il preprocessing e la segmentazione dei documenti.

### Funzionalità Principali

#### Parsing Documenti
- **`parse_documents`**: Estrae testo da file PDF, DOCX, TXT, MD

#### Chunking
- **`chunk_documents`**: Segmenta documenti in chunk più piccoli
  - **Strategie supportate**:
    - `token`: Chunking basato su token
    - `word`: Chunking basato su parole
    - `sentence`: Chunking basato su frasi
    - `recursive`: Chunking ricorsivo

### Formati Supportati
- **Input**: PDF, DOCX, TXT, MD
- **Output**: JSONL con chunk strutturati

### Dipendenze
- `llama-index-readers-file`
- `chonkie`

---

## 5. Reranker Server (Porta 8005)

**Scopo**: Migliora la qualità dei risultati di retrieval tramite reranking.

### Funzionalità Principali

#### Inizializzazione
- **`reranker_init`**: Inizializza il modello di reranking

#### Reranking
- **`reranker_rerank`**: Rirankera i risultati di retrieval per migliorare la rilevanza

#### Deployment
- **`rerank_deploy_service`**: Deploy del servizio di reranking
- **`rerank_deploy_search`**: Chiamata a servizio di reranking remoto

### Caratteristiche
- Supporto per modelli infinity-emb
- Reranking asincrono per performance ottimali
- Integrazione con pipeline di retrieval

### Dipendenze
- `infinity-emb`

---

## 6. Evaluation Server (Porta 8006)

**Scopo**: Valuta la qualità delle risposte generate tramite metriche standard.

### Funzionalità Principali

#### Metriche Supportate
- **`accuracy_score`**: Accuratezza basata su normalizzazione del testo
- **`exact_match_score`**: Match esatto tra predizione e ground truth
- **`string_em_score`**: String exact match con normalizzazione
- **`cover_exact_match_score`**: Cover exact match per token
- **`f1_score`**: F1 score basato su token
- **`rouge1_score`**: ROUGE-1 score
- **`rouge2_score`**: ROUGE-2 score
- **`rougel_score`**: ROUGE-L score

#### Valutazione
- **`evaluate`**: Valuta predizioni contro ground truth
- **`save_evaluation_results`**: Salva risultati in formato JSON con timestamp

### Caratteristiche
- Normalizzazione del testo per confronti robusti
- Supporto per multiple ground truth per query
- Output formattato con tabelle markdown
- Salvataggio automatico con timestamp

### Dipendenze
- `rouge-score`
- `tabulate`

---

## 7. Benchmark Server (Porta 8007)

**Scopo**: Carica e gestisce dataset di benchmark per valutazione.

### Funzionalità Principali

#### Caricamento Dati
- **`get_data`**: Carica dataset da file locali
  - **Formati supportati**: JSONL, JSON, Parquet
  - **Funzionalità**: Shuffling, limitazione, mapping chiavi

### Caratteristiche
- Supporto per multiple fonti dati
- Shuffling controllato con seed
- Mapping flessibile delle chiavi
- Limitazione configurabile dei dati

### Dipendenze
- `pandas`

---

## 8. Custom Server (Porta 8008)

**Scopo**: Fornisce funzioni di utilità personalizzate per estrazione e processing.

### Funzionalità Principali

#### Estrazione Query
- **`search_r1_query_extract`**: Estrae query da risposte con tag `<search>`
- **`r1_searcher_query_extract`**: Estrae query con tag `<|begin_of_query|>`
- **`search_o1_query_extract`**: Estrae query con tag `<|begin_search_query|>`

#### Processing Risposte
- **`output_extract_from_boxed`**: Estrae contenuto da tag `\boxed{}`
- **`ircot_get_first_sent`**: Estrae prima frase da risposte
- **`ircot_extract_ans`**: Estrae risposte finali da chain-of-thought

#### Generazione Query
- **`iterretgen_nextquery`**: Genera query successive per iterative retrieval

### Caratteristiche
- Pattern matching robusto con regex
- Gestione di formati di output complessi
- Supporto per chain-of-thought reasoning

---

## 9. Prompt Server (Porta 8009)

**Scopo**: Gestisce la creazione e il rendering di prompt template per vari scenari.

### Funzionalità Principali

#### Template QA
- **`qa_boxed`**: Prompt per Q&A con output boxed
- **`qa_boxed_multiple_choice`**: Prompt per Q&A a scelta multipla
- **`qa_rag_boxed`**: Prompt per Q&A con RAG
- **`qa_rag_boxed_multiple_choice`**: Prompt per Q&A RAG a scelta multipla

#### Template RankCoT
- **`RankCoT_kr`**: Prompt per knowledge retrieval
- **`RankCoT_qa`**: Prompt per Q&A con chain-of-thought

#### Template IRCOT
- **`ircot_next_prompt`**: Prompt per iterative retrieval chain-of-thought

#### Template WebNote
- **`webnote_init_page`**: Inizializzazione pagina WebNote
- **`webnote_gen_plan`**: Generazione piano di ricerca
- **`webnote_gen_subq`**: Generazione sub-query
- **`webnote_fill_page`**: Riempimento pagina con contenuti
- **`webnote_gen_answer`**: Generazione risposta finale

#### Template Search
- **`search_r1_gen`**: Generazione per search-r1
- **`r1_searcher_gen`**: Generazione per r1-searcher
- **`search_o1_init`**: Inizializzazione search-o1
- **`searcho1_reasoning_indocument`**: Reasoning in-document per search-o1
- **`search_o1_insert`**: Inserimento risultati di ricerca

### Caratteristiche
- Template Jinja2 per flessibilità
- Supporto per multiple scelte (A, B, C, ...)
- Gestione di documenti e contesto
- Supporto per reasoning iterativo

### Dipendenze
- `jinja2`

---

## 10. Router Server (Porta 8010)

**Scopo**: Gestisce il routing e il controllo del flusso tra diversi stati del sistema.

### Funzionalità Principali

#### Routing Base
- **`route1`**: Routing basato su condizioni semplici
- **`route2`**: Routing con stato fisso

#### Controllo Flusso
- **`ircot_check_end`**: Verifica completamento per IRCOT
- **`search_r1_check`**: Verifica completamento per search-r1
- **`r1_searcher_check`**: Verifica completamento per r1-searcher
- **`search_o1_check`**: Verifica completamento per search-o1
- **`webnote_check_page`**: Verifica completamento pagine WebNote

### Caratteristiche
- Pattern matching per token di fine
- Gestione stati (complete/incomplete/stop/retrieve)
- Supporto per multiple strategie di reasoning

---

## Configurazione e Deployment

### Porte di Default
- **8000**: Health check server
- **8001**: SayHello
- **8002**: Retriever
- **8003**: Generation
- **8004**: Corpus
- **8005**: Reranker
- **8006**: Evaluation
- **8007**: Benchmark
- **8008**: Custom
- **8009**: Prompt
- **8010**: Router

### Variabili d'Ambiente
- `CUDA_VISIBLE_DEVICES`: Controllo GPU per modelli locali
- `LLM_API_KEY`: API key per servizi LLM
- `RETRIEVER_API_KEY`: API key per servizi di retrieval
- `EXA_API_KEY`: API key per Exa search
- `TAVILY_API_KEY`: API key per Tavily search
- `MILVUS_HOST`: Host del database Milvus (default: localhost)
- `MILVUS_PORT`: Porta del database Milvus (default: 19530)

### Health Check
Tutti i server espongono un endpoint di health check su `http://localhost:8000/health` che restituisce:
```json
{
  "status": "healthy",
  "service": "ultrarag-mcp"
}
```

## Database Vettoriali Supportati

### Milvus (Raccomandato per Produzione)
- **Vantaggi**: Scalabilità, performance, gestione distribuita
- **Configurazione**: `MILVUS_HOST` e `MILVUS_PORT` environment variables
- **Funzioni**: `retriever_init_milvus`, `retriever_index_milvus`, `retriever_search_milvus`
- **Uso**: Ideale per deployment Kubernetes con volumi elevati di dati

### FAISS (Per Sviluppo/Test)
- **Vantaggi**: Veloce, semplice da usare
- **Limitazioni**: Memory-intensive, non distribuito
- **Funzioni**: `retriever_init`, `retriever_index`, `retriever_search`

### LanceDB (Alternativa Leggera)
- **Vantaggi**: Leggero, basato su file
- **Funzioni**: `retriever_index_lancedb`, `retriever_search_lancedb`

## Note sui Problemi di Risorse

Come evidenziato dall'utente, il sistema può incontrare problemi di memoria e risorse, specialmente durante:

1. **Build Docker**: Kaniko richiede memoria sufficiente per buildare immagini con dipendenze pesanti
2. **Inizializzazione Modelli**: I modelli di embedding e reranking possono richiedere RAM significativa
3. **Inferenza GPU**: I modelli vLLM richiedono memoria GPU dedicata
4. **Indicizzazione FAISS**: La creazione di indici può essere memory-intensive

### Raccomandazioni
- **Usare Milvus** per ambienti di produzione per migliore gestione delle risorse
- Utilizzare build CPU-only quando possibile
- Configurare limiti di memoria appropriati per Kubernetes
- Considerare l'uso di modelli più leggeri per ambienti con risorse limitate
- Implementare monitoring delle risorse per identificare colli di bottiglia
