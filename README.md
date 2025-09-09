# UltraRAG Backend

## English

UltraRAG is an advanced RAG (Retrieval-Augmented Generation) framework that combines multiple AI models and techniques to provide enhanced document understanding and question answering capabilities.

### Features
- CPU-optimized deployment for environments without GPU
- Integration with external MinIO storage
- Advanced document processing and analysis
- Multi-model approach for improved accuracy
- Memory-efficient operation

### Installation
The project uses Conda for dependency management. Two environment configurations are available:
- `environment.yml`: Full version with GPU support
- `environment-cpu.yml`: CPU-only version for environments without GPU

To install the CPU version:
```bash
conda env create -f environment-cpu.yml
conda activate ultrarag
```

### Configuration
The system requires:
- MinIO credentials for document storage
- Environment variables for API keys and endpoints
- Proper network access to MinIO service

---

## Italiano

UltraRAG è un framework RAG (Retrieval-Augmented Generation) avanzato che combina diversi modelli AI e tecniche per fornire capacità migliorate di comprensione dei documenti e risposta alle domande.

### Caratteristiche
- Deployment ottimizzato per CPU per ambienti senza GPU
- Integrazione con storage MinIO esterno
- Elaborazione e analisi avanzata dei documenti
- Approccio multi-modello per una maggiore accuratezza
- Operatività efficiente in termini di memoria

### Installazione
Il progetto utilizza Conda per la gestione delle dipendenze. Sono disponibili due configurazioni dell'ambiente:
- `environment.yml`: Versione completa con supporto GPU
- `environment-cpu.yml`: Versione solo CPU per ambienti senza GPU

Per installare la versione CPU:
```bash
conda env create -f environment-cpu.yml
conda activate ultrarag
```

### Configurazione
Il sistema richiede:
- Credenziali MinIO per lo storage dei documenti
- Variabili d'ambiente per chiavi API ed endpoints
- Accesso di rete appropriato al servizio MinIO