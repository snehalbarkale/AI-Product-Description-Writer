🚀 AI-Powered E-Commerce Product Description Generator
Final Submission — Internship Project
This project is an AI-based product description generator built using Python and the OpenAI API.
It automatically creates SEO-optimized, conversion-focused product descriptions for e-commerce platforms with minimal user input.

📌 Features Implemented
✅ 1. Description Generation
Extracts product features
Generates benefit-driven descriptions
Creates short + long descriptions
Produces clean bullet points
Identifies unique selling points (USPs)

✅ 2. SEO Optimization
Keyword extraction
SEO-optimized title generation
Meta description creation
Keyword density scoring
Suggestions for SEO improvement

✅ 3. Multi-Channel Output
For every product, the system generates:
Website-ready descriptions
Amazon-style listing bullets
Social media caption
Email marketing snippet

✅ 4. Batch Generation System (50+ Products Processed)
The batch script:
Reads input from CSV
Processes multiple products automatically
Handles rate limits safely
Saves all output into organized folders:
/outputs/descriptions/*.json
/outputs/seo_reports/*.json
/outputs/combined/combined.csv

🚀 5. Error Handling & LLM Recovery
Automatic retries with exponential backoff
JSON cleanup + repair using AI
Full resilience against API rate limits

🔧 Technical Requirements
Python 3.8+
OpenAI API Key

Libraries:
requests, argparse, json, csv, time, os

▶️ How to Run the Project
1. Install Dependencies
pip install -r requirements.txt
2. Set Your API Key
export OPENAI_API_KEY=your_key_here   # macOS / Linux
setx OPENAI_API_KEY "your_key_here"   # Windows
3. Run Single Product Generator
python generator.py --name "Product Name" --features "Feature1; Feature2; Feature3"
4. Run Batch Generator
python batch_generate_v2.py --input sample_products.csv --out outputs

📁 Project Output Summary
✔️ 48+ product descriptions generated
✔️ SEO reports saved
✔️ Combined CSV ready for upload or integration

🏁 Project Completed & Ready for Submission
This project demonstrates:
Strong Python skills
API integration
Automation ability

SEO-focused content generation

Error-tolerant, production-ready architecture
