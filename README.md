🚀 AI-Powered E-Commerce Product Description Generator
Final Submission – Internship Project
This project is an AI-based automated product description generator built using Python and the OpenAI API.
It creates SEO-optimized, marketing-ready, and platform-specific descriptions for e-commerce websites.

📌 Features Implemented
✅ 1. Product Description Generation
Extracts raw features
Generates:
Short Description
Long Description
Bullet Points
USP Highlights

✅ 2. SEO Optimization
Keyword extraction
SEO-friendly titles
Meta descriptions
Keyword density scoring
SEO improvement suggestions

✅ 3. Multi-Channel Output
For every product, the system generates:
Website-ready product description
Amazon-style listing components
Social media captions
Marketing taglines

✅ 4. Batch Generation (50+ Products)
A full automation script is included which:
Reads product list from CSV
Generates content for all products
Handles rate limits + auto retries
Saves outputs to:
/outputs/descriptions/*.json  
/outputs/seo_reports/*.json  
/outputs/combined/combined.csv  

✅ 5. Error Handling & Recovery
Smart JSON auto-repair
Exponential backoff
Automated retry logic
Clean logging system

📂 Folder Structure
product-description-generator/
│
├── generator.py
├── batch_generate.py
├── batch_generate_v2.py
├── model_client.py
├── seo_utils.py
├── extractor.py
├── sample_products.csv
│
├── outputs/
│   ├── descriptions/
│   ├── seo_reports/
│   └── combined/
│
├── logs/
└── README.md

🖼️ Project Visuals
📌 Codebase Overview
<img width="558" height="580" alt="image" src="[https://github.com/user-attachments/assets/4ed06676-0bb0-4f33-a97d-da54013ff1d7](https://github.com/user-attachments/assets/4ed06676-0bb0-4f33-a97d-da54013ff1d7)" />

📌 Output Example (JSON)
<img width="1800" height="863" alt="image" src="https://github.com/user-attachments/assets/c1e3b52b-86fa-48a0-8d4d-ef8a933c3768" />

📌 Batch Generator Running
<img width="944" height="759" alt="image" src="https://github.com/user-attachments/assets/755d0167-e42f-4cd6-983e-973462136ede" />
<img width="825" height="769" alt="image" src="https://github.com/user-attachments/assets/ea26e5f3-9803-4b23-8097-e3379b3e42da" />
<img width="822" height="466" alt="image" src="https://github.com/user-attachments/assets/fa5739ce-87e4-44cb-ae30-1218af49b291" />

▶️ How to Run the Project
1. Install requirements
pip install -r requirements.txt

2. Add API key to environment
export OPENAI_API_KEY=your_key_here

3. Run single product generation
python generator.py --name "Wireless Earbuds" --features "Bluetooth, ANC"

4. Run batch generation
python batch_generate_v2.py --input sample_products.csv --out outputs --delay 10

📦 Sample Output (Preview)
{
  "title": "Wireless Earbuds with Noise Cancellation",
  "short_description": "...",
  "long_description": "...",
  "bullets": [...],
  "keywords": [...],
  "seo_report": {...}
}


(Full outputs available inside the /outputs/ folder.)

🏁 Final Summary

This project successfully automates product content creation for e-commerce, reducing manual effort and improving SEO quality.
It is production-ready, scalable, and supports batch generation with full recovery from API errors.
