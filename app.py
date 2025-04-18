import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')
NOTION_VERSION = os.environ.get('NOTION_VERSION', '2022-06-28')

HEADERS = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Notion-Version': NOTION_VERSION,
    'Content-Type': 'application/json',
}

@app.route("/add_task", methods=["POST"])
def add_task():
    data           = request.get_json()
    title          = data.get("title")
    description    = data.get("description")
    parent_task_id = data.get("parent_task_id")       # single ID string
    child_task_ids = data.get("child_task_ids", [])   # list of ID strings
    task_group_id  = data.get("task_group_id")        # single ID string

    # Build the Notion payload
    props = {
        "Name": {
            "title": [{"text": {"content": title}}],
        }
    }
    if description:
        props["Description"] = {
            "rich_text": [{"text": {"content": description}}]
        }
    if parent_task_id:
        props["Parent task"] = {
            "relation": [{"id": parent_task_id}]
        }
    if child_task_ids:
        props["Child tasks"] = {
            "relation": [{"id": cid} for cid in child_task_ids]
        }
    if task_group_id:
        props["Task Group"] = {
            "relation": [{"id": task_group_id}]
        }

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": props
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json=payload
    )
    return jsonify(resp.json()), resp.status_code

@app.route('/list_tasks', methods=['GET'])
def list_tasks():
    category = request.args.get('category')
    query = {'page_size': 100}
    if category:
        query['filter'] = {
            'property': 'Category',
            'multi_select': {'contains': category}
        }

    resp = requests.post(
        f'https://api.notion.com/v1/databases/{DATABASE_ID}/query',
        headers=HEADERS,
        json=query
    )
    return jsonify(resp.json()), resp.status_code

if __name__ == '__main__':
    app.run()