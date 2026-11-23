# Hosting SeeSound on seesound.org (Cloudflare)

Written 2026-11-03 by the assistant. **Nothing here has been run against your Cloudflare account or a server** (the files were checked for syntax only); follow it with Kiet and expect small fixes.

## What you get
| Address | What | Protected |
|---|---|---|
| `seesound.org` | one static page (`site/index.html`, Cloudflare Pages) | public, no data |
| `collect.seesound.org` | learner app (teachers use `/?page=collect`) | Cloudflare Access (invited e-mails only) |
| `admin.seesound.org` | Dev app (Rate, Log, ...) | Cloudflare Access (only the research team) |

The app runs on one server (Kiet's machine, a lab machine, or a VPS) in Docker. No port of the server is opened to the internet: a Cloudflare Tunnel connects out to Cloudflare, which gives you HTTPS (needed for the microphone) and the sign-in wall.

## Steps
1. **Server**: a computer with Docker, at least 8 GB RAM, 20 GB disk, always on during the sessions. A GPU is not needed.
2. **Code and model**: clone the repository; put the phone-recogniser checkpoint (folder with `pytorch_model.bin` and `vocab.json`, 1.2 GB, `facebook/wav2vec2-xlsr-53-espeak-cv-ft`) in `model/` at the repository root. `data/` is created by the program (recordings, profiles, logs).
3. **Cloudflare Tunnel**: Zero Trust dashboard > Networks > Tunnels > Create a tunnel (Cloudflared). Copy the token into `deploy/.env` (from `deploy/.env.example`). Under *Public hostnames* add `collect.seesound.org` -> `http://learner:8502` and `admin.seesound.org` -> `http://dev:8501`.
4. **Cloudflare Access** (Zero Trust > Access > Applications > Self-hosted): one application for `collect.seesound.org` allowing the teachers' e-mail addresses (one-time PIN to the e-mail), one for `admin.seesound.org` allowing only the research team. **Do this before starting the tunnel**, otherwise the apps are open to everyone (the Dev app has no login of its own, and the learner home page lists children's names).
5. **Start**: `docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d --build` from the repository root. Check `https://collect.seesound.org/?page=collect`.
6. **Landing page**: Cloudflare Pages > create a project from the repository, build output directory `site`, custom domain `seesound.org`.

## If the page loads but is stuck on "Please wait" (websocket)
Streamlit behind a proxy can refuse the websocket. Add to the `command` of both apps `--server.enableCORS=false --server.enableXsrfProtection=false` (only acceptable because Access sits in front), or set `--server.corsAllowedOrigins=https://collect.seesound.org`.

## Data and privacy (read with the consent form)
- Recordings and logs are in `data/` on the server. **Back them up** (encrypted copy to a second place), and delete a participant on request from Dev app > Rate > Export and delete. Retention in the consent form: 1 year.
- The camera-log server is switched off when hosted (`SEESOUND_CAMLOG=off`): a hosted browser cannot reach it.
- The consent form says where the data are kept. **If the server is a rented VPS or the teachers upload zips to a shared Google Drive folder, the wording "a research computer managed by Kiet Pham" is no longer accurate**: it now says a secure server managed by Kiet and a restricted shared folder; the ethics/department decision should confirm this. Make the Drive folder *restricted* (invited accounts, upload only for teachers), never "anyone with the link".

## Where to host
- **Pilot (recommended)**: Kiet's or a lab machine behind the tunnel. It matches the consent wording, costs nothing, and the data stay in your hands. Downside: it must be on during the sessions.
- **Later**: a small VPS (about 4 CPU and 8 GB RAM, roughly 20-40 USD a month; check prices), in a region the ethics decision allows. Same files, same steps.
- **Not suitable**: Cloudflare Workers/Pages for the apps themselves, Streamlit Community Cloud, Hugging Face Spaces (no room for the model, no durable private storage).

## Update
`git pull` then `docker compose ... up -d --build`. Streamlit keeps modules in memory, so a restart is needed after code changes.
