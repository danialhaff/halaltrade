import re

# 1. Append CSS rule for inline grids
css_append = """
@media (max-width: 768px) {
  /* Override React inline grid styles on mobile */
  div[style*="grid-template-columns"] {
    grid-template-columns: 1fr !important;
  }
}
"""
with open('frontend/src/index.css', 'a', encoding='utf-8') as f:
    f.write(css_append)

# 2. Wrap tables in App.jsx
with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('<table className="data-table"', '<div className="table-responsive"><table className="data-table"')
content = content.replace('</table>', '</table></div>')

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
