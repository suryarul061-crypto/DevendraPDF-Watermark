# Devendra Autocom Pvt Ltd — PDF Watermark Launcher

## What it does
- Handles a PDF passed by Windows file association.
- Writes a separate watermarked copy to `%LOCALAPPDATA%\DevendraPDF\Watermarked`.
- Adds `Logo.png` at the bottom-right of every page.
- Opens the watermarked copy in Adobe Reader when detected, otherwise Microsoft Edge (configurable).
- Never writes to the source PDF.
- Logs activity to `%LOCALAPPDATA%\DevendraPDF\Logs\launcher.log`.

## Limitations
- Only PDFs opened through this launcher are watermarked. Existing PDF viewer app buttons, browser built-in PDF viewers, email preview panes, and other paths that bypass this launcher are not intercepted.
- This does not bulk-process all existing PDFs automatically. Open them through the launcher or implement a separately approved batch run.
- Encrypted/password-protected PDFs and PDFs with detectable digital-signature fields are skipped. If signature metadata cannot be inspected reliably, the file is also skipped. The source is preserved.
- This starter project is unsigned. SmartScreen or antivirus may warn about an unsigned internally built EXE. Review and sign it before wider deployment if your organization uses code signing.
- Use only a company logo you are authorized to use.

## Build without installing Python on employee PCs
1. Create a private GitHub repository and upload this source folder, including `.github/workflows/build.yml`.
2. In GitHub, open Actions and run **Build Devendra PDF Watermark EXE** (or push to `main`).
3. Download artifact `DevendraPDF-Windows-x64`; extract `DevendraPDF.exe`.
4. Put the official transparent `Logo.png` beside `DevendraPDF.exe`.
5. Copy `DevendraPDF.exe`, `Logo.png`, `install.ps1`, and `uninstall.ps1` to a USB drive or secure internal share.

## Install on each PC (run as the intended Windows user)
1. Extract the four files into one folder, e.g. `C:\IT\DevendraPDF-Setup`.
2. Right-click Start > Terminal (Admin is not normally required for this per-user install). If script execution is restricted, use your approved IT process rather than changing the machine-wide policy.
3. Run:
   `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1`
4. Settings should open. Go to **Apps > Default apps**, search `.pdf`, and choose `DevendraPDF` if it appears. Windows intentionally requires user interaction to set the default.
5. Test a copy of a non-sensitive, unsigned, unencrypted multi-page PDF. Double-click it. The watermarked copy should open in Edge or Adobe Reader. Confirm the original's file size and modified time are unchanged.

## Per-PC viewer preference
Edit `%LOCALAPPDATA%\Programs\DevendraPDF\config.json`:
- `"viewer": "auto"` prefers Adobe Reader, then Edge.
- `"viewer": "edge"` prefers Edge.
- `"viewer": "acrobat"` prefers Adobe Reader.

If a particular Adobe installation is not detected, set `viewer` to `edge` or update `viewer_candidates()` in `main.py` for your approved installation path, then rebuild.

## Rollback
1. Settings > Apps > Default apps > search `.pdf` > choose the previous PDF viewer.
2. Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\uninstall.ps1`.
3. The uninstall script retains watermarked copies and logs. Delete `%LOCALAPPDATA%\DevendraPDF` manually only after your retention policy permits it.

## Notes
Windows 10/11 x64 is the intended target. Pilot on one PC first. Review the code and scan the EXE before wider deployment.


### Browser support

The launcher can open the generated watermarked PDF in Microsoft Edge or Google Chrome when installed. In mixed environments, `viewer: "auto"` prefers Edge, then Chrome, then Adobe Reader. This only applies to PDFs opened through this launcher; it does not intercept PDFs previewed inside unrelated apps or browser tabs.
