# Claude cloud photo uploads

The ELIOS photo uploader is a small hosted MCP tool. Claude fills the Figma wrappers and obtains
single-use upload URLs with Figma `upload_assets`; this service transfers the existing issue photo
from GitHub to those slots. The transfer runs on the service, independently of Claude's shell.

Endpoint: `https://elios-guide-photo-uploader.nearbyelk1.chatgpt.site/claude-mcp`

In Claude, add a custom connector named **ELIOS photo uploader** with this endpoint. Choose **No sign-in**, then add a required `authorization` request header with value
`Bearer <uploader credential>` supplied at setup; never put a credential in this repository or the task
prompt. Enable the connector alongside GitHub publishing and Figma in both scheduled tasks.

The tool `upload_guide_photo` takes `date`, `commit_sha`, `slot`, and one or two `uploads`, each
containing `language`, `node_id`, and the fresh `submit_url`. It verifies that the requested commit’s content and photo bytes still match the current guide branch,
both language files, the nonempty passing fact-check report, the shared photo filename and licence,
the image signature and its 10 MB limit. It rejects arbitrary destinations and redirects. Returned
results include the file hash and per-language placement status. Partial failures are reported;
single-use URLs are not retried or included in results.

The service transports the selected image; it does not judge whether a photograph is appropriate.
Claude must inspect the actual image and both filled wrappers. A required photo failure blocks the
Figma completion commit. Fix the photo in the issue branch, revalidate it, then retry with fresh URLs.

Do not queue a rebuild until the connector passes a real upload test in Claude. For a previously
filled issue, a date in `automation/rebuild.txt` requests a refill of that same issue, not a new date.
Rebuilding with an unsuitable repository photo would repeat the unsuitable image.

The service is hosted with Sites. Its source is maintained in the Site's separate source repository;
the local checkout is `.local-sites/elios-photo-uploader`. Run `node --test` there. The site's
`UPLOADER_TOKEN` is a runtime secret. The service needs no GitHub or Figma API token: the repository
is public, and Figma's short-lived upload URL authorizes only the requested placement.

The hosted transfer was tested on 2026-11-09 with two temporary Figma frames. Both returned
success and their image fills matched the repository photo; the frames were removed afterward.
The service has 11 passing tests. This verifies the cloud transfer, not Claude’s connector setup
or whether the selected photograph is appropriate for the story.
