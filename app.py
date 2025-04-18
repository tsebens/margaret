import os
from copy import deepcopy

import requests
from flask_openapi3 import OpenAPI, Info, Schema, Server
from flask import jsonify

# --- API Info & Initialization ---
info = Info(
    title="Notion Relay API",
    version="1.0",
    description="Relay endpoints for Notion integration"
)
app = OpenAPI(
    __name__,
    info=info,
    servers=[
        Server(url='http://' + os.environ.get("HEROKU_APP_DEFAULT_DOMAIN_NAME"))
    ]
)

# --- Notion Credentials (from Heroku env) ---
NOTION_TOKEN   = os.environ["NOTION_TOKEN"]
DATABASE_ID    = os.environ["NOTION_DATABASE_ID"]
NOTION_VERSION = os.environ.get("NOTION_VERSION", "2022-06-28")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

# --- Pydantic Schema for Task Input ---
class Task(Schema):
    title: str
    description: str = None
    parent_task_id: str = None
    child_task_ids: list[str] = []
    task_group_id: str = None

# --- Endpoints ---
@app.post(
    "/add_task",
    summary="Create a new Task in Notion",
)
def add_task(body: Task):
    """
    Receives a Task object and creates a new page in the Notion Tasks DB.
    """
    props = {
        "Name": {"title": [{"text": {"content": body.title}}]}
    }
    if body.description:
        props["Description"] = {"rich_text": [{"text": {"content": body.description}}]}
    if body.parent_task_id:
        props["Parent task"] = {"relation": [{"id": body.parent_task_id}]}
    if body.child_task_ids:
        props["Child tasks"] = {"relation": [{"id": cid} for cid in body.child_task_ids]}
    if body.task_group_id:
        props["Task Group"] = {"relation": [{"id": body.task_group_id}]}

    payload = {"parent": {"database_id": DATABASE_ID}, "properties": props}
    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json=payload
    )
    return jsonify(resp.json()), resp.status_code

@app.get(
    "/list_tasks",
    summary="List existing tasks",
)
def list_tasks(category: str = None):
    """
    Optionally filters by multi-select Category. Returns the raw Notion DB query.
    """
    query = {"page_size": 100}
    if category:
        query["filter"] = {
            "property": "Category",
            "multi_select": {"contains": category}
        }
    resp = requests.post(
        f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
        headers=HEADERS,
        json=query
    )
    return jsonify(resp.json()), resp.status_code

