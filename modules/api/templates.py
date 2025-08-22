"""
HTML templates for API documentation pages.
Extracted from main.py to improve code organization.
"""


def get_documentation_homepage_html(app_title: str, app_version: str) -> str:
    """Generate HTML for API documentation homepage."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{app_title} - API Documentation Center</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
                line-height: 1.6;
                color: #333;
            }}
            .header {{
                text-align: center;
                margin-bottom: 3rem;
                padding: 2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
            }}
            .cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin-bottom: 3rem;
            }}
            .card {{
                padding: 2rem;
                border: 1px solid #e1e5e9;
                border-radius: 8px;
                text-decoration: none;
                color: inherit;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-decoration: none;
            }}
            .card h3 {{
                margin-top: 0;
                color: #1976d2;
            }}
            .features {{
                background: #f8f9fa;
                padding: 2rem;
                border-radius: 8px;
            }}
            .feature-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-top: 1rem;
            }}
            .feature {{
                background: white;
                padding: 1.5rem;
                border-radius: 6px;
                border-left: 4px solid #1976d2;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 {app_title}</h1>
            <p>Intelligent Knowledge Management System</p>
            <p>Version: {app_version}</p>
        </div>
        
        <div class="cards">
            <a href="/docs" class="card">
                <h3>📊 Swagger UI</h3>
                <p>Interactive API documentation with testing support.</p>
                <p><strong>For</strong>: Developer testing, API exploration</p>
            </a>
            
            <a href="/redoc" class="card">
                <h3>📚 ReDoc</h3>
                <p>Beautiful documentation with optimized layout.</p>
                <p><strong>For</strong>: Documentation reading</p>
            </a>
            
            <a href="/openapi.json" class="card">
                <h3>⚙️ OpenAPI JSON</h3>
                <p>OpenAPI specification for code generation.</p>
                <p><strong>For</strong>: Tool integration</p>
            </a>
            
            <a href="/health" class="card">
                <h3>🏥 Health Check</h3>
                <p>System status and health monitoring.</p>
                <p><strong>For</strong>: System monitoring</p>
            </a>
        </div>
        
        <div class="features">
            <h2>🚀 Core Features</h2>
            <div class="feature-grid">
                <div class="feature">
                    <h4>📚 Document Processing</h4>
                    <p>Upload and process PDF, Word, TXT files with intelligent chunking.</p>
                </div>
                <div class="feature">
                    <h4>🏷️ Topic Management</h4>
                    <p>Create and organize knowledge topics with relationships.</p>
                </div>
                <div class="feature">
                    <h4>🔍 Semantic Search</h4>
                    <p>Advanced search with vector similarity and keyword matching.</p>
                </div>
                <div class="feature">
                    <h4>⚡ Async Processing</h4>
                    <p>High-performance async operations with task queues.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
