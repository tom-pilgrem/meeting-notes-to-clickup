import clickup, json

result = clickup.create_task({
    "title": "Pipeline test task",
    "assignee": "Tom Pilgrem",
    "priority": "normal",
})
print(json.dumps(result, indent=2))