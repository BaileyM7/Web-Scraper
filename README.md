# Bill Processing System

A system for automatically fetching, processing, and generating press releases from legislative bills from congress.gov and related sources.

## Overview

This system automatically:
1. Scrapes bill text from congressional websites
2. Processes the content using AI to generate press releases
3. Stores results in a database
4. Sends summary emails on completion

## Dependencies

### Python Libraries
- `sys` - Standard library for system-specific parameters and functions
- `getopt` - Standard library for command line option parsing
- `csv` - Standard library for CSV file operations
- `logging` - Standard library for logging functionality
- `time` - Standard library for time-related functions
- `datetime` - Standard library for date and time manipulation

### Custom Modules
- `url_processing` - Contains functions for URL handling and content extraction
- `openai_api` - OpenAI integration for text processing
- `db_insert` - Database connection and operations
- `scripts.populateCsv` - CSV population utilities
- `email_utils` - Email sending functionality

### External Services
- OpenAI API - Used for text processing and generating press releases
- Database server - For storing processed content

## Installation

1. Clone this repository
2. Install the required Python packages
3. Set up your database configuration (see Configuration section)
4. Ensure you have an OpenAI API key properly configured

## Configuration

Before running the script, make sure you have:

1. A database set up and properly configured for connection
2. OpenAI API key accessible to the system
3. The `sources.dmp.sql` file in the root directory
4. CSV files in the `csv/` directory:
   - `senate.csv`
   - `house.csv`

## Usage

Run the script with the following command line options:

```
python process_bills.py [OPTIONS]
```

### Options:
- `-P` - Populate CSV files first before processing
- `-s` - Process Senate bills
- `-h` - Process House bills
- `-i [a_id]` - Specify the author ID for the database

### Examples:

Process Senate bills:
```
python process_bills.py -s -i 56
```

Process House bills:
```
python process_bills.py -h -i 57
```

Populate CSV first:
```
python process_bills.py -P 
```

## Main Features

### URL Processing
- Extracts URLs from CSV files
- Handles both static and dynamic content loading
- Special handling for congress.gov URLs

### AI Content Generation
- Uses OpenAI API to process legislative text
- Generates press releases based on bill content
- Adds source attribution to generated content

### Database Operations
- Checks for duplicate entries
- Inserts new stories with proper metadata
- Loads SQL dumps for source information

### Logging and Reporting
- Comprehensive logging system
- Generates summary reports
- Sends email notifications with operation results

## Output

The script produces:
1. Log files with detailed execution information
2. Database entries for each processed bill
3. Email summaries of the processing run

## Troubleshooting

If you encounter issues:
1. Check the log file in the root directory
2. Verify your database connection settings
3. Ensure your OpenAI API key is valid
4. Confirm the CSV files are properly formatted

## Version

Current Version: 2.2.1 (04/07/2025)