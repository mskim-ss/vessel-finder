# Vessel Finder

Public vessel tracking dashboard for monitoring ship status, current location, ETD, ETA, and AISStream live updates.

## Files
- `vessel-finder-start.html` - main UI
- `vessel-finder-server.js` - Node server for AISStream and API endpoints
- `package.json` - start script
- `render.yaml` - Render deployment config

## Local development
```bash
npm install
npm start
```

## Notes
- Keep `.vessel-finder-live.json` out of GitHub because it may contain saved local API data.
- Deploy as a Node web service on a public host to enable live AISStream connectivity.
