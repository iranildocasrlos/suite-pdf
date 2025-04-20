echo "mkdir -p ~/.streamlit/" > setup.sh
echo "echo \"[server]\nheadless = true\nport = \$PORT\nenableCORS = false\n\n[browser]\ngatherUsageStats = false\" > ~/.streamlit/config.toml" >> setup.sh
chmod +x setup.sh
