# GCP Cloud Cost Optimizer - Demo Mode
# Run without GCP credentials - uses sample data for testing

python billing_collector.py

# Start the web dashboard
streamlit run app.py

# Or combine both
python -m streamlit run app.py --server.headless false
