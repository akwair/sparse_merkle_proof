# Post-run execution and transfer notes

The third-platform supplement was registered on the server at 2026-10-23T08:58:21.055059+00:00, before dispatch. Its SHA256 is `9cf8be6c0d68bb285966a542aa1d622ffec8eec9ee178d769690f73672eed35f`; all 42 registered files remain unchanged. The original Round5 84-file registration and Linux executables were reused unchanged.

The single formal attempt used `../round5/runs/linux_host3_001` and `../round5/launches/linux.dxXR86tS`. Actual launcher and runner exits were zero. The supplement's completion links its source snapshot to the formal completion. No rerun, observation removal, threshold change or timed-path change was made.

Before deployment, review found and corrected gaps in the external provenance wrapper: it now verifies the full original registered source manifest before invoking the old validator, and checks the resolved destinations, including the exact formal work directory, before dispatch. Focused failing and passing tests were retained. The first prepared transfer archive was superseded before extraction by `inputs_002.tar.gz`; neither preparation was a formal experiment. The 13 final helper tests passed locally and on the server before registration.

The returned archive contained 1739 files and had SHA256 `c72b7c0e3e180700f1cb08b34f07752afa3758538844ddeb79ac6b1334a9d37f`. Extraction checked all paths and required existing files to be byte-identical; only new files were created. The local common log retained its full previous prefix and appended 10,787 bytes from the remote log. `REMOTE_ALL_RUNS.log` preserves the complete received snapshot.

Both independent audits succeeded and agree in every field except their filesystem locations. The locally recomputed pairwise comparison is exactly equal to the remote comparison as parsed JSON. An initial byte-equality assertion failed because the unchanged Python serializer wrote CRLF on Windows and LF on Linux. Inspection found no differing JSON key, value or type; replacing CRLF with LF makes the files byte-identical. Both serialized files and their process exits are retained. This was a post-run serialization check, not an experimental failure or a change to the numerical analysis.

All server-side study materials, temporary files and caches reside under the authorized project directory. Credentials are not retained in study artifacts. The original preflight transfer transcription issue is separately documented in the registered validation notes.
