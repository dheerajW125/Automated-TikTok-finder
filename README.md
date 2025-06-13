# Automated TikTok Finder 🎯

This project is an automated TikTok profile finder that uses a combination of search engine scraping and metadata extraction to find and enrich TikTok profile information based on user-provided keywords or names.

## 🚀 Features

- 🔍 **Automated Search**: Uses BrightData SERP proxy to perform Google searches for TikTok profiles.
- 🧠 **Smart Matching**: Implements fuzzy name matching logic to validate relevant TikTok profiles.
- 📦 **Metadata Extraction**: Integrates with external APIs (e.g., RapidAPI) to fetch profile details like followers, likes, and bio.
- 📝 **Output in JSON**: Returns enriched and structured TikTok profile data for downstream use.
- 🌐 **Headless Scraping**: Uses `undetected_chromedriver` with Selenium for stealthy scraping.

## 📁 Project Structure

Automated-TikTok-finder/

├── main.py # Entry point for the script

├── serp_search.py # Module for Google search using BrightData SERP

├── profile_parser.py # Profile metadata extraction logic

├── utils.py # Helper functions (e.g., string matching)

├── requirements.txt # Python dependencies

└── README.md # Project documentation



## 🧰 Tech Stack

- **Python 3.8+**
- **Selenium** (via `undetected_chromedriver`)
- **BrightData SERP Proxy** (Google Search automation)
- **RapidAPI** (for TikTok metadata)
- **FuzzyWuzzy / RapidFuzz** (for name similarity scoring)
- **JSON / Pandas** (for data formatting and manipulation)

## 🛠️ Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/dheerajW125/Automated-TikTok-finder.git
   cd Automated-TikTok-finder
2. Install dependencies:
    pip install -r requirements.txt
3. Configure credentials: Add your BrightData credentials and RapidAPI key in a .env file or directly in the script.

 4.Run the script: python main.py
