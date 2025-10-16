// electron/preload.cjs (CommonJS)
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('app', {
    hello: () => 'Hello from preload (isolated, safe)',
});
