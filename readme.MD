# canvas-parent repo
This will automate fetching missing and upcoming assignments (like the dashboard page)

## requirements
This needs two environment variables
```
export CANVAS_AUTH_TOKEN=""
export CANVAS_BASE_URL="https://...com"
export CANVAS_USER_ID="12345"
```

## canvas information
- https://developerdocs.instructure.com/services/canvas/resources/planner
- https://developerdocs.instructure.com/services/canvas/oauth2/file.oauth#using-access-tokens

## TODO
- dates are hard coded
- pick up what has been turned in but not graded
