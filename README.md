# Bill Processing System

A Python-based automation pipeline for fetching, processing, and generating press releases from U.S. congressional bills. This system scrapes legislative content from Congress.gov, uses OpenAI's API to summarize and reformat it into media-ready releases, stores the results in a database, and sends email summaries.

---

## 🔧 Features

* 🔍 **Dynamic Bill Scraping**
  Scrapes text and summaries from official congressional sources.

* 🧠 **AI Content Generation**
  Uses OpenAI's GPT models to turn legislative language into clear press releases.

* 💃 **Database Integration**
  Stores processed data in a MySQL database, complete with logging and duplication checks.

* 📩 **Email Notifications**
  Sends automated summaries of processed bills to stakeholders.

* 📁 **Flexible Input**
  Reads from structured CSV files (`senate.csv`, `house.csv`) and supports population from dynamic sources.

---

## 📦 Dependencies

### 🐍 Python Standard Libraries

* `sys`, `getopt`, `csv`, `logging`, `time`, `datetime`

### 📁 Custom Modules

* `url_processing.py` – Parses and fetches bill content
* `openai_api.py` – Handles GPT calls
* `db_insert.py` – Manages DB insertion logic
* `scripts/populateCsv.py` – CSV data population
* `email_utils.py` – Summary email support

### 🌐 External Services

* **OpenAI API** – For text summarization and press release generation
* **MySQL Database** – For persistent storage of processed outputs

---

## ⚙️ Setup

1. **Clone the repository**

2. **Install Python dependencies**

   Most dependencies are standard libraries.

3. **Prepare your environment**

   * Place your OpenAI API key in `utils/govkey.txt`
   * Configure DB credentials in `configs/db_config.yml`
   * Ensure `sources.dmp.sql` is in the root directory

---

## 🚀 Usage

### Run the processor:

```bash
python main.py [OPTIONS]
```

### Options:

* `-P` – Populate the CSV files first
* `-s` – Process Senate bills
* `-h` – Process House bills
* `-t` – Run in test mode (does not insert to DB or send emails)

### Examples:

Process Senate bills:

```bash
python main.py -s
```

Process House bills:

```bash
python main.py -h
```

Populate CSV first and process:

```bash
python main.py -P -s
```

---

## 📟 Output

* ✅ AI-generated press releases
* 📥 Entries in your MySQL database
* 📧 Email reports summarizing each processing batch
* 📄 Log files with full diagnostic info

---

## 💪 Troubleshooting

* Check `debug.log` in the root directory
* Verify your database and OpenAI key configurations
* Ensure CSV files are properly formatted and encoded

---

## 📌 Version

**Current Version:** 3.1.9
**Last Updated:** August 2025

---