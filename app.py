import os
import requests
from flask import Flask, request, jsonify
from flasgger import Swagger

app = Flask(__name__)

# --- Configure Swagger ---
BASE_URL = os.environ.get("HEROKU_APP_DEFAULT_DOMAIN_NAME", "localhost:5000")
swagger_template = {
    "openapi": "3.0.0",
    "info": {
        "title": "Notion Relay API",
        "version": "1.0",
        "description": "Relay endpoints for Notion integration"
    },
    "servers": [
        {"url": f"https://{BASE_URL}", "description": "Primary API server"}
    ],
    "components": {
        "schemas": {
            "Task": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string", "description": "The task Name (Title)"},
                    "description": {"type": "string", "description": "Detailed description of the task"},
                    "parent_task_id": {"type": "string", "description": "Notion page ID of the parent task (optional)"},
                    "child_task_ids": {"type": "array", "items": {"type": "string"}, "description": "List of Notion page IDs for child tasks (optional)"},
                    "task_group_id": {"type": "string", "description": "Notion page ID of the Task Group (optional)"}
                }
            }
        }
    }
}

swagger = Swagger(app, template=swagger_template)

# --- Notion credentials ---
NOTION_TOKEN   = os.environ["NOTION_TOKEN"]
DATABASE_ID    = os.environ["NOTION_DATABASE_ID"]
NOTION_VERSION = os.environ.get("NOTION_VERSION", "2022-06-28")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

@app.route('/add_task', methods=['POST'])
def add_task():
    """
    Create a new Task in Notion
    ---
    operationId: addTask
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Task'
    responses:
      200:
        description: Task created successfully
        content:
          application/json:
            schema:
              type: object
      400:
        description: Invalid input
    """
    data = request.get_json() or {}
    title          = data.get('title')
    description    = data.get('description')
    parent_task_id = data.get('parent_task_id')
    child_task_ids = data.get('child_task_ids', [])
    task_group_id  = data.get('task_group_id')

    props = {"Name": {"title": [{"text": {"content": title}}]}}
    if description:
        props['Description'] = {"rich_text": [{"text": {"content": description}}]}
    if parent_task_id:
        props['Parent task'] = {"relation": [{"id": parent_task_id}]}
    if child_task_ids:
        props['Child tasks'] = {"relation": [{"id": cid} for cid in child_task_ids]}
    if task_group_id:
        props['Task Group'] = {"relation": [{"id": task_group_id}]}

    payload = {"parent": {"database_id": DATABASE_ID}, "properties": props}
    resp = requests.post('https://api.notion.com/v1/pages', headers=HEADERS, json=payload)
    return jsonify(resp.json()), resp.status_code

@app.route('/list_tasks', methods=['GET'])
def list_tasks():
    """
    List existing tasks
    ---
    operationId: listTasks
    parameters:
      - in: query
        name: category
        schema:
          type: string
        description: Filter tasks by Category name (optional)
    responses:
      200:
        description: A list of tasks from Notion
        content:
          application/json:
            schema:
              type: object
    """
    category = request.args.get('category')
    query = {"page_size": 100}
    if category:
        query['filter'] = {"property": "Category", "multi_select": {"contains": category}}
    resp = requests.post(f'https://api.notion.com/v1/databases/{DATABASE_ID}/query', headers=HEADERS, json=query)
    return jsonify(resp.json()), resp.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
