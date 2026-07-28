# Responsible use

This project is for personal archival and restoration workflows involving content I own or have permission to handle.

## What this tool is for

- Backing up my own Instagram highlight/story material.
- Restoring ordered local story media through a normal browser workflow.
- Keeping a local, reproducible workflow for archive maintenance.
- Experimenting with browser automation while keeping login and security decisions manual.

## What this tool is not for

- Scraping or republishing other people's content without permission.
- Bypassing login, verification, CAPTCHA, or platform safety checks.
- Collecting credentials, cookies, or session data.
- Running mass automation or growth/spam workflows.

## Design boundaries

- Authentication stays manual in Chrome.
- The scripts do not ask for passwords.
- Browser profile folders, cookies, sessions, caches, downloads, and exported media are ignored by Git.
- The restore workflow depends on the user controlling the browser and extension page.

## Operational notes

- Use dry-run mode before restoring a folder.
- Keep PyAutoGUI failsafe enabled.
- Be ready to stop the script with `Ctrl+C`.
- Expect maintenance when Instagram or extension UI changes.
