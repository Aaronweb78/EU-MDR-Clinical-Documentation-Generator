# EU MDR Clinical Documentation Generator

A professional, **fully offline** desktop application for generating EU MDR 2017/745 compliant clinical documentation including CEP, CER, SSCP, and LSR documents.

## Features

### Core Capabilities
- **100% Offline** - All processing happens locally on your machine
- **500+ Document Support** - Process PDF, DOCX, XLSX, and TXT files
- **Intelligent Classification** - Automatic document categorization
- **Entity Extraction** - Extract device information, specifications, and regulatory data
- **Vector Search** - Semantic search using ChromaDB for relevant context retrieval
- **Local LLM Generation** - Uses Ollama for report generation (no cloud dependencies)

### Generated Documents
1. **Clinical Evaluation Plan (CEP)** - Per MEDDEV 2.7/1 Rev 4
2. **Clinical Evaluation Report (CER)** - Per EU MDR Annex XIV
3. **Summary of Safety and Clinical Performance (SSCP)** - Per EU MDR Annex XIV
4. **Literature Search Report (LSR)** - Systematic literature review documentation

### Professional UI
-  Modern dark theme interface
-  Real-time processing progress
-  Section-by-section report generation
-  Professional DOCX export with formatting
-  Configurable settings

## System Requirements

### Hardware
- **Minimum:** 8GB RAM, RTX 3060 or better
- **Recommended:** 16GB RAM, RTX 4060 or better
- **Storage:** 10GB free space (plus space for documents)

### Software
- **OS:** Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- **Python:** 3.11 or higher
- **Ollama:** Latest version with Llama 3 8B model

## Installation

### 1. Install Ollama

Download and install Ollama from [https://ollama.ai](https://ollama.ai)

Pull the Llama 3 8B model:
```bash
ollama pull llama3:8b
```

Verify Ollama is running:
```bash
ollama list
```

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/mdr-doc-generator.git
cd mdr-doc-generator
```

### 3. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize Database

The database will be automatically initialized on first run.

## Usage

### Starting the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Workflow

#### 1. Create a Project
- Navigate to **Projects** page
- Click **Create New Project**
- Enter project name, device name, and device class
- Click **Create Project**

#### 2. Upload Files
- Go to **Upload Files** page
- Drag and drop or select files (PDF, DOCX, XLSX, TXT)
- Click **Upload All Files**
- Supported document types:
  - Device specifications and design documents
  - Risk analysis and FMEA
  - Clinical study reports
  - Literature articles
  - Test reports
  - IFU and labeling
  - Biocompatibility data
  - And more...

#### 3. Process Files
- Navigate to **Process Files** page
- Choose processing options:
  - Use LLM for classification (more accurate, slower)
  - Use LLM for entity extraction (more comprehensive, slower)
- Click **Start Processing**
- Wait for processing to complete
  - Text extraction
  - Document classification
  - Entity extraction
  - Text chunking (500 tokens)
  - Embedding generation
  - Vector storage

#### 4. Review Classification
- Go to **Review Classification** page
- Review auto-classified documents
- Adjust categories if needed
- Mark key documents for priority
- Filter and bulk edit classifications

#### 5. Generate Reports
- Navigate to **Generate Reports** page
- Select which reports to generate:
  - [ ] Clinical Evaluation Plan (CEP)
  - [ ] Clinical Evaluation Report (CER)
  - [ ] Summary of Safety and Clinical Performance (SSCP)
  - [ ] Literature Search Report (LSR)
- Click **Generate Selected Reports**
- Monitor real-time generation progress
- Review generated sections

#### 6. Export Documents
- Go to **Export** page
- Export individual reports or all at once
- Download professional DOCX files
- Files saved to `output/[project_id]/`

#### 7. Configure Settings
- Navigate to **Settings** page
- Configure Ollama connection
- Adjust chunking parameters
- Set company information
- Test system components

## Configuration

### Ollama Settings
- **Server URL:** `http://localhost:11434` (default)
- **Model:** `llama3:8b` (default)
- **Temperature:** `0.3` (for consistency)
- **Max Tokens:** `2000` per section

### Embedding Settings
- **Model:** `all-MiniLM-L6-v2`
- **Chunk Size:** `500` tokens
- **Chunk Overlap:** `50` tokens
- **Max Chunks for Context:** `10`

### Document Categories
- Device Description
- Intended Use
- Risk Management
- Biocompatibility
- Clinical Study
- Literature
- Performance Testing
- Sterilization
- Software
- Post-Market
- Regulatory
- Quality
- Labeling
- Other

## Troubleshooting

### Ollama Connection Issues

**Problem:** "Ollama Not Connected" error

**Solution:**
1. Verify Ollama is running: `ollama list`
2. Check URL in Settings page
3. Ensure model is pulled: `ollama pull llama3:8b`
4. Restart Ollama service

### Processing Errors

**Problem:** Files fail to process

**Solution:**
1. Check file format (must be PDF, DOCX, XLSX, or TXT)
2. Verify file is not corrupted
3. Check file permissions
4. Review processing logs

### Out of Memory

**Problem:** Application crashes during processing

**Solution:**
1. Reduce batch size in processing options
2. Process fewer files at once
3. Close other applications
4. Upgrade RAM if processing 500+ files regularly

### Slow Generation

**Problem:** Report generation is very slow

**Solution:**
1. Disable LLM classification (use keyword-based)
2. Reduce number of chunks retrieved (in config.py)
3. Use faster Ollama model
4. Upgrade GPU

## Privacy & Security

- **100% Offline** - No internet connection required
- **Local Processing** - All data stays on your machine
- **No Cloud APIs** - No data sent to external servers
- **Secure Storage** - All files stored locally
- **GDPR Compliant** - No data collection or tracking

## Performance

### Typical Processing Times (RTX 4060)

| Operation | Time per File | Notes |
|-----------|--------------|-------|
| Text Extraction | 1-5 seconds | Depends on file size |
| Classification (Keyword) | <1 second | Fast |
| Classification (LLM) | 5-10 seconds | More accurate |
| Chunking | <1 second | Fast |
| Embedding | 1-2 seconds | Per file |
| Report Section Generation | 30-60 seconds | Per section |

### Expected Total Time

- **100 files:** ~30 minutes (keyword classification)
- **100 files:** ~60 minutes (LLM classification)
- **Report generation:** ~20-40 minutes (4 reports)


## Disclaimer

This tool assists in generating clinical documentation but does not replace professional regulatory expertise. All generated content must be reviewed and validated by qualified regulatory professionals before submission to notified bodies or regulatory authorities.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review Ollama documentation

## References

- EU MDR 2017/745
- MEDDEV 2.7/1 Rev 4
- ISO 14155:2020
- ISO 14971:2019

---

