# Vessel Finder Deployment

This folder is ready to deploy as a Node web service.

## Files
- `vessel-finder-start.html`
- `vessel-finder-server.js`
- `package.json`
- `render.yaml`

## Render steps
1. Create a new Web Service.
2. Point it at this folder or upload these files to a repo.
3. Use `npm install` as the build command.
4. Use `npm start` as the start command.
5. Set the service port from the platform if needed. The app reads `PORT`.

## Important
- The app needs a public web host to reach AISStream.
- A local file or `127.0.0.1` URL will not work for real AIS connectivity.
- Add the AISStream API key in the app after deployment.

## Expected result
- The page loads from a public URL.
- `실시간 연결` stores the key on the server.
- MMSI-based current location updates can then work when AISStream data is available.
