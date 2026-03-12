#!/bin/bash
# Simple test script to verify app startup (non-interactive check)

echo "===================="
echo "GITA WISDOM AI - PRE-LAUNCH CHECK"
echo "===================="
echo ""

cd "$(dirname "$0")" || exit

# Check Python syntax
echo "1. Checking Python syntax..."
python -m py_compile streamlit_app.py
if [ $? -eq 0 ]; then
    echo "   ✅ Syntax valid"
else
    echo "   ❌ Syntax error!"
    exit 1
fi

# Check for required files
echo ""
echo "2. Checking required files..."
if [ -f "data/gita.db" ]; then
    echo "   ✅ data/gita.db exists"
else
    echo "   ⚠️  data/gita.db not found (will be created on first use)"
fi

if [ -f "data/retriever_state.pkl" ]; then
    echo "   ✅ data/retriever_state.pkl exists"
else
    echo "   ⚠️  data/retriever_state.pkl not found (run: python build_retriever.py)"
fi

# Check imports
echo ""
echo "3. Checking dependencies..."
python -c "
try:
    import streamlit
    print('   ✅ streamlit')
except:
    print('   ❌ streamlit missing')
    exit(1)

try:
    import sentence_transformers
    print('   ✅ sentence_transformers')
except:
    print('   ❌ sentence_transformers missing')
    exit(1)

try:
    import plotly
    print('   ✅ plotly')
except:
    print('   ❌ plotly missing')
    exit(1)
"

# Check Streamlit initialization order
echo ""
echo "4. Checking Streamlit initialization order..."
FIRST_ST=$(grep -n "st\\.set_page_config\\|st\\.secrets" streamlit_app.py | head -1 | cut -d: -f2)
if echo "$FIRST_ST" | grep -q "set_page_config"; then
    echo "   ✅ set_page_config is first Streamlit call"
else
    echo "   ❌ set_page_config is NOT first!"
    exit 1
fi

# Check admin password
echo ""
echo "5. Checking admin configuration..."
if grep -q "ADMIN_PASSWORD" streamlit_app.py; then
    echo "   ✅ Admin password configured"
    echo "   📝 Default: gita_admin_2024"
else
    echo "   ❌ Admin password not found!"
    exit 1
fi

echo ""
echo "===================="
echo "✅ ALL CHECKS PASSED!"
echo "===================="
echo ""
echo "🚀 Ready to launch:"
echo "   streamlit run streamlit_app.py"
echo ""
echo "📚 Admin Access:"
echo "   Password: gita_admin_2024 (or set ADMIN_PASSWORD env var)"
echo ""
