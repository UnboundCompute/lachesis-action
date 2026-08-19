# Lachesis demo — render with charmbracelet/vhs:
#   brew install vhs        # or: go install github.com/charmbracelet/vhs@latest
#   vhs demo/demo.tape      # writes demo/demo.gif
#
# Prereqs the tape assumes are already set up in the recording shell:
#   pip install "git+https://github.com/UnboundCompute/lachesis"
#   python3 -m tools.vendor_typescript   # (from a lachesis checkout)
# Point PROJECT at any small TS/Python/C project with a guard differential;
# the bundled lachesis fixture at
#   lachesis/frontends/typescript/fixtures/project
# is the canonical one and produces the output below.

Output demo/demo.gif
Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 700
Set Theme "Dracula"
Set TypingSpeed 45ms
Set Padding 24

Type "# 1. Build a code graph of the project"
Enter
Sleep 600ms
Type "lachesis-analyze ./project graph.kuzu --prune --incremental"
Enter
Sleep 2s

Type "# 2. Overview — one guard differential surfaced"
Enter
Sleep 500ms
Type "lachesis-query graph.kuzu overview --format text | grep -i 'guard differential'"
Enter
Sleep 1500ms
# ->  Guard differentials: 1

Type "# 3. Look at the handler that forgot the check"
Enter
Sleep 500ms
Type "lachesis-query graph.kuzu handler-security getDocument --format text"
Enter
Sleep 2s
# ->  status: UNGUARDED   differential_siblings: [\"getInvoice\"]
#     getInvoice guards the identical sink; getDocument does not.

Sleep 2500ms
