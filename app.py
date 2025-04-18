import os
import requests
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields

app = Flask(__name__)

# Initialize Flask-RestX API
api = Api(
    app,
    version="1.0",
    title="Notion Relay API",
    description="Relay endpoints for Notion integration",
    doc="/docs"
)

# Notion credentials from env
NOTION_TOKEN   = os.environ["NOTION_TOKEN"]
DATABASE_ID    = os.environ["NOTION_DATABASE_ID"]
NOTION_VERSION = os.environ.get("NOTION_VERSION", "2022-06-28")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

# Define the Task input model for documentation
task_model = api.model("Task", {
    "title": fields.String(required=True, description="The task Name (Title)"),
    "description": fields.String(description="Detailed description of the task"),
    "parent_task_id": fields.String(description="ID of parent task (optional)"),
    "child_task_ids": fields.List(fields.String, description="List of child task IDs (optional)"),
    "task_group_id": fields.String(description="ID of the Task Group (optional)")
})

@api.route("/add_task")
class AddTask(Resource):
    @api.expect(task_model)
    @api.response(200, "Task created successfully")
    @api.response(400, "Invalid input")
    def post(self):
        data = request.get_json()
        title          = data.get("title")
        description    = data.get("description")
        parent_task_id = data.get("parent_task_id")
        child_task_ids = data.get("child_task_ids", [])
        task_group_id  = data.get("task_group_id")

        props = {
            "Name": {"title": [{"text": {"content": title}}]}
        }
        if description:
            props["Description"] = {"rich_text": [{"text": {"content": description}}]}
        if parent_task_id:
            props["Parent task"] = {"relation": [{"id": parent_task_id}]}
        if child_task_ids:
            props["Child tasks"] = {"relation": [{"id": cid} for cid in child_task_ids]}
        if task_group_id:
            props["Task Group"] = {"relation": [{"id": task_group_id}]}

        payload = {"parent": {"database_id": DATABASE_ID}, "properties": props}
        resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
        return jsonify(resp.json()), resp.status_code

@api.route("/list_tasks")
class ListTasks(Resource):
    @api.doc(params={"category": "Filter by Category name (optional)"})
    def get(self):
        category = request.args.get("category")
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

# Endpoint to serve the OpenAPI (Swagger) JSON
@app.route("/openapi.json")
def openapi_json():
    return jsonify(api.__schema__)

if __name__ == "__main__":
    app.run()
