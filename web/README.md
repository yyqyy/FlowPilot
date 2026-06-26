# FlowPilot Studio (web editor)

A browser-based visual editor for FlowPilot automation workflows. You build a workflow by
dragging nodes and connecting them, then **export a self-contained Python script** that runs the
automation locally — fast (OpenCV template matching) and precise (direct input control).

The browser is only the editor. The exported script is the runtime, so no desktop GUI framework is
involved and nothing runs your mouse/keyboard until you run that script yourself.

## Stack

- [Vite](https://vite.dev/) + React + TypeScript
- [@xyflow/react](https://reactflow.dev/) for the node canvas
- [zustand](https://github.com/pmndrs/zustand) for state, Tailwind CSS for styling

## Develop

```powershell
cd web
npm install
npm run dev      # http://localhost:5173
```

```powershell
npm run build    # type-check + production build into dist/
npm run preview  # serve the production build
```

## How export works

`Export script` walks the graph from **Start** along one outgoing edge per node and emits a
standalone `*.py`. Run it with:

```powershell
pip install opencv-python mss numpy pyautogui
python your-workflow.py
```

Node types map to the script as follows:

| Node | Generated behavior |
| --- | --- |
| Find image | `cv2.matchTemplate` (TM_CCOEFF_NORMED); stops if below the confidence threshold |
| Click | `pyautogui.click` at a fixed point or the last image match |
| Type text | `pyautogui.write` |
| Delay | `time.sleep(random.uniform(min, max))` |

### Template images

Pick an image with the inspector button, or drag an image file onto the canvas to drop in a
ready-made Find image node. Browsers cannot expose a selected file's real path, so the picked image
is **embedded** into the workflow (base64) and decoded in memory by the exported script
(`cv2.imdecode`) — no path is needed and the script stays self-contained. You can still type an
on-disk path instead, which the script reads with `cv2.imread`.

The script enables PyAutoGUI's fail-safe: slam the mouse into a screen corner to abort. It also
waits 3 seconds before the first action so you can switch to the target window.

## Safety

Only automate software, accounts, and devices you own or are authorized to use. Do not use the
exported scripts to bypass anti-cheat, CAPTCHAs, access controls, or a service's rules.
