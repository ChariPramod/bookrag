# Eval set changelog

v1 → v2. Format changed from a flat `gold` list to `evidence` (a list of
pieces; a piece is found if *any* of its paragraphs is retrieved — see
`docs/adr/0003-evidence-pieces.md`). Every question was re-audited against
the parsed text with `eval/audit.py`, `eval/find.py`, and `eval/show.py`
before this version was written. Question wording was never changed —
only evidence locations, answer text, and one question type.

- **hod-02**: evidence `[1,18],[1,26]` → `[1,18]`. `[1,26]` is the aunt
  goodbye-tea scene; it doesn't independently explain *how* she got him
  the job, only that he said goodbye to her. `[1,18]` alone contains the
  mechanism ("She wrote... determined to make no end of fuss to get me
  appointed").
- **hod-08**: evidence `[3,0]` → two pieces, `[2,33]` and `[3,16]`. The word
  "harlequin" itself — the actual nickname the question asks about — never
  appears in chapter 3. It's used twice in `[2,33]` ("He looked like a
  harlequin... The harlequin on the bank"). `[3,16]` independently uses
  "the man of patches" as an equivalent epithet. `[3,0]` ("in motley") was
  dropped: evocative, but it doesn't name him with anything nickname-like.
  Answer text expanded to mention both epithets.
- **pp-03**: evidence `[22,2]` → `[22,0],[22,1]` (one piece). `[22,0]`
  states the fact the question is really about — "its object was nothing
  less than to secure her from any return of Mr. Collins's addresses...
  Such was Miss Lucas's scheme" — which the old solo paragraph only
  implied.
- **pp-04**: evidence `[56,47],[56,66]` → `[56,46],[56,57],[56,66]` (one
  piece). Neither original paragraph actually contains the demand; both
  are reaction lines around it. `[56,57]` — "will you promise me never to
  enter into such an engagement?" — is the demand itself and was missing
  entirely.
- **pp-09**: evidence `[35,4]` → two pieces, `[35,4]` and `[36,5],[36,6]`.
  The old gold was the letter's raw text, not what makes Elizabeth
  *doubt her judgment* — that's her rereading and reaction two chapters
  later ("she had been blind, partial, prejudiced, absurd"), added as a
  second, independently-sufficient piece.
- **pp-12**: added `[36,5],[36,6]` as a piece, for the same reason as pp-09
  — the thematic arc this question asks about isn't complete without the
  reconsideration scene.
- **sh-04**: evidence `[5,51]` → `[5,129],[5,132]`. The old paragraph only
  contains the initials "K.K.K."; it never says what they stand for. The
  question asks what organization is *signified* — that's answered when
  Holmes names "the Ku Klux Klan" and gives its definition.
- **sh-05 / sh-11**: evidence `[2,210]` → `[2,207],[2,208],[2,210]` (one
  piece) for both questions. Holmes's tunnel explanation spans several
  paragraphs (`[2,207]`: "running a tunnel to some other building";
  `[2,208]`: the bank abuts the premises; `[2,210]`: the tunnel is
  complete) — the old gold only had the last beat of it.
- **sh-06**: evidence `[3,127]` → two pieces, `[3,115],[3,117],[3,119],
  [3,121]` (the live typewriter-evidence reveal scene, ending "I have
  caught him!") and `[3,135]` (Holmes's later retrospective explanation
  to Watson, independently sufficient on its own). The old paragraph was
  about *why Mary didn't suspect* the con, not the unmasking itself.
  Answer text expanded to name the mechanism (typewriter match).
- **sh-07**: evidence `[6,74]` → `[6,196],[6,197]`. The old paragraph is
  Holmes and Watson discussing Boone *before* the reveal. The actual
  unmasking — "Let me introduce you to Mr. Neville St. Clair" and the
  disguise coming off — is `[6,196]`-`[6,197]`.
- **sh-12 / sh-13**: evidence updated to point at the corrected sh-06/sh-07
  locations above, since these questions reuse that evidence.
- **sh-14**: type `thematic` → `factual`. It's answered by one quoted line
  ("It is a capital mistake to theorise before one has data"), not a
  cross-passage theme.
- **sh-16** (new): not-in-book question, "What is Mrs. Hudson's first
  name?" — verified with `find.py` that she's never given one. Brings
  not-in-book questions to 2 per book (6 total), matching hod and pp.

No paragraph was found to be outright wrong (containing something other
than what the answer claims) — every fix above was either a gold location
that was topically adjacent but didn't independently contain the answer,
or a piece missing from a multi-paragraph answer.
