const {
  app,
  BrowserWindow,
  shell,
  protocol,
  net,
} = require("electron");

const path = require("path");
const { pathToFileURL } = require("url");

const isDev = process.argv.includes("--dev");
const APP_SCHEME = "glenmoniques-staff";
const APP_ORIGIN = "glenmoniques-staff://app";

protocol.registerSchemesAsPrivileged([
  {
    scheme: APP_SCHEME,
    privileges: {
      standard: true,
      secure: true,
      supportFetchAPI: true,
      corsEnabled: true,
    },
  },
]);

function registerAppProtocol() {
  const distRoot = path.resolve(
    __dirname,
    "..",
    "dist",
  );

  protocol.handle(
    APP_SCHEME,
    (request) => {
      const requestUrl = new URL(request.url);
      let relativePath = decodeURIComponent(
        requestUrl.pathname || "/",
      ).replace(/^\/+/, "");

      if (!relativePath) {
        relativePath = "index.html";
      }

      const candidate = path.resolve(
        distRoot,
        relativePath,
      );

      const insideDist =
        candidate === path.join(distRoot, "index.html") ||
        candidate.startsWith(distRoot + path.sep);

      if (!insideDist) {
        return new Response(
          "Forbidden",
          { status: 403 },
        );
      }

      return net.fetch(
        pathToFileURL(candidate).toString(),
      );
    },
  );
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1460,
    height: 920,
    minWidth: 1080,
    minHeight: 700,
    backgroundColor: "#edf1f4",
    title: "Glen Moniques Staff Portal",
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (
      url.startsWith("https://") ||
      url.startsWith("http://")
    ) {
      shell.openExternal(url);
    }

    return { action: "deny" };
  });

  if (isDev) {
    win.loadURL("http://127.0.0.1:5176");
    win.webContents.openDevTools({
      mode: "detach",
      activate: false,
    });
  } else {
    win.loadURL(
      `${APP_ORIGIN}/index.html`,
    );
  }
}

app.whenReady().then(() => {
  registerAppProtocol();
  createWindow();

  app.on("activate", () => {
    if (
      BrowserWindow.getAllWindows().length === 0
    ) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
