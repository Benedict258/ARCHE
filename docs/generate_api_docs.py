#!/usr/bin/env python3
"""Generate comprehensive API documentation from ARCHE endpoints."""

import json
from typing import Any, Dict, List
from api.main import app


class APIDocGenerator:
    """Generate API documentation from FastAPI app."""
    
    def __init__(self):
        self.app = app
        self.docs = {
            "title": app.title,
            "version": app.version,
            "description": app.description,
            "openapi": app.openapi(),
            "endpoints": [],
        }
    
    def generate_markdown(self) -> str:
        """Generate markdown documentation."""
        md = f"# {self.app.title}\n\n"
        md += f"**Version**: {self.app.version}\n\n"
        
        if self.app.description:
            md += f"{self.app.description}\n\n"
        
        md += "## Endpoints\n\n"
        
        openapi = self.app.openapi()
        paths = openapi.get("paths", {})
        
        for path, methods in paths.items():
            md += f"### {path}\n\n"
            
            for method, details in methods.items():
                md += f"#### {method.upper()}\n\n"
                
                if "summary" in details:
                    md += f"**Summary**: {details['summary']}\n\n"
                
                if "description" in details:
                    md += f"**Description**: {details['description']}\n\n"
                
                # Request body
                if "requestBody" in details:
                    md += "**Request Body**:\n"
                    md += "```json\n"
                    req_schema = details["requestBody"]["content"]["application/json"]["schema"]
                    md += json.dumps(req_schema, indent=2)
                    md += "\n```\n\n"
                
                # Response
                if "responses" in details:
                    md += "**Responses**:\n\n"
                    for code, resp in details["responses"].items():
                        md += f"- **{code}**: {resp.get('description', 'N/A')}\n"
                    md += "\n"
                
                # Parameters
                if "parameters" in details:
                    md += "**Parameters**:\n\n"
                    for param in details["parameters"]:
                        md += f"- **{param['name']}** ({param['in']}): {param.get('description', 'N/A')}\n"
                    md += "\n"
                
                md += "---\n\n"
        
        return md
    
    def generate_postman_collection(self) -> Dict[str, Any]:
        """Generate Postman collection for testing."""
        openapi = self.app.openapi()
        paths = openapi.get("paths", {})
        
        items = []
        
        for path, methods in paths.items():
            for method, details in methods.items():
                request_body = None
                if "requestBody" in details:
                    req_schema = details["requestBody"]["content"]["application/json"]["schema"]
                    # Create example from schema
                    request_body = self._schema_to_example(req_schema)
                
                item = {
                    "name": f"{method.upper()} {path}",
                    "request": {
                        "method": method.upper(),
                        "url": "{{base_url}}" + path,
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json",
                                "type": "text",
                            }
                        ],
                    },
                    "response": [],
                }
                
                if request_body:
                    item["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(request_body, indent=2),
                    }
                
                items.append(item)
        
        return {
            "info": {
                "name": self.app.title,
                "description": self.app.description,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "http://127.0.0.1:8000",
                    "type": "string",
                }
            ],
            "item": items,
        }
    
    def _schema_to_example(self, schema: Dict) -> Any:
        """Convert JSON schema to example value."""
        if "example" in schema:
            return schema["example"]
        
        if schema.get("type") == "object":
            obj = {}
            for prop_name, prop_schema in schema.get("properties", {}).items():
                obj[prop_name] = self._schema_to_example(prop_schema)
            return obj
        
        if schema.get("type") == "array":
            items_schema = schema.get("items", {})
            return [self._schema_to_example(items_schema)]
        
        if schema.get("type") == "string":
            return "example_string"
        
        if schema.get("type") == "number":
            return 0.5
        
        if schema.get("type") == "integer":
            return 1
        
        if schema.get("type") == "boolean":
            return True
        
        return None


def main():
    """Generate documentation files."""
    gen = APIDocGenerator()
    
    # Generate Markdown
    md_content = gen.generate_markdown()
    with open("docs/API.md", "w") as f:
        f.write(md_content)
    print("✓ Generated docs/API.md")
    
    # Generate Postman collection
    postman_collection = gen.generate_postman_collection()
    with open("docs/ARCHE_Postman_Collection.json", "w") as f:
        json.dump(postman_collection, f, indent=2)
    print("✓ Generated docs/ARCHE_Postman_Collection.json")
    
    # Generate OpenAPI spec
    openapi_spec = gen.docs["openapi"]
    with open("docs/openapi.json", "w") as f:
        json.dump(openapi_spec, f, indent=2)
    print("✓ Generated docs/openapi.json")
    
    print("\n✅ Documentation generated successfully!")


if __name__ == "__main__":
    main()
