const {
  app,
  BrowserWindow,
  shell,
} = require("electron");

const path = require("path");

const isDev = process.argv.includes("--dev");

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
    win.loadFile(
      path.join(
        __dirname,
        "..",
        "dist",
        "index.html",
      ),
    );
  }
}

app.whenReady().then(() => {
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
